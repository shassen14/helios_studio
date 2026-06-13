"""`Packet` — the dot that rides an edge. The "system is alive" motif (Beat 5).

Defined once so every episode's data-flow looks identical. SERIES_PLAN.md:
"define its look once."
"""

from __future__ import annotations

from manim import WHITE, Dot, MoveAlongPath, rate_functions

from .types import type_color


class Packet(Dot):
    """A single datum travelling along a wire.

    Colour defaults to the wire's type colour so a `Pose` packet is the same blue
    as the `Pose` wire it rides.
    """

    def __init__(self, type_name: str | None = None, radius: float = 0.08, **kwargs):
        color = type_color(type_name) if type_name else WHITE
        super().__init__(radius=radius, color=color, **kwargs)
        self.set_stroke(WHITE, width=1, opacity=0.6)
        self.type_name = type_name

    def flow_along(self, arrow, run_time: float = 1.0, rate_func=rate_functions.ease_in_out_sine):
        """Animation: ride from the start to the end of a TypedArrow/path.

        Place the packet at the wire start first (``packet.move_to(arrow.get_start())``)
        or just `self.play(packet.flow_along(wire))` after `add`-ing it.
        """
        return MoveAlongPath(self, arrow, run_time=run_time, rate_func=rate_func)
