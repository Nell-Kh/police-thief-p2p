"""Typed view over the signed shared game contract (``config/game.json``).

Every field maps one-to-one to a parameter of the rulebook's Mandatory
Parameters Table (Appendix F). Loading is deliberately **strict**: a missing key
raises instead of silently defaulting, because a peer that guesses a value would
break the byte-for-byte contract identity the rulebook demands. The shipped
``config/game.json`` carries the table's binding values, so the shipped defaults
are the table's defaults.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .config_io import ConfigError

Cell = tuple[int, int]


def _section(contract: dict[str, Any], name: str) -> dict[str, Any]:
    """Fetch a mandatory top-level section of the contract."""
    value = contract.get(name)
    if not isinstance(value, dict):
        raise ConfigError(f"contract: missing or malformed section {name!r}")
    return value


def _get(section: dict[str, Any], key: str, name: str) -> Any:
    """Fetch a mandatory key from a contract section."""
    if key not in section:
        raise ConfigError(f"contract: section {name!r} is missing key {key!r}")
    return section[key]


def _cell(section: dict[str, Any], key: str, name: str) -> Cell:
    """Fetch a mandatory ``[row, col]`` coordinate pair."""
    raw = _get(section, key, name)
    if not isinstance(raw, (list, tuple)) or len(raw) != 2:
        raise ConfigError(f"contract: {name}.{key} must be a [row, col] pair")
    return (int(raw[0]), int(raw[1]))


@dataclass(frozen=True)
class BoardConfig:
    """Board geometry, agent count and starting positions."""

    grid_size: int
    num_agents: int
    thief_start: Cell
    cop_start: Cell
    axis_origin_corner: str
    axis_start_index: int


@dataclass(frozen=True)
class WorldConfig:
    """Verbal-game world settings: arena flavour and hint length cap."""

    map_area: str
    hint_max_words: int


@dataclass(frozen=True)
class MovementConfig:
    """Legal move set, barrier quota, step ceiling and survival threshold."""

    move_set: tuple[str, ...]
    max_barriers: int
    max_moves: int
    survival_threshold: int


@dataclass(frozen=True)
class ScoringConfig:
    """Points awarded for every termination scenario."""

    capture_cop: int
    capture_thief: int
    survival_cop: int
    survival_thief: int
    tie_score: int
    technical_loss: int


@dataclass(frozen=True)
class PheromoneConfig:
    """Scent emission intensity, decay rate and emission-window size."""

    center_intensity: float
    decay: float
    grid_size: int
    min_center_intensity: float


@dataclass(frozen=True)
class NetworkConfig:
    """Timeouts, league counters and the series token budget."""

    response_timeout_sec: int
    watchdog_timeout_sec: int
    num_games: int
    diversity_reward: int
    min_games_to_pass: int
    max_games_per_team: int
    token_budget_per_series: int


@dataclass(frozen=True)
class RateLimiterConfig:
    """Gatekeeper limits protecting the outgoing API pipeline."""

    requests_per_minute: int
    concurrent_requests: int
    retry_backoff_sec: int
    max_retries: int
    queue_depth: int


@dataclass(frozen=True)
class GameContract:
    """The complete signed contract both peers load byte-for-byte identically."""

    board: BoardConfig
    world: WorldConfig
    movement: MovementConfig
    scoring: ScoringConfig
    pheromones: PheromoneConfig
    network: NetworkConfig
    rate_limiter: RateLimiterConfig
