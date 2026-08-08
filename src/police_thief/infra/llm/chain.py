"""Provider composition: throttling, fallback, and construction from config.

Two wrappers implement the rulebook's cost discipline:

* :class:`ThrottledProvider` - the paid model runs only once every
  ``every_n_steps`` turns; the free template covers the rest.
* :class:`FallbackProvider` - any provider failure (network, key, quota,
  exhausted budget) silently falls back to the template, so the verbal layer
  can never cost a game.
"""

from __future__ import annotations

from .base import HintProvider, HintRequest, ProviderError
from .ledger import TokenLedger
from .template import TemplateProvider


class FallbackProvider(HintProvider):
    """Try the primary provider; on any failure, use the backup."""

    name = "fallback"

    def __init__(self, primary: HintProvider, backup: HintProvider) -> None:
        """Wrap ``primary`` with ``backup`` as the safety net."""
        self._primary = primary
        self._backup = backup
        self.fallbacks_used = 0

    def generate(self, request: HintRequest) -> str:
        """Generate via the primary, falling back on :class:`ProviderError`."""
        try:
            return self._primary.generate(request)
        except ProviderError:
            self.fallbacks_used += 1
            return self._backup.generate(request)


class ThrottledProvider(HintProvider):
    """Run the expensive provider once every ``every_n_steps``; else the cheap one."""

    name = "throttled"

    def __init__(self, expensive: HintProvider, cheap: HintProvider, every_n_steps: int) -> None:
        """Wrap the pair; ``every_n_steps`` below 1 means never throttle."""
        self._expensive = expensive
        self._cheap = cheap
        self._every = max(1, every_n_steps)

    def generate(self, request: HintRequest) -> str:
        """Route the request by step number."""
        if request.step % self._every == 0:
            return self._expensive.generate(request)
        return self._cheap.generate(request)


class BudgetGuard(HintProvider):
    """Refuse paid calls once the agreed token budget is exhausted."""

    name = "budget_guard"

    def __init__(self, inner: HintProvider, ledger: TokenLedger) -> None:
        """Wrap a paid provider with the series budget."""
        self._inner = inner
        self._ledger = ledger

    def generate(self, request: HintRequest) -> str:
        """Delegate while budget remains; otherwise fail into the fallback.

        Raises:
            ProviderError: when the series token budget is exhausted.
        """
        if self._ledger.exhausted:
            raise ProviderError("series token budget exhausted")
        return self._inner.generate(request)


def build_provider(
    provider_name: str,
    every_n_steps: int,
    ledger: TokenLedger,
    model: str = "",
    timeout_sec: float = 10.0,
) -> HintProvider:
    """Assemble the provider chain the private TOML selects.

    ``template`` stands alone. Every paid mode is wrapped as:
    throttle(budget_guard(paid), template) inside a final fallback to the
    template - the guarantees compose.

    Args:
        timeout_sec: wall-clock ceiling on one paid request, so a stalled
            network can never hold a turn past the opponent's watchdog.
    """
    template = TemplateProvider()
    if provider_name == "template":
        return template
    if provider_name == "ollama":
        from .ollama import OllamaProvider

        paid: HintProvider = OllamaProvider(model=model, ledger=ledger)
    elif provider_name == "claude_api":
        from .claude_api import ClaudeApiProvider

        paid = ClaudeApiProvider(model=model, ledger=ledger, timeout_sec=timeout_sec)
    elif provider_name == "claude_cli":
        from .claude_cli import ClaudeCliProvider

        paid = ClaudeCliProvider(ledger=ledger)
    else:
        raise ValueError(f"unknown verbal provider {provider_name!r}")
    guarded = BudgetGuard(paid, ledger)
    throttled = ThrottledProvider(guarded, template, every_n_steps)
    return FallbackProvider(throttled, template)
