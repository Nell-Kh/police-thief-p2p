"""Tests for the pre-game terms exchange and its locks."""

from __future__ import annotations

from pathlib import Path

import pytest

from police_thief.domain.negotiation import (
    TermsRejectedError,
    build_terms,
    validate_terms,
)
from police_thief.shared.config import ConfigManager


@pytest.fixture
def police(config_dir: Path) -> ConfigManager:
    return ConfigManager.load("police", config_dir)


@pytest.fixture
def thief(config_dir: Path) -> ConfigManager:
    return ConfigManager.load("thief", config_dir)


def terms_of(config: ConfigManager, **overrides):
    base = build_terms(
        config, peer_id="team-x", games_played=2, sub_game=1, step0_commit="c" * 64
    )
    base.update(overrides)
    return base


def test_terms_carry_every_binding_lock(police: ConfigManager) -> None:
    terms = terms_of(police)
    assert terms["config_sha256"] == police.config_sha256
    assert len(terms["scent_lock"]) == 64
    assert terms["games_played"] == 2
    assert terms["step0_commit"] == "c" * 64


def test_matching_terms_are_accepted(police: ConfigManager, thief: ConfigManager) -> None:
    """Two peers with byte-identical contracts accept each other."""
    accepted = validate_terms(
        terms_of(thief),
        our_config_sha256=police.config_sha256,
        our_scent_lock=terms_of(police)["scent_lock"],
        expect_role="thief",
    )
    assert accepted["peer_id"] == "team-x"


def test_a_contract_mismatch_is_refused(police: ConfigManager, thief: ConfigManager) -> None:
    with pytest.raises(TermsRejectedError, match="contract mismatch"):
        validate_terms(
            terms_of(thief, config_sha256="f" * 64),
            our_config_sha256=police.config_sha256,
            our_scent_lock=terms_of(police)["scent_lock"],
            expect_role="thief",
        )


def test_a_scent_model_mismatch_is_refused(police: ConfigManager, thief: ConfigManager) -> None:
    """Different decay physics means the race must not start (ch. 4.5 lock)."""
    with pytest.raises(TermsRejectedError, match="scent-model mismatch"):
        validate_terms(
            terms_of(thief, scent_lock="e" * 64),
            our_config_sha256=police.config_sha256,
            our_scent_lock=terms_of(police)["scent_lock"],
            expect_role="thief",
        )


def test_the_wrong_role_is_refused(police: ConfigManager) -> None:
    with pytest.raises(TermsRejectedError, match="expected terms from 'thief'"):
        validate_terms(
            terms_of(police),
            our_config_sha256=police.config_sha256,
            our_scent_lock=terms_of(police)["scent_lock"],
            expect_role="thief",
        )


def test_a_missing_game_count_is_refused(police: ConfigManager, thief: ConfigManager) -> None:
    """The diversity-incentive declaration is mandatory at game start."""
    with pytest.raises(TermsRejectedError, match="games_played"):
        validate_terms(
            terms_of(thief, games_played=-1),
            our_config_sha256=police.config_sha256,
            our_scent_lock=terms_of(police)["scent_lock"],
            expect_role="thief",
        )


def test_a_missing_step0_commitment_is_refused(
    police: ConfigManager, thief: ConfigManager
) -> None:
    with pytest.raises(TermsRejectedError, match="step0 commitment"):
        validate_terms(
            terms_of(thief, step0_commit=""),
            our_config_sha256=police.config_sha256,
            our_scent_lock=terms_of(police)["scent_lock"],
            expect_role="thief",
        )


def test_non_object_terms_are_refused(police: ConfigManager) -> None:
    with pytest.raises(TermsRejectedError, match="must be an object"):
        validate_terms(
            ["nope"],  # type: ignore[arg-type]
            our_config_sha256=police.config_sha256,
            our_scent_lock="x",
            expect_role="thief",
        )
