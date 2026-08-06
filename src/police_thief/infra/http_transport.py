"""The real network transport: MCP over HTTP to the opponent's public URL.

During early development the URL points at localhost; for league play it is the
opponent's tunnel URL (ngrok, Localtonet) - nothing else changes, which is the
point of the transport abstraction. Reliability lives one layer up: the
PeerClient wraps every call in a deadline and a bounded retry, and the
orchestrator converts exhaustion into a clean technical loss.
"""

from __future__ import annotations

import asyncio
from typing import Any

from .transport import TransportError


class McpHttpTransport:
    """Delivers protocol messages to a remote peer's FastMCP server."""

    def __init__(self, url: str) -> None:
        """Bind the transport to the opponent's MCP endpoint.

        Args:
            url: e.g. ``http://127.0.0.1:8802/mcp`` in development, or a
                public ``https://...ngrok...`` address in the league.
        """
        if not url.startswith(("http://", "https://")):
            raise TransportError(f"opponent URL must be http(s), got {url!r}")
        self._url = url

    @property
    def url(self) -> str:
        """The opponent endpoint this transport talks to."""
        return self._url

    def send(self, tool: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Call the opponent's ``tool`` with ``payload`` and return its reply.

        Each call opens a short-lived client session; at one call per game
        step, connection reuse is not worth the added state.

        Raises:
            TransportError: on any connection or protocol failure, so the
                PeerClient's retry-and-backoff can take over.
        """
        try:
            return asyncio.run(self._call(tool, payload))
        except TransportError:
            raise
        except Exception as error:
            raise TransportError(f"{tool}: transport failure ({error})") from error

    async def _call(self, tool: str, payload: dict[str, Any]) -> dict[str, Any]:
        """One async round-trip to the opponent's server."""
        try:
            from fastmcp import Client
        except ImportError as error:  # pragma: no cover - dependency is declared
            raise TransportError("fastmcp is required for network play") from error
        try:
            async with Client(self._url) as client:
                arg_name = "payload" if tool == "submit_audit" else "message"
                result = await client.call_tool(tool, {arg_name: payload})
        except Exception as error:
            raise TransportError(f"{tool}: call to {self._url} failed ({error})") from error
        return _extract_reply(result)


def _extract_reply(result: Any) -> dict[str, Any]:
    """Normalize a fastmcp call result into the plain dict our protocol uses."""
    data = getattr(result, "data", None)
    if isinstance(data, dict):
        return data
    structured = getattr(result, "structured_content", None)
    if isinstance(structured, dict):
        return structured.get("result", structured)
    raise TransportError(f"opponent returned an unreadable reply: {result!r}")
