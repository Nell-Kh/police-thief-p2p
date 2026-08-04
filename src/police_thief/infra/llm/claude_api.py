"""The cloud provider: a small Claude model (Haiku) over the Anthropic API.

Real token consumption, measured from the API's own usage numbers and counted
against the agreed series budget. The API key comes from the environment only
(``ANTHROPIC_API_KEY``) - never from code or configuration files.
"""

from __future__ import annotations

import os

from .base import HintProvider, HintRequest, ProviderError, clip_words, direction_word
from .ledger import TokenLedger

DEFAULT_MODEL = "claude-3-5-haiku-latest"

SYSTEM_PROMPT = (
    "You are the {role} in a cops-and-robbers chase set in {area}. "
    "Write ONE taunting hint of at most {max_words} words claiming you moved "
    "{direction}. Mention a real landmark of {area}. Output only the hint text."
)


class ClaudeApiProvider(HintProvider):
    """Generates hints with a small cloud model; every token is metered."""

    name = "claude_api"

    def __init__(self, model: str, ledger: TokenLedger) -> None:
        """Bind the provider to a model name and the consumption ledger."""
        self._model = model or DEFAULT_MODEL
        self._ledger = ledger
        self._client = None

    def _get_client(self):
        """Build the SDK client lazily so imports never require a key.

        Raises:
            ProviderError: if the SDK or the API key is unavailable.
        """
        if self._client is not None:
            return self._client
        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise ProviderError("ANTHROPIC_API_KEY is not set")
        try:
            import anthropic
        except ImportError as error:  # pragma: no cover - dependency is declared
            raise ProviderError("anthropic SDK is not installed") from error
        self._client = anthropic.Anthropic()
        return self._client

    def generate(self, request: HintRequest) -> str:
        """Ask the model for one hint; measure and clip the result.

        Raises:
            ProviderError: on any API failure - the chain falls back to the
                template so the game continues.
        """
        client = self._get_client()
        claimed = request.claimed_direction()
        system = SYSTEM_PROMPT.format(
            role=request.role,
            area=request.map_area or "a nameless city",
            max_words=request.max_words,
            direction=direction_word(claimed),
        )
        try:
            response = client.messages.create(
                model=self._model,
                max_tokens=60,
                system=system,
                messages=[{"role": "user", "content": f"Step {request.step}. The hint:"}],
            )
        except Exception as error:
            raise ProviderError(f"claude_api call failed: {error}") from error
        usage = getattr(response, "usage", None)
        self._ledger.record(
            step=request.step,
            provider=self.name,
            input_tokens=getattr(usage, "input_tokens", 0) or 0,
            output_tokens=getattr(usage, "output_tokens", 0) or 0,
        )
        text = "".join(
            block.text for block in response.content if getattr(block, "type", "") == "text"
        )
        if not text.strip():
            raise ProviderError("claude_api returned no text")
        return clip_words(text.strip(), request.max_words)
