"""The single source of truth for data-type -> visual identity.

SERIES_PLAN.md is explicit: "Centralize the type->color map here so it's
consistent forever." Every `TypedPort` / `TypedArrow` in every episode pulls its
colour *and shape* from this module, so a `Pose` looks like a `Pose` in episode 1
and still does in the SLAM episode.

The *shape* is what makes the episode-1 "connectors that physically won't mate"
beat (B4) work: mismatched types are different silhouettes, not just different
colours (also friendlier to colour-blind viewers).
"""

from __future__ import annotations

from manim import (
    BLUE_B,
    GREEN_B,
    GREY_B,
    ORANGE,
    PURPLE_B,
    RED_B,
    TEAL_B,
    YELLOW_B,
)

# Port silhouettes used to key data types apart. Consumed by helios_manim.port.
PORT_SHAPES = ("triangle", "square", "semicircle", "pentagon", "diamond")

# The canonical registry. Keys are the *series vocabulary* type names that appear
# as on-screen captions (Beat 4). Keep these aligned with the real Helios types
# in HELIOS_PROJECT_CONTEXT.md as nodes get opened up.
#
# Add a type here exactly once; never hard-code a colour in a scene.
TYPE_REGISTRY: dict[str, dict] = {
    # name            colour      port silhouette
    "Number":      {"color": GREY_B,   "shape": "square"},      # the ep1 doubler toy type
    "Pose":        {"color": BLUE_B,   "shape": "triangle"},    # where the robot thinks it is
    "LaserScan":   {"color": ORANGE,   "shape": "semicircle"},  # raw range sensor
    "OccupancyGrid": {"color": TEAL_B, "shape": "square"},      # the map
    "Path":        {"color": GREEN_B,  "shape": "pentagon"},    # planner output
    "Twist":       {"color": YELLOW_B, "shape": "diamond"},     # velocity command (controller)
    "Belief":      {"color": PURPLE_B, "shape": "triangle"},    # estimate + uncertainty
    "Detection":   {"color": RED_B,    "shape": "diamond"},     # perception output
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


def types_match(a: str, b: str) -> bool:
    """Whether two ports can connect. Today: exact name match.

    Centralised so the "won't mate" rule lives in one place — later this can grow
    into subtype/compatibility rules without touching any scene.
    """
    return a == b
