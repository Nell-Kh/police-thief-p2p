"""The legal state machine of a single game turn.

Every turn walks a fixed cycle, and only the transitions listed below are
possible. An illegal transition raises immediately rather than leaving the peer
in an undefined state, which is the first line of defence against deadlock: with
no central referee, two agents each waiting for the other would otherwise freeze
a match with no error at all (rulebook ch. 8.3).
"""

from __future__ import annotations

from ..constants import (
    PHASE_AWAITING_REVEAL,
    PHASE_COMMITTING,
    PHASE_COMPUTING,
    PHASE_TECHNICAL_LOSS,
    PHASE_VERIFYING,
    PHASE_WAITING,
)


class IllegalTransitionError(RuntimeError):
    """Raised when a phase transition is not permitted by the machine."""


class GamePhaseMachine:
    """Guards the order in which a turn's phases may occur."""

    #: Each phase maps to the set of phases it may legally move to.
    TRANSITIONS: dict[str, frozenset[str]] = {
        PHASE_WAITING: frozenset({PHASE_COMPUTING}),
        PHASE_COMPUTING: frozenset({PHASE_COMMITTING, PHASE_TECHNICAL_LOSS}),
        PHASE_COMMITTING: frozenset({PHASE_AWAITING_REVEAL}),
        PHASE_AWAITING_REVEAL: frozenset({PHASE_VERIFYING, PHASE_TECHNICAL_LOSS}),
        PHASE_VERIFYING: frozenset({PHASE_WAITING}),
        PHASE_TECHNICAL_LOSS: frozenset(),
    }

    def __init__(self, state: str = PHASE_WAITING) -> None:
        """Start the machine, by default waiting for the opponent.

        Raises:
            IllegalTransitionError: if ``state`` is not a known phase.
        """
        if state not in self.TRANSITIONS:
            raise IllegalTransitionError(f"unknown phase {state!r}")
        self._state = state
        self._trail: list[str] = [state]

    @property
    def state(self) -> str:
        """The phase the machine is currently in."""
        return self._state

    @property
    def trail(self) -> tuple[str, ...]:
        """Every phase visited so far, in order - useful for diagnostics."""
        return tuple(self._trail)

    @property
    def terminal(self) -> bool:
        """Whether the machine has reached a phase it can never leave."""
        return not self.TRANSITIONS[self._state]

    def can(self, target: str) -> bool:
        """Whether a transition to ``target`` would be legal right now."""
        return target in self.TRANSITIONS[self._state]

    def transition(self, target: str) -> str:
        """Move to ``target``.

        Returns:
            The new phase.

        Raises:
            IllegalTransitionError: if the transition is not in the table. A
                logic bug therefore surfaces as a visible error during
                development instead of a silent deadlock during a match.
        """
        if target not in self.TRANSITIONS:
            raise IllegalTransitionError(f"unknown phase {target!r}")
        if not self.can(target):
            raise IllegalTransitionError(f"illegal transition: {self._state} -> {target}")
        self._state = target
        self._trail.append(target)
        return self._state

    def fail(self) -> str:
        """Take the emergency exit to ``TECHNICAL_LOSS`` if one exists here.

        Called when the opponent disconnects or a deadline expires. From a phase
        with no emergency exit the machine is forced there anyway, because a
        peer that cannot continue must announce a result rather than hang.
        """
        if self.can(PHASE_TECHNICAL_LOSS):
            return self.transition(PHASE_TECHNICAL_LOSS)
        self._state = PHASE_TECHNICAL_LOSS
        self._trail.append(PHASE_TECHNICAL_LOSS)
        return self._state

    def start_turn(self) -> str:
        """Begin a new turn from the waiting phase."""
        return self.transition(PHASE_COMPUTING)

    def __repr__(self) -> str:
        """Developer-facing summary."""
        return f"GamePhaseMachine(state={self._state!r})"
