"""The command-line provider: ``claude -p`` via the Claude Code CLI.

The highest-cost mode, kept for completeness. Consumption is estimated from
word counts because the CLI does not report usage numbers.
"""

from __future__ import annotations

import shutil
import subprocess

from .base import HintProvider, HintRequest, ProviderError, clip_words, direction_word
from .ledger import TokenLedger

PROMPT = (
    "You are the {role} in a cops-and-robbers chase set in {area}. "
    "Write one taunting hint of at most {max_words} words claiming you moved "
    "{direction}. Output only the hint."
)

#: Crude words-to-tokens estimate used when the tool reports no usage.
TOKENS_PER_WORD = 1.5


class ClaudeCliProvider(HintProvider):
    """Generates hints by shelling out to the Claude Code CLI."""

    name = "claude_cli"

    def __init__(self, ledger: TokenLedger, binary: str = "claude") -> None:
        """Bind the provider to the CLI binary and the consumption ledger."""
        self._ledger = ledger
        self._binary = binary

    def generate(self, request: HintRequest) -> str:
        """Run ``claude -p`` once and return its clipped output.

        Raises:
            ProviderError: if the CLI is missing, fails, or prints nothing.
        """
        if shutil.which(self._binary) is None:
            raise ProviderError(f"{self._binary!r} CLI is not installed")
        prompt = PROMPT.format(
            role=request.role,
            area=request.map_area or "a nameless city",
            max_words=request.max_words,
            direction=direction_word(request.claimed_direction()),
        )
        try:
            completed = subprocess.run(  # noqa: S603
                [self._binary, "-p", prompt],
                capture_output=True,
                text=True,
                timeout=45,
                check=True,
            )
        except (subprocess.SubprocessError, OSError) as error:
            raise ProviderError(f"claude CLI failed: {error}") from error
        text = completed.stdout.strip()
        if not text:
            raise ProviderError("claude CLI returned no text")
        estimate = int(len((prompt + text).split()) * TOKENS_PER_WORD)
        self._ledger.record(
            step=request.step, provider=self.name, input_tokens=estimate, output_tokens=0
        )
        return clip_words(text, request.max_words)
