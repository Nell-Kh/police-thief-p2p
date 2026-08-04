"""Tests for the replay session - the Replay Viewer's verified engine."""

from __future__ import annotations

from pathlib import Path

import pytest

from police_thief.domain.logbook import Logbook
from police_thief.domain.replay import ReplaySession, grid_size_of, parse_barriers
from police_thief.domain.sealing import turn_record


@pytest.fixture
def book() -> Logbook:
    """A three-turn thief log with a barrier appearing at step 2."""
    book = Logbook("replay", 1, "thief")
    walls: list[tuple[int, int]] = []
    for step, (position, move) in enumerate(
        [((2, 3), "N"), ((2, 4), "E"), ((2, 5), "E")], start=1
    ):
        if step == 2:
            walls.append((1, 1))
        book.append(
            turn_record(
                step=step, role="thief", grid_size=7, position=position,
                barriers=frozenset(walls), move=move, intent="truth",
                hint=f"hint {step}", tokens_step=0, tokens_total=0,
            )
        )
    return book


def test_state_summary_parsing_round_trips() -> None:
    state = "grid=7x7;self=[2, 4];barriers=[[1, 1], [3, 3]]"
    assert grid_size_of(state) == 7
    assert parse_barriers(state) == [(1, 1), (3, 3)]


def test_malformed_state_fields_degrade_gracefully() -> None:
    assert grid_size_of("nonsense") == 0
    assert parse_barriers("barriers=oops") == []
    assert parse_barriers("no marker at all") == []


def test_the_session_walks_forward_and_back_within_bounds(book: Logbook) -> None:
    session = ReplaySession(book)
    assert session.scene()["step"] == 1
    session.forward()
    session.forward()
    assert session.scene()["step"] == 3
    session.forward()  # already at the last turn
    assert session.scene()["step"] == 3
    session.back()
    session.back()
    session.back()  # already at the first turn
    assert session.scene()["step"] == 1


def test_every_step_of_a_clean_log_is_verified_ok(book: Logbook) -> None:
    session = ReplaySession(book)
    for _ in range(3):
        assert session.current_verdict() == "Verified OK"
        session.forward()
    assert session.overall_verdict() == "Verified OK"


def test_the_scene_reconstructs_the_revealed_board(book: Logbook) -> None:
    session = ReplaySession(book)
    session.forward()
    scene = session.scene()
    assert scene["step"] == 2
    assert scene["position"] == (2, 4)
    assert scene["barriers"] == [(1, 1)]
    assert scene["grid"] == 7
    assert scene["hint"] == "hint 2"
    assert scene["verdict"] == "Verified OK"


def test_one_edited_step_turns_tampered_and_voids_the_match(book: Logbook) -> None:
    """The tiniest change in past data voids the whole match, no appeal."""
    book.records[1]["payload"]["hint"] = "history, rewritten"
    session = ReplaySession(book)
    session.forward()
    assert session.current_verdict() == "TAMPERED"
    assert session.overall_verdict() == "TAMPERED"
    session.back()
    assert session.current_verdict() == "Verified OK"  # the step itself is intact
    assert session.overall_verdict() == "TAMPERED"  # but the match stays void


def test_a_session_loads_from_a_saved_file(book: Logbook, tmp_path: Path) -> None:
    path = book.save(tmp_path)
    session = ReplaySession.load(path)
    assert session.overall_verdict() == "Verified OK"
    assert session.scene()["position"] == (2, 3)


def test_an_empty_log_is_handled(tmp_path: Path) -> None:
    session = ReplaySession(Logbook("empty", 1, "police"))
    assert session.current is None
    assert session.scene()["position"] is None
    assert session.overall_verdict() == "Verified OK"
    assert session.forward() == 0 and session.back() == 0
