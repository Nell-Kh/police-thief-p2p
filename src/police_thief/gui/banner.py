"""The turn banner: the asynchronous state machine made visible.

Green ``YOUR TURN`` when the opponent's message has arrived and acting is
enabled; gray ``LOCKED`` from the moment our commitment is sent until the turn
returns. While locked, the interface ignores input - the lock is what prevents
a race condition in which both sides act on the same step (ch. 7.3.2).
"""

from __future__ import annotations

from typing import Any

STATE_YOUR_TURN = "YOUR TURN"
STATE_LOCKED = "LOCKED"

_COLOURS = {STATE_YOUR_TURN: "#2e9e4f", STATE_LOCKED: "#9a9a9a"}


class TurnBanner:
    """A label reflecting whose turn it is."""

    def __init__(self, parent: Any) -> None:
        """Create the banner inside ``parent`` (a Tk container), locked."""
        import tkinter

        self.state = STATE_LOCKED
        self.label = tkinter.Label(
            parent,
            text=STATE_LOCKED,
            bg=_COLOURS[STATE_LOCKED],
            fg="white",
            font=("Arial", 16, "bold"),
            width=14,
            pady=10,
        )
        self.label.pack(side="top", padx=8, pady=8)

    def your_turn(self) -> None:
        """The opponent's turn message arrived: acting is enabled."""
        self._set(STATE_YOUR_TURN)

    def locked(self) -> None:
        """Our commitment left the machine: input is ignored until the turn returns."""
        self._set(STATE_LOCKED)

    @property
    def accepts_input(self) -> bool:
        """Whether the interface should honour user actions right now."""
        return self.state == STATE_YOUR_TURN

    def _set(self, state: str) -> None:
        self.state = state
        self.label.configure(text=state, bg=_COLOURS[state])
