"""The opening handshake retry loop: keep offering terms until answered.

Split out of :mod:`peer_boot` - this is the one piece of the boot sequence
with real retry/backoff logic; everything else in that module is straight-line
wiring.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from ..infra.mcp_client import PeerUnreachableError

if TYPE_CHECKING:
    from .orchestrator import Orchestrator


def rendezvous(
    orchestrator: Orchestrator,
    peer_id: str,
    games_played: int,
    wait_seconds: float,
    clock: Callable[[], float] = time.monotonic,
    announce: Callable[[str], None] = lambda _message: None,
) -> tuple[dict[str, Any] | None, str | None]:
    """Keep offering terms until the opponent answers or the window closes.

    Returns ``(reply, None)`` on a handshake, ``(None, None)`` when the window
    expired with the opponent still dark, and ``(None, detail)`` when the
    opponent answered but *refused* - a contract or lock mismatch, which no
    amount of retrying can fix and which must therefore stop the loop at once.

    A :class:`PeerUnreachableError` means "not started yet", not "lost", so it
    is caught and retried here rather than through
    :meth:`Orchestrator.run_guarded`: that helper drives the phase machine into
    ``TECHNICAL_LOSS`` - terminal, with no exits - on the very first miss,
    leaving nothing to retry with.
    """
    deadline = clock() + wait_seconds
    waited = False
    while True:
        try:
            return orchestrator.start_match(peer_id=peer_id, games_played=games_played), None
        except PeerUnreachableError:
            if clock() >= deadline:
                return None, None
            if not waited:
                announce("opponent not up yet - waiting for it to start...")
                waited = True
        except Exception as refusal:  # a refusal is an answer, not a silence
            return None, str(refusal)
