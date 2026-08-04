"""Explicit version tracking for code and configuration.

Guidelines ch. 8.1: both the code and the configuration files carry an explicit
version starting at 1.00. The application validates configuration-version
compatibility at startup, so a peer never plays with a contract it cannot read.
"""

from typing import Final

#: Version of this code base. Bumped on every significant change.
__version__: Final[str] = "1.00"

#: Minimum configuration ``version`` this code accepts.
CONFIG_VERSION: Final[str] = "1.00"

#: Shared-contract ``schema_version`` this code implements (rulebook Appendix B).
CONTRACT_SCHEMA_VERSION: Final[str] = "1.2"


class ConfigVersionError(ValueError):
    """Raised when a configuration file's version is missing or incompatible."""


def _as_float(label: str, value: object) -> float:
    """Parse a dotted version string into a comparable float."""
    try:
        return float(str(value))
    except (TypeError, ValueError) as exc:  # pragma: no cover - defensive
        raise ConfigVersionError(f"{label}: unreadable version {value!r}") from exc


def check_config_version(config: dict, label: str = "config") -> str:
    """Validate that a configuration mapping carries a compatible version.

    Args:
        config: parsed configuration mapping.
        label: human-readable name used in error messages.

    Returns:
        The version string found in the mapping.

    Raises:
        ConfigVersionError: if ``version`` is absent or older than
            :data:`CONFIG_VERSION`.
    """
    if "version" not in config:
        raise ConfigVersionError(f"{label}: missing mandatory 'version' key")
    found = str(config["version"])
    if _as_float(label, found) < _as_float(label, CONFIG_VERSION):
        raise ConfigVersionError(
            f"{label}: version {found} is older than required {CONFIG_VERSION}"
        )
    return found


def check_schema_version(contract: dict) -> str:
    """Validate the shared contract's ``schema_version``.

    A mismatch means the two peers implement different contract layouts, which
    would break the byte-for-byte identity the rulebook demands, so we refuse.
    """
    found = str(contract.get("schema_version", ""))
    if found != CONTRACT_SCHEMA_VERSION:
        raise ConfigVersionError(
            f"contract: schema_version {found!r} != expected {CONTRACT_SCHEMA_VERSION!r}"
        )
    return found
