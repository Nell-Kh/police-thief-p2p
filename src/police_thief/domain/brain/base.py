"""The brain contract: where all of an agent's intelligence lives.

The rulebook mandates a *separate strategy module* plugged into the runtime at a
precise point - after the incoming hint is decoded, before the outgoing commit
is packed. A brain receives a :class:`BrainView` (everything the agent may
legally know) and returns an :class:`Action`. Nothing else in the system makes
movement decisions, and the language model never does: moves are pure Python.

A team's own brain is selected in the private TOML, section ``[strategy]``, in
``package.module:Class`` notation, and must inherit from :class:`BrainBase` and
override ``_pick_move`` (and, for the cop, optionally ``_decide_move`` to also
choose barriers).
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module

from ...shared.schema import GameContract
from ..board import Board, Cell
from ..engine import Action


class BrainLoadError(ValueError):
    """Raised when a configured brain class cannot be loaded."""


@dataclass(frozen=True)
class BrainView:
    """What a brain is allowed to see when deciding.

    ``target`` is the brain's best estimate of the opponent's cell. In the
    blind stage it is the true position (full-information world); once scent
    and hints arrive it becomes the belief map's argmax. The brain cannot tell
    the difference - which is exactly the plug point the design wants.
    """

    role: str
    position: Cell
    target: Cell
    board: Board
    barriers_left: int
    step: int


class BrainBase:
    """Base class every strategy brain inherits from."""

    def __init__(self, role: str, contract: GameContract) -> None:
        """Bind the brain to its role and the signed contract."""
        self.role = role
        self.contract = contract

    def _pick_move(self, view: BrainView) -> str:
        """Choose this turn's move. Subclasses must override.

        Raises:
            NotImplementedError: always, on the base class.
        """
        raise NotImplementedError("a brain must override _pick_move")

    def _decide_move(self, view: BrainView) -> Action:
        """Choose the full action - move plus optional barrier.

        The default wraps :meth:`_pick_move` with no barrier; a cop brain that
        wants to build walls overrides this.
        """
        return Action(move=self._pick_move(view))

    def decide(self, view: BrainView) -> Action:
        """Public entry point used by the runtime."""
        return self._decide_move(view)


def load_brain(spec: str, role: str, contract: GameContract) -> BrainBase:
    """Instantiate a brain from its ``package.module:Class`` specification.

    Args:
        spec: e.g. ``"police_thief.domain.brain.blind:BlindPoliceBrain"``.
        role: the role the brain will play.
        contract: the signed contract handed to the brain.

    Raises:
        BrainLoadError: if the spec is malformed, the module or class is
            missing, or the class is not a :class:`BrainBase`.
    """
    module_name, _, class_name = spec.partition(":")
    if not module_name or not class_name:
        raise BrainLoadError(f"brain spec {spec!r} is not in package.module:Class form")
    try:
        module = import_module(module_name)
    except ImportError as error:
        raise BrainLoadError(f"cannot import brain module {module_name!r}: {error}") from error
    brain_class = getattr(module, class_name, None)
    if brain_class is None:
        raise BrainLoadError(f"module {module_name!r} has no class {class_name!r}")
    if not (isinstance(brain_class, type) and issubclass(brain_class, BrainBase)):
        raise BrainLoadError(f"{spec!r} is not a BrainBase subclass")
    return brain_class(role, contract)
