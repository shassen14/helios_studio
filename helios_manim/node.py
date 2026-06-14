"""`Node` — the box. The most reused Mobject in the whole series (Beat 3).

Design goal from SERIES_PLAN.md: "Must scale from the episode-1 doubler to
SLAM-era subgraphs — design the API now." So the construction is deliberately
plain and the interesting state (highlight/dim, compute load, ports) is exposed
as methods/attributes rather than baked into __init__.
"""

from __future__ import annotations

import numpy as np
from manim import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    Dot,
    RoundedRectangle,
    Text,
    VGroup,
)

from .port import TypedPort
from .style import STYLE


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
    flow:
        Which way data moves *through* this node, so its ports sit on the edges
        the wires arrive at. ``"LR"`` (default) puts inputs on the left and
        outputs on the right; ``"TB"`` puts inputs on top and outputs on the
        bottom (a top-down tree). Set by :class:`~helios_manim.pipeline.Pipeline`
        from its layout ``direction``.
    """

    def __init__(
        self,
        label: str,
        accent=None,
        compute_load: float = 0.0,
        width: float = None,
        height: float = None,
        flow: str = "LR",
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.accent = accent if accent is not None else STYLE.node_default_accent
        self.compute_load = max(0.0, min(1.0, compute_load))
        self.flow = flow

        self.box = RoundedRectangle(
            corner_radius=STYLE.node_corner_radius,
            width=width if width is not None else STYLE.node_width,
            height=height if height is not None else STYLE.node_height,
            stroke_color=self.accent,
            stroke_width=STYLE.node_stroke,
            fill_color=STYLE.node_fill,
            fill_opacity=1.0,
        )
        self.label = Text(label, weight=STYLE.node_label_weight).scale(STYLE.node_label_scale)
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
        self.inputs[key or type_name] = port
        self.add(port)
        self.layout_ports()
        return port

    def add_output(self, type_name: str, key: str | None = None) -> TypedPort:
        """Attach a typed output port to the right edge."""
        port = TypedPort(type_name, direction="out")
        self.outputs[key or type_name] = port
        self.add(port)
        self.layout_ports()
        return port

    def remove_port(self, key: str, direction: str) -> TypedPort | None:
        """Drop a registered port by key and relayout its edge.

        Used by Pipeline.disconnect/remove_node. Returns the removed port (or
        None if absent) so a caller can fade it out.
        """
        registry = self.inputs if direction == "in" else self.outputs
        port = registry.pop(key, None)
        if port is not None and port in self.submobjects:
            self.remove(port)
        self.layout_ports()
        return port

    def layout_ports(self):
        """Distribute ports evenly along their edges.

        The edges depend on :attr:`flow`: ``"LR"`` uses left (inputs) / right
        (outputs); ``"TB"`` uses top (inputs) / bottom (outputs). A single port
        sits at the edge *centre* (preserving the original single-port look that
        SingleBox/TypedArrows and ``input_point``/``output_point`` rely on).
        Multiple ports spread evenly along the edge, kept clear of the rounded
        corners by ``port_edge_inset``.
        """
        in_edge, out_edge = ("top", "bottom") if self.flow == "TB" else ("left", "right")
        self._distribute(list(self.inputs.values()), in_edge)
        self._distribute(list(self.outputs.values()), out_edge)
        return self

    def _distribute(self, ports: list[TypedPort], edge: str):
        """Place ``ports`` along one box ``edge`` (left/right/top/bottom)."""
        if not ports:
            return
        box = self.box
        vertical = edge in ("left", "right")  # ports vary in y along this edge
        if vertical:
            fixed = box.get_left()[0] if edge == "left" else box.get_right()[0]
            centre = box.get_center()[1]
            lo = box.get_bottom()[1] + STYLE.port_edge_inset
            hi = box.get_top()[1] - STYLE.port_edge_inset
        else:
            fixed = box.get_top()[1] if edge == "top" else box.get_bottom()[1]
            centre = box.get_center()[0]
            lo = box.get_left()[0] + STYLE.port_edge_inset
            hi = box.get_right()[0] - STYLE.port_edge_inset

        if len(ports) == 1:
            coords = [centre]
        else:
            # hi -> first declared port (top for LR, left for TB).
            coords = np.linspace(hi, lo, len(ports))
        for port, c in zip(ports, coords):
            point = [fixed, c, 0.0] if vertical else [c, fixed, 0.0]
            port.move_to(np.array(point))

    def input_point(self):
        return self.box.get_top() if self.flow == "TB" else self.box.get_left()

    def output_point(self):
        return self.box.get_bottom() if self.flow == "TB" else self.box.get_right()

    # --- emphasis ----------------------------------------------------------
    def highlight(self):
        """Bring this node to full opacity (foreground it during a beat)."""
        self.set_opacity(STYLE.full_opacity)
        self.box.set_stroke(self.accent, width=STYLE.node_stroke_highlight)
        return self

    def dim(self):
        """Push this node into the background."""
        self.set_opacity(STYLE.dim_opacity)
        return self

    # --- internals ---------------------------------------------------------
    def _add_load_pips(self):
        """Up to ``pip_count`` small pips in the corner encoding compute_load."""
        n = STYLE.pip_count
        n_lit = round(self.compute_load * n)
        if n_lit == 0:
            return
        pips = VGroup()
        for i in range(n):
            pip = Dot(radius=STYLE.pip_radius)
            lit = i < n_lit
            pip.set_fill(
                self.accent if lit else STYLE.node_default_accent,
                opacity=STYLE.pip_lit_opacity if lit else STYLE.pip_unlit_opacity,
            )
            pip.set_stroke(width=0)
            pips.add(pip)
        pips.arrange(RIGHT, buff=STYLE.pip_buff)
        # tuck into the top-left corner of the box
        pips.next_to(self.box.get_corner(UP + LEFT), DOWN + RIGHT, buff=STYLE.pip_corner_buff)
        self.add(pips)
