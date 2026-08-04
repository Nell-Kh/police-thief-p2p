"""The wire format exchanged between the two peers.

Messages are plain dictionaries so they cross the MCP boundary unchanged and can
be hashed canonically. Each builder produces a validated envelope; each parser
raises on anything malformed, because a peer must never act on a message it did
not fully understand.

Note the deliberate split: geometric facts that both sides must agree on
(commitments, revealed moves, barrier declarations, capture claims) travel as
structured fields, while everything an agent says *about its own position*
travels only as free natural language in ``hint``. There is no numeric-position
channel, by design.
"""

from __future__ import annotations

from typing import Any

from ..constants import INTENTS, MOVE_DELTAS, ROLES

MSG_HANDSHAKE = "handshake"
MSG_COMMIT = "commit"
MSG_ACK = "ack"
MSG_REVEAL = "reveal"
MSG_CAPTURE_CLAIM = "capture_claim"
MSG_AUDIT = "audit"

MESSAGE_KINDS = (
    MSG_HANDSHAKE,
    MSG_COMMIT,
    MSG_ACK,
    MSG_REVEAL,
    MSG_CAPTURE_CLAIM,
    MSG_AUDIT,
)


class MessageError(ValueError):
    """Raised when a message is malformed or fails validation."""


def _require(payload: dict[str, Any], key: str, kind: str) -> Any:
    """Fetch a mandatory field from a message payload."""
    if key not in payload:
        raise MessageError(f"{kind}: missing field {key!r}")
    return payload[key]


def envelope(kind: str, role: str, step: int, **fields: Any) -> dict[str, Any]:
    """Build a message envelope shared by every message kind.

    Raises:
        MessageError: on an unknown kind or role, or a negative step.
    """
    if kind not in MESSAGE_KINDS:
        raise MessageError(f"unknown message kind {kind!r}")
    if role not in ROLES:
        raise MessageError(f"unknown role {role!r}")
    if step < 0:
        raise MessageError(f"step must not be negative, got {step}")
    return {"kind": kind, "role": role, "step": step, **fields}


def handshake(role: str, config_sha256: str, games_played: int, peer_id: str) -> dict[str, Any]:
    """Opening message: who I am, which contract I hold, how many games I have played.

    The declared game count is what weights the diversity incentive, and a false
    declaration disqualifies the team, so it travels in the very first message.
    """
    return envelope(
        MSG_HANDSHAKE,
        role,
        0,
        config_sha256=config_sha256,
        games_played=games_played,
        peer_id=peer_id,
    )


def commit(role: str, step: int, digest: str) -> dict[str, Any]:
    """Commitment message: the sealed digest only, never its content."""
    if not digest:
        raise MessageError("commit: digest must not be empty")
    return envelope(MSG_COMMIT, role, step, digest=digest)


def ack(role: str, step: int, digest: str) -> dict[str, Any]:
    """Acknowledgement that the opponent's commitment was received and locked."""
    return envelope(MSG_ACK, role, step, digest=digest)


def reveal(role: str, step: int, move: str, intent: str, hint: str) -> dict[str, Any]:
    """Reveal message: the move and the verbal hint. The nonce stays secret.

    Raises:
        MessageError: on an unknown move or intent flag.
    """
    if move not in MOVE_DELTAS:
        raise MessageError(f"reveal: unknown move {move!r}")
    if intent not in INTENTS:
        raise MessageError(f"reveal: intent must be one of {INTENTS}, got {intent!r}")
    return envelope(MSG_REVEAL, role, step, move=move, intent=intent, hint=hint)


def capture_claim(role: str, step: int, claimed: bool) -> dict[str, Any]:
    """A capture claim, or the truthful answer to one.

    The answer is under a cryptographic truth duty: it is sealed in the step's
    commitment, so a lie is exposed by the end-of-game audit.
    """
    return envelope(MSG_CAPTURE_CLAIM, role, step, claimed=bool(claimed))


def audit(role: str, entries: list[dict[str, Any]]) -> dict[str, Any]:
    """End-of-game message carrying the full log, nonces included."""
    return envelope(MSG_AUDIT, role, 0, entries=entries)


def parse(payload: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """Validate an incoming message and return ``(kind, payload)``.

    Raises:
        MessageError: if the envelope is malformed or the kind is unknown.
    """
    if not isinstance(payload, dict):
        raise MessageError("message must be an object")
    kind = _require(payload, "kind", "message")
    if kind not in MESSAGE_KINDS:
        raise MessageError(f"unknown message kind {kind!r}")
    role = _require(payload, "role", kind)
    if role not in ROLES:
        raise MessageError(f"{kind}: unknown role {role!r}")
    _require(payload, "step", kind)
    return kind, payload
