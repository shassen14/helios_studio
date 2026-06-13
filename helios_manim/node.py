"""`Node` — the box. The most reused Mobject in the whole series (Beat 3).

Design goal from SERIES_PLAN.md: "Must scale from the episode-1 doubler to
SLAM-era subgraphs — design the API now." So the construction is deliberately
plain and the interesting state (highlight/dim, compute load, ports) is exposed
as methods/attributes rather than baked into __init__.
"""

from __future__ import annotations

from manim import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    WHITE,
    Dot,
    RoundedRectangle,
    Text,
    VGroup,
)

from .port import TypedPort

# A node dimmed to background vs. brought to the foreground. Tuned once here.
_DIM_OPACITY = 0.25
_FULL_OPACITY = 1.0


class Node(VGroup):
    """One unit of the pipeline: input -> transform -> output.

    Parameters
    ----------
    label:
        Text shown inside the box (e.g. "double", "Estimator").
    accent:
        Border/title colour. Often the *output* type colour, so a node visually
        advertises what it produces.
    compute_load:
        0.0 -> reflexive (a controller), 1.0 -> heavy deliberation (a planner).
        Rendered as a small stack of "load" pips — the visual weight hint from
        SERIES_PLAN.md. TODO(ep5/ep6): animate this filling as a planner churns.
    """

    def __init__(
        self,
        label: str,
        accent=WHITE,
        compute_load: float = 0.0,
        width: float = 2.6,
        height: float = 1.4,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.accent = accent
        self.compute_load = max(0.0, min(1.0, compute_load))

        self.box = RoundedRectangle(
            corner_radius=0.14,
            width=width,
            height=height,
            stroke_color=accent,
            stroke_width=3.0,
            fill_color="#0e1116",
            fill_opacity=1.0,
        )
        self.label = Text(label, weight="MEDIUM").scale(0.42)
        self.label.move_to(self.box.get_center())

        self.add(self.box, self.label)
        self._add_load_pips()

        # Ports are registered via add_input/add_output so a Pipeline can wire
        # them by type. name -> TypedPort.
        self.inputs: dict[str, TypedPort] = {}
        self.outputs: dict[str, TypedPort] = {}

    # --- ports -------------------------------------------------------------
    def add_input(self, type_name: str, key: str | None = None) -> TypedPort:
        """Attach a typed input port to the left edge."""
        port = TypedPort(type_name, direction="in")
        port.move_to(self.box.get_left())
        self.inputs[key or type_name] = port
        self.add(port)
        return port

    def add_output(self, type_name: str, key: str | None = None) -> TypedPort:
        """Attach a typed output port to the right edge."""
        port = TypedPort(type_name, direction="out")
        port.move_to(self.box.get_right())
        self.outputs[key or type_name] = port
        self.add(port)
        return port

    def input_point(self):
        return self.box.get_left()

    def output_point(self):
        return self.box.get_right()

    # --- emphasis ----------------------------------------------------------
    def highlight(self):
        """Bring this node to full opacity (foreground it during a beat)."""
        self.set_opacity(_FULL_OPACITY)
        self.box.set_stroke(self.accent, width=4.0)
        return self

    def dim(self):
        """Push this node into the background."""
        self.set_opacity(_DIM_OPACITY)
        return self

    # --- internals ---------------------------------------------------------
    def _add_load_pips(self):
        """Up to 3 small pips in the corner encoding compute_load."""
        n_lit = round(self.compute_load * 3)
        if n_lit == 0:
            return
        pips = VGroup()
        for i in range(3):
            pip = Dot(radius=0.045)
            pip.set_fill(self.accent if i < n_lit else WHITE, opacity=1.0 if i < n_lit else 0.15)
            pip.set_stroke(width=0)
            pips.add(pip)
        pips.arrange(RIGHT, buff=0.06)
        # tuck into the top-left corner of the box
        pips.next_to(self.box.get_corner(UP + LEFT), DOWN + RIGHT, buff=0.12)
        self.add(pips)
