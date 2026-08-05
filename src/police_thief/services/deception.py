"""The deception controller: what the hint should claim, and when.

The scent field cannot lie and the movement cannot lie - the hint is the one
channel the agent controls. Against an opponent who cross-checks hints with
scent (as we do), every directional hint backfires: truth corroborates their
belief, and a detected lie damps the claimed region - which concentrates
their belief exactly where we are. Against such a verifier the only safe
sentence is a *vague* one. Against a naive opponent who follows hints
blindly, directional lies are cheap misdirection. The adaptive mode tells
the two apart using the one signal the wire gives away for free: the cop's
own capture claims reveal its belief argmax every turn. Claims landing close
mean we face a verifier - go quiet; claims wandering mean the hints are
working - keep lying.
"""

from __future__ import annotations

from ..constants import INTENT_LIE, INTENT_TRUTH
from ..infra.llm.base import STYLE_DIRECTIONAL, STYLE_VAGUE

MODE_ADAPTIVE = "adaptive"
MODE_VAGUE = "vague"
MODE_MISLEAD = "mislead"
MODE_HONEST = "honest"

MODES = (MODE_ADAPTIVE, MODE_VAGUE, MODE_MISLEAD, MODE_HONEST)


class DeceptionPolicy:
    """Chooses each turn's sealed intent and hint style."""

    def __init__(
        self,
        mode: str = MODE_ADAPTIVE,
        *,
        tracked_gap: int = 2,
        window: int = 3,
    ) -> None:
        """Configure the policy.

        Args:
            mode: one of :data:`MODES`; everything but ``adaptive`` is fixed.
            tracked_gap: a claim landing within this true-path distance
                counts as the opponent "seeing" us.
            window: how many recent claims the adaptive mode considers.
        """
        if mode not in MODES:
            raise ValueError(f"deception mode must be one of {MODES}, got {mode!r}")
        self.mode = mode
        self._tracked_gap = tracked_gap
        self._window = window
        self._gaps: list[int] = []

    def observe_claim_gap(self, gap: int) -> None:
        """Record the distance between an opponent claim and our true cell."""
        self._gaps.append(gap)

    @property
    def opponent_sees_us(self) -> bool:
        """Whether recent claims have been landing on or near our cell."""
        recent = self._gaps[-self._window :]
        if not recent:
            return False
        return sum(recent) / len(recent) <= self._tracked_gap

    def choose(self) -> tuple[str, str]:
        """This turn's ``(intent, style)``.

        The intent is sealed into the commitment; the style shapes the hint
        text. A vague hint carries the ``truth`` intent - saying nothing is
        not a lie - so the end-of-game audit stays clean.
        """
        if self.mode == MODE_HONEST:
            return INTENT_TRUTH, STYLE_DIRECTIONAL
        if self.mode == MODE_MISLEAD:
            return INTENT_LIE, STYLE_DIRECTIONAL
        if self.mode == MODE_VAGUE:
            return INTENT_TRUTH, STYLE_VAGUE
        if self.opponent_sees_us:
            return INTENT_TRUTH, STYLE_VAGUE  # a verifier: starve it
        return INTENT_LIE, STYLE_DIRECTIONAL  # lost or naive: keep it lost


def policy_from_config(config) -> DeceptionPolicy:
    """Build the policy from the ``[deception]`` section of the private TOML."""
    return DeceptionPolicy(
        mode=str(config.private_value("deception", "mode", MODE_ADAPTIVE)),
        tracked_gap=int(config.private_value("deception", "tracked_gap", 2)),
        window=int(config.private_value("deception", "window", 3)),
    )
