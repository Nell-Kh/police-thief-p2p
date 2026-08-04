"""Tests for configuration I/O, canonical serialization and hashing."""

from __future__ import annotations

from pathlib import Path

import pytest

from police_thief.shared.config_io import (
    ConfigError,
    apply_overlay,
    canonical_json,
    read_json,
    read_toml,
    sha256_of,
)


def test_read_json_parses_the_shipped_contract(config_dir: Path) -> None:
    payload = read_json(config_dir / "game.json")
    assert payload["board_and_agents"]["grid_size"] == 7


def test_read_json_rejects_a_missing_file(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="missing configuration file"):
        read_json(tmp_path / "absent.json")


def test_read_json_rejects_malformed_content(tmp_path: Path) -> None:
    broken = tmp_path / "broken.json"
    broken.write_text("{not json", encoding="utf-8")
    with pytest.raises(ConfigError, match="malformed JSON"):
        read_json(broken)


def test_read_json_rejects_a_non_object_top_level(tmp_path: Path) -> None:
    listy = tmp_path / "list.json"
    listy.write_text("[1, 2, 3]", encoding="utf-8")
    with pytest.raises(ConfigError, match="top level must be an object"):
        read_json(listy)


def test_read_toml_parses_the_shipped_private_config(config_dir: Path) -> None:
    payload = read_toml(config_dir / "police" / "game.toml")
    assert payload["network"]["my_port"] == 8801


def test_read_toml_rejects_a_missing_file(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="missing configuration file"):
        read_toml(tmp_path / "absent.toml")


def test_read_toml_rejects_malformed_content(tmp_path: Path) -> None:
    broken = tmp_path / "broken.toml"
    broken.write_text("this is = = not toml", encoding="utf-8")
    with pytest.raises(ConfigError, match="malformed TOML"):
        read_toml(broken)


def test_canonical_json_sorts_keys_and_omits_whitespace() -> None:
    """Both peers must produce byte-identical text for identical content."""
    assert canonical_json({"b": 1, "a": 2}) == '{"a":2,"b":1}'


def test_canonical_json_is_order_independent() -> None:
    first = canonical_json({"x": 1, "y": {"n": 2, "m": 3}})
    second = canonical_json({"y": {"m": 3, "n": 2}, "x": 1})
    assert first == second


def test_sha256_is_stable_across_key_ordering() -> None:
    assert sha256_of({"a": 1, "b": 2}) == sha256_of({"b": 2, "a": 1})


def test_sha256_changes_on_the_smallest_value_change() -> None:
    """SHA-256 is sensitive to every bit - the basis of forgery detection."""
    assert sha256_of({"move": "N"}) != sha256_of({"move": "S"})


def test_sha256_returns_a_64_character_hex_digest() -> None:
    digest = sha256_of({"any": "payload"})
    assert len(digest) == 64
    assert all(char in "0123456789abcdef" for char in digest)


def test_overlay_lets_the_shared_contract_win() -> None:
    """A private file can never weaken a signed condition."""
    merged = apply_overlay({"grid_size": 3}, {"grid_size": 7})
    assert merged["grid_size"] == 7


def test_overlay_merges_nested_sections_key_by_key() -> None:
    private = {"net": {"port": 8801, "timeout": 999}}
    shared = {"net": {"timeout": 30}}
    merged = apply_overlay(private, shared)
    assert merged["net"] == {"port": 8801, "timeout": 30}


def test_overlay_keeps_private_only_keys() -> None:
    merged = apply_overlay({"my_port": 8801}, {"grid_size": 7})
    assert merged["my_port"] == 8801


def test_overlay_does_not_mutate_its_inputs() -> None:
    private = {"section": {"value": 1}}
    shared = {"section": {"value": 2}}
    apply_overlay(private, shared)
    assert private == {"section": {"value": 1}}
