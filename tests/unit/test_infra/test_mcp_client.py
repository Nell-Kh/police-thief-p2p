"""Tests for the outbound peer client: deadlines, retries and give-up."""

from __future__ import annotations

import pytest

from police_thief.infra.mcp_client import PeerClient, PeerUnreachableError
from police_thief.infra.transport import FlakyTransport, LoopbackTransport
from police_thief.services.deadline import DeadlineExpiredError
from police_thief.services.inbound import InboundHandler

DIGEST = "c" * 64


@pytest.fixture
def opponent() -> InboundHandler:
    """A thief peer receiving our police messages."""
    return InboundHandler(config_sha256=DIGEST, expect_role="police")


@pytest.fixture
def build(network_config, rate_limits, fake_clock):
    """Build a client, optionally recording backoff sleeps."""

    def _build(transport, sleeps: list[float] | None = None, clock=None) -> PeerClient:
        return PeerClient(
            transport,
            network_config,
            rate_limits,
            sleep=(sleeps.append if sleeps is not None else lambda _: None),
            clock=clock or fake_clock,
        )

    return _build


def test_a_handshake_reaches_the_opponent(opponent: InboundHandler, build) -> None:
    client = build(LoopbackTransport(opponent))
    reply = client.handshake("police", DIGEST, games_played=1, peer_id="team-a")
    assert reply["accepted"]


def test_every_protocol_message_has_a_client_method(opponent: InboundHandler, build) -> None:
    client = build(LoopbackTransport(opponent))
    client.handshake("police", DIGEST, 0, "team-a")
    client.commit("police", 0, "a" * 64)
    client.acknowledge("police", 0, "a" * 64)
    client.reveal("police", 0, "N", "truth", "by the park")
    client.capture_claim("police", 0, False)
    client.audit("police", [{"step": 0}])
    assert [message["kind"] for message in opponent.received] == [
        "handshake",
        "commit",
        "ack",
        "reveal",
        "capture_claim",
        "audit",
    ]


def test_a_transient_failure_is_retried(opponent: InboundHandler, build) -> None:
    transport = FlakyTransport(LoopbackTransport(opponent), failures=2)
    sleeps: list[float] = []
    reply = build(transport, sleeps).handshake("police", DIGEST, 0, "team-a")
    assert reply["accepted"]
    assert sleeps == [5, 5]


def test_the_retry_budget_is_bounded(opponent: InboundHandler, build) -> None:
    """After the budget is spent we give up rather than wait forever."""
    transport = FlakyTransport(LoopbackTransport(opponent), failures=99)
    with pytest.raises(PeerUnreachableError, match="after 3 attempts"):
        build(transport).handshake("police", DIGEST, 0, "team-a")


def test_no_backoff_is_slept_after_the_final_attempt(opponent, build, rate_limits) -> None:
    transport = FlakyTransport(LoopbackTransport(opponent), failures=99)
    sleeps: list[float] = []
    with pytest.raises(PeerUnreachableError):
        build(transport, sleeps).handshake("police", DIGEST, 0, "team-a")
    assert len(sleeps) == rate_limits.max_retries - 1


def test_a_late_reply_is_treated_as_a_failure(opponent, build, fake_clock) -> None:
    """A missed deadline is a failure, not an invitation to keep waiting."""
    clock = fake_clock

    class SlowTransport:
        def send(self, tool: str, payload: dict) -> dict:
            clock.advance(31)
            return {"accepted": True}

    client = build(SlowTransport(), clock=clock)
    with pytest.raises(DeadlineExpiredError, match="deadline"):
        client.commit("police", 0, "a" * 64)


def test_a_reply_inside_the_deadline_is_accepted(build, fake_clock) -> None:
    clock = fake_clock

    class PromptTransport:
        def send(self, tool: str, payload: dict) -> dict:
            clock.advance(29)
            return {"accepted": True}

    assert build(PromptTransport(), clock=clock).commit("police", 0, "a" * 64)["accepted"]


def test_nothing_stays_in_flight_after_a_successful_call(opponent: InboundHandler, build) -> None:
    client = build(LoopbackTransport(opponent))
    client.commit("police", 0, "a" * 64)
    assert client.deadlines.in_flight == ()


def test_nothing_stays_in_flight_after_giving_up(opponent: InboundHandler, build) -> None:
    transport = FlakyTransport(LoopbackTransport(opponent), failures=99)
    client = build(transport)
    with pytest.raises(PeerUnreachableError):
        client.commit("police", 0, "a" * 64)
    assert client.deadlines.in_flight == ()


def test_the_deadline_comes_from_the_contract(opponent, build, network_config) -> None:
    client = build(LoopbackTransport(opponent))
    assert client.deadlines.timeout_sec == network_config.response_timeout_sec


def test_calling_a_tool_the_opponent_lacks_is_refused(build) -> None:
    transport = LoopbackTransport(object())
    with pytest.raises(PeerUnreachableError):
        build(transport).commit("police", 0, "a" * 64)
