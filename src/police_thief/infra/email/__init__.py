"""Gmail reporting infrastructure: OAuth, sending, and lifecycle reports.

Rulebook ch. 9.3 and Appendix A: after every counted game each side sends,
by itself, a machine-readable JSON report to the lecturer's report address.
The layer splits into :mod:`oauth` (send-only credentials), :mod:`sender`
(MIME assembly, draft/send modes, 429 back-off), :mod:`reports` (the league-
shaped lifecycle payloads), :mod:`consensus` (the settlement hash both teams
must match) and :mod:`naming` (file names and canonical bytes on disk). All
outgoing traffic passes the Gatekeeper.
"""

from .consensus import mutual_agreement_hash, mutual_agreement_scope, sign_report
from .naming import write_lifecycle_file
from .oauth import GMAIL_SEND_SCOPE, load_credentials
from .reports import declaration_payload, result_payload
from .sender import GmailSender, RateLimitedError, build_report_email, configured_sender

__all__ = [
    "GMAIL_SEND_SCOPE",
    "GmailSender",
    "RateLimitedError",
    "build_report_email",
    "configured_sender",
    "declaration_payload",
    "load_credentials",
    "mutual_agreement_hash",
    "mutual_agreement_scope",
    "result_payload",
    "sign_report",
    "write_lifecycle_file",
]
