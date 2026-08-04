"""Tests for the lifecycle reports - sealed declaration, locked config, totals."""

from __future__ import annotations

import json
from pathlib import Path

from police_thief.constants import AGENT_REPORT_ADDRESS
from police_thief.domain.crypto import verify
from police_thief.infra.email.reports import (
    config_file_name,
    config_payload,
    declaration_file_name,
    declaration_payload,
    result_file_name,
    result_payload,
    write_lifecycle_file,
)
from police_thief.shared.config_io import canonical_json, sha256_of

TEAMS = {"A": {"name": "nell", "members": ["nell"]}, "B": {"name": "rivals", "members": ["x"]}}
REPOS = {
    "A_police": "https://github.com/nell/police-agent",
    "A_thief": "https://github.com/nell/thief-agent",
    "B_police": "https://github.com/x/police",
    "B_thief": "https://github.com/x/thief",
}


def make_declaration() -> dict:
    return declaration_payload(
        game_uid="uid-7", game_id="G7", teams=TEAMS, repositories=REPOS,
        mcp_servers={"police": "https://a.example:8801", "thief": "https://b.example:8802"},
        hardware={"cpu": "arm", "ram_gb": 16}, llm_model="claude-haiku",
        token_budget=200000, started_at="2026-08-04T10:00:00Z",
    )


def test_the_declaration_is_sealed_and_verifiable() -> None:
    record = make_declaration()
    assert verify(record["payload"], record["nonce"], record["commit"])
    frozen = record["payload"]
    assert frozen["repositories"] == REPOS  # all four links - ch. 9.4
    assert frozen["token_budget"] == 200000
    assert frozen["ended_at"] is None  # stamped only at close


def test_the_config_file_locks_the_contract_with_its_hash() -> None:
    contract = {"board_and_agents": {"grid_size": 7}}
    record = config_payload("uid-7", "G7", 3, contract)
    assert record["config_sha256"] == sha256_of(contract)
    assert record["sub_game_number"] == 3


def test_the_result_totals_are_recomputed_from_the_details() -> None:
    minis = [
        {"number": 1, "github_commit": "aaa1111", "police_points": 20, "thief_points": 0,
         "event": "capture"},
        {"number": 2, "github_commit": "bbb2222", "police_points": 5, "thief_points": 10,
         "event": "survival"},
    ]
    record = result_payload(
        game_uid="uid-7", game_id="G7", teams=TEAMS, repositories=REPOS,
        mini_games=minis, tokens_total=1234,
        agreement={"ours": "a" * 64, "theirs": "a" * 64},
    )
    assert record["totals"] == {"police": 25, "thief": 10}
    assert record["mini_games"][0]["github_commit"] == "aaa1111"
    assert record["tokens_total"] == 1234


def test_file_names_derive_from_the_game_id() -> None:
    assert declaration_file_name("G7") == "declaration_G7.json"
    assert config_file_name("G7", 4) == "config_G7_g04.json"
    assert result_file_name("G7") == "result_G7.json"


def test_lifecycle_files_are_canonical_json_on_disk(tmp_path: Path) -> None:
    record = config_payload("uid-7", "G7", 1, {"a": 1})
    path = write_lifecycle_file(tmp_path / "results", config_file_name("G7", 1), record)
    text = path.read_text(encoding="utf-8")
    assert text == canonical_json(record)  # byte-identical to the mailed copy
    assert json.loads(text) == record


def test_the_binding_report_address_is_the_rulebooks() -> None:
    assert AGENT_REPORT_ADDRESS == "rmisegal+uoh26finalgame@gmail.com"
