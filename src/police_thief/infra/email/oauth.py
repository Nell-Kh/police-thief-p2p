"""OAuth 2.0 for Gmail, at the least privilege the project can live on.

Appendix A, followed to the letter: the only scope ever requested is
``gmail.send`` - the reporting agent needs to send, so it must not be able
to read or delete. ``credentials.json`` (downloaded from the Cloud Console)
and ``token.json`` (created by the first authorization flow) are both
secrets and both git-ignored; pushing either equals publishing the mailbox
key. The Google libraries are imported lazily so the whole test suite runs
with the network mocked and no consent screen ever opens in CI.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

#: The single requested scope - send only, no read, no modify (Appendix A 1.3).
GMAIL_SEND_SCOPE = "https://www.googleapis.com/auth/gmail.send"


class CredentialsMissingError(FileNotFoundError):
    """Raised when ``credentials.json`` is absent - setup was skipped."""


def load_credentials(
    credentials_path: str | Path = "credentials.json",
    token_path: str | Path = "token.json",
) -> Any:
    """Return authorized user credentials, refreshing or minting as needed.

    The order mirrors Appendix A section 3: reuse ``token.json`` when it
    exists (refreshing a stale access token via the long-lived refresh
    token), and only fall back to the one-time browser consent flow when
    no token has ever been minted.

    Raises:
        CredentialsMissingError: if the consent flow is needed but the
            Cloud Console secret file is not present.
    """
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials

    token_file = Path(token_path)
    credentials = None
    if token_file.exists():
        credentials = Credentials.from_authorized_user_file(str(token_file), [GMAIL_SEND_SCOPE])
    if credentials and credentials.valid:
        return credentials
    if credentials and credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
    else:
        credentials = _run_consent_flow(credentials_path)
    token_file.write_text(credentials.to_json(), encoding="utf-8")
    return credentials


def _run_consent_flow(credentials_path: str | Path) -> Any:
    """The one-time browser authorization that creates the token pair."""
    from google_auth_oauthlib.flow import InstalledAppFlow

    secret_file = Path(credentials_path)
    if not secret_file.exists():
        raise CredentialsMissingError(
            f"{secret_file} not found - download it from the Cloud Console "
            "(Appendix A step 4) and keep it out of git"
        )
    flow = InstalledAppFlow.from_client_secrets_file(str(secret_file), [GMAIL_SEND_SCOPE])
    return flow.run_local_server(port=0)


def build_gmail_service(credentials: Any) -> Any:
    """The Gmail API service object used by the sender layer."""
    from googleapiclient.discovery import build

    return build("gmail", "v1", credentials=credentials)
