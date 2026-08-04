"""SimulationSdk - the single entry point to all business logic.

Every consumer (CLI, GUI, the peer runtime, tests, third-party integrations)
goes through this facade; none of them import domain modules directly and none
of them contain game logic of their own. That keeps the rules in one place and
makes the whole system callable from a single object.
"""

from __future__ import annotations

from pathlib import Path

from ..constants import ROLE_POLICE, ROLE_THIEF
from ..domain.board import Cell
from ..domain.engine import Action, Engine
from ..domain.rules import barrier_placements, legal_moves
from ..domain.scoring import Outcome, series_totals
from ..domain.state import GameState
from ..shared.config import ConfigManager
from ..shared.schema import GameContract


class SimulationSdk:
    """Facade exposing the game to every consumer."""

    def __init__(self, config: ConfigManager) -> None:
        """Bind the SDK to a loaded configuration."""
        self._config = config
        self._engine = Engine(config.contract)

    @classmethod
    def load(cls, role: str, config_dir: str | Path = "config") -> SimulationSdk:
        """Build an SDK for ``role`` from the configuration directory."""
        return cls(ConfigManager.load(role, config_dir))

    @property
    def role(self) -> str:
        """The role this peer plays."""
        return self._config.role

    @property
    def contract(self) -> GameContract:
        """The signed game contract in force."""
        return self._config.contract

    @property
    def config_sha256(self) -> str:
        """Digest of the contract, exchanged with the opponent before play."""
        return self._config.config_sha256

    def new_game(self) -> GameState:
        """Start a fresh mini-game at the contract's opening positions."""
        return self._engine.new_game()

    def legal_moves(self, state: GameState, role: str) -> list[str]:
        """The moves ``role`` may legally play from its current cell."""
        return legal_moves(state.board, state.position_of(role))

    def barrier_options(self, state: GameState) -> list[Cell]:
        """The cells the cop could block this turn, quota permitting."""
        if state.barriers_left(self.contract) <= 0:
            return []
        return barrier_placements(state.board, state.cop)

    def play_cop(self, state: GameState, move: str, barrier: Cell | None = None) -> None:
        """Apply the cop's action for this turn."""
        self._engine.apply(state, ROLE_POLICE, Action(move=move, barrier=barrier))

    def play_thief(self, state: GameState, move: str) -> None:
        """Apply the thief's action for this turn."""
        self._engine.apply(state, ROLE_THIEF, Action(move=move))

    def end_turn(self, state: GameState) -> None:
        """Close the turn once both agents have acted, and test for survival."""
        self._engine.end_turn(state)

    def forfeit(self, state: GameState, reason: str) -> None:
        """End the game as a technical loss."""
        self._engine.forfeit(state, reason)

    def outcome(self, state: GameState) -> Outcome | None:
        """The result of the mini-game, or ``None`` while it is still running."""
        return state.outcome

    def points(self, state: GameState, role: str) -> int:
        """Points ``role`` scored in a finished mini-game."""
        if state.outcome is None:
            raise ValueError("the mini-game has not finished yet")
        return state.outcome.points_for(role)

    @staticmethod
    def series_totals(outcomes: list[Outcome]) -> tuple[int, int]:
        """Cumulative cop and thief points across a series of mini-games."""
        return series_totals(outcomes)

    def opponent_role(self) -> str:
        """The role of the peer on the other side of the network."""
        return ROLE_THIEF if self.role == ROLE_POLICE else ROLE_POLICE
