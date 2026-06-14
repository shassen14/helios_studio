"""`Packet` — the datum that rides an edge. The "system is alive" motif (Beat 5).

Defined once so every episode's data-flow looks identical. SERIES_PLAN.md:
"define its look once."

A packet's *body* comes from the type registry's glyph (``type_glyph``): a
``Number`` rides as its value in a disc, a ``Pose`` as a little coordinate frame.
Colour keys the type; the glyph shows what the data *is*. A type with no glyph
falls back to the original plain dot, so this stays backwards-compatible and can
be filled in one type at a time.
"""

from __future__ import annotations

from manim import WHITE, Dot, MoveAlongPath, VGroup, rate_functions

from .style import STYLE
from .types import type_color, type_glyph


class Packet(VGroup):
    """A single datum travelling along a wire.

    Parameters
    ----------
    type_name:
        Drives colour and (if registered) the glyph. ``None`` -> a white dot.
    value:
        Optional concrete value handed to the glyph factory, so a Number packet
        can render "3". Glyphs degrade gracefully when it's absent.
    radius:
        Overrides the fallback-dot radius (ignored when the type has a glyph).
    """

    def __init__(
        self,
        type_name: str | None = None,
        value=None,
        radius: float | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.type_name = type_name
        self.value = value
        color = type_color(type_name) if type_name else WHITE

        glyph_fn = type_glyph(type_name) if type_name else None
        if glyph_fn is not None:
            body = glyph_fn(value, color)
        else:
            r = radius if radius is not None else STYLE.packet_radius
            body = Dot(radius=r, color=color)
            body.set_stroke(WHITE, width=STYLE.packet_stroke, opacity=STYLE.packet_stroke_opacity)
        self.body = body
        self.add(body)

    def flow_along(self, arrow, run_time: float | None = None, rate_func=rate_functions.ease_in_out_sine):
        """Animation: ride from the start to the end of a TypedArrow/path.

        Place the packet at the wire start first (``packet.move_to(arrow.get_start())``)
        or just `self.play(packet.flow_along(wire))` after `add`-ing it.
        """
        rt = run_time if run_time is not None else STYLE.packet_run_time
        return MoveAlongPath(self, arrow, run_time=rt, rate_func=rate_func)
