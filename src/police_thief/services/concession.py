"""The trapped side's concession: the loss, sealed and truthfully announced.

Split out of :mod:`turn_taking` - conceding and answering a capture claim are
both "declare the truth when caught" (rule #21), not part of composing a
regular move turn.
"""

from __future__ import annotations

from ..domain.logbook import Logbook
from ..domain.turnmsg import TurnMessage, encode_scent
from .world_view import WorldView


def concession_message(*, view: WorldView, book: Logbook) -> TurnMessage:
    """The trapped thief's final message: the loss, sealed and announced.

    A trapping barrier (or a matching capture claim) ends the game on the
    thief's side of the wire - but the cop cannot see the thief's cell, so
    without this message the winner would never learn it won. The concession
    is sealed into the logbook like any turn, making a false concession (or a
    denied one) auditable, and travels as a ``win_claim`` naming the police.
    """
    record = book.append(
        {
            "step": view.step,
            "role": view.role,
            "type": "concession",
            "result": dict(view.result or {}),
        }
    )
    view.note("conceding the mini-game to the police")
    return TurnMessage(
        step=view.step,
        sender=view.role,
        hint="",
        smell_grid=encode_scent(view.my_scent.snapshot()),
        commit=record["commit"],
        claim_response={"claim": list(view.position), "caught": True},
    )


def answer_claim(view: WorldView) -> dict | None:
    """The thief's truthful answer to the cop's last capture claim."""
    if view.role != "thief" or view.pending_claim is None:
        return None
    claim = view.pending_claim
    view.pending_claim = None
    caught = tuple(claim) == view.position
    return {"claim": claim, "caught": caught}
