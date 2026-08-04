"""Tests for the HTTP transport and the peer boot, all network mocked."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from police_thief.infra.http_transport import McpHttpTransport, _extract_reply
from police_thief.infra.transport import TransportError
from police_thief.services import peer_boot
from police_thief.services.peer_boot import BootReport, build_peer, check_connectivity
from police_thief.shared.config import ConfigManager


def test_a_non_http_url_is_rejected() -> None:
    with pytest.raises(TransportError, match="must be http"):
        McpHttpTransport("ftp://somewhere/mcp")


def test_the_url_is_exposed() -> None:
    transport = McpHttpTransport("https://tunnel.example/mcp")
    assert transport.url == "https://tunnel.example/mcp"


def test_send_returns_the_reply_dict(monkeypatch: pytest.MonkeyPatch) -> None:
    transport = McpHttpTransport("http://127.0.0.1:9/mcp")

    async def fake_call(_tool: str, _payload: dict) -> dict:
        return {"accepted": True}

    monkeypatch.setattr(transport, "_call", fake_call)
    assert transport.send("handshake", {})["accepted"]


def test_an_unexpected_failure_becomes_a_transport_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    transport = McpHttpTransport("http://127.0.0.1:9/mcp")

    async def explode(_tool: str, _payload: dict) -> dict:
        raise RuntimeError("connection reset")

    monkeypatch.setattr(transport, "_call", explode)
    with pytest.raises(TransportError, match="transport failure"):
        transport.send("commit", {})


def test_extract_prefers_structured_data() -> None:
    result = SimpleNamespace(data={"accepted": True}, structured_content=None)
    assert _extract_reply(result) == {"accepted": True}


def test_extract_falls_back_to_structured_content() -> None:
    result = SimpleNamespace(data=None, structured_content={"result": {"accepted": True}})
    assert _extract_reply(result) == {"accepted": True}


def test_an_unreadable_reply_is_an_error() -> None:
    with pytest.raises(TransportError, match="unreadable reply"):
        _extract_reply(SimpleNamespace(data=None, structured_content=None))


def test_build_peer_wires_the_configured_opponent_url(config_dir) -> None:
    orchestrator = build_peer(ConfigManager.load("police", config_dir))
    assert orchestrator.role == "police"


def test_check_connectivity_reports_a_successful_handshake(
    monkeypatch: pytest.MonkeyPatch, config_dir
) -> None:
    fake = SimpleNamespace(
        run_guarded=lambda action: {"accepted": True},
        inbound=SimpleNamespace(opponent_games_played=4),
    )
    monkeypatch.setattr(peer_boot, "build_peer", lambda _config: fake)
    monkeypatch.setattr(peer_boot, "start_server", lambda *_a, **_k: None)
    report = check_connectivity(ConfigManager.load("police", config_dir), "team-a", 1)
    assert isinstance(report, BootReport)
    assert report.handshake_ok
    assert "opponent declared 4 games" in report.detail
    assert report.my_port == 8801


def test_check_connectivity_reports_a_clean_technical_loss(
    monkeypatch: pytest.MonkeyPatch, config_dir
) -> None:
    """An unreachable opponent must produce a report, never a hang or a crash."""
    fake = SimpleNamespace(
        run_guarded=lambda action: None,
        inbound=SimpleNamespace(opponent_games_played=None),
    )
    monkeypatch.setattr(peer_boot, "build_peer", lambda _config: fake)
    monkeypatch.setattr(peer_boot, "start_server", lambda *_a, **_k: None)
    report = check_connectivity(ConfigManager.load("police", config_dir), "team-a", 0)
    assert not report.handshake_ok
    assert "technical loss" in report.detail


def test_check_connectivity_reports_a_contract_rejection(
    monkeypatch: pytest.MonkeyPatch, config_dir
) -> None:
    """A digest mismatch is a refusal to play, reported as such."""

    def refuse(_action):
        raise RuntimeError("contract mismatch: ours abc, theirs def")

    fake = SimpleNamespace(run_guarded=refuse, inbound=SimpleNamespace())
    monkeypatch.setattr(peer_boot, "build_peer", lambda _config: fake)
    monkeypatch.setattr(peer_boot, "start_server", lambda *_a, **_k: None)
    report = check_connectivity(ConfigManager.load("thief", config_dir), "team-b", 0)
    assert not report.handshake_ok
    assert "contract mismatch" in report.detail
