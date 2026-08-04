"""Commit-reveal over SHA-256: sealing, verification, and record audit.

Every game step is sealed before it is played out loud: the full record -
state, position, move, intent, hint, step, role - is serialized canonically,
joined with a fresh cryptographic nonce, and hashed. Only the hash travels
during play; payloads and nonces are disclosed at the end-of-game audit, where
each side recomputes every hash. One mismatch proves tampering - no statistics,
no discretion (rulebook ch. 5).

The seal format follows the reference implementation for interoperability:
``sha256(canonical_json(payload) + "|" + nonce)``. The book's inline example
hashes the nonce inside the JSON instead; per the front-matter rule its code
samples are illustrative, and matching the league's de-facto format wins
(ADR-6/ADR-7).
"""

from __future__ import annotations

import hashlib
import secrets
from typing import Any

from ..shared.config_io import canonical_json

#: Bytes of entropy per nonce; 16 bytes = 32 hex characters.
NONCE_BYTES = 16


def new_nonce() -> str:
    """A fresh cryptographic nonce - ``secrets``, never ``random``.

    Uniqueness makes identical actions hash differently every step, and the
    entropy defeats dictionary attacks over the small move space.
    """
    return secrets.token_hex(NONCE_BYTES)


def digest_of(payload: dict[str, Any], nonce: str) -> str:
    """The commitment digest of ``payload`` sealed with ``nonce``."""
    material = f"{canonical_json(payload)}|{nonce}"
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def seal(payload: dict[str, Any]) -> dict[str, Any]:
    """Seal a record: draw a nonce, compute the digest, keep all three.

    Returns:
        ``{"payload": ..., "nonce": ..., "commit": ...}`` - the full record
        stays local; only ``commit`` may travel before the audit.
    """
    nonce = new_nonce()
    return {"payload": payload, "nonce": nonce, "commit": digest_of(payload, nonce)}


def verify(payload: dict[str, Any], nonce: str, commit: str) -> bool:
    """Whether a revealed payload and nonce reproduce the committed digest.

    Constant-time comparison; the answer is binary - there is no "almost".
    """
    return secrets.compare_digest(digest_of(payload, nonce), commit)


def audit_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Re-verify a full set of revealed records against their commitments.

    Returns:
        ``passed`` (bool), ``verified_steps`` and ``failed_steps`` (lists of
        the ``step`` field of each record, or its index when absent). A single
        failure fails the audit: the smallest change alters the hash entirely.
    """
    verified: list[Any] = []
    failed: list[Any] = []
    for index, record in enumerate(records):
        label = record.get("payload", {}).get("step", index)
        try:
            ok = verify(record["payload"], record["nonce"], record["commit"])
        except (KeyError, TypeError):
            ok = False
        (verified if ok else failed).append(label)
    return {"passed": not failed, "verified_steps": verified, "failed_steps": failed}
