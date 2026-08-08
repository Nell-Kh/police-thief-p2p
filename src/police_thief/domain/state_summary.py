"""Canonical state-string encoding and extraction from revealed records.

The commit payload pins its board situation to a compact string (``state``)
rather than structured fields, so this module owns both directions: building
that string (:func:`state_summary`) and reading facts back out of it or of a
revealed turn payload (the ``parse_*``/``revealed_*``/``turn_payloads``
family). The Replay Viewer and the mutual audit both need the same readbacks,
so they share this module instead of re-deriving the parsing rules.
"""

from __future__ import annotations

import ast
from typing import Any

from .board import Cell
from .sealing import revealed_position


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
