"""The local match runner: brains driving a game through the SDK.

This is the single-process harness used for development, testing and the CLI
demo. It builds each side's :class:`BrainView` - the only window a brain gets -
asks the brain to decide, and applies the action through the SDK. The networked
turn loop (commit-reveal over MCP) reuses the same brains at the same plug
point; only the transport around them changes.
"""

from __future__ import annotations

from ..constants import ROLE_POLICE, ROLE_THIEF
from ..domain.brain.base import BrainBase, BrainView, load_brain
from ..domain.state import GameState
from ..sdk import SimulationSdk
from ..shared.config import ConfigManager

#: Default brains used when the private TOML names no [strategy] section.
DEFAULT_BRAINS = {
    ROLE_POLICE: "police_thief.domain.brain.blind:BlindPoliceBrain",
    ROLE_THIEF: "police_thief.domain.brain.blind:BlindThiefBrain",
}


def configured_brain(config: ConfigManager, role: str) -> BrainBase:
    """Load the brain the private TOML selects for ``role``.

    The ``[strategy]`` keys are ``police_class`` and ``thief_class``; an absent
    key falls back to the built-in default for that role.
    """
    key = f"{role}_class"
    spec = config.private_value("strategy", key, DEFAULT_BRAINS[role])
    return load_brain(spec, role, config.contract)


class LocalMatchRunner:
    """Runs a complete mini-game between two brains in one process."""

    def __init__(
        self,
        sdk: SimulationSdk,
        police_brain: BrainBase,
        thief_brain: BrainBase,
    ) -> None:
        """Bind the runner to an SDK and the two competing brains."""
        self._sdk = sdk
        self._brains = {ROLE_POLICE: police_brain, ROLE_THIEF: thief_brain}

    def view_for(self, state: GameState, role: str) -> BrainView:
        """Build the window a brain sees this turn.

        In the blind stage the target is the opponent's true cell; once belief
        maps exist, this is the seam where the argmax replaces the truth.
        """
        opponent = ROLE_THIEF if role == ROLE_POLICE else ROLE_POLICE
        return BrainView(
            role=role,
            position=state.position_of(role),
            target=state.position_of(opponent),
            board=state.board,
            barriers_left=state.barriers_left(self._sdk.contract),
            step=state.step,
        )

    def play_turn(self, state: GameState) -> None:
        """Play one full turn: the cop decides and acts, then the thief."""
        cop_action = self._brains[ROLE_POLICE].decide(self.view_for(state, ROLE_POLICE))
        self._sdk.play_cop(state, cop_action.move, cop_action.barrier)
        if not state.finished:
            thief_action = self._brains[ROLE_THIEF].decide(self.view_for(state, ROLE_THIEF))
            self._sdk.play_thief(state, thief_action.move)
        self._sdk.end_turn(state)

    def play(self, max_turns: int | None = None) -> GameState:
        """Play a whole mini-game and return its final state.

        Args:
            max_turns: safety stop for tests; the contract's step ceiling ends
                the game on its own in normal play.
        """
        state = self._sdk.new_game()
        turns = 0
        while not state.finished:
            self.play_turn(state)
            turns += 1
            if max_turns is not None and turns >= max_turns:
                break
        return state


def runner_from_config(config: ConfigManager) -> LocalMatchRunner:
    """Build a runner whose brains come from the private configuration."""
    return LocalMatchRunner(
        SimulationSdk(config),
        police_brain=configured_brain(config, ROLE_POLICE),
        thief_brain=configured_brain(config, ROLE_THIEF),
    )
