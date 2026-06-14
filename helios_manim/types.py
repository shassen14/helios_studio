"""The single source of truth for data-type -> visual identity.

SERIES_PLAN.md is explicit: "Centralize the type->color map here so it's
consistent forever." Every `TypedPort` / `TypedArrow` in every episode pulls its
colour *and shape* from this module, so a `Pose` looks like a `Pose` in episode 1
and still does in the SLAM episode.

The *shape* is what makes the episode-1 "connectors that physically won't mate"
beat (B4) work: mismatched types are different silhouettes, not just different
colours (also friendlier to colour-blind viewers).

A type carries *three* visual concerns, all centralised here:

* **colour** — which wires/ports are "the blue ones" (type identity at a glance).
* **shape** — the *port* silhouette; different shapes physically won't mate (B4).
* **glyph** — what a *datum of that type looks like riding a wire* (B5/B3): a
  ``Number`` shows its value in a disc, a ``Pose`` shows a little coordinate
  frame. Colour keys the type; the glyph shows what the data *is*. Types without
  a glyph fall back to :class:`~helios_manim.packet.Packet`'s plain dot, so this
  can be filled in one type at a time.
"""

from __future__ import annotations

from manim import (
    BLUE_B,
    GREEN_B,
    GREY_B,
    ORANGE,
    ORIGIN,
    PURPLE_B,
    RED_B,
    RIGHT,
    TEAL_B,
    UP,
    YELLOW_B,
    Circle,
    Dot,
    Line,
    Text,
    VGroup,
)

from .style import STYLE

# Port silhouettes used to key data types apart. Consumed by helios_manim.port.
PORT_SHAPES = ("triangle", "square", "semicircle", "pentagon", "diamond")


# --- packet glyphs --------------------------------------------------------
# Each factory takes ``(value, color)`` and returns a small Mobject to ride a
# wire. ``value`` is optional: with one, a Number shows "3"; without, it degrades
# to a bare disc (so the abstract ChainThem packets still read as data).
def _glyph_number(value, color):
    """A datum of type Number: its value inside a small disc."""
    s = STYLE.packet_glyph_size
    disc = Circle(radius=s * 0.55, color=color, stroke_width=2.5)
    disc.set_fill(color, opacity=0.12)
    parts = [disc]
    if value is not None:
        txt = Text(str(value), weight="BOLD", color=color)
        txt.set(height=s * 0.5)
        txt.move_to(disc.get_center())
        parts.append(txt)
    return VGroup(*parts)


def _glyph_pose(value, color):
    """A datum of type Pose: a tiny coordinate frame (origin + x/y axes)."""
    s = STYLE.packet_glyph_size
    x_axis = Line(ORIGIN, RIGHT * s, color=color, stroke_width=3)
    y_axis = Line(ORIGIN, UP * s, color=color, stroke_width=3)
    origin = Dot(point=ORIGIN, radius=s * 0.1, color=color)
    return VGroup(x_axis, y_axis, origin)


# The canonical registry. Keys are the *series vocabulary* type names that appear
# as on-screen captions (Beat 4). Keep these aligned with the real Helios types
# in HELIOS_PROJECT_CONTEXT.md as nodes get opened up.
#
# Add a type here exactly once; never hard-code a colour in a scene.
TYPE_REGISTRY: dict[str, dict] = {
    # name            colour      port silhouette         packet glyph (optional)
    "Number": {
        "color": GREY_B,
        "shape": "square",
        "glyph": _glyph_number,
    },  # the ep1 doubler toy type
    "Pose": {
        "color": BLUE_B,
        "shape": "triangle",
        "glyph": _glyph_pose,
    },  # where the robot thinks it is
    "LaserScan": {"color": ORANGE, "shape": "semicircle"},  # raw range sensor
    "OccupancyGrid": {"color": TEAL_B, "shape": "square"},  # the map
    "Path": {"color": GREEN_B, "shape": "pentagon"},  # planner output
    "Twist": {"color": YELLOW_B, "shape": "diamond"},  # velocity command (controller)
    "Belief": {"color": PURPLE_B, "shape": "triangle"},  # estimate + uncertainty
    "Detection": {"color": RED_B, "shape": "diamond"},  # perception output
}

# Fallback for a type not yet in the registry, so a scene never crashes mid-draft.
_UNKNOWN = {"color": GREY_B, "shape": "square"}


def type_style(name: str) -> dict:
    """Return ``{"color", "shape"}`` for a type name (case-insensitive-ish)."""
    return TYPE_REGISTRY.get(name, _UNKNOWN)


def type_color(name: str):
    """Convenience: just the colour for a type name."""
    return type_style(name)["color"]


def type_shape(name: str) -> str:
    """Convenience: just the port silhouette key for a type name."""
    return type_style(name)["shape"]


def type_glyph(name: str):
    """Return the packet-glyph factory ``(value, color) -> Mobject`` for a type.

    ``None`` if the type has no glyph yet — callers (``Packet``) fall back to a
    plain dot, so glyphs can be added one type at a time.
    """
    return type_style(name).get("glyph")


def types_match(a: str, b: str) -> bool:
    """Whether two ports can connect. Today: exact name match.

    Centralised so the "won't mate" rule lives in one place — later this can grow
    into subtype/compatibility rules without touching any scene.
    """
    return a == b
