"""`TypedPort` and `TypedArrow` — the typed-wires system (Beat 4).

The teaching beat (config-time): a node outputting a `Pose` will only wire into a
port that *also* wants a `Pose`. Compatibility is keyed by **colour alone** —
"blue plugs into blue". Every port is the same little disc; only its colour
differs, so a matching pair reads as obviously matching and a mismatch reads as
obviously not. `reject_animation` *shows* a refused connection (shake + X) for the
mismatch moment.

(We used to give each type a distinct port silhouette; that was dropped because
the shapes carried an orientation that fought the top-down layout and a viewer had
to be taught the shape->type mapping. See helios_manim.types for the rationale.)
"""

from __future__ import annotations

from manim import (
    PI,
    Arrow,
    Dot,
    FadeIn,
    FadeOut,
    Indicate,
    Line,
    Succession,
    VGroup,
    Wiggle,
)

from .style import STYLE
from .types import type_color, types_match


class TypedPort(Dot):
    """A typed connection point on a node edge.

    A uniform small disc coloured by its type — colour is the whole signal. Carries
    ``type_name`` so a Pipeline (or the `reject` beat) can reason about
    compatibility, and ``direction`` so a node knows which edge it sits on.
    """

    def __init__(self, type_name: str, direction: str = "out"):
        self.type_name = type_name
        self.direction = direction  # "in" | "out"
        color = type_color(type_name)
        super().__init__(radius=STYLE.port_size / 2, color=color)
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


def _reject_x(center):
    """A small red X to flash over a refused connection."""
    s = STYLE.reject_x_size / 2
    a = Line([-s, -s, 0.0], [s, s, 0.0])
    b = Line([-s, s, 0.0], [s, -s, 0.0])
    x = VGroup(a, b).move_to(center)
    x.set_stroke(STYLE.reject_color, width=STYLE.reject_x_stroke)
    return x


def reject_animation(src_port: TypedPort, dst_port: TypedPort):
    """The Beat-4 'won't connect' moment: shake the offending pair and flash an X.

    The colours don't match, so the wire is refused: the input port wiggles, flashes
    red, and a red X blinks over the gap between the two ports. Returns an animation
    you can `self.play(...)`. Intentionally does NOT build a wire — the whole point
    is that the connection is refused. The X mobject is added and removed by the
    animation itself, so the caller doesn't manage it.
    """
    midpoint = (src_port.get_center() + dst_port.get_center()) / 2
    x = _reject_x(midpoint)
    return Succession(
        Wiggle(
            dst_port,
            scale_value=STYLE.reject_wiggle_scale,
            rotation_angle=STYLE.reject_wiggle_angle * PI,
        ),
        Indicate(dst_port, color=STYLE.reject_color, scale_factor=STYLE.reject_indicate_scale),
        FadeIn(x, run_time=STYLE.reject_x_fade),
        FadeOut(x, run_time=STYLE.reject_x_fade),
    )
