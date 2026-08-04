"""The belief heatmap: probability translated into deepening reds.

Chapter 7.3.1 verbatim: each side's window shows only *its own belief* about
the opponent - never the opponent's true cell. Higher probability, deeper red;
the argmax cell is marked ``T?`` (the focus of suspicion), our own cell ``C``.
Rendering only - every number comes from the tested domain layer.
"""

from __future__ import annotations

from typing import Any

Cell = tuple[int, int]

#: Cell edge in pixels, from config/setup.json in the assembled window.
DEFAULT_CELL_PX = 56


def red_shade(probability: float, peak: float) -> str:
    """The fill colour for a probability: white through deepening reds."""
    if peak <= 0:
        return "#ffffff"
    strength = max(0.0, min(1.0, probability / peak))
    channel = int(255 - 195 * strength)
    return f"#ff{channel:02x}{channel:02x}"


class BeliefHeatmap:
    """A canvas grid painting one agent's belief map."""

    def __init__(self, parent: Any, grid_size: int, cell_px: int = DEFAULT_CELL_PX) -> None:
        """Create the canvas inside ``parent`` (a Tk container)."""
        import tkinter

        self._size = grid_size
        self._px = cell_px
        edge = grid_size * cell_px
        self.canvas = tkinter.Canvas(parent, width=edge, height=edge, bg="white")
        self.canvas.pack(side="left", padx=8, pady=8)

    def render(
        self,
        belief: dict[Cell, float],
        own_position: Cell,
        barriers: frozenset[Cell] | set[Cell],
        argmax: Cell,
    ) -> None:
        """Repaint the grid from the current belief snapshot."""
        self.canvas.delete("all")
        peak = max(belief.values(), default=0.0)
        for row in range(self._size):
            for col in range(self._size):
                cell = (row, col)
                x0, y0 = col * self._px, row * self._px
                x1, y1 = x0 + self._px, y0 + self._px
                blocked = cell in barriers
                fill = "#222222" if blocked else red_shade(belief.get(cell, 0.0), peak)
                self.canvas.create_rectangle(x0, y0, x1, y1, fill=fill, outline="#cccccc")
                label = self._label_for(cell, own_position, argmax, barriers)
                if label:
                    self.canvas.create_text(
                        (x0 + x1) // 2, (y0 + y1) // 2, text=label, font=("Arial", 14, "bold")
                    )

    @staticmethod
    def _label_for(
        cell: Cell, own: Cell, argmax: Cell, barriers: frozenset[Cell] | set[Cell]
    ) -> str:
        """The glyph for a cell: our position, the suspicion focus, or nothing."""
        if cell == own:
            return "C"
        if cell == argmax and cell not in barriers:
            return "T?"
        return ""
