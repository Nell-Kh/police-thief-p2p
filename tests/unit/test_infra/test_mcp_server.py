"""Tests for the MCP server adapter.

The adapter must stay thin: it registers one tool per message kind and forwards
each to the handler. These tests check the wiring, not the protocol logic, which
is covered against the handler directly.
"""

from __future__ import annotations

import asyncio

import pytest

from police_thief.infra.mcp_server import TOOL_NAMES, build_server
from police_thief.services.inbound import InboundHandler

DIGEST = "c" * 64


@pytest.fixture
def handler() -> InboundHandler:
    return InboundHandler(config_sha256=DIGEST, expect_role="thief")


def _tools(server) -> dict:
    """Resolve the server's registered tools without a running event loop."""
    return {tool.name: tool for tool in asyncio.run(server.list_tools())}


def test_the_server_exposes_every_protocol_tool(handler: InboundHandler) -> None:
    assert set(TOOL_NAMES) <= set(_tools(build_server(handler)))


def test_the_server_takes_the_peer_name(handler: InboundHandler) -> None:
    assert build_server(handler, name="my_peer").name == "my_peer"


def test_the_default_server_name_identifies_a_peer(handler: InboundHandler) -> None:
    assert build_server(handler).name == "police_thief_peer"


def test_every_registered_tool_is_documented(handler: InboundHandler) -> None:
    """The schema an opponent reads must describe what each tool does."""
    tools = _tools(build_server(handler))
    for name in TOOL_NAMES:
        assert tools[name].description


def test_a_registered_tool_forwards_to_the_handler(handler: InboundHandler) -> None:
    """The adapter holds no logic of its own - it delegates every call."""
    tools = _tools(build_server(handler))
    from police_thief.domain import messages

    payload = messages.commit("thief", 0, "a" * 64)
    asyncio.run(build_server(handler).call_tool("commit", {"payload": payload}))
    assert handler.committed_digest(0) == "a" * 64
    assert set(tools) >= set(TOOL_NAMES)


def test_the_tool_list_covers_the_whole_protocol() -> None:
    assert set(TOOL_NAMES) == {
        "handshake",
        "commit",
        "ack",
        "reveal",
        "capture_claim",
        "audit",
    }
