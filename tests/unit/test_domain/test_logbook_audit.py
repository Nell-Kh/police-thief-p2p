"""Tests for the logbook and the two-layer mutual audit."""

from __future__ import annotations

from pathlib import Path

import pytest

from police_thief.domain.audit import audit_disclosure, verify_concession, verify_trajectory
from police_thief.domain.logbook import Logbook
from police_thief.domain.sealing import step0_record, turn_record
from police_thief.shared.config import ConfigManager


@pytest.fixture
def contract(config_dir: Path):
    return ConfigManager.load("police", config_dir).contract


def walk(book: Logbook, cells_moves: list[tuple[tuple[int, int], str]], role: str) -> None:
    """Seal a trajectory into a book."""
    for step, (position, move) in enumerate(cells_moves, start=1):
        book.append(
            turn_record(
                step=step,
                role=role,
                grid_size=7,
                position=position,
                barriers=frozenset(),
                move=move,
                intent="truth",
                hint="on the move",
                tokens_step=0,
                tokens_total=0,
            )
        )


def thief_book() -> Logbook:
    """A clean thief log: (3,3) -> N -> (2,3) -> E -> (2,4)."""
    book = Logbook("g1", 1, "thief")
    book.append(step0_record({"os": "L"}, "m", "1.00", "abc", "team", 1, 0))
    walk(book, [((2, 3), "N"), ((2, 4), "E")], "thief")
    return book


def test_the_logbook_is_append_only_and_sealed() -> None:
    book = thief_book()
    assert len(book.records) == 3
    assert all({"payload", "nonce", "commit"} <= set(r) for r in book.records)


def test_the_public_view_shows_commitments_only() -> None:
    """During play nothing but step numbers and hashes may be visible."""
    for entry in thief_book().public_view():
        assert set(entry) == {"step", "commit"}


def test_commitment_lookup_by_step() -> None:
    book = thief_book()
    assert book.commitment_for(1) is not None
    assert book.commitment_for(99) is None


def test_the_book_saves_and_loads_with_the_mandated_name(tmp_path: Path) -> None:
    book = thief_book()
    book.close({"type": "survival", "winner": "thief"})
    path = book.save(tmp_path)
    assert path.name == "log_g1_g01.json"
    loaded = Logbook.load(path)
    assert loaded.records == book.records
    assert loaded.result == {"type": "survival", "winner": "thief"}


def test_a_clean_disclosure_passes_both_audit_layers(contract) -> None:
    report = audit_disclosure(thief_book().audit_payload(), contract)
    assert report.hashes_ok
    assert report.physics_ok
    assert report.passed
    assert report.verdict == "Verified OK"


def test_a_forged_hash_is_tampered(contract) -> None:
    disclosure = thief_book().audit_payload()
    disclosure["records"][1]["payload"]["hint"] = "rewritten history"
    report = audit_disclosure(disclosure, contract)
    assert not report.hashes_ok
    assert report.verdict == "TAMPERED"


def test_a_teleport_fails_physics_even_with_clean_hashes(contract) -> None:
    """Our edge over the reference: hash-consistent but impossible logs fail."""
    book = Logbook("g1", 1, "thief")
    walk(book, [((2, 3), "N"), ((6, 6), "E")], "thief")  # (2,3) -> (6,6) is a teleport
    report = audit_disclosure(book.audit_payload(), contract)
    assert report.hashes_ok
    assert not report.physics_ok
    assert report.verdict == "TAMPERED"
    assert any("declared E" in violation for violation in report.violations)


def test_a_wrong_start_cell_fails_physics(contract) -> None:
    book = Logbook("g1", 1, "thief")
    walk(book, [((5, 5), "N")], "thief")  # thief starts at (3,3); (3,3)+N=(2,3)
    assert verify_trajectory(book.records, contract, "thief")


def test_an_off_board_position_fails_physics(contract) -> None:
    book = Logbook("g1", 1, "police")
    book.append(
        turn_record(
            step=1, role="police", grid_size=7, position=(-1, 0), barriers=frozenset(),
            move="N", intent="truth", hint="", tokens_step=0, tokens_total=0,
        )
    )
    violations = verify_trajectory(book.records, contract, "police")
    assert any("off the board" in violation for violation in violations)


def test_a_position_less_record_degrades_and_is_never_an_accusation(contract) -> None:
    """A peer that reveals no cell is using a LEGAL schema, not tampering.

    Kit SPEC §3: the payload schema is not an interop constraint. Treating our
    own schema as everyone's is how a checker calls an honest, sealed, counted
    series *tampered* - the mistake the kit warns "must not get a second home".
    The displacement check simply has no evidence here; it must not fire.
    """
    book = Logbook("g1", 1, "police")
    record = book.append({"type": "turn", "step": 1, "move": "move:N"})
    assert record
    assert verify_trajectory(book.records, contract, "police") == []


def test_a_state_only_record_is_still_fully_checked(contract) -> None:
    """The widened source: no `position` key, but a reference-spelled `state`."""
    book = Logbook("g1", 1, "police")
    book.append({"type": "turn", "step": 1, "move": "move:N",
                 "state": "grid=7x7;self=[5, 5];barriers=[]"})
    violations = verify_trajectory(book.records, contract, "police")
    assert any("stood at" in violation for violation in violations), (
        "a teleport spelled only in `state` must still be caught"
    )


def test_a_malformed_state_degrades_rather_than_resolving_to_a_cell(contract) -> None:
    """SPEC: the parse must be strict; what it cannot read must NOT become a cell."""
    book = Logbook("g1", 1, "police")
    book.append({"type": "turn", "step": 1, "move": "move:N",
                 "state": "grid=7x7;self=banana;barriers=[]"})
    assert verify_trajectory(book.records, contract, "police") == []


def test_an_illegal_move_is_caught_even_without_a_position(contract) -> None:
    """Degrading on the cell must not switch off the checks that need no cell."""
    book = Logbook("g1", 1, "police")
    book.append({"type": "turn", "step": 1, "move": "move:NE"})
    violations = verify_trajectory(book.records, contract, "police")
    assert any("illegal move" in violation for violation in violations)


def _boxed_in_book(*, actually_trapped: bool) -> Logbook:
    """A thief log that stays at its signed start cell (3,3), optionally walled in."""
    book = Logbook("g1", 1, "thief")
    barriers = frozenset({(2, 3), (4, 3), (3, 2), (3, 4)}) if actually_trapped else frozenset()
    book.append(
        turn_record(
            step=1, role="thief", grid_size=7, position=(3, 3), barriers=barriers,
            move="STAY", intent="truth", hint="", tokens_step=0, tokens_total=0,
        )
    )
    book.append({"step": 1, "role": "thief", "type": "concession",
                 "result": {"type": "capture", "winner": "police", "how": "boxed in (rule 47)"}})
    return book


def test_a_true_rule_47_concession_corroborates_and_passes(contract) -> None:
    report = audit_disclosure(_boxed_in_book(actually_trapped=True).audit_payload(), contract)
    assert report.hashes_ok
    assert report.physics_ok
    assert report.verdict == "Verified OK"


def test_a_false_rule_47_concession_is_caught_by_the_audit(contract) -> None:
    """A concession claiming 'boxed in' where a legal step still existed is a lie."""
    report = audit_disclosure(_boxed_in_book(actually_trapped=False).audit_payload(), contract)
    assert report.hashes_ok  # the hashes are perfectly clean - only physics catches this
    assert not report.physics_ok
    assert report.verdict == "TAMPERED"
    assert any("boxed in" in violation for violation in report.violations)


def test_verify_concession_ignores_non_rule47_reasons() -> None:
    """A trapping-barrier or capture-claim win is already covered by the cop's own log."""
    records = [{"payload": {"type": "concession", "result": {"how": "trapping barrier"}}}]
    assert verify_concession(records) == []


def test_verify_concession_flags_a_rule47_claim_with_no_prior_turn() -> None:
    records = [{"payload": {"type": "concession", "result": {"how": "boxed in (rule 47)"}}}]
    assert any("no prior turn" in v for v in verify_concession(records))


def test_verify_concession_degrades_on_an_unreadable_last_turn() -> None:
    """No revealed cell is a legal schema, so the trail check is skipped, not failed."""
    records = [
        {"payload": {"type": "turn", "step": 1}},  # no position or state at all
        {"payload": {"type": "concession", "result": {"how": "boxed in (rule 47)"}}},
    ]
    assert verify_concession(records) == []


# The kit's own probe_f1_concession_corroboration.py cases, ported verbatim.
# Each is a way a self-declared capture goes wrong, or a way its FIX goes wrong.
_TRAIL_45 = [{"payload": {"type": "turn", "step": 1, "move": "move:STAY",
                          "position": [4, 6], "state": "grid=7x7;self=[4, 6];barriers=[]"}},
             {"payload": {"type": "turn", "step": 2, "move": "move:W",
                          "position": [4, 5], "state": "grid=7x7;self=[4, 5];barriers=[]"}}]
_TRAIL_45_BLIND = [{"payload": {"type": "turn", "step": 1, "move": "move:STAY"}},
                   {"payload": {"type": "turn", "step": 2, "move": "move:W"}}]
_TRAIL_22 = [{"payload": {"type": "turn", "step": 1, "move": "move:STAY",
                          "position": [2, 3], "state": "grid=7x7;self=[2, 3];barriers=[]"}},
             {"payload": {"type": "turn", "step": 2, "move": "move:W",
                          "position": [2, 2], "state": "grid=7x7;self=[2, 2];barriers=[]"}}]
# Walks the other way, so the trail ENDS on the cell the cop claimed.
_TRAIL_46 = [{"payload": {"type": "turn", "step": 1, "move": "move:STAY",
                          "position": [4, 5], "state": "grid=7x7;self=[4, 5];barriers=[]"}},
             {"payload": {"type": "turn", "step": 2, "move": "move:E",
                          "position": [4, 6], "state": "grid=7x7;self=[4, 6];barriers=[]"}}]


@pytest.mark.parametrize(
    ("label", "clean", "records", "kwargs"),
    [
        ("F-1 honest concession, reveal carries positions", True, _TRAIL_45,
         {"conceded_at": (4, 5), "own_barriers": [(4, 5)]}),
        ("F-1 the same, reveal carries NO position -> degrades, never accuses",
         True, _TRAIL_45_BLIND, {"conceded_at": (4, 5), "own_barriers": [(4, 5)]}),
        ("F-1 position-less AND not captured under our barriers -> STILL refused",
         False, _TRAIL_45_BLIND, {"conceded_at": (2, 2), "own_barriers": [(4, 5)]}),
        ("a concession over a cell our barriers never touched", False, _TRAIL_22,
         {"conceded_at": (2, 2), "own_barriers": [(4, 5)]}),
        ("a concession the revealed trail never reached", False, _TRAIL_45,
         {"conceded_at": (6, 6), "own_barriers": [(5, 6), (6, 5)]}),
        ("F-2 a FALSE answer echoing our claimed cell -> refused, not believed",
         False, _TRAIL_22, {"answered_at": (4, 6)}),
        ("F-2 a TRUE answer, trail ends where the answer said", True,
         _TRAIL_46, {"answered_at": (4, 6)}),
        ("F-2 a position-less answer degrades rather than accusing", True,
         _TRAIL_45_BLIND, {"answered_at": (4, 6)}),
    ],
)
def test_the_kit_f1_f2_corroboration_cases(label, clean, records, kwargs) -> None:
    violations = verify_concession(records, board_size=7, **kwargs)
    assert (violations == []) is clean, f"{label}: {violations}"


@pytest.mark.parametrize(
    "disclosure",
    [
        "not even a dict",
        {"sender": "thief", "records": "records-should-be-a-list"},
        {"sender": "thief", "records": 42},
        {"sender": "thief", "records": ["a-record-should-be-an-object", 7]},
        {"sender": "thief", "records": [{"payload": 5, "nonce": None, "commit": 9}]},
    ],
)
def test_a_malformed_disclosure_fails_the_audit_without_crashing(contract, disclosure) -> None:
    """A hostile peer's broken records forfeit the peer - they never crash us.

    Without the structural guard each of these reaches a ``.get`` on a string
    or an int deep in verification and raises AttributeError, which - not being
    a contained network failure - would crash the whole series. The audit must
    instead return a clean failed verdict, so the driver scores a tamper
    forfeit and plays on.
    """
    report = audit_disclosure(disclosure, contract)
    assert report.passed is False
    assert report.verdict == "TAMPERED"


def test_a_structurally_sound_but_empty_disclosure_still_parses(contract) -> None:
    """The guard rejects broken structure only - a legal empty log is not broken."""
    report = audit_disclosure({"sender": "thief", "records": []}, contract)
    assert report.hashes_ok is True  # nothing to contradict; not a crash, not a forfeit
