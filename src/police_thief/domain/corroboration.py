"""Corroborating a self-declared capture instead of believing it.

Kit SPEC §3.1's zero-step final lets a thief announce its own capture, which is
what stops a rule-46/47 ending forking the game - one peer settling CAPTURE
while the other waits out the clock and settles TIMEOUT, the contradictory shape
rule 35 zeroes for both. But the announcement is a *claim*, and a capture pays
the thief 5 where the zeroed row it replaces pays 0, so the cop must check it.

The kit's audit (findings F-1/F-2) records two ways that check goes wrong and
one way its fix can:

* reading the claim against the opponent's revealed **position trail**, which a
  peer sealing ``action+state`` simply does not have - so every honest rule-46/47
  ending of such a peer settled ``tamper_forfeit``;
* classifying a ``caught: true`` that echoes the cop's own broadcast cell as an
  *answer* and skipping corroboration entirely - the worse lie, because it pays
  the thief 5 AND the cop 20, so both peers profit and neither looks;
* "fixing" the first by switching the check off, which quietly repeals the
  second. A degradation must **narrow** the check, never disable it.

Everything here is therefore checked against evidence *we* hold: the stones on
our own board, and what the opponent said on our own wire.
"""

from __future__ import annotations

from typing import Any

from .board import Board, BoardError, Cell
from .rules import is_trapped
from .state_summary import grid_size_of, last_turn_payload, parse_barriers, revealed_cell

#: The concession reason that needs re-deriving; other reasons (a trapping
#: barrier, a matching capture claim) are already declared by the cop's own
#: public turn records.
RULE_47 = "boxed in (rule 47)"


def captured_under_our_barriers(
    claimed: Cell, own_barriers: list[Cell], board_size: int
) -> bool:
    """Whether *our own* stones alone already explain a capture on ``claimed``.

    Two ways they can: a barrier standing on the cell itself (rule 46), or every
    neighbour blocked so no legal step remains (rule 47). We placed these stones,
    so this corroborates a claim without trusting one byte of the reveal.
    """
    try:
        board = Board(board_size, frozenset(own_barriers))
    except (ValueError, TypeError, BoardError):
        return False
    return tuple(claimed) in {tuple(cell) for cell in own_barriers} or is_trapped(board, claimed)


def _rule_47_self_check(records: list[dict[str, Any]]) -> list[str]:
    """Re-derive a rule-47 concession from the conceder's own revealed board."""
    concessions = [
        record.get("payload", {})
        for record in records
        if record.get("payload", {}).get("type") == "concession"
    ]
    if not concessions:
        return []
    if str(concessions[-1].get("result", {}).get("how", "")) != RULE_47:
        return []
    last_turn = last_turn_payload(records)
    if last_turn is None:
        return ["concession claims rule-47 but no prior turn establishes a position"]
    position = revealed_cell(last_turn)
    if position is None:
        return []  # a legal schema showing no cell: a note, never an accusation
    try:
        board = Board(grid_size_of(str(last_turn.get("state", ""))),
                      parse_barriers(str(last_turn.get("state", ""))))
    except (ValueError, TypeError, BoardError):
        return []
    if not is_trapped(board, position):
        return ["concession claims rule-47 (boxed in) but a legal move still existed"]
    return []


def verify_concession(
    records: list[dict[str, Any]],
    *,
    board_size: int = 0,
    own_barriers: list[Cell] | None = None,
    conceded_at: Cell | None = None,
    answered_at: Cell | None = None,
) -> list[str]:
    """Violations in a self-declared capture (empty list = corroborated).

    With no claimed cell supplied, falls back to re-deriving a rule-47
    concession from the conceder's own reveal. With one, the claim is checked
    against every source that exists, ANDed:

    * the revealed trail, which must actually have reached the claimed cell;
    * our own barriers, which for a *concession* must already explain a capture
      there. An *answer* skips this one - a capture by overlap involves no stone.

    A peer revealing no cell is using a legal schema (SPEC §3), so the trail
    check is skipped rather than failed - but the barrier check still runs, so a
    position-less concession over a cell our stones never touched is refused.
    """
    claimed = conceded_at
    is_answer = claimed is None and answered_at is not None
    if is_answer:
        claimed = answered_at
    if claimed is None:
        return _rule_47_self_check(records)

    violations: list[str] = []
    last_turn = last_turn_payload(records)
    reached = revealed_cell(last_turn) if last_turn is not None else None
    if reached is not None and tuple(reached) != tuple(claimed):
        kind = "answer" if is_answer else "concession"
        violations.append(
            f"{kind} names {tuple(claimed)} but the revealed trail ended at {tuple(reached)}"
        )
    if (
        not is_answer
        and own_barriers is not None
        and not captured_under_our_barriers(claimed, own_barriers, board_size)
    ):
        violations.append(
            f"concession names {tuple(claimed)}, a cell our barriers never captured"
        )
    return violations
