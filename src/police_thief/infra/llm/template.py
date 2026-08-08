"""The template provider: pre-written hints, zero tokens, no network.

The rulebook's recommended default. Sentences are chosen deterministically by
step number, flavoured with landmarks of the agreed arena (``map_area``), and
clipped to the signed word cap. Because it can never fail, it is also the
fallback behind every paid provider - a game always finishes.
"""

from __future__ import annotations

from .base import STYLE_VAGUE, HintProvider, HintRequest, clip_words, direction_word

#: Real landmarks per supported arena; an unknown arena uses generic scenery.
#: "Haifa" is the arena this repo's ``config/game.json`` commits, so it must
#: carry real landmarks - a shipped arena falling through to
#: :data:`GENERIC_LANDMARKS` would quietly drain the hints of local flavour
#: (FR-11), which ``test_llm.py`` pins.
LANDMARKS: dict[str, tuple[str, ...]] = {
    "Haifa": (
        "the Bahá'í Gardens",
        "Mount Carmel",
        "the German Colony",
        "the port",
        "Wadi Nisnas",
        "the Louis Promenade",
    ),
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

#: Pure atmosphere - no direction, no movement claim, nothing to falsify.
VAGUE_PATTERNS: tuple[str, ...] = (
    "The city hides me well, ask {landmark} if you doubt it.",
    "Somewhere between {landmark} and nowhere, good luck.",
    "{landmark} keeps my secrets better than you keep pace.",
    "Every alley near {landmark} tells a different story about me.",
    "I could be watching you from {landmark} at this very moment.",
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
        if request.style == STYLE_VAGUE:
            pattern = VAGUE_PATTERNS[request.step % len(VAGUE_PATTERNS)]
            return clip_words(pattern.format(landmark=landmark), request.max_words)
        claimed = request.claimed_direction()
        if claimed is None:
            pattern = STAY_PATTERNS[request.step % len(STAY_PATTERNS)]
            text = pattern.format(landmark=landmark)
        else:
            pattern = PATTERNS[request.step % len(PATTERNS)]
            text = pattern.format(direction=direction_word(claimed), landmark=landmark)
        return clip_words(text, request.max_words)
