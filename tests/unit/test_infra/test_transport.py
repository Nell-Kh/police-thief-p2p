"""Tests for the transport abstraction between peers."""

from __future__ import annotations

import pytest

from police_thief.domain import messages
from police_thief.infra.transport import (
    FlakyTransport,
    LoopbackTransport,
    Transport,
    TransportError,
)
from police_thief.services.inbound import InboundHandler

DIGEST = "c" * 64


@pytest.fixture
def opponent() -> InboundHandler:
    return InboundHandler(config_sha256=DIGEST, expect_role="police")


def test_the_loopback_delivers_to_the_matching_tool(opponent: InboundHandler) -> None:
    transport = LoopbackTransport(opponent)
    reply = transport.send("commit", messages.commit("police", 0, "a" * 64))
    assert reply["accepted"]
    assert opponent.committed_digest(0) == "a" * 64


def test_the_loopback_records_what_was_sent(opponent: InboundHandler) -> None:
    transport = LoopbackTransport(opponent)
    transport.send("commit", messages.commit("police", 2, "a" * 64))
    tool, payload = transport.sent[0]
    assert tool == "commit"
    assert payload["step"] == 2


def test_an_unknown_tool_is_refused() -> None:
    """A peer cannot invoke a tool its opponent does not expose."""
    with pytest.raises(TransportError, match="no tool named 'gossip'"):
        LoopbackTransport(object()).send("gossip", {})


def test_the_flaky_transport_fails_its_budget_then_delivers(
    opponent: InboundHandler,
) -> None:
    transport = FlakyTransport(LoopbackTransport(opponent), failures=1)
    with pytest.raises(TransportError, match="simulated delivery failure"):
        transport.send("commit", messages.commit("police", 0, "a" * 64))
    assert transport.send("commit", messages.commit("police", 0, "a" * 64))["accepted"]


def test_both_transports_satisfy_the_protocol(opponent: InboundHandler) -> None:
    """Any transport is interchangeable: loopback, localhost or a tunnel."""
    assert isinstance(LoopbackTransport(opponent), Transport)
    assert isinstance(FlakyTransport(LoopbackTransport(opponent), 0), Transport)
