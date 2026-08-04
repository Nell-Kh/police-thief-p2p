"""Processing the opponent's turn message: inference, events, endings.

This is the receiving half of a turn: fold the transmitted scent into the
belief, judge the hint against it, apply the public events (a declared barrier,
a capture claim, its truthful answer, a survival claim), and decide whether the
mini-game just ended. The turn token travels with the message - once this
function returns, it is our turn.
"""

from __future__ import annotations

from ..domain.turnmsg import TurnMessage, decode_scent
from ..shared.schema import GameContract
from .world_view import WorldView


def receive_turn(view: WorldView, message: TurnMessage, contract: GameContract) -> None:
    """Fold one opponent turn into this peer's world view."""
    scent = decode_scent(message.smell_grid)
    view.belief.diffuse()
    view.belief.observe_scent(scent)
    appraisal = view.trust.appraise(message.hint, scent)
    if appraisal.region:
        view.belief.observe_region(appraisal.region, appraisal.factor)
    view.note(f"opponent step {message.step}: hint {appraisal.verdict}")
    _apply_barrier(view, message)
    _apply_capture_claim(view, message, contract)
    _apply_claim_response(view, message, contract)
    _apply_win_claim(view, message, contract)


def _apply_barrier(view: WorldView, message: TurnMessage) -> None:
    """A publicly declared barrier becomes part of our board too."""
    if message.barrier_placed is None:
        return
    cell = (message.barrier_placed[0], message.barrier_placed[1])
    if view.board.is_free(cell):
        view.board.place_barrier(cell)
        view.note(f"opponent declared a barrier at {cell}")
        if cell == view.position and view.role == "thief":
            view.result = {"type": "capture", "winner": "police", "how": "trapping barrier"}


def _apply_capture_claim(view: WorldView, message: TurnMessage, contract: GameContract) -> None:
    """The cop announced its cell; the thief must answer truthfully next turn.

    If the claim matches our cell, the game is over - the truth duty is
    absolute, and the audit would expose a lie anyway.
    """
    if message.capture_claim is None or view.role != "thief":
        return
    view.pending_claim = list(message.capture_claim)
    if tuple(message.capture_claim) == view.position:
        view.result = {"type": "capture", "winner": "police", "how": "capture claim"}
        view.note("caught - answering truthfully")


def _apply_claim_response(view: WorldView, message: TurnMessage, contract: GameContract) -> None:
    """The thief's truthful answer resolves the cop's last claim."""
    if message.claim_response is None or view.role != "police":
        return
    caught = bool(message.claim_response.get("caught"))
    claim = message.claim_response.get("claim")
    if caught:
        view.result = {"type": "capture", "winner": "police", "how": "capture claim"}
    elif isinstance(claim, list) and len(claim) == 2:
        # Negative evidence the reference throws away: that cell is ruled out.
        view.belief.exclude((int(claim[0]), int(claim[1])))
        view.note(f"claim at {tuple(claim)} answered: not there")


def _apply_win_claim(view: WorldView, message: TurnMessage, contract: GameContract) -> None:
    """A survival claim is accepted when the threshold has truly been reached."""
    if message.win_claim is None:
        return
    if message.win_claim.get("type") == "survival":
        if message.step >= contract.movement.survival_threshold:
            view.result = {"type": "survival", "winner": "thief"}
        else:
            view.note("premature survival claim ignored")
