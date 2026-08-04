"""Coordination layer: the state machine and the reliability patterns.

``Orchestrator`` is deliberately **not** re-exported here. It is the composition
root that wires this package to ``infra``, so importing it eagerly would create a
package-level cycle (``infra.mcp_client`` needs ``services.deadline``). Import it
from :mod:`police_thief.services.orchestrator` instead.
"""

from .deadline import DeadlineExpiredError, DeadlineTracker
from .inbound import HandshakeRejectedError, InboundHandler
from .phase_machine import GamePhaseMachine, IllegalTransitionError
from .watchdog import Watchdog

__all__ = [
    "DeadlineExpiredError",
    "DeadlineTracker",
    "GamePhaseMachine",
    "HandshakeRejectedError",
    "IllegalTransitionError",
    "InboundHandler",
    "Watchdog",
]
