"""Tests for the immutable structural constants."""

from __future__ import annotations

from police_thief import constants as c


def test_roles_are_exactly_cop_and_thief() -> None:
    assert c.ROLES == (c.ROLE_POLICE, c.ROLE_THIEF)


def test_move_set_is_four_orthogonal_directions_plus_stay() -> None:
    assert set(c.MOVE_DELTAS) == {"N", "S", "E", "W", "STAY"}


def test_no_move_is_diagonal() -> None:
    """Rulebook ch. 3.4: a diagonal move is illegal and cannot be expressed."""
    for d_row, d_col in c.MOVE_DELTAS.values():
        assert d_row == 0 or d_col == 0


def test_every_step_displaces_by_exactly_one_cell() -> None:
    for move in c.STEPPING_MOVES:
        d_row, d_col = c.MOVE_DELTAS[move]
        assert abs(d_row) + abs(d_col) == 1


def test_staying_does_not_displace() -> None:
    assert c.MOVE_DELTAS[c.MOVE_STAY] == (0, 0)


def test_north_decreases_the_row_index() -> None:
    """ADR-4: top-left origin, the row index grows downward."""
    assert c.MOVE_DELTAS[c.MOVE_NORTH] == (-1, 0)
    assert c.MOVE_DELTAS[c.MOVE_SOUTH] == (1, 0)


def test_east_increases_the_column_index() -> None:
    assert c.MOVE_DELTAS[c.MOVE_EAST] == (0, 1)
    assert c.MOVE_DELTAS[c.MOVE_WEST] == (0, -1)


def test_move_order_is_a_total_deterministic_ordering() -> None:
    """Deterministic tie-breaking keeps both peers reproducible."""
    assert set(c.MOVE_ORDER) == set(c.MOVE_DELTAS)
    assert len(c.MOVE_ORDER) == len(set(c.MOVE_ORDER))


def test_stepping_moves_exclude_stay() -> None:
    assert c.MOVE_STAY not in c.STEPPING_MOVES
    assert len(c.STEPPING_MOVES) == 4


def test_intent_flags_are_truth_and_lie() -> None:
    assert c.INTENTS == (c.INTENT_TRUTH, c.INTENT_LIE)


def test_lifecycle_file_names_derive_from_the_game_identifier() -> None:
    """Appendix F.3: names derive from game_id so games never mix."""
    assert c.DECLARATION_FILE.format(game_id="abc") == "declaration_abc.json"
    assert c.CONFIG_FILE.format(game_id="abc", mini=1) == "config_abc_g01.json"
    assert c.LOG_FILE.format(game_id="abc", mini=12) == "log_abc_g12.json"
    assert c.RESULT_FILE.format(game_id="abc") == "result_abc.json"


def test_report_address_is_the_only_binding_destination() -> None:
    assert c.AGENT_REPORT_ADDRESS == "rmisegal+uoh26finalgame@gmail.com"
    assert c.LECTURER_ADDRESS == "rmisegal@gmail.com"


def test_canonical_separators_omit_whitespace() -> None:
    assert c.CANONICAL_SEPARATORS == (",", ":")


def test_phase_names_cover_the_full_state_machine() -> None:
    phases = {
        c.PHASE_WAITING,
        c.PHASE_COMPUTING,
        c.PHASE_COMMITTING,
        c.PHASE_AWAITING_REVEAL,
        c.PHASE_VERIFYING,
        c.PHASE_TECHNICAL_LOSS,
    }
    assert len(phases) == 6


def test_termination_events_are_distinct() -> None:
    events = {c.EVENT_CAPTURE, c.EVENT_SURVIVAL, c.EVENT_TIE, c.EVENT_TECHNICAL_LOSS}
    assert len(events) == 4
