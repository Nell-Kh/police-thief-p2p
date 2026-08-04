"""The template provider: pre-written hints, zero tokens, no network.

The rulebook's recommended default. Sentences are chosen deterministically by
step number, flavoured with landmarks of the agreed arena (``map_area``), and
clipped to the signed word cap. Because it can never fail, it is also the
fallback behind every paid provider - a game always finishes.
"""

from __future__ import annotations

from .base import HintProvider, HintRequest, clip_words, direction_word

#: Real landmarks per supported arena; the empty arena uses generic scenery.
LANDMARKS: dict[str, tuple[str, ...]] = {
    "New York": (
        "Times Square",
        "the Brooklyn Bridge",
        "Central Park",
        "Wall Street",
        "Grand Central",
        "the High Line",
    ),
    "London": (
        "Tower Bridge",
        "Camden Market",
        "the Underground",
        "Piccadilly Circus",
        "the Thames",
    ),
    "Paris": (
        "the Metro",
        "Montmartre",
        "the Seine",
        "Les Halles",
        "the Latin Quarter",
    ),
}

GENERIC_LANDMARKS: tuple[str, ...] = (
    "the old market",
    "the riverside",
    "the freight yard",
    "the arcade",
    "the rooftops",
)

#: Sentence skeletons; {direction} and {landmark} are substituted.
PATTERNS: tuple[str, ...] = (
    "Slipping {direction} past {landmark}, try to keep up.",
    "You will find only my shadow {direction} of {landmark}.",
    "Heading {direction}, {landmark} covers my tracks.",
    "I drifted {direction} near {landmark} while you hesitated.",
    "Look {direction}, somewhere around {landmark} - or not.",
)

STAY_PATTERNS: tuple[str, ...] = (
    "Not moving an inch, {landmark} suits me fine.",
    "Still here by {landmark}, patience is a weapon.",
)


class TemplateProvider(HintProvider):
    """Deterministic, offline, free - and therefore always available."""

    name = "template"

    def generate(self, request: HintRequest) -> str:
        """Compose a hint from the pre-written pools.

        Choice is keyed by the step number, so the same request reproduces the
        same sentence on every replay.
        """
        landmarks = LANDMARKS.get(request.map_area, GENERIC_LANDMARKS)
        landmark = landmarks[request.step % len(landmarks)]
        claimed = request.claimed_direction()
        if claimed is None:
            pattern = STAY_PATTERNS[request.step % len(STAY_PATTERNS)]
            text = pattern.format(landmark=landmark)
        else:
            pattern = PATTERNS[request.step % len(PATTERNS)]
            text = pattern.format(direction=direction_word(claimed), landmark=landmark)
        return clip_words(text, request.max_words)
