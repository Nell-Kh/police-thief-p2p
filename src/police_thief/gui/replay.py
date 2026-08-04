"""The Replay Viewer: a saved match as cryptographic testimony.

A mandatory submission requirement (ch. 7.4). The viewer loads a final log
file, lets the examiner step forward and backward through the match, and at
every step re-verifies the revealed record against its original commitment -
the full sealed record, as chapter 5 specifies. A match is stamped with a green
``Verified OK`` or a red ``TAMPERED`` banner; one tampered step voids it all,
with no appeal. All verification lives in the tested domain layer
(:mod:`police_thief.domain.replay`); this file only draws.
"""

from __future__ import annotations

from pathlib import Path

from ..domain.audit import VERDICT_OK
from ..domain.replay import ReplaySession


class ReplayWindow:
    """Step-through viewer over a saved logbook."""

    def __init__(self, log_path: str | Path, cell_px: int = 56) -> None:
        """Load the log and build the window.

        Raises:
            RuntimeError: when Tk or a display is unavailable.
        """
        try:
            import tkinter
        except ImportError as error:  # pragma: no cover - platform dependent
            raise RuntimeError("tkinter is required for the replay viewer") from error
        self.session = ReplaySession.load(log_path)
        try:
            self.root = tkinter.Tk()
        except tkinter.TclError as error:  # pragma: no cover - headless machine
            raise RuntimeError(f"no display available for the replay: {error}") from error
        self.root.title(f"Replay - {Path(log_path).name}")
        self.stamp = tkinter.Label(self.root, font=("Arial", 16, "bold"), fg="white",
                                   width=22, pady=8)
        self.stamp.pack(side="top", pady=6)
        self.detail = tkinter.Label(self.root, font=("Arial", 11))
        self.detail.pack(side="top")
        self.canvas = tkinter.Canvas(self.root, bg="white")
        self.canvas.pack(padx=8, pady=8)
        controls = tkinter.Frame(self.root)
        controls.pack(side="bottom", pady=6)
        tkinter.Button(controls, text="<< back", command=self._back).pack(side="left", padx=6)
        tkinter.Button(controls, text="forward >>", command=self._forward).pack(side="left")
        self._px = cell_px
        self._draw()

    def _back(self) -> None:
        self.session.back()
        self._draw()

    def _forward(self) -> None:
        self.session.forward()
        self._draw()

    def _draw(self) -> None:
        """Render the current step and its verification stamp."""
        scene = self.session.scene()
        overall = self.session.overall_verdict()
        verdict = scene["verdict"]
        if overall != VERDICT_OK:
            self.stamp.configure(text=f"{overall} (match void)", bg="#c0392b")
        elif verdict == VERDICT_OK:
            self.stamp.configure(text=verdict, bg="#2e9e4f")
        else:  # pragma: no cover - covered via overall above
            self.stamp.configure(text=verdict, bg="#c0392b")
        self.detail.configure(
            text=f'step {scene["step"]} | hint: "{scene["hint"]}"'
        )
        self._draw_board(scene)

    def _draw_board(self, scene: dict) -> None:
        """Paint the revealed board of this step."""
        grid = scene["grid"] or 7
        edge = grid * self._px
        self.canvas.configure(width=edge, height=edge)
        self.canvas.delete("all")
        for row in range(grid):
            for col in range(grid):
                x0, y0 = col * self._px, row * self._px
                fill = "#222222" if (row, col) in scene["barriers"] else "#ffffff"
                self.canvas.create_rectangle(
                    x0, y0, x0 + self._px, y0 + self._px, fill=fill, outline="#cccccc"
                )
        if scene["position"] is not None:
            row, col = scene["position"]
            self.canvas.create_text(
                col * self._px + self._px // 2,
                row * self._px + self._px // 2,
                text=self.session.book.role[0].upper(),
                font=("Arial", 14, "bold"),
            )

    def run(self) -> None:  # pragma: no cover - blocking UI loop
        """Hand control to Tk until the window closes."""
        self.root.mainloop()
