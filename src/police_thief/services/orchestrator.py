"""The Orchestrator: a single gateway to every subsystem of a peer.

Instead of each module knowing every other one - which breeds tangled mutual
dependency - all coordination passes through this one component. It owns the
MCP client, the inbound handler, the phase machine, the deadline tracker and the
watchdog, and it hands the game rules to the SDK. It contains **no** decision
logic and **no** low-level communication of its own: its job is to coordinate,
not to execute (rulebook ch. 8.3).
"""

from __future__ import annotations

from typing import Any

from ..constants import PHASE_TECHNICAL_LOSS
from ..domain.state import GameState
from ..infra.mcp_client import PeerClient, PeerUnreachableError
from ..infra.transport import Transport
from ..sdk import SimulationSdk
from ..shared.config import ConfigManager
from .deadline import DeadlineExpiredError
from .inbound import InboundHandler
from .phase_machine import GamePhaseMachine
from .recovery import Recovery
from .watchdog import Watchdog
from .wiring import build_subsystems


class Orchestrator:
    """Coordinates one peer's subsystems behind a single entry point."""

    def __init__(self, config: ConfigManager, transport: Transport) -> None:
        """Wire the subsystems for one peer.

        Args:
            config: the loaded configuration for this role.
            transport: how messages reach the opponent.
        """
        self._state: GameState | None = None
        self._recovery = Recovery()
        parts = build_subsystems(config, transport, self._persist, self._recovery.shutdown)
        self._sdk = parts.sdk
        self._phases = parts.phases
        self._client = parts.client
        self._inbound = parts.inbound
        self._watchdog = parts.watchdog

    @property
    def role(self) -> str:
        """The role this peer plays."""
        return self._sdk.role

    @property
    def sdk(self) -> SimulationSdk:
        """The business entry point holding the game rules."""
        return self._sdk

    @property
    def phases(self) -> GamePhaseMachine:
        """The turn state machine guarding legal transitions."""
        return self._phases

    @property
    def client(self) -> PeerClient:
        """The outbound side: calls to the opponent."""
        return self._client

    @property
    def inbound(self) -> InboundHandler:
        """The inbound side: messages from the opponent."""
        return self._inbound

    @property
    def watchdog(self) -> Watchdog:
        """The process guard that rescues state from a freeze."""
        return self._watchdog

    @property
    def state(self) -> GameState:
        """The current mini-game.

        Raises:
            RuntimeError: if no match has been started yet.
        """
        if self._state is None:
            raise RuntimeError("no match in progress; call start_match first")
        return self._state

    @property
    def recovery(self) -> Recovery:
        """The state the watchdog rescued, and whether shutdown ran."""
        return self._recovery

    def start_match(self, peer_id: str, games_played: int) -> dict[str, Any]:
        """Open a match: create the board and shake hands with the opponent.

        The handshake carries our contract digest and our declared game count,
        so a contract mismatch stops play before the first move.
        """
        self._state = self._sdk.new_game()
        self._watchdog.beat()
        return self._client.handshake(
            role=self.role,
            config_sha256=self._sdk.config_sha256,
            games_played=games_played,
            peer_id=peer_id,
        )

    def heartbeat(self) -> str:
        """Report liveness to the watchdog and get its verdict."""
        self._watchdog.beat()
        return self._watchdog.check()

    def guard(self) -> str:
        """Ask the watchdog whether the loop has frozen, without beating."""
        return self._watchdog.check()

    def fail(self, reason: str) -> None:
        """Take the emergency exit: technical loss, announced and recorded.

        A peer that cannot continue must announce a result rather than hang, so
        this is always reachable, from any phase.
        """
        self._phases.fail()
        if self._state is not None:
            self._sdk.forfeit(self._state, reason)

    def run_guarded(self, action: Any) -> Any:
        """Run a step of the turn, converting a stall into a technical loss.

        Any failure to reach the opponent - exhausted retries or an expired
        deadline - ends the turn cleanly instead of leaving it hanging.
        """
        try:
            return action()
        except (PeerUnreachableError, DeadlineExpiredError) as error:
            self.fail(str(error))
            return None

    @property
    def lost(self) -> bool:
        """Whether this peer has reached the terminal technical-loss phase."""
        return self._phases.state == PHASE_TECHNICAL_LOSS

    def _persist(self) -> None:
        """Watchdog callback: keep the state so the match can be recovered."""
        self._recovery.persist(self._state)
