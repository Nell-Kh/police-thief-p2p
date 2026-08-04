"""Assembling and dispatching the report email - draft or send, never spam.

Chapter 9.3.3's iron rules, in code: the report is a machine-readable JSON
*attachment* (a plaintext report is rejected and the round's points are
lost), the recipient comes from configuration, and an HTTP 429 from Google
is never answered with a blind retry - the send is surrendered to the
Gatekeeper's queue and waits for the next window. ``draft`` mode exercises
the whole pipeline while parking the message in Drafts, which is how the
system is rehearsed without mailing the lecturer.
"""

from __future__ import annotations

import base64
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

from ...shared.config_io import canonical_json
from ...shared.gatekeeper import Gatekeeper

MODE_DRAFT = "draft"
MODE_SEND = "send"


class RateLimitedError(RuntimeError):
    """Google said 429 - back off; the Gatekeeper queue owns the retry."""


def build_report_email(
    to_address: str, subject: str, body: str, attachment_name: str, payload: dict[str, Any]
) -> dict[str, str]:
    """A Gmail API message: short human note plus the JSON report attached.

    The attachment bytes are canonical JSON, so the mailed report hashes
    identically to the lifecycle file written to disk.
    """
    message = MIMEMultipart()
    message["to"] = to_address
    message["subject"] = subject
    message.attach(MIMEText(body))
    attachment = MIMEApplication(
        canonical_json(payload).encode("utf-8"), _subtype="json", name=attachment_name
    )
    attachment["Content-Disposition"] = f'attachment; filename="{attachment_name}"'
    message.attach(attachment)
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode("ascii")
    return {"raw": raw}


def _is_rate_limited(error: Exception) -> bool:
    """Whether an API error is Google's 429 Too Many Requests."""
    response = getattr(error, "resp", None)
    return getattr(response, "status", None) == 429


def configured_sender(
    manager: Any, service: Any, rate_limits_path: str = "config/rate_limits.json"
) -> GmailSender:
    """A GmailSender assembled purely from configuration - nothing hardcoded.

    Recipient and mode come from the ``[email]`` section of the private
    TOML; the Gatekeeper's limits come from the ``gmail`` service entry in
    ``config/rate_limits.json``.
    """
    from ...shared.config_io import read_json

    email_cfg = manager.private("email")
    limits = read_json(rate_limits_path)["rate_limits"]["services"]["gmail"]
    gatekeeper = Gatekeeper(
        requests_per_minute=int(limits["requests_per_minute"]),
        daily_quota=int(limits["daily_quota"]),
        queue_depth=int(limits["queue_depth"]),
    )
    return GmailSender(
        service,
        recipient=str(email_cfg["recipient"]),
        mode=str(email_cfg.get("mode", MODE_DRAFT)),
        gatekeeper=gatekeeper,
    )


class GmailSender:
    """One team's outgoing-report pipe: gates first, Gmail last."""

    def __init__(
        self,
        service: Any,
        recipient: str,
        mode: str = MODE_DRAFT,
        gatekeeper: Gatekeeper | None = None,
    ) -> None:
        """Wire the Gmail service behind the Gatekeeper.

        Args:
            service: the Gmail API service (or a test double).
            recipient: report destination, from ``[email]`` in the TOML.
            mode: ``draft`` (rehearsal) or ``send`` (the real league report).
            gatekeeper: the three-gate guard; ``None`` only in unit tests.
        """
        if mode not in (MODE_DRAFT, MODE_SEND):
            raise ValueError(f"unknown email mode: {mode!r}")
        self._service = service
        self.recipient = recipient
        self.mode = mode
        self._gatekeeper = gatekeeper

    def send_report(
        self, subject: str, body: str, attachment_name: str, payload: dict[str, Any]
    ) -> str:
        """Build the report email and push it through the gates.

        Returns:
            The Gatekeeper status (``sent``/``queued``/``locked``), or
            ``sent`` when no Gatekeeper is wired (tests only).
        """
        message = build_report_email(self.recipient, subject, body, attachment_name, payload)
        if self._gatekeeper is None:
            self._dispatch(message)
            return "sent"
        return self._gatekeeper.execute(lambda: self._dispatch(message), label=attachment_name)

    def _dispatch(self, message: dict[str, str]) -> Any:
        """The actual API call - draft or send - with 429 turned into back-off."""
        try:
            if self.mode == MODE_DRAFT:
                request = self._service.users().drafts().create(
                    userId="me", body={"message": message}
                )
            else:
                request = self._service.users().messages().send(userId="me", body=message)
            return request.execute()
        except Exception as error:
            if _is_rate_limited(error):
                raise RateLimitedError("Gmail quota exceeded (HTTP 429); backing off") from error
            raise
