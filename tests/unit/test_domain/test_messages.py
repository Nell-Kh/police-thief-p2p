"""Tests for the peer-to-peer wire format."""

from __future__ import annotations

import pytest

from police_thief.domain import messages
from police_thief.domain.messages import MessageError


def test_an_envelope_carries_kind_role_and_step() -> None:
    envelope = messages.envelope("commit", "police", 3, digest="abc")
    assert envelope["kind"] == "commit"
    assert envelope["role"] == "police"
    assert envelope["step"] == 3
    assert envelope["digest"] == "abc"


def test_an_unknown_message_kind_is_rejected() -> None:
    with pytest.raises(MessageError, match="unknown message kind"):
        messages.envelope("gossip", "police", 0)


def test_an_unknown_role_is_rejected() -> None:
    with pytest.raises(MessageError, match="unknown role"):
        messages.envelope("commit", "burglar", 0)


def test_a_negative_step_is_rejected() -> None:
    with pytest.raises(MessageError, match="must not be negative"):
        messages.envelope("commit", "police", -1)


def test_the_handshake_declares_the_contract_and_game_count() -> None:
    """A false game-count declaration disqualifies, so it travels up front."""
    message = messages.handshake("police", "d" * 64, games_played=3, peer_id="team-a")
    assert message["config_sha256"] == "d" * 64
    assert message["games_played"] == 3
    assert message["peer_id"] == "team-a"


def test_a_commit_carries_only_the_digest() -> None:
    """The commitment reveals nothing about the move it seals."""
    message = messages.commit("thief", 5, "a" * 64)
    assert set(message) == {"kind", "role", "step", "digest"}


def test_an_empty_digest_is_rejected() -> None:
    with pytest.raises(MessageError, match="must not be empty"):
        messages.commit("thief", 5, "")


def test_an_ack_echoes_the_digest_it_locks() -> None:
    assert messages.ack("police", 5, "a" * 64)["digest"] == "a" * 64


def test_a_reveal_carries_the_move_intent_and_hint_but_no_nonce() -> None:
    """The nonce stays secret until the end-of-game audit."""
    message = messages.reveal("thief", 5, "N", "lie", "heading past Times Square")
    assert "nonce" not in message
    assert message["move"] == "N"
    assert message["intent"] == "lie"


def test_a_reveal_with_an_unknown_move_is_rejected() -> None:
    with pytest.raises(MessageError, match="unknown move"):
        messages.reveal("thief", 5, "NE", "truth", "hint")


def test_a_reveal_with_an_unknown_intent_is_rejected() -> None:
    """An agent must declare in advance whether it is lying."""
    with pytest.raises(MessageError, match="intent must be one of"):
        messages.reveal("thief", 5, "N", "maybe", "hint")


def test_a_capture_claim_carries_a_boolean() -> None:
    assert messages.capture_claim("police", 7, True)["claimed"] is True
    assert messages.capture_claim("thief", 7, False)["claimed"] is False


def test_an_audit_message_carries_the_log_entries() -> None:
    message = messages.audit("police", [{"step": 0, "nonce": "abc"}])
    assert message["entries"] == [{"step": 0, "nonce": "abc"}]


def test_parse_returns_the_kind_and_payload() -> None:
    kind, payload = messages.parse(messages.commit("police", 1, "a" * 64))
    assert kind == "commit"
    assert payload["step"] == 1


def test_parse_rejects_a_non_object() -> None:
    with pytest.raises(MessageError, match="must be an object"):
        messages.parse(["not", "a", "dict"])  # type: ignore[arg-type]


def test_parse_rejects_a_missing_kind() -> None:
    with pytest.raises(MessageError, match="missing field 'kind'"):
        messages.parse({"role": "police", "step": 0})


def test_parse_rejects_an_unknown_kind() -> None:
    with pytest.raises(MessageError, match="unknown message kind"):
        messages.parse({"kind": "gossip", "role": "police", "step": 0})


def test_parse_rejects_an_unknown_role() -> None:
    with pytest.raises(MessageError, match="unknown role"):
        messages.parse({"kind": "commit", "role": "burglar", "step": 0})


def test_parse_rejects_a_missing_step() -> None:
    with pytest.raises(MessageError, match="missing field 'step'"):
        messages.parse({"kind": "commit", "role": "police"})


def test_no_message_carries_a_numeric_position() -> None:
    """Positional information may travel only as free natural language."""
    built = [
        messages.handshake("police", "d" * 64, 0, "team-a"),
        messages.commit("police", 1, "a" * 64),
        messages.ack("police", 1, "a" * 64),
        messages.reveal("police", 1, "N", "truth", "near the river"),
        messages.capture_claim("police", 1, False),
    ]
    for message in built:
        assert "position" not in message
        assert "row" not in message
        assert "col" not in message
