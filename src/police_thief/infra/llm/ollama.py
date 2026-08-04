"""The local provider: an Ollama model at localhost - zero API tokens.

Local generation still costs compute, so calls are metered with estimated
counts for the research notebook, but nothing is charged against the series
budget's *paid* consumption in spirit: the rulebook treats Ollama as a
zero-API-token mode.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request

from .base import HintProvider, HintRequest, ProviderError, clip_words, direction_word
from .ledger import TokenLedger

DEFAULT_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "llama3.2"

PROMPT = (
    "You are the {role} in a cops-and-robbers chase set in {area}. "
    "Write one taunting hint of at most {max_words} words claiming you moved "
    "{direction}. Output only the hint."
)


class OllamaProvider(HintProvider):
    """Generates hints with a local model; free of API tokens and rate limits."""

    name = "ollama"

    def __init__(self, model: str, ledger: TokenLedger, url: str = DEFAULT_URL) -> None:
        """Bind the provider to a local model and endpoint."""
        self._model = model or DEFAULT_MODEL
        self._ledger = ledger
        self._url = url

    def generate(self, request: HintRequest) -> str:
        """Ask the local model for one hint.

        Raises:
            ProviderError: if Ollama is unreachable or returns no text.
        """
        prompt = PROMPT.format(
            role=request.role,
            area=request.map_area or "a nameless city",
            max_words=request.max_words,
            direction=direction_word(request.claimed_direction()),
        )
        body = json.dumps({"model": self._model, "prompt": prompt, "stream": False})
        http_request = urllib.request.Request(
            self._url, data=body.encode("utf-8"), headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(http_request, timeout=20) as reply:  # noqa: S310
                payload = json.loads(reply.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
            raise ProviderError(f"ollama call failed: {error}") from error
        text = str(payload.get("response", "")).strip()
        if not text:
            raise ProviderError("ollama returned no text")
        self._ledger.record(
            step=request.step,
            provider=self.name,
            input_tokens=int(payload.get("prompt_eval_count", 0) or 0),
            output_tokens=int(payload.get("eval_count", 0) or 0),
        )
        return clip_words(text, request.max_words)
