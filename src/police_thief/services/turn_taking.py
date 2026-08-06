"""Composing this peer's turn: decide, seal, and build the wire message.

The strategy brain decides the move (never the language model), the verbal
layer composes the hint under the signed word cap, the full truth is sealed
into the logbook, and only the public parts leave the machine: the commitment
hash, the hint, the scent grid, and the events the rules require to be open.
"""

from __future__ import annotations

from ..domain.board import Cell
from ..domain.brain.base import BrainBase
from ..domain.brain.pathfind import distance
from ..domain.logbook import Logbook
from ..domain.rules import validate_barrier, validate_move
from ..domain.sealing import turn_record
from ..domain.turnmsg import TurnMessage, encode_scent
from ..infra.llm import HintProvider, HintRequest, TokenLedger
from ..infra.llm.base import STYLE_DIRECTIONAL
from ..shared.schema import GameContract
from .deception import DeceptionPolicy
from .world_view import WorldView

#: Lie about our direction when the believed opponent is this close (BFS).
LIE_RANGE = 3


def choose_intent(view: WorldView) -> str:
    """Deterministic deception policy: lie when the hunt is close.

    The intent flag is sealed into the commitment either way - the choice is
    binding and auditable.
    """
    gap = distance(view.board, view.position, view.belief.argmax())
    return "lie" if 0 <= gap <= LIE_RANGE else "truth"


def take_turn(
    *,
    view: WorldView,
    contract: GameContract,
    brain: BrainBase,
    provider: HintProvider,
    ledger: TokenLedger,
    book: Logbook,
    policy: DeceptionPolicy | None = None,
) -> TurnMessage:
    """Play this peer's turn locally and return the message to send.

    Raises:
        IllegalMoveError / IllegalBarrierError: if the brain proposed an
            action the physics refuse - caught here, before anything leaves
            the machine, because each side enforces the rules on itself first.
    """
    action = brain.decide(view.brain_view(contract))
    barrier: Cell | None = action.barrier
    if barrier is not None:
        validate_barrier(
            board=view.board,
            cop=view.position,
            cell=barrier,
            move=action.move,
            used=view.barriers_used,
            quota=contract.movement.max_barriers,
        )
        view.board.place_barrier(barrier)
        view.barriers_used += 1
    view.position = validate_move(view.board, view.position, action.move)
    view.step += 1
    view.my_scent.advance(view.position)
    if policy is not None:
        _sync_claim_gaps(view, policy)
        intent, style = policy.choose()
    else:
        intent, style = choose_intent(view), STYLE_DIRECTIONAL
    direction = action.move if action.move != "STAY" else None
    tokens_before = ledger.total
    hint = provider.generate(
        HintRequest(
            role=view.role,
            intent=intent,
            true_direction=direction,
            map_area=contract.world.map_area,
            max_words=contract.world.hint_max_words,
            step=view.step,
            style=style,
        )
    )
    record = book.append(
        turn_record(
            step=view.step,
            role=view.role,
            grid_size=view.board.size,
            position=view.position,
            barriers=view.board.barriers,
            move=action.move,
            intent=intent,
            hint=hint,
            tokens_step=ledger.total - tokens_before,
            tokens_total=ledger.total,
        )
    )
    view.note(f"step {view.step}: played {action.move} ({intent})")
    survived = view.step >= contract.movement.survival_threshold
    return TurnMessage(
        step=view.step,
        sender=view.role,
        hint=hint,
        smell_grid=encode_scent(view.my_scent.snapshot()),
        commit=record["commit"],
        barrier_placed=list(barrier) if barrier is not None else None,
        capture_claim=list(view.position) if view.role == "police" else None,
        claim_response=_answer_claim(view),
        win_claim={"type": "survival"} if view.role == "thief" and survived else None,
    )


def _sync_claim_gaps(view: WorldView, policy: DeceptionPolicy) -> None:
    """Feed claim distances collected by the receive side into the policy."""
    while view.claim_gaps:
        policy.observe_claim_gap(view.claim_gaps.pop(0))


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


def _answer_claim(view: WorldView) -> dict | None:
    """The thief's truthful answer to the cop's last capture claim."""
    if view.role != "thief" or view.pending_claim is None:
        return None
    claim = view.pending_claim
    view.pending_claim = None
    caught = tuple(claim) == view.position
    return {"claim": claim, "caught": caught}
