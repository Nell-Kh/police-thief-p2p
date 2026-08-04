"""The verbal layer's contract: providers that turn intent into a hint.

The movement decision is always algorithmic; the language model touches only
this layer - composing the natural-language hint (truthful or deceptive) that
travels to the opponent. Four operating modes exist (template, ollama,
claude_api, claude_cli), all interchangeable behind :class:`HintProvider`, and
every mode obeys the signed word cap.
"""

from __future__ import annotations

from dataclasses import dataclass

from ...constants import INTENT_LIE, INTENT_TRUTH, INTENTS


class ProviderError(RuntimeError):
    """Raised when a provider cannot produce a hint (network, key, quota)."""


#: Direction letters to spoken words, for prompt building and templates.
DIRECTION_WORDS = {"N": "north", "S": "south", "E": "east", "W": "west"}


@dataclass(frozen=True)
class HintRequest:
    """Everything a provider may know when composing one hint.

    ``true_direction`` is the direction the agent actually moved (or ``None``
    for staying). With ``intent == "lie"`` the provider must point elsewhere;
    with ``intent == "truth"`` it must be honest. The intent itself is sealed
    in the step's commitment, so the choice is binding either way.
    """

    role: str
    intent: str
    true_direction: str | None
    map_area: str
    max_words: int
    step: int

    def __post_init__(self) -> None:
        """Validate the intent flag."""
        if self.intent not in INTENTS:
            raise ValueError(f"intent must be one of {INTENTS}, got {self.intent!r}")

    def claimed_direction(self) -> str | None:
        """The direction the hint should point at, honouring the intent.

        A lie deterministically claims the opposite of the true direction, so
        the same request always produces the same deception - reproducibility
        matters more than variety here.
        """
        opposite = {"N": "S", "S": "N", "E": "W", "W": "E"}
        if self.intent == INTENT_TRUTH:
            return self.true_direction
        if self.true_direction is None:
            return "N" if self.step % 2 == 0 else "E"
        return opposite[self.true_direction]


class HintProvider:
    """Base class of every verbal-layer provider."""

    #: Provider name as configured in ``[trash_talk] provider``.
    name = "base"

    def generate(self, request: HintRequest) -> str:
        """Compose a hint for ``request``. Subclasses must override.

        Raises:
            ProviderError: when the provider cannot deliver; callers fall back
                to the zero-token template so a game always finishes.
        """
        raise NotImplementedError("a provider must override generate")


def clip_words(text: str, max_words: int) -> str:
    """Enforce the signed hint word cap on any provider's output.

    The cap applies to the template and to the language model alike; model
    output is clipped even though the cap is also stated in its prompt.
    """
    words = text.split()
    return " ".join(words[:max_words])


def direction_word(direction: str | None) -> str:
    """A speakable word for a direction letter (or a vague word for staying)."""
    if direction is None:
        return "nowhere"
    return DIRECTION_WORDS[direction]


__all__ = [
    "DIRECTION_WORDS",
    "INTENT_LIE",
    "INTENT_TRUTH",
    "HintProvider",
    "HintRequest",
    "ProviderError",
    "clip_words",
    "direction_word",
]
