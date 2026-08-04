"""Gmail reporting infrastructure: OAuth, sending, and lifecycle reports.

Rulebook ch. 9.3 and Appendix A: after every counted game each side sends,
by itself, a machine-readable JSON report to the lecturer's report address.
The layer splits into :mod:`oauth` (send-only credentials), :mod:`sender`
(MIME assembly, draft/send modes, 429 back-off) and :mod:`reports` (the four
lifecycle JSON files). All outgoing traffic passes the Gatekeeper.
"""

from .oauth import GMAIL_SEND_SCOPE, load_credentials
from .reports import declaration_payload, result_payload, write_lifecycle_file
from .sender import GmailSender, RateLimitedError, build_report_email, configured_sender

__all__ = [
    "GMAIL_SEND_SCOPE",
    "GmailSender",
    "RateLimitedError",
    "build_report_email",
    "configured_sender",
    "declaration_payload",
    "load_credentials",
    "result_payload",
    "write_lifecycle_file",
]
