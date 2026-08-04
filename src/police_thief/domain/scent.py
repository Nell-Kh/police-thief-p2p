"""The pheromone scent field: emission, decay, and the pre-series lock.

Every time an agent moves *or stays*, a scent field of size
``pheromone_grid_size`` (5x5) forms around its cell: the centre takes
``pheromone_center_intensity`` (0.9) and intensity falls radially exactly as
printed in the rulebook's Figure 4. At the end of every **full turn** - after
both agents have completed their moves - all traces decay by ``pheromone_decay``
(rho = 0.10). The update rule, verbatim from chapter 4:

    tau_ij(t+1) = max(0, (1 - rho) * tau_ij(t) + delta_tau_ij)

The scent is a natural, uncontrollable phenomenon: an agent cannot plant a
false trail; each side emits its own field and *reads only the opponent's*.
Before a series, both teams must exchange this exact model - formula plus a
concrete numeric example - and lock it with a SHA-256 hash; this module can
produce that canonical lock (rulebook ch. 4.5).
"""

from __future__ import annotations

from ..shared.config_io import sha256_of
from ..shared.schema import PheromoneConfig
from .board import Cell

#: Radial intensity ratios of Figure 4, keyed by the sorted absolute offsets
#: from the emission centre, expressed in ninetieths so that a 0.9 centre
#: reproduces the printed matrix digit for digit:
#: 0.90 / 0.62 / 0.42 / 0.20 / 0.14 / 0.04.
EMISSION_RATIOS: dict[tuple[int, int], int] = {
    (0, 0): 90,
    (0, 1): 62,
    (1, 1): 42,
    (0, 2): 20,
    (1, 2): 14,
    (2, 2): 4,
}

#: The formula string locked before a series, as the two teams agree it.
FORMULA = "tau_ij(t+1) = max(0, (1 - rho) * tau_ij(t) + delta_tau_ij)"


def emission_delta(config: PheromoneConfig, source: Cell, cell: Cell) -> float:
    """The fresh intensity ``delta_tau`` that ``source`` writes onto ``cell``.

    Zero outside the emission window. The window is square, spanning
    ``pheromone_grid_size`` cells per side around the source.
    """
    reach = config.grid_size // 2
    d_row = abs(cell[0] - source[0])
    d_col = abs(cell[1] - source[1])
    if d_row > reach or d_col > reach:
        return 0.0
    ratio = EMISSION_RATIOS[(min(d_row, d_col), max(d_row, d_col))]
    return config.center_intensity * ratio / 90


class ScentField:
    """One agent's scent field, as its opponent perceives it."""

    def __init__(self, board_size: int, config: PheromoneConfig) -> None:
        """Create an empty field over a ``board_size`` x ``board_size`` grid."""
        self._size = board_size
        self._config = config
        self._tau: dict[Cell, float] = {}

    @property
    def config(self) -> PheromoneConfig:
        """The locked emission-decay parameters this field obeys."""
        return self._config

    def intensity(self, cell: Cell) -> float:
        """Current scent intensity in ``cell`` (0.0 when quiet)."""
        return self._tau.get(cell, 0.0)

    def advance(self, agent_cell: Cell) -> None:
        """Apply one full turn: decay every trace, then add this turn's emission.

        This is the verbatim update rule applied to every cell at once. The
        result is clamped into the printed range [0, center]: the ``max(0, .)``
        clamp is explicit in the formula, and the upper bound follows from the
        book's stated range for tau and its re-emission figure, which holds at
        0.9 while the agent stays present.
        """
        survive = 1.0 - self._config.decay
        ceiling = self._config.center_intensity
        updated: dict[Cell, float] = {}
        for row in range(self._size):
            for col in range(self._size):
                cell = (row, col)
                fresh = emission_delta(self._config, agent_cell, cell)
                value = max(0.0, survive * self._tau.get(cell, 0.0) + fresh)
                value = min(ceiling, value)
                if value > 0.0:
                    updated[cell] = value
        self._tau = updated

    def snapshot(self) -> dict[Cell, float]:
        """A copy of every non-quiet cell - what the opponent samples."""
        return dict(self._tau)

    def expected_fresh_trail(self) -> float:
        """Intensity a one-turn-old trail should show: (1 - rho) * center.

        This is the yardstick of the lie-detection example: a declared path
        with no such residue exposes the declaration as false.
        """
        return (1.0 - self._config.decay) * self._config.center_intensity


def lock_payload(config: PheromoneConfig) -> dict:
    """The canonical description of the emission-decay model, ready to lock.

    Contains the formula, every quantitative parameter, the full radial matrix,
    and the concrete numeric example the rulebook requires alongside it: a
    centre cell takes tau = 0.9, and after one decay turn at rate rho the
    result is 0.9 * (1 - rho).
    """
    return {
        "formula": FORMULA,
        "rho": config.decay,
        "center_intensity": config.center_intensity,
        "field_size": config.grid_size,
        "emission_ratios_ninetieths": {
            f"{low},{high}": value for (low, high), value in sorted(EMISSION_RATIOS.items())
        },
        "numeric_example": {
            "center_tau": config.center_intensity,
            "after_one_decay_turn": round((1.0 - config.decay) * config.center_intensity, 10),
        },
    }


def lock_sha256(config: PheromoneConfig) -> str:
    """The SHA-256 both teams exchange to lock the scent model pre-series."""
    return sha256_of(lock_payload(config))
