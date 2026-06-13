"""helios_manim — the reusable component library for the Helios video series.

Import everything a scene needs:

    from helios_manim import Node, TypedArrow, TypedPort, Packet, Pipeline

The single-tool payoff (SERIES_PLAN.md): every episode composes from these same
primitives instead of redrawing boxes and arrows. Build out the library before
episode 2; episode 1 is its first customer.
"""

from .node import Node
from .packet import Packet
from .pipeline import Pipeline
from .port import TypedArrow, TypedPort, reject_animation
from .types import (
    TYPE_REGISTRY,
    type_color,
    type_shape,
    type_style,
    types_match,
)

__all__ = [
    "Node",
    "Packet",
    "Pipeline",
    "TypedArrow",
    "TypedPort",
    "reject_animation",
    "TYPE_REGISTRY",
    "type_color",
    "type_shape",
    "type_style",
    "types_match",
]
