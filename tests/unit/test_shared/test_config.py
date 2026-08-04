"""Tests for ConfigManager behaviour: loading, validation and access.

Assertions on the *values* of the shipped contract live in
``test_contract_values.py``; this module covers the manager itself.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from police_thief.shared.config import ConfigManager
from police_thief.shared.config_io import ConfigError
from police_thief.shared.version import ConfigVersionError


def test_load_builds_a_manager_for_each_role(config_dir: Path) -> None:
    assert ConfigManager.load("police", config_dir).role == "police"
    assert ConfigManager.load("thief", config_dir).role == "thief"


def test_unknown_role_is_rejected(raw_shared, raw_private_police) -> None:
    with pytest.raises(ConfigError, match="unknown role"):
        ConfigManager(raw_shared, raw_private_police, "burglar")


def test_missing_version_is_rejected(raw_shared, raw_private_police) -> None:
    del raw_shared["version"]
    with pytest.raises(ConfigVersionError):
        ConfigManager(raw_shared, raw_private_police, "police")


def test_missing_contract_section_is_rejected(raw_shared, raw_private_police) -> None:
    del raw_shared["scoring"]
    with pytest.raises(ConfigError, match="missing or malformed section 'scoring'"):
        ConfigManager(raw_shared, raw_private_police, "police")


def test_missing_contract_key_is_rejected(raw_shared, raw_private_police) -> None:
    """Strict loading: a peer must never silently guess a binding value."""
    del raw_shared["board_and_agents"]["grid_size"]
    with pytest.raises(ConfigError, match="missing key 'grid_size'"):
        ConfigManager(raw_shared, raw_private_police, "police")


def test_malformed_start_position_is_rejected(raw_shared, raw_private_police) -> None:
    raw_shared["board_and_agents"]["cop_start"] = [0]
    with pytest.raises(ConfigError, match=r"must be a \[row, col\] pair"):
        ConfigManager(raw_shared, raw_private_police, "police")


def test_non_numeric_binding_value_is_rejected(raw_shared, raw_private_police) -> None:
    raw_shared["movement_and_barriers"]["max_barriers"] = "many"
    with pytest.raises(ConfigError, match="malformed value"):
        ConfigManager(raw_shared, raw_private_police, "police")


def test_raw_contract_is_exposed_as_a_copy(config_dir: Path) -> None:
    manager = ConfigManager.load("police", config_dir)
    manager.raw_contract["board_and_agents"] = None
    assert manager.contract.board.grid_size >= 7


def test_both_peers_compute_the_same_contract_digest(config_dir: Path) -> None:
    """Byte-for-byte identical contracts must hash identically on both sides."""
    police = ConfigManager.load("police", config_dir)
    thief = ConfigManager.load("thief", config_dir)
    assert police.config_sha256 == thief.config_sha256
    assert len(police.config_sha256) == 64


def test_digest_changes_when_a_condition_changes(config_copy: Path) -> None:
    """Any contract edit is detectable at negotiation time."""
    original = ConfigManager.load("police", config_copy).config_sha256
    contract_path = config_copy / "game.json"
    payload = json.loads(contract_path.read_text(encoding="utf-8"))
    payload["movement_and_barriers"]["max_barriers"] = 20
    contract_path.write_text(json.dumps(payload), encoding="utf-8")
    assert ConfigManager.load("police", config_copy).config_sha256 != original


def test_private_sections_expose_local_settings(config_dir: Path) -> None:
    manager = ConfigManager.load("police", config_dir)
    assert manager.private("network")["my_port"] == 8801
    assert manager.private_value("trash_talk", "provider") == "claude_api"


def test_absent_private_section_returns_an_empty_mapping(config_dir: Path) -> None:
    manager = ConfigManager.load("police", config_dir)
    assert manager.private("no_such_section") == {}
    assert manager.private_value("no_such_section", "key", "fallback") == "fallback"


def test_non_table_private_section_is_rejected(raw_shared, raw_private_police) -> None:
    raw_private_police["network"] = "not-a-table"
    manager = ConfigManager(raw_shared, raw_private_police, "police")
    with pytest.raises(ConfigError, match="must be a table"):
        manager.private("network")


def test_private_settings_cannot_weaken_the_contract(raw_shared, raw_private_police) -> None:
    """Physics is exposed only through the contract, so a private override is inert."""
    raw_private_police["board_and_agents"] = {"grid_size": 3}
    manager = ConfigManager(raw_shared, raw_private_police, "police")
    assert manager.contract.board.grid_size >= 7


def test_peers_use_separate_private_files(config_dir: Path) -> None:
    """Mandatory separation: the two roles never share configuration."""
    police = ConfigManager.load("police", config_dir)
    thief = ConfigManager.load("thief", config_dir)
    assert police.private("network")["my_port"] != thief.private("network")["my_port"]
