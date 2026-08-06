"""Builder that turns the raw ``config/game.json`` mapping into a typed contract.

Kept separate from :mod:`shared.schema` (definitions) and :mod:`shared.config`
(orchestration) so every file stays within the 150-line rule.
"""

from __future__ import annotations

from typing import Any

from .config_io import ConfigError
from .schema import (
    BoardConfig,
    GameContract,
    MovementConfig,
    NetworkConfig,
    PheromoneConfig,
    RateLimiterConfig,
    ScoringConfig,
    WorldConfig,
    _cell,
    _get,
    _section,
)


def _board(contract: dict[str, Any]) -> BoardConfig:
    name = "board_and_agents"
    section = _section(contract, name)
    return BoardConfig(
        grid_size=int(_get(section, "grid_size", name)),
        num_agents=int(_get(section, "num_agents", name)),
        thief_start=_cell(section, "thief_start", name),
        cop_start=_cell(section, "cop_start", name),
        axis_origin_corner=str(_get(section, "axis_origin_corner", name)),
        axis_start_index=int(_get(section, "axis_start_index", name)),
    )


def _world(contract: dict[str, Any]) -> WorldConfig:
    name = "world"
    section = _section(contract, name)
    return WorldConfig(
        map_area=str(_get(section, "map_area", name)),
        hint_max_words=int(_get(section, "hint_max_words", name)),
    )


def _movement(contract: dict[str, Any]) -> MovementConfig:
    name = "movement_and_barriers"
    section = _section(contract, name)
    return MovementConfig(
        move_set=tuple(str(move) for move in _get(section, "move_set", name)),
        max_barriers=int(_get(section, "max_barriers", name)),
        max_moves=int(_get(section, "max_moves", name)),
        survival_threshold=int(_get(section, "survival_threshold", name)),
    )


def _scoring(contract: dict[str, Any]) -> ScoringConfig:
    name = "scoring"
    section = _section(contract, name)
    return ScoringConfig(
        capture_cop=int(_get(section, "capture_cop", name)),
        capture_thief=int(_get(section, "capture_thief", name)),
        survival_cop=int(_get(section, "survival_cop", name)),
        survival_thief=int(_get(section, "survival_thief", name)),
        tie_score=int(_get(section, "tie_score", name)),
        technical_loss=int(_get(section, "technical_loss", name)),
    )


def _pheromones(contract: dict[str, Any]) -> PheromoneConfig:
    name = "pheromones"
    section = _section(contract, name)
    return PheromoneConfig(
        center_intensity=float(_get(section, "pheromone_center_intensity", name)),
        decay=float(_get(section, "pheromone_decay", name)),
        grid_size=int(_get(section, "pheromone_grid_size", name)),
        min_center_intensity=float(section.get("pheromone_min_center_intensity", 0.5)),
    )


def _network(contract: dict[str, Any]) -> NetworkConfig:
    name = "network_and_league"
    section = _section(contract, name)
    return NetworkConfig(
        response_timeout_sec=int(_get(section, "response_timeout_sec", name)),
        watchdog_timeout_sec=int(_get(section, "watchdog_timeout_sec", name)),
        num_games=int(_get(section, "num_games", name)),
        diversity_reward=int(_get(section, "diversity_reward", name)),
        min_games_to_pass=int(_get(section, "min_games_to_pass", name)),
        max_games_per_team=int(_get(section, "max_games_per_team", name)),
        token_budget_per_series=int(_get(section, "token_budget_per_series", name)),
    )


def _rate_limiter(contract: dict[str, Any]) -> RateLimiterConfig:
    name = "rate_limiter_gatekeeper"
    section = _section(contract, name)
    return RateLimiterConfig(
        requests_per_minute=int(_get(section, "requests_per_minute", name)),
        concurrent_requests=int(_get(section, "concurrent_requests", name)),
        retry_backoff_sec=int(_get(section, "retry_backoff_sec", name)),
        max_retries=int(_get(section, "max_retries", name)),
        queue_depth=int(_get(section, "queue_depth", name)),
    )


def build_contract(raw: dict[str, Any]) -> GameContract:
    """Build a typed :class:`GameContract` from the raw shared mapping.

    Args:
        raw: parsed ``config/game.json``.

    Returns:
        The fully typed contract.

    Raises:
        ConfigError: if any mandatory section or key is absent or malformed.
    """
    try:
        return GameContract(
            board=_board(raw),
            world=_world(raw),
            movement=_movement(raw),
            scoring=_scoring(raw),
            pheromones=_pheromones(raw),
            network=_network(raw),
            rate_limiter=_rate_limiter(raw),
        )
    except (TypeError, ValueError) as exc:
        if isinstance(exc, ConfigError):
            raise
        raise ConfigError(f"contract: malformed value ({exc})") from exc
