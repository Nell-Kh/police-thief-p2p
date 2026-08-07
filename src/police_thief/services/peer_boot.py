"""Booting one peer process: server thread up, orchestrator wired, handshake.

This is the two-process mode the separation rule demands: each role runs this
boot in its own process, with its own configuration directory, reachable at its
own port - and reaches its opponent only through the opponent's URL. The full
turn loop plugs in with the protocol layer; the boot already proves the pipe:
serve, connect, shake hands, and fail *cleanly* when the opponent never answers.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass

from ..infra.http_transport import McpHttpTransport
from ..infra.mcp_server import build_server
from ..shared.config import ConfigManager
from .orchestrator import Orchestrator


@dataclass(frozen=True)
class BootReport:
    """What happened when a peer booted and reached for its opponent."""

    role: str
    my_port: int
    opponent_url: str
    handshake_ok: bool
    detail: str


def build_peer(config: ConfigManager) -> Orchestrator:
    """Wire one peer's orchestrator against its configured opponent URL."""
    opponent_url = str(config.private_value("network", "opponent_url", ""))
    return Orchestrator(config, McpHttpTransport(opponent_url))


def start_server(orchestrator: Orchestrator, port: int, host: str = "0.0.0.0") -> threading.Thread:  # noqa: S104
    """Run this peer's MCP server in a daemon thread.

    Bound to all interfaces so a tunnel can expose it publicly; the thread dies
    with the process, and the watchdog owns crash handling above us.
    """
    server = build_server(orchestrator.inbound)

    def _serve() -> None:  # pragma: no cover - blocking network loop
        """Block forever running the FastMCP HTTP transport."""
        server.run(transport="http", host=host, port=port, show_banner=False)

    thread = threading.Thread(target=_serve, name=f"mcp-server-{port}", daemon=True)
    thread.start()
    return thread


def check_connectivity(config: ConfigManager, peer_id: str, games_played: int) -> BootReport:
    """Boot a peer, serve, and attempt the opening handshake once.

    This is the M5 probe: with the opponent reachable (localhost or through a
    tunnel), the handshake exchanges contract digests and game counts. With the
    opponent dark, the retry budget runs out and the peer reports a clean
    failure instead of hanging - exactly the behaviour the league requires.
    """
    my_port = int(config.private_value("network", "my_port", 8800))
    opponent_url = str(config.private_value("network", "opponent_url", ""))
    orchestrator = build_peer(config)
    start_server(orchestrator, my_port)
    try:
        reply = orchestrator.run_guarded(
            lambda: orchestrator.start_match(peer_id=peer_id, games_played=games_played)
        )
    except Exception as error:  # handshake rejection is a refusal, not a crash
        return BootReport(config.role, my_port, opponent_url, False, str(error))
    if reply is None:
        return BootReport(
            config.role,
            my_port,
            opponent_url,
            False,
            "opponent unreachable - technical loss declared cleanly",
        )
    known = orchestrator.inbound.opponent_games_played
    seen = f"; opponent declared {known} games" if known is not None else ""
    return BootReport(
        config.role, my_port, opponent_url, True, f"handshake accepted{seen}"
    )
