"""Read-only accessors onto an :class:`~.orchestrator.Orchestrator`'s wired parts.

A single concern, split out of ``orchestrator.py`` to keep that module under
the file-size cap: naming and exposing the subsystems ``Orchestrator.__init__``
already wired, plus the "current mini-game" convenience property. No logic of
its own - every accessor here just forwards to an attribute set by the class
that mixes this in.
"""

from __future__ import annotations

from ..domain.state import GameState
from ..infra.mcp_client import PeerClient
from ..sdk import SimulationSdk
from .inbound import InboundHandler
from .phase_machine import GamePhaseMachine
from .recovery import Recovery
from .watchdog import Watchdog


class OrchestratorAccessors:
    """Named, typed access to the subsystems an Orchestrator owns."""

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
