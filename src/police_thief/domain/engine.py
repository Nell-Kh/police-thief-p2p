"""Turn application and termination detection.

The engine is the only place that mutates a :class:`GameState`. It validates
each action against the rules, applies it, and then asks whether the mini-game
has ended. Both peers run this same engine over the same signed contract, so
they reach identical conclusions without a referee.

Turn order is **cop first, then thief** - a documented choice (the rulebook does
not fix one), applied identically on both sides so the two logs agree.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..constants import MOVE_STAY, ROLE_POLICE, ROLE_THIEF
from ..shared.schema import GameContract
from .board import Cell
from .rules import IllegalBarrierError, is_trapped, validate_barrier, validate_move
from .scoring import capture, survival, technical_loss
from .state import GameState


@dataclass(frozen=True)
class Action:
    """What an agent does on its turn: a move, optionally plus a barrier.

    Only the cop may attach a barrier, and only when ``move`` is ``STAY``.
    """

    move: str
    barrier: Cell | None = None


class Engine:
    """Applies actions to a game state and decides when the game is over."""

    def __init__(self, contract: GameContract) -> None:
        """Bind the engine to the signed contract that defines the physics."""
        self._contract = contract

    @property
    def contract(self) -> GameContract:
        """The contract this engine enforces."""
        return self._contract

    def new_game(self) -> GameState:
        """Create a fresh game state at the contract's opening positions."""
        return GameState.from_contract(self._contract)

    def apply(self, state: GameState, role: str, action: Action) -> None:
        """Validate and apply one agent's action, then test for termination.

        Raises:
            IllegalMoveError: if the move is unknown, leaves the board, or enters a
                barrier.
            IllegalBarrierError: if a barrier placement breaks the barrier law, or if
                the thief attempts to place one at all.
        """
        if state.finished:
            return
        origin = state.position_of(role)
        target = validate_move(state.board, origin, action.move)
        state.set_position(role, target)
        if action.barrier is not None:
            self._place_barrier(state, role, action)
        state.record(f"step {state.step}: {role} plays {action.move}")
        self._check_termination(state)

    def _place_barrier(self, state: GameState, role: str, action: Action) -> None:
        """Apply a barrier placement declared alongside a ``STAY`` move.

        The placement is announced openly: the cop must declare every barrier
        and its exact location truthfully, so it is recorded in the history.
        """
        if role != ROLE_POLICE:
            raise IllegalBarrierError("only the cop may place barriers")
        cell = action.barrier
        if cell is None:  # pragma: no cover - guarded by the caller
            return
        validate_barrier(
            board=state.board,
            cop=state.cop,
            cell=cell,
            move=action.move,
            used=state.barriers_used,
            quota=self._contract.movement.max_barriers,
        )
        state.board.place_barrier(cell)
        state.barriers_used += 1
        state.record(f"step {state.step}: cop declares barrier at {cell}")

    def _check_termination(self, state: GameState) -> None:
        """Decide whether the mini-game has just ended."""
        scoring = self._contract.scoring
        if state.overlapping():
            state.outcome = capture(scoring, "the agents occupy the same cell")
        elif state.board.is_barrier(state.thief):
            state.outcome = capture(scoring, "a barrier was placed on the thief's cell")
        elif is_trapped(state.board, state.thief):
            state.outcome = capture(scoring, "the thief has no legal move left")

    def end_turn(self, state: GameState) -> None:
        """Close a full turn (both agents have acted) and test for survival."""
        if state.finished:
            return
        state.step += 1
        threshold = self._contract.movement.survival_threshold
        ceiling = self._contract.movement.max_moves
        if state.step >= min(threshold, ceiling):
            state.outcome = survival(
                self._contract.scoring,
                f"the thief survived {state.step} steps without capture",
            )

    def play_turn(self, state: GameState, cop: Action, thief: Action) -> None:
        """Apply a complete turn: the cop acts, then the thief, then the clock."""
        self.apply(state, ROLE_POLICE, cop)
        self.apply(state, ROLE_THIEF, thief)
        self.end_turn(state)

    def forfeit(self, state: GameState, reason: str) -> None:
        """End the game as a technical loss - a crash, timeout, or forgery."""
        state.outcome = technical_loss(self._contract.scoring, reason)
        state.record(f"technical loss: {reason}")


def stay() -> Action:
    """Convenience constructor for a plain ``STAY`` action."""
    return Action(move=MOVE_STAY)


def stay_and_block(cell: Cell) -> Action:
    """Convenience constructor for the cop's stay-and-place-a-barrier action."""
    return Action(move=MOVE_STAY, barrier=cell)


__all__ = ["Action", "Engine", "stay", "stay_and_block"]
