"""Builders of the records that get sealed - Step-0 and every game turn.

Field names follow the reference implementation's sealed records so the two
sides of a league match audit each other without translation. The Step-0
record additionally carries ``github_commit`` - the exact commit hash of the
code playing this game, a mandatory declaration (rulebook ch. 5.5): code may
change between games, but every game must record precisely what ran.
"""

from __future__ import annotations

from typing import Any

from .board import Cell
from .crypto import seal


def state_summary(grid_size: int, position: Cell, barriers: frozenset[Cell]) -> str:
    """A compact, canonical description of the board as this agent sees it.

    Pins the commitment to a specific game situation, so an old commitment
    cannot be replayed in a new context.
    """
    blocked = sorted(barriers)
    return f"grid={grid_size}x{grid_size};self={list(position)};barriers={[list(b) for b in blocked]}"


def step0_record(
    spec: dict[str, Any],
    model: str,
    code_version: str,
    github_commit: str,
    group_name: str,
    sub_game_number: int,
    token_budget: int,
) -> dict[str, Any]:
    """The pre-game declaration: hardware, model, code identity, budget.

    Sealed before the first move; its commitment makes the declared spec and
    the declared commit hash impossible to rewrite afterwards.
    """
    return {
        "step": 0,
        "type": "system_spec",
        "spec": spec,
        "model": model,
        "code_version": code_version,
        "github_commit": github_commit,
        "group_name": group_name,
        "sub_game_number": sub_game_number,
        "token_budget": token_budget,
    }


def turn_record(
    *,
    step: int,
    role: str,
    grid_size: int,
    position: Cell,
    barriers: frozenset[Cell],
    move: str,
    intent: str,
    hint: str,
    tokens_step: int,
    tokens_total: int,
) -> dict[str, Any]:
    """One turn's full truth, sealed before the turn message is sent.

    The position and move live ONLY here - the wire carries just the hash -
    which is what makes the end-of-game audit meaningful.
    """
    return {
        "step": step,
        "role": role,
        "type": "turn",
        "state": state_summary(grid_size, position, barriers),
        "position": list(position),
        "move": f"move:{move}",
        "intent": intent,
        "hint": hint,
        "tokens_step": tokens_step,
        "tokens_total": tokens_total,
    }


def sealed(payload: dict[str, Any]) -> dict[str, Any]:
    """Seal any record built by this module (a thin, explicit alias)."""
    return seal(payload)


def revealed_move(record_payload: dict[str, Any]) -> str:
    """The bare move letter out of a revealed record's ``move:X`` field."""
    value = str(record_payload.get("move", ""))
    return value.split(":", 1)[1] if ":" in value else value


def revealed_position(record_payload: dict[str, Any]) -> Cell:
    """The ``(row, col)`` position out of a revealed record."""
    row, col = record_payload["position"]
    return (int(row), int(col))
