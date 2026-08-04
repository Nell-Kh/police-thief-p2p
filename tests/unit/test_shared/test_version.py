"""Tests for explicit version tracking and compatibility validation."""

from __future__ import annotations

import pytest

from police_thief.shared import version as version_module
from police_thief.shared.version import (
    CONFIG_VERSION,
    CONTRACT_SCHEMA_VERSION,
    ConfigVersionError,
    check_config_version,
    check_schema_version,
)


def test_code_version_starts_at_the_mandated_baseline() -> None:
    """Guidelines ch. 8.1: versioning starts at 1.00 and never regresses."""
    assert float(version_module.__version__) >= 1.00


def test_config_version_baseline_is_declared() -> None:
    assert float(CONFIG_VERSION) >= 1.00


def test_check_config_version_accepts_the_current_version() -> None:
    assert check_config_version({"version": CONFIG_VERSION}) == CONFIG_VERSION


def test_check_config_version_accepts_a_newer_version() -> None:
    assert check_config_version({"version": "2.50"}) == "2.50"


def test_check_config_version_rejects_a_missing_version() -> None:
    with pytest.raises(ConfigVersionError, match="missing mandatory 'version'"):
        check_config_version({}, label="config/game.json")


def test_check_config_version_rejects_an_older_version() -> None:
    with pytest.raises(ConfigVersionError, match="older than required"):
        check_config_version({"version": "0.90"})


def test_check_schema_version_accepts_the_implemented_schema() -> None:
    contract = {"schema_version": CONTRACT_SCHEMA_VERSION}
    assert check_schema_version(contract) == CONTRACT_SCHEMA_VERSION


def test_check_schema_version_rejects_a_foreign_schema() -> None:
    """A schema mismatch means the peers cannot hold identical contracts."""
    with pytest.raises(ConfigVersionError, match="schema_version"):
        check_schema_version({"schema_version": "9.9"})


def test_check_schema_version_rejects_an_absent_schema() -> None:
    with pytest.raises(ConfigVersionError):
        check_schema_version({})


def test_shipped_shared_config_declares_compatible_versions(raw_shared) -> None:
    """The shipped contract must satisfy both version gates."""
    assert check_config_version(raw_shared, label="config/game.json")
    assert check_schema_version(raw_shared) == CONTRACT_SCHEMA_VERSION


@pytest.mark.parametrize("role", ["police", "thief"])
def test_shipped_private_configs_declare_a_version(
    role: str, raw_private_police, raw_private_thief
) -> None:
    raw = raw_private_police if role == "police" else raw_private_thief
    assert check_config_version(raw, label=f"config/{role}/game.toml")
