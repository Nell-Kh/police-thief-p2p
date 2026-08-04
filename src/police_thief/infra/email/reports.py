"""The four lifecycle JSON files of one league game (rulebook ch. 9.3.3).

One shared ``game_uid`` threads through all four so files from different
games can never mix; each file name derives from the ``game_id``. The
declaration freezes everything that must not change mid-game (teams, repos,
servers, hardware, model, token cap) under a cryptographic seal; the config
file locks the agreed physics per mini-game; the logbook is written by
:mod:`police_thief.domain.logbook`; and the result file - the one mailed to
the report address - totals every mini-game with commit ids and tokens.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ...constants import CONFIG_FILE, DECLARATION_FILE, RESULT_FILE
from ...domain.crypto import seal
from ...shared.config_io import canonical_json, sha256_of


def declaration_payload(
    *,
    game_uid: str,
    game_id: str,
    teams: dict[str, Any],
    repositories: dict[str, str],
    mcp_servers: dict[str, str],
    hardware: dict[str, Any],
    llm_model: str,
    token_budget: int,
    started_at: str,
    ended_at: str | None = None,
) -> dict[str, Any]:
    """The sealed pre-game declaration - everything constant, frozen.

    Args:
        teams: both teams' names and members.
        repositories: the four GitHub links (cop and thief, both teams).
        mcp_servers: each side's public FastMCP address.
        hardware: this side's signed hardware spec (``sysinfo.hardware_spec``).
        started_at / ended_at: ISO timestamps; the end is stamped at close.
    """
    payload = {
        "type": "declaration",
        "game_uid": game_uid,
        "game_id": game_id,
        "teams": teams,
        "repositories": repositories,
        "mcp_servers": mcp_servers,
        "hardware": hardware,
        "llm_model": llm_model,
        "token_budget": token_budget,
        "started_at": started_at,
        "ended_at": ended_at,
    }
    return seal(payload)


def config_payload(
    game_uid: str, game_id: str, mini: int, contract_raw: dict[str, Any]
) -> dict[str, Any]:
    """One mini-game's locked shared configuration, hash included.

    The embedded sha256 is the same value both sides compared during
    negotiation - the reader can re-derive it from ``contract`` alone.
    """
    return {
        "type": "config",
        "game_uid": game_uid,
        "game_id": game_id,
        "sub_game_number": mini,
        "contract": contract_raw,
        "config_sha256": sha256_of(contract_raw),
    }


def result_payload(
    *,
    game_uid: str,
    game_id: str,
    teams: dict[str, Any],
    repositories: dict[str, str],
    mini_games: list[dict[str, Any]],
    tokens_total: int,
    agreement: dict[str, str],
) -> dict[str, Any]:
    """The final result report - the mandatory JSON mailed to the lecturer.

    Args:
        mini_games: one entry per mini-game with its number, the exact
            ``github_commit`` that played it, each side's points and the
            terminating event.
        agreement: both sides' SHA-256 confirmations of the agreed result.

    The cumulative totals are recomputed here from the per-mini-game rows,
    so the summary can never drift from its own details.
    """
    totals = {
        "police": sum(int(game.get("police_points", 0)) for game in mini_games),
        "thief": sum(int(game.get("thief_points", 0)) for game in mini_games),
    }
    return {
        "type": "result",
        "game_uid": game_uid,
        "game_id": game_id,
        "teams": teams,
        "repositories": repositories,
        "mini_games": mini_games,
        "totals": totals,
        "tokens_total": tokens_total,
        "agreement": agreement,
    }


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

    Canonical bytes on disk mean the file's hash equals the hash of the
    same payload attached to the report email - one truth, two copies.
    """
    target = Path(directory)
    target.mkdir(parents=True, exist_ok=True)
    path = target / file_name
    path.write_text(canonical_json(payload), encoding="utf-8")
    return path
