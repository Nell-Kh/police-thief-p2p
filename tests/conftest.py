"""Shared pytest fixtures.

Fixtures load the *shipped* configuration files so the test suite also proves
that ``config/game.json`` itself stays consistent with the rulebook's Mandatory
Parameters Table.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

import pytest

from police_thief.shared.config_io import read_json, read_toml

REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = REPO_ROOT / "config"


@pytest.fixture
def config_dir() -> Path:
    """Path of the shipped ``config/`` directory."""
    return CONFIG_DIR


@pytest.fixture
def raw_shared() -> dict[str, Any]:
    """The shipped shared contract, freshly parsed for each test."""
    return read_json(CONFIG_DIR / "game.json")


@pytest.fixture
def raw_private_police() -> dict[str, Any]:
    """The shipped private configuration of the police peer."""
    return read_toml(CONFIG_DIR / "police" / "game.toml")


@pytest.fixture
def raw_private_thief() -> dict[str, Any]:
    """The shipped private configuration of the thief peer."""
    return read_toml(CONFIG_DIR / "thief" / "game.toml")


@pytest.fixture
def config_copy(tmp_path: Path) -> Path:
    """A writable copy of ``config/`` for tests that mutate configuration."""
    destination = tmp_path / "config"
    shutil.copytree(CONFIG_DIR, destination)
    return destination
