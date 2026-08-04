"""Construction of a peer's subsystems.

Kept apart from the :class:`Orchestrator` itself so that *wiring* and
*coordinating* stay separate concerns - and so both files stay well within the
150-line rule. Nothing here makes decisions; it only assembles.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from ..domain.negotiation import scent_lock_for
from ..infra.mcp_client import PeerClient
from ..infra.transport import Transport
from ..sdk import SimulationSdk
from ..shared.config import ConfigManager
from .inbound import InboundHandler
from .phase_machine import GamePhaseMachine
from .watchdog import Watchdog


@dataclass(frozen=True)
class Subsystems:
    """The five components an orchestrator coordinates."""

    sdk: SimulationSdk
    phases: GamePhaseMachine
    client: PeerClient
    inbound: InboundHandler
    watchdog: Watchdog


def build_subsystems(
    config: ConfigManager,
    transport: Transport,
    on_persist: Callable[[], None],
    on_shutdown: Callable[[], None],
) -> Subsystems:
    """Assemble one peer's subsystems from its configuration.

    Args:
        config: the loaded configuration for this role.
        transport: how messages reach the opponent.
        on_persist: watchdog callback saving state for later recovery.
        on_shutdown: watchdog callback releasing connections and closing logs.

    Returns:
        The assembled subsystems, ready for the orchestrator to coordinate.
    """
    sdk = SimulationSdk(config)
    contract = config.contract
    return Subsystems(
        sdk=sdk,
        phases=GamePhaseMachine(),
        client=PeerClient(transport, contract.network, contract.rate_limiter),
        inbound=InboundHandler(
            config_sha256=config.config_sha256,
            scent_lock=scent_lock_for(contract.pheromones),
            expect_role=sdk.opponent_role(),
        ),
        watchdog=Watchdog(
            timeout_sec=contract.network.watchdog_timeout_sec,
            on_persist=on_persist,
            on_shutdown=on_shutdown,
        ),
    )
