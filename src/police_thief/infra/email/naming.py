"""Lifecycle artifact names and their bytes on disk.

The four per-game files all derive their names from the ``game_id`` (rulebook
ch. 9.3.3), and every file is written in the canonical compact form - the same
bytes the report email attaches, so one hash covers both copies.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ...constants import CONFIG_FILE, DECLARATION_FILE, RESULT_FILE
from ...shared.config_io import canonical_json


def declaration_file_name(game_id: str) -> str:
    """``declaration_<game_id>.json``."""
    return DECLARATION_FILE.format(game_id=game_id)


def config_file_name(game_id: str, mini: int) -> str:
    """``config_<game_id>_gNN.json``."""
    return CONFIG_FILE.format(game_id=game_id, mini=mini)


def result_file_name(game_id: str) -> str:
    """``result_<game_id>.json``."""
    return RESULT_FILE.format(game_id=game_id)


def write_lifecycle_file(directory: str | Path, file_name: str, payload: dict[str, Any]) -> Path:
    """Write one lifecycle file as canonical JSON and return its path.

    Canonical bytes on disk mean the file's hash equals the hash of the same
    payload attached to the report email - one truth, two copies.
    """
    target = Path(directory)
    target.mkdir(parents=True, exist_ok=True)
    path = target / file_name
    path.write_text(canonical_json(payload), encoding="utf-8")
    return path
