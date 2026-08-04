"""Inbound side over MCP: the tools this peer exposes to its opponent.

Every peer is simultaneously a server and a client - that symmetry is the whole
point of the peer-to-peer design, and MCP is the project's required standard, so
it is not swapped for anything else.

This module is a thin adapter: it registers one MCP tool per message kind and
forwards each straight to the :class:`InboundHandler`, which holds all the
logic. Keeping it thin is what lets the protocol be tested without a network.
"""

from __future__ import annotations

from typing import Any

from ..services.inbound import InboundHandler

#: The tool names a peer exposes; the client calls these by name.
TOOL_NAMES = ("handshake", "commit", "ack", "reveal", "capture_claim", "audit")


def build_server(handler: InboundHandler, name: str = "police_thief_peer") -> Any:
    """Create a FastMCP server exposing this peer's tools.

    Args:
        handler: the object that validates and records incoming messages.
        name: the server's MCP name.

    Returns:
        A configured ``FastMCP`` instance, ready to run over HTTP.

    Raises:
        RuntimeError: if the ``fastmcp`` package is unavailable.
    """
    try:
        from fastmcp import FastMCP
    except ImportError as error:  # pragma: no cover - dependency is declared
        raise RuntimeError("fastmcp is required to expose a peer server") from error

    mcp = FastMCP(name)

    @mcp.tool
    def handshake(payload: dict[str, Any]) -> dict[str, Any]:
        """Open a match: exchange contract digests and declared game counts."""
        return handler.handshake(payload)

    @mcp.tool
    def commit(payload: dict[str, Any]) -> dict[str, Any]:
        """Receive the opponent's sealed commitment for a step."""
        return handler.commit(payload)

    @mcp.tool
    def ack(payload: dict[str, Any]) -> dict[str, Any]:
        """Receive the opponent's acknowledgement of our commitment."""
        return handler.ack(payload)

    @mcp.tool
    def reveal(payload: dict[str, Any]) -> dict[str, Any]:
        """Receive a revealed move and verbal hint."""
        return handler.reveal(payload)

    @mcp.tool
    def capture_claim(payload: dict[str, Any]) -> dict[str, Any]:
        """Receive a capture claim, or the truthful answer to ours."""
        return handler.capture_claim(payload)

    @mcp.tool
    def audit(payload: dict[str, Any]) -> dict[str, Any]:
        """Receive the opponent's full log for the end-of-game audit."""
        return handler.audit(payload)

    return mcp


def serve(handler: InboundHandler, port: int, host: str = "0.0.0.0") -> None:  # noqa: S104
    """Run this peer's MCP server until the process stops.

    Bound to all interfaces so a tunnel (ngrok, Localtonet) can expose it to the
    public internet, which league play requires - localhost is only good enough
    during early development.
    """
    server = build_server(handler)
    server.run(transport="http", host=host, port=port)  # pragma: no cover - blocking call
