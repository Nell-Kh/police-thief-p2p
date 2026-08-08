"""End-of-game reporting for a :class:`~.match_runtime.MatchRuntime`.

Split out of ``match_runtime.py`` - sealing the audit disclosure, gathering
our own corroborating evidence, and scoring the claimed result are all
"what do we report once the mini-game is over", a separate concern from
playing the turns that got it there.
"""

from __future__ import annotations

from typing import Any


class MatchReporting:
    """Audit disclosure, corroborating evidence and scoring for one mini-game."""

    def disclosure(self) -> dict[str, Any]:
        """The end-of-game audit payload: every payload and nonce, plus our claim."""
        self.book.close(self.result or {"type": "undecided"})
        return self.book.audit_payload(self.result)

    def audit_evidence(self) -> dict[str, Any]:
        """Local evidence for corroborating the opponent's self-declared capture.

        Pass straight into :func:`domain.audit.audit_disclosure` as keywords. It
        carries only things we know first-hand - the stones on our own board and
        what the opponent claimed on our wire - so a ``caught: true`` is checked
        against our own record instead of being believed (kit F-1/F-2). Every
        field may legitimately be absent, in which case that layer stands down.
        """
        claim = self.view.final_claim
        cell = (claim[0], claim[1]) if claim is not None else None
        return {
            "own_barriers": sorted(self.view.board.barriers),
            "conceded_at": None if self.view.final_claim_is_answer else cell,
            "answered_at": cell if self.view.final_claim_is_answer else None,
        }

    def points(self) -> int:
        """The points this peer's claimed result awards it."""
        scoring = self.contract.scoring
        result = self.result or {}
        if result.get("type") == "capture":
            return scoring.capture_cop if self.view.role == "police" else scoring.capture_thief
        if result.get("type") == "survival":
            return scoring.survival_thief if self.view.role == "thief" else scoring.survival_cop
        return scoring.technical_loss
