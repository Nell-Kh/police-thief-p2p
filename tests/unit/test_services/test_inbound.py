"""Tests for the inbound message handler."""

from __future__ import annotations

import pytest

from police_thief.domain import messages
from police_thief.domain.messages import MessageError
from police_thief.services.inbound import HandshakeRejectedError, InboundHandler

DIGEST = "c" * 64


@pytest.fixture
def handler() -> InboundHandler:
    """A police peer expecting messages from the thief."""
    return InboundHandler(config_sha256=DIGEST, expect_role="thief")


def test_a_matching_handshake_is_accepted(handler: InboundHandler) -> None:
    reply = handler.handshake(messages.handshake("thief", DIGEST, 2, "team-b"))
    assert reply["accepted"]
    assert handler.opponent_games_played == 2
    assert handler.opponent_peer_id == "team-b"


def test_a_contract_mismatch_refuses_the_match(handler: InboundHandler) -> None:
    """Different digests mean different physics: the match must not start."""
    with pytest.raises(HandshakeRejectedError, match="contract mismatch"):
        handler.handshake(messages.handshake("thief", "f" * 64, 0, "team-b"))


def test_a_message_from_the_wrong_role_is_refused(handler: InboundHandler) -> None:
    """A peer never accepts a message claiming to be from itself."""
    with pytest.raises(MessageError, match="expected a message from 'thief'"):
        handler.commit(messages.commit("police", 0, "a" * 64))


def test_a_commitment_is_recorded(handler: InboundHandler) -> None:
    handler.commit(messages.commit("thief", 0, "a" * 64))
    assert handler.committed_digest(0) == "a" * 64


def test_a_second_commitment_for_a_step_is_refused(handler: InboundHandler) -> None:
    """Once sealed, a move cannot be replaced."""
    handler.commit(messages.commit("thief", 0, "a" * 64))
    with pytest.raises(MessageError, match="already committed"):
        handler.commit(messages.commit("thief", 0, "b" * 64))


def test_an_acknowledgement_is_accepted(handler: InboundHandler) -> None:
    assert handler.ack(messages.ack("thief", 0, "a" * 64))["accepted"]


def test_a_reveal_must_follow_a_commitment(handler: InboundHandler) -> None:
    """Revealing a move that was never committed is meaningless - and refused."""
    with pytest.raises(MessageError, match="never committed"):
        handler.reveal(messages.reveal("thief", 0, "N", "truth", "north side"))


def test_a_reveal_after_a_commitment_is_recorded(handler: InboundHandler) -> None:
    handler.commit(messages.commit("thief", 0, "a" * 64))
    reply = handler.reveal(messages.reveal("thief", 0, "N", "lie", "by the bridge"))
    assert reply["digest"] == "a" * 64
    assert handler.reveals[0]["move"] == "N"


def test_a_capture_claim_is_recorded(handler: InboundHandler) -> None:
    assert handler.capture_claim(messages.capture_claim("thief", 3, True))["claimed"]


def test_an_audit_message_stores_the_entries(handler: InboundHandler) -> None:
    reply = handler.audit(messages.audit("thief", [{"step": 0}, {"step": 1}]))
    assert reply["entries"] == 2
    assert len(handler.audit_entries) == 2


def test_an_audit_with_malformed_entries_is_refused(handler: InboundHandler) -> None:
    payload = messages.audit("thief", [])
    payload["entries"] = "not-a-list"
    with pytest.raises(MessageError, match="entries must be a list"):
        handler.audit(payload)


def test_an_empty_audit_is_accepted(handler: InboundHandler) -> None:
    payload = messages.audit("thief", [])
    assert handler.audit(payload)["entries"] == 0


def test_every_accepted_message_is_recorded(handler: InboundHandler) -> None:
    handler.handshake(messages.handshake("thief", DIGEST, 0, "team-b"))
    handler.commit(messages.commit("thief", 0, "a" * 64))
    assert [message["kind"] for message in handler.received] == ["handshake", "commit"]


def test_an_unknown_step_has_no_digest(handler: InboundHandler) -> None:
    assert handler.committed_digest(99) is None
