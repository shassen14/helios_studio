"""The single source of truth for *geometry and visuals*.

Sibling to :mod:`helios_manim.types` (which owns type -> colour/shape). Where
``types.py`` centralises *what a type looks like*, this module centralises *how
big the boxes are, how far apart, how thick the strokes, how a packet reads* —
every magic number that used to be inlined at its use site.

The point (from the plan): one place to "tune the look" or "move things around".
Bump a field on :data:`STYLE` and every Node/Port/Arrow/Pipeline/camera helper
that reads it moves together.
"""

from __future__ import annotations

from dataclasses import dataclass

from manim import WHITE


@dataclass(frozen=True)
class Style:
    """Frozen bundle of every geometry/visual constant in the library.

    Grouped by the Mobject that consumes the field. Construct your own and pass
    it around if you ever need an alternate look; the library defaults to the
    module singleton :data:`STYLE`.
    """

    # --- Node (the box) ----------------------------------------------------
    node_width: float = 2.6
    node_height: float = 1.4
    node_corner_radius: float = 0.14
    node_stroke: float = 3.0
    node_stroke_highlight: float = 4.0
    node_fill: str = "#0e1116"
    node_label_scale: float = 0.42
    node_label_weight: str = "MEDIUM"
    node_default_accent = WHITE

    # --- Emphasis (highlight / dim) ---------------------------------------
    dim_opacity: float = 0.25
    full_opacity: float = 1.0

    # --- Load pips (compute_load hint in the corner) ----------------------
    pip_count: int = 3
    pip_radius: float = 0.045
    pip_buff: float = 0.06
    pip_corner_buff: float = 0.12
    pip_lit_opacity: float = 1.0
    pip_unlit_opacity: float = 0.15

    # --- Ports (typed connection points) ----------------------------------
    # A uniform disc whose colour is the type; ``port_size`` is its diameter.
    port_size: float = 0.16
    port_stroke: float = 1.5
    # Margin kept clear of the box corners when distributing multiple ports
    # along an edge, so the outermost ports don't sit on the rounded corner.
    port_edge_inset: float = 0.22

    # --- Arrows (wires) ----------------------------------------------------
    arrow_stroke: float = 4.0
    arrow_tip_length: float = 0.18
    arrow_buff: float = 0.1

    # --- Packets (the datum that rides a wire) ----------------------------
    packet_radius: float = 0.08
    packet_stroke: float = 1.0
    packet_stroke_opacity: float = 0.6
    packet_run_time: float = 1.0
    # Nominal extent of a *typed* packet glyph (the "3" disc, the Pose frame),
    # as opposed to the bare dot used when a type has no glyph.
    packet_glyph_size: float = 0.34

    # --- Layout / camera ---------------------------------------------------
    # Gap between adjacent *layers* along the flow axis (left->right or top->down).
    node_buff: float = 1.6
    # Gap between sibling nodes that share a layer (the branches of a DAG).
    cross_buff: float = 0.9
    # Padding kept clear of the frame edge by both fit-to-frame and camera
    # focus, so nothing renders flush against the border.
    frame_margin: float = 0.6
    # Length of the bare in/out arrows in the SingleBox stub scene.
    stub_arrow_len: float = 1.6
    # Producer/consumer spacing for the TypedArrows mismatch beat.
    mismatch_gap: float = 3.0

    # --- Reject animation (the "won't connect" beat) ----------------------
    reject_color: str = "#ff4d4d"
    reject_wiggle_scale: float = 1.4
    reject_wiggle_angle: float = 0.06  # multiplied by PI at the use site
    reject_indicate_scale: float = 1.3
    # The red X blinked over a refused connection.
    reject_x_size: float = 0.34
    reject_x_stroke: float = 4.0
    reject_x_fade: float = 0.25


# The library-wide singleton. Import and read fields off this everywhere.
STYLE = Style()
