"""Verbal-layer providers: template, Ollama, Claude API and Claude CLI.

The movement decision never lives here; these produce only the natural-language
hint, under the signed word cap, with every model token metered.
"""

from .base import HintProvider, HintRequest, ProviderError, clip_words
from .chain import BudgetGuard, FallbackProvider, ThrottledProvider, build_provider
from .ledger import TokenLedger
from .template import TemplateProvider

__all__ = [
    "BudgetGuard",
    "FallbackProvider",
    "HintProvider",
    "HintRequest",
    "ProviderError",
    "TemplateProvider",
    "ThrottledProvider",
    "TokenLedger",
    "build_provider",
    "clip_words",
]
