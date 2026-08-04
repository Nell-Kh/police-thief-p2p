"""Token consumption ledger.

Every language-model call is measured; the totals are cryptographically locked
at Step-0 and reported in the end-of-game JSON (``tokens_step``,
``tokens_total`` in the sealed records). The template provider costs zero, so a
whole series can legally run at zero consumption.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class TokenEntry:
    """One measured call to a language model."""

    step: int
    provider: str
    input_tokens: int
    output_tokens: int

    @property
    def total(self) -> int:
        """Tokens consumed by this call."""
        return self.input_tokens + self.output_tokens


@dataclass
class TokenLedger:
    """Accumulates token consumption across a mini-game and a series."""

    budget: int
    entries: list[TokenEntry] = field(default_factory=list)

    def record(self, step: int, provider: str, input_tokens: int, output_tokens: int) -> None:
        """Record one call's measured consumption.

        Raises:
            ValueError: on negative token counts.
        """
        if input_tokens < 0 or output_tokens < 0:
            raise ValueError("token counts must not be negative")
        self.entries.append(TokenEntry(step, provider, input_tokens, output_tokens))

    @property
    def total(self) -> int:
        """Tokens consumed so far."""
        return sum(entry.total for entry in self.entries)

    def step_total(self, step: int) -> int:
        """Tokens consumed during one game step."""
        return sum(entry.total for entry in self.entries if entry.step == step)

    @property
    def remaining(self) -> int:
        """Tokens left inside the agreed series budget (never negative)."""
        return max(0, self.budget - self.total)

    @property
    def exhausted(self) -> bool:
        """Whether the agreed budget has been fully consumed."""
        return self.total >= self.budget

    def summary(self) -> dict:
        """The consumption summary reported in the end-of-game JSON."""
        by_provider: dict[str, int] = {}
        for entry in self.entries:
            by_provider[entry.provider] = by_provider.get(entry.provider, 0) + entry.total
        return {
            "budget": self.budget,
            "total_tokens": self.total,
            "by_provider": by_provider,
            "calls": len(self.entries),
        }
