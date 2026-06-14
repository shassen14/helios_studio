"""`TypedPort` and `TypedArrow` — the typed-wires system (Beat 4).

The teaching beat: a node outputting a `Pose` *physically cannot* plug into one
expecting a `LaserScan`. We sell that with (a) colour and (b) silhouette from the
type registry, plus a `reject()` animation for the mismatch moment.
"""

from __future__ import annotations

import numpy as np
from manim import (
    DOWN,
    LEFT,
    PI,
    RIGHT,
    UP,
    Arrow,
    Indicate,
    RegularPolygon,
    Square,
    Succession,
    Wiggle,
)

from .style import STYLE
from .types import type_color, type_shape, types_match


def _port_mobject(shape: str, color):
    """Build the little silhouette that marks a port's type."""
    if shape == "triangle":
        m = RegularPolygon(n=3, start_angle=0)
    elif shape == "semicircle":
        # A flat-bottomed half-disc approximated with a wide, short polygon.
        m = RegularPolygon(n=6, start_angle=0)
    elif shape == "pentagon":
        m = RegularPolygon(n=5, start_angle=PI / 2)
    elif shape == "diamond":
        m = Square().rotate(PI / 4)
    else:  # "square" and unknown fallback
        m = Square()
    m.set_width(STYLE.port_size)
    m.set_fill(color, opacity=1.0)
    m.set_stroke(color, width=STYLE.port_stroke)
    return m


class TypedPort(RegularPolygon):
    """A typed connection point on a node edge.

    Subclasses RegularPolygon only so it composes as a Mobject; the real
    silhouette is rebuilt from the registry. Carries ``type_name`` so a Pipeline
    (or the `reject` beat) can reason about compatibility.
    """

    def __init__(self, type_name: str, direction: str = "out"):
        self.type_name = type_name
        self.direction = direction  # "in" | "out"
        shape = type_shape(type_name)
        color = type_color(type_name)
        # Initialise as the right silhouette directly.
        n = {"triangle": 3, "semicircle": 6, "pentagon": 5}.get(shape, 4)
        super().__init__(n=n, start_angle=PI / 2 if shape == "pentagon" else 0)
        if shape == "diamond":
            self.rotate(PI / 4)
        self.set_width(STYLE.port_size)
        self.set_fill(color, opacity=1.0)
        self.set_stroke(color, width=STYLE.port_stroke)


class TypedArrow(Arrow):
    """A wire between two ports, coloured by the type flowing through it.

    Use :meth:`connect` to build one from two ports; it validates the types so a
    miswired scene fails loudly rather than silently lying.
    """

    def __init__(self, start, end, type_name: str, **kwargs):
        self.type_name = type_name
        super().__init__(
            start=start,
            end=end,
            color=type_color(type_name),
            buff=STYLE.arrow_buff,
            stroke_width=STYLE.arrow_stroke,
            tip_length=STYLE.arrow_tip_length,
            **kwargs,
        )

    @classmethod
    def connect(cls, src_port: TypedPort, dst_port: TypedPort, **kwargs) -> "TypedArrow":
        """Wire an output port to an input port. Raises on a type mismatch."""
        if not types_match(src_port.type_name, dst_port.type_name):
            raise ValueError(
                f"type mismatch: {src_port.type_name} -> {dst_port.type_name} "
                "(use reject_animation() to *show* this on purpose)"
            )
        return cls(src_port.get_center(), dst_port.get_center(), src_port.type_name, **kwargs)

    def path(self):
        """The line a Packet rides along (start -> end)."""
        return self


def reject_animation(src_port: TypedPort, dst_port: TypedPort):
    """The Beat-4 'won't mate' moment: shake the offending pair and flash.

    Returns an animation you can `self.play(...)`. Intentionally does NOT build a
    wire — the whole point is that the connection is refused.
    """
    return Succession(
        Wiggle(
            dst_port,
            scale_value=STYLE.reject_wiggle_scale,
            rotation_angle=STYLE.reject_wiggle_angle * PI,
        ),
        Indicate(dst_port, color=STYLE.reject_color, scale_factor=STYLE.reject_indicate_scale),
    )
