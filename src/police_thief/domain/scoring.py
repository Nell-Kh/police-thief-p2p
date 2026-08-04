"""Point allocation for every way a mini-game can end.

The scoring table (rulebook ch. 3.5) is deliberately asymmetric: a capture pays
the cop his highest reward, prolonged survival pays the thief his. A technical
loss zeroes both sides, so neither peer gains by breaking the protocol. Every
value carries **fixed** status in the parameters table and is read from the
signed contract - never hardcoded here.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..constants import (
    EVENT_CAPTURE,
    EVENT_SURVIVAL,
    EVENT_TECHNICAL_LOSS,
    EVENT_TIE,
)
from ..shared.schema import ScoringConfig


@dataclass(frozen=True)
class Outcome:
    """The result of a finished mini-game."""

    event: str
    cop_points: int
    thief_points: int
    reason: str

    def points_for(self, role: str) -> int:
        """Points awarded to ``role`` ("police" or "thief")."""
        from ..constants import ROLE_POLICE, ROLE_THIEF

        if role == ROLE_POLICE:
            return self.cop_points
        if role == ROLE_THIEF:
            return self.thief_points
        raise ValueError(f"unknown role {role!r}")


def capture(scoring: ScoringConfig, reason: str = "the cop captured the thief") -> Outcome:
    """The cop caught the thief - by overlap, or by a trapping barrier."""
    return Outcome(
        event=EVENT_CAPTURE,
        cop_points=scoring.capture_cop,
        thief_points=scoring.capture_thief,
        reason=reason,
    )


def survival(scoring: ScoringConfig, reason: str = "the thief survived to the threshold") -> Outcome:
    """The thief stayed free for the full survival threshold."""
    return Outcome(
        event=EVENT_SURVIVAL,
        cop_points=scoring.survival_cop,
        thief_points=scoring.survival_thief,
        reason=reason,
    )


def technical_loss(scoring: ScoringConfig, reason: str) -> Outcome:
    """A crash, a missed deadline, or a cryptographic forgery: nobody scores."""
    return Outcome(
        event=EVENT_TECHNICAL_LOSS,
        cop_points=scoring.technical_loss,
        thief_points=scoring.technical_loss,
        reason=reason,
    )


def tie(scoring: ScoringConfig, reason: str = "the series ended level") -> Outcome:
    """A tied series against one opponent pays both sides the tie score."""
    return Outcome(
        event=EVENT_TIE,
        cop_points=scoring.tie_score,
        thief_points=scoring.tie_score,
        reason=reason,
    )


def series_totals(outcomes: list[Outcome]) -> tuple[int, int]:
    """Sum the cop and thief points across a series of mini-games."""
    cop = sum(outcome.cop_points for outcome in outcomes)
    thief = sum(outcome.thief_points for outcome in outcomes)
    return cop, thief
