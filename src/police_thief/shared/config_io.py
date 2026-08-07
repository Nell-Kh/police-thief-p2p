"""Configuration file I/O, canonical serialization and hashing.

Split out of :mod:`shared.config` to honour the 150-line file rule. This module
knows how to *read bytes* and *hash them*; it holds no game semantics.

JSON carries everything the two peers must agree on (and is therefore signed);
TOML carries private per-peer settings only (rulebook Appendix B).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

try:
    import tomllib
except ImportError:
    import tomli as tomllib

from ..constants import CANONICAL_SEPARATORS


class ConfigError(ValueError):
    """Raised when a configuration file is missing or malformed."""


def read_json(path: str | Path) -> dict[str, Any]:
    """Read a JSON configuration file into a mapping."""
    file_path = Path(path)
    if not file_path.is_file():
        raise ConfigError(f"missing configuration file: {file_path}")
    try:
        with file_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except json.JSONDecodeError as exc:
        raise ConfigError(f"malformed JSON in {file_path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ConfigError(f"{file_path}: top level must be an object")
    return payload


def read_toml(path: str | Path) -> dict[str, Any]:
    """Read a TOML configuration file into a mapping."""
    file_path = Path(path)
    if not file_path.is_file():
        raise ConfigError(f"missing configuration file: {file_path}")
    try:
        with file_path.open("rb") as handle:
            return tomllib.load(handle)
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"malformed TOML in {file_path}: {exc}") from exc


def canonical_json(payload: Any) -> str:
    """Serialize a payload canonically: sorted keys and fixed separators.

    Both peers must produce byte-identical text for the same logical content,
    otherwise their SHA-256 signatures would differ for identical data.
    """
    return json.dumps(
        payload,
        sort_keys=True,
        separators=CANONICAL_SEPARATORS,
        ensure_ascii=False,
    )


def sha256_of(payload: Any) -> str:
    """Return the hex SHA-256 digest of a payload's canonical serialization."""
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def apply_overlay(private: dict[str, Any], shared: dict[str, Any]) -> dict[str, Any]:
    """Overlay the signed shared contract on top of a private mapping.

    Rulebook Appendix B closing rule: where the shared ``game.json`` defines a
    key, its value wins - a private file can never weaken a signed condition.
    The merge is recursive so nested sections are overlaid key by key rather
    than replaced wholesale.

    Args:
        private: the per-peer mapping (loses every conflict).
        shared: the signed shared mapping (wins every conflict).

    Returns:
        A new merged mapping; neither input is mutated.
    """
    merged: dict[str, Any] = dict(private)
    for key, shared_value in shared.items():
        private_value = merged.get(key)
        if isinstance(private_value, dict) and isinstance(shared_value, dict):
            merged[key] = apply_overlay(private_value, shared_value)
        else:
            merged[key] = shared_value
    return merged
