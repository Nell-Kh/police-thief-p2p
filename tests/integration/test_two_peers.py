"""Two peers exchanging the full protocol - the M2 milestone.

Both sides run the same machinery, wired back to back so every message a peer
sends is received, validated and decoded by the other. The transport is the only
thing swapped out: in a league match it is an HTTP tunnel, here it is an
in-process loopback, and the message flow is identical either way.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from police_thief.services.orchestrator import Orchestrator
from police_thief.shared.config import ConfigManager


class DeferredTransport:
    """A loopback whose destination is attached after construction.

    Two peers each need the other to exist first, so the link is completed once
    both are built.
    """

    def __init__(self) -> None:
        self.peer: Orchestrator | None = None
        self.sent: list[tuple[str, dict[str, Any]]] = []

    def send(self, tool: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Route a message into the other peer's inbound handler."""
        if self.peer is None:  # pragma: no cover - wired by the fixture
            raise RuntimeError("transport is not connected to a peer")
        self.sent.append((tool, payload))
        return getattr(self.peer.inbound, tool)(payload)


@pytest.fixture
def peers(config_dir: Path) -> tuple[Orchestrator, Orchestrator]:
    """A police peer and a thief peer, each able to reach the other."""
    to_thief, to_police = DeferredTransport(), DeferredTransport()
    police = Orchestrator(ConfigManager.load("police", config_dir), to_thief)
    thief = Orchestrator(ConfigManager.load("thief", config_dir), to_police)
    to_thief.peer, to_police.peer = thief, police
    return police, thief


def test_both_peers_hold_the_same_contract(peers) -> None:
    police, thief = peers
    assert police.sdk.config_sha256 == thief.sdk.config_sha256


def test_a_handshake_crosses_in_both_directions(peers) -> None:
    police, thief = peers
    assert police.start_match(peer_id="team-a", games_played=1)["accepted"]
    assert thief.start_match(peer_id="team-b", games_played=4)["accepted"]
    assert thief.inbound.opponent_games_played == 1
    assert police.inbound.opponent_games_played == 4


def test_a_commitment_travels_intact(peers) -> None:
    """A message leaving one peer is received and decoded correctly by the other."""
    police, thief = peers
    police.start_match(peer_id="team-a", games_played=0)
    police.client.commit("police", 0, "a" * 64)
    assert thief.inbound.committed_digest(0) == "a" * 64


def test_a_full_step_of_the_protocol_completes(peers) -> None:
    police, thief = peers
    police.start_match(peer_id="team-a", games_played=0)
    thief.start_match(peer_id="team-b", games_played=0)

    police.client.commit("police", 0, "a" * 64)
    thief.client.commit("thief", 0, "b" * 64)
    police.client.acknowledge("police", 0, "b" * 64)
    thief.client.acknowledge("thief", 0, "a" * 64)
    police.client.reveal("police", 0, "S", "truth", "moving down the avenue")
    thief.client.reveal("thief", 0, "N", "lie", "heading for the bridge")

    assert thief.inbound.reveals[0]["move"] == "S"
    assert police.inbound.reveals[0]["intent"] == "lie"


def test_each_peer_walks_its_own_phase_machine(peers) -> None:
    """Symmetry: both sides run the same state machine independently."""
    police, thief = peers
    for peer in (police, thief):
        peer.phases.start_turn()
        peer.phases.transition("COMMITTING")
        peer.phases.transition("AWAITING_REVEAL")
        peer.phases.transition("VERIFYING")
        assert peer.phases.transition("WAITING_FOR_OPPONENT") == "WAITING_FOR_OPPONENT"


def test_no_positional_data_crosses_the_wire(peers) -> None:
    """Position may only be implied by free natural language, never encoded."""
    police, thief = peers
    police.start_match(peer_id="team-a", games_played=0)
    police.client.commit("police", 0, "a" * 64)
    police.client.reveal("police", 0, "S", "truth", "somewhere near the park")
    for message in thief.inbound.received:
        assert not {"position", "row", "col", "cell"} & set(message)


def test_the_audit_hands_over_the_whole_log(peers) -> None:
    police, thief = peers
    entries = [{"step": step, "nonce": f"n{step}"} for step in range(3)]
    police.client.audit("police", entries)
    assert len(thief.inbound.audit_entries) == 3


def test_a_dead_peer_does_not_block_the_other(peers) -> None:
    """One side going dark ends its turn cleanly instead of hanging the match."""
    police, _ = peers
    police.start_match(peer_id="team-a", games_played=0)
    police.fail("the opponent stopped responding")
    assert police.lost
    assert police.state.outcome is not None
    assert police.state.outcome.event == "technical_loss"
