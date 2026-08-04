"""Tests for subsystem assembly and the watchdog's recovery record."""

from __future__ import annotations

from pathlib import Path

from police_thief.infra.transport import LoopbackTransport
from police_thief.services.inbound import InboundHandler
from police_thief.services.recovery import Recovery
from police_thief.services.wiring import build_subsystems
from police_thief.shared.config import ConfigManager


def test_wiring_assembles_all_five_subsystems(config_dir: Path) -> None:
    config = ConfigManager.load("police", config_dir)
    opponent = InboundHandler(
        config_sha256=config.config_sha256, scent_lock="x", expect_role="police"
    )
    parts = build_subsystems(
        config, LoopbackTransport(opponent), on_persist=lambda: None, on_shutdown=lambda: None
    )
    assert parts.sdk.role == "police"
    assert parts.phases.state == "WAITING_FOR_OPPONENT"
    assert parts.client.deadlines.timeout_sec == config.contract.network.response_timeout_sec
    assert parts.inbound is not None
    assert parts.watchdog.timeout_sec == config.contract.network.watchdog_timeout_sec


def test_the_inbound_handler_expects_the_opposite_role(config_dir: Path) -> None:
    config = ConfigManager.load("thief", config_dir)
    opponent = InboundHandler(
        config_sha256=config.config_sha256, scent_lock="x", expect_role="thief"
    )
    parts = build_subsystems(
        config, LoopbackTransport(opponent), on_persist=lambda: None, on_shutdown=lambda: None
    )
    assert parts.inbound.expect_role == "police"


def test_a_fresh_recovery_holds_nothing() -> None:
    recovery = Recovery()
    assert recovery.state is None
    assert not recovery.shutdown_called


def test_recovery_keeps_what_the_watchdog_rescued() -> None:
    recovery = Recovery()
    recovery.persist({"step": 7})
    recovery.shutdown()
    assert recovery.state == {"step": 7}
    assert recovery.shutdown_called
