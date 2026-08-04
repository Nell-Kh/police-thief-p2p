"""Shared infrastructure: configuration, versioning, gatekeeper, system info.

Modules in this package are dependency-free utilities consumed by every other
layer. They must not import from ``domain``, ``services`` or ``infra``.
"""

from .config import ConfigManager
from .config_io import ConfigError, canonical_json, sha256_of
from .schema import GameContract
from .version import CONFIG_VERSION, ConfigVersionError, __version__

__all__ = [
    "CONFIG_VERSION",
    "ConfigError",
    "ConfigManager",
    "ConfigVersionError",
    "GameContract",
    "__version__",
    "canonical_json",
    "sha256_of",
]
