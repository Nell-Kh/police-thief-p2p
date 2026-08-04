"""Pre-game negotiation: the terms both sides must lock before move one.

The terms bundle everything the rulebook requires agreed and cryptographically
locked before a series: the contract digest (byte-identical ``game.json``), the
scent-model lock (formula + numeric example, ch. 4.5), the declared count of
counted games already played (the diversity-incentive declaration - lying here
disqualifies), the team identity, and the Step-0 commitment hash that seals the
hardware declaration and the exact code commit being played.
"""

from __future__ import annotations

from typing import Any

from ..shared.config import ConfigManager
from ..shared.schema import PheromoneConfig
from .scent import lock_sha256


class TermsRejectedError(RuntimeError):
    """Raised when the opponent's terms do not match ours."""


def build_terms(
    config: ConfigManager,
    *,
    peer_id: str,
    games_played: int,
    sub_game: int,
    step0_commit: str,
) -> dict[str, Any]:
    """The terms message this peer offers at negotiation."""
    return {
        "role": config.role,
        "peer_id": peer_id,
        "games_played": int(games_played),
        "sub_game": int(sub_game),
        "config_sha256": config.config_sha256,
        "scent_lock": lock_sha256(config.contract.pheromones),
        "step0_commit": step0_commit,
    }


def validate_terms(
    theirs: dict[str, Any],
    *,
    our_config_sha256: str,
    our_scent_lock: str,
    expect_role: str,
) -> dict[str, Any]:
    """Accept or refuse an opponent's terms.

    Refusal conditions: wrong role, a contract digest that is not
    byte-identical to ours, or a different scent-model lock - different
    physics means the race must not start.

    Raises:
        TermsRejectedError: naming exactly what disagreed.
    """
    if not isinstance(theirs, dict):
        raise TermsRejectedError("terms must be an object")
    if theirs.get("role") != expect_role:
        raise TermsRejectedError(
            f"expected terms from {expect_role!r}, got {theirs.get('role')!r}"
        )
    their_digest = str(theirs.get("config_sha256", ""))
    if their_digest != our_config_sha256:
        raise TermsRejectedError(
            f"contract mismatch: ours {our_config_sha256[:12]}, theirs {their_digest[:12]}"
        )
    their_lock = str(theirs.get("scent_lock", ""))
    if their_lock != our_scent_lock:
        raise TermsRejectedError(
            f"scent-model mismatch: ours {our_scent_lock[:12]}, theirs {their_lock[:12]}"
        )
    if int(theirs.get("games_played", -1)) < 0:
        raise TermsRejectedError("games_played declaration missing or negative")
    if not str(theirs.get("step0_commit", "")):
        raise TermsRejectedError("step0 commitment missing")
    return theirs


def scent_lock_for(pheromones: PheromoneConfig) -> str:
    """The scent-model lock for a given pheromone configuration."""
    return lock_sha256(pheromones)
