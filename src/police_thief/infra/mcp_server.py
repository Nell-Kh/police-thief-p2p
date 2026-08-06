"""Inbound side over MCP: the tools this peer exposes to its opponent.

Every peer is simultaneously a server and a client - that symmetry is the whole
point of the peer-to-peer design, and MCP is the project's required standard.
The tool set follows the reference implementation (ADR-7): ``negotiate``,
``receive_turn``, ``submit_audit`` and ``receive_control``. One asymmetry is
load-bearing (interop kit, verified against the reference): ``submit_audit``
takes ``payload`` while the other three take ``message`` - a peer that sends
the wrong keyword gets a schema fault, not a game. This module stays a thin
adapter over the :class:`InboundHandler`, which holds all the logic.
"""

from __future__ import annotations

from typing import Any

from ..services.inbound import InboundHandler

#: The tool names a peer exposes; the client calls these by name.
TOOL_NAMES = ("negotiate", "receive_turn", "submit_audit", "receive_control")


def build_server(handler: InboundHandler, name: str = "police_thief_peer") -> Any:
    """Create a FastMCP server exposing this peer's tools.

    Raises:
        RuntimeError: if the ``fastmcp`` package is unavailable.
    """
    try:
        from fastmcp import FastMCP
    except ImportError as error:  # pragma: no cover - dependency is declared
        raise RuntimeError("fastmcp is required to expose a peer server") from error

    mcp = FastMCP(name)

    @mcp.tool
    def negotiate(message: dict[str, Any]) -> dict[str, Any]:
        """Open a match: exchange locked terms (contract, scent model, counts)."""
        return handler.negotiate(message)

    @mcp.tool
    def receive_turn(message: dict[str, Any]) -> dict[str, Any]:
        """Receive one turn message; the turn token travels with it."""
        return handler.receive_turn(message)

    @mcp.tool
    def submit_audit(payload: dict[str, Any]) -> dict[str, Any]:
        """Receive the opponent's full end-of-game disclosure."""
        return handler.submit_audit(payload)

    @mcp.tool
    def receive_control(message: dict[str, Any]) -> dict[str, Any]:
        """Receive out-of-band signalling - the only channel a refusal can travel.

        Every tool in this wire shape returns ``{"ok": True}``, so a refusal
        cannot be a return value; it arrives as a pushed control message.
        """
        return handler.receive_control(message)

    return mcp


def serve(handler: InboundHandler, port: int, host: str = "0.0.0.0") -> None:  # noqa: S104
    """Run this peer's MCP server until the process stops.

    Bound to all interfaces so a tunnel (ngrok, Localtonet) can expose it to the
    public internet, which league play requires.
    """
    server = build_server(handler)
    server.run(transport="http", host=host, port=port)  # pragma: no cover - blocking call
