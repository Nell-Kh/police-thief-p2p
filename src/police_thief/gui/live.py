"""The live window: one peer's local truth, and nothing more.

Assembles the belief heatmap and the turn banner for a running match. The
window exposes only what the agent may legally know - its own position, the
public barriers, its belief about the opponent. There is no bird's-eye view
anywhere in this codebase to accidentally show (ch. 7.2's local-truth
principle, mandatory rules #8/#9).
"""

from __future__ import annotations

from ..services.world_view import WorldView


class LiveWindow:
    """The per-side live GUI: heatmap plus turn banner."""

    def __init__(self, role: str, grid_size: int, cell_px: int = 56) -> None:
        """Build the window; requires a display (runs on the player's machine).

        Raises:
            RuntimeError: when Tk is unavailable (e.g. a headless server).
        """
        try:
            import tkinter
        except ImportError as error:  # pragma: no cover - platform dependent
            raise RuntimeError("tkinter is required for the live GUI") from error
        from .banner import TurnBanner
        from .heatmap import BeliefHeatmap

        try:
            self.root = tkinter.Tk()
        except tkinter.TclError as error:  # pragma: no cover - headless machine
            raise RuntimeError(f"no display available for the live GUI: {error}") from error
        self.root.title(f"Police-Thief - {role} (local truth)")
        self.banner = TurnBanner(self.root)
        self.heatmap = BeliefHeatmap(self.root, grid_size, cell_px)
        self.status = tkinter.Label(self.root, text="", font=("Arial", 11))
        self.status.pack(side="bottom", pady=4)

    def refresh(self, view: WorldView) -> None:
        """Repaint everything from the peer's current world view."""
        self.heatmap.render(
            belief=view.belief.snapshot(),
            own_position=view.position,
            barriers=view.board.barriers,
            argmax=view.belief.argmax(),
        )
        self.status.configure(
            text=f"step {view.step} | barriers used {view.barriers_used}"
        )
        self.root.update_idletasks()
        self.root.update()

    def your_turn(self) -> None:
        """Flip the banner green: the opponent's message arrived."""
        self.banner.your_turn()

    def locked(self) -> None:
        """Flip the banner gray: our commitment is out, input is ignored."""
        self.banner.locked()
