"""Builders of the records that get sealed - Step-0 and every game turn.

Field names follow the reference implementation's sealed records so the two
sides of a league match audit each other without translation. The Step-0
record additionally carries ``github_commit`` - the exact commit hash of the
code playing this game, a mandatory declaration (rulebook ch. 5.5): code may
change between games, but every game must record precisely what ran.
"""

from __future__ import annotations

import ast
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


def parse_barriers(state: str) -> list[Cell]:
    """The barrier list out of a sealed record's canonical state summary.

    Shared by the Replay Viewer and the mutual audit's concession check - both
    need to reconstruct the board a state summary describes.
    """
    marker = "barriers="
    index = state.find(marker)
    if index < 0:
        return []
    try:
        cells = ast.literal_eval(state[index + len(marker):])
        return [(int(row), int(col)) for row, col in cells]
    except (ValueError, SyntaxError, TypeError):
        return []


def grid_size_of(state: str) -> int:
    """The board side out of a state summary like ``grid=7x7;...``."""
    try:
        return int(state.split("grid=", 1)[1].split("x", 1)[0])
    except (IndexError, ValueError):
        return 0


def turn_payloads(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """The revealed turn payloads of a disclosed log, in step order."""
    turns = [
        record.get("payload", {})
        for record in records
        if record.get("payload", {}).get("type") == "turn"
    ]
    return sorted(turns, key=lambda payload: payload.get("step", 0))


def last_turn_payload(records: list[dict[str, Any]]) -> dict[str, Any] | None:
    """The most recent revealed turn, or ``None`` if the log has no turn at all."""
    turns = turn_payloads(records)
    return turns[-1] if turns else None


def revealed_cell(payload: dict[str, Any]) -> Cell | None:
    """The revealed position of one turn, from any legal spelling, or ``None``.

    Tries the reference's ``position`` key first, then the ``self=`` field of a
    reference-spelled ``state`` summary, then gives up. ``None`` means "this
    peer's schema does not show me a cell" - a *legal* schema (kit SPEC §3), not
    evidence of anything, so callers must degrade rather than accuse.
    """
    try:
        return revealed_position(payload)
    except (KeyError, ValueError, TypeError):
        return parse_self_cell(str(payload.get("state", "")))


def parse_self_cell(state: str) -> Cell | None:
    """The ``self=`` cell of a reference-spelled state summary, or ``None``.

    A second, *optional* source for a revealed position: kit SPEC §3 says the
    payload schema is not an interop constraint, so a peer may seal ``state``
    without a separate ``position`` key. Widening where the trail comes from is
    explicitly allowed - under one hard condition the spec spells out: the parse
    must be STRICT, and anything it cannot read confidently must degrade to
    ``None`` rather than resolve to a cell. A loose parse that mis-reads a
    malformed summary into the *wrong* cell would not widen verification; it
    would invent a new way to accuse an honest peer.
    """
    marker = "self="
    index = state.find(marker)
    if index < 0:
        return None
    tail = state[index + len(marker):].split(";", 1)[0]
    try:
        cell = ast.literal_eval(tail)
    except (ValueError, SyntaxError, TypeError):
        return None
    if not (isinstance(cell, (list, tuple)) and len(cell) == 2):
        return None
    row, col = cell
    if isinstance(row, bool) or isinstance(col, bool):  # bool is an int subclass
        return None
    if not (isinstance(row, int) and isinstance(col, int)):
        return None
    return (row, col)


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
