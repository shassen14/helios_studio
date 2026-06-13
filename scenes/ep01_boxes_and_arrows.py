"""Episode 1 — "A Robot Is Just Boxes and Arrows".

Scene-per-beat skeleton tracking context/ep01_boxes_and_arrows.md. Each Scene is
small and independently renderable (per the iteration-speed workflow), so fixing
one beat never re-renders the whole episode.

Render the scene under your cursor in Neovim with <leader>mr, or:

    uv run manim render -ql -p scenes/ep01_boxes_and_arrows.py SingleBox

These are STUBS: enough to render *something* on screen so the workflow is real,
with TODOs where the actual animation work goes. The narration for each beat is
quoted from the script for convenience while animating.
"""

from __future__ import annotations

from manim import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    Create,
    FadeIn,
    Scene,
    Text,
    Write,
)

from helios_manim import Node, Packet, Pipeline, TypedArrow, reject_animation
from helios_manim.types import type_color


class SingleBox(Scene):
    """Beat 3 — the single box. The most important beat in the channel.

    "This is a node. Something goes in, it does one job, something comes out."
    Insultingly simple on purpose: a node that doubles a number. Do NOT make it
    robotics yet.
    """

    def construct(self):
        node = Node("double", accent=type_color("Number"))
        node.add_input("Number")
        node.add_output("Number")

        # Bare in/out arrows to nothing yet — just "something in, something out".
        in_arrow = TypedArrow(
            node.input_point() + LEFT * 1.6, node.input_point(), "Number"
        )
        out_arrow = TypedArrow(
            node.output_point(), node.output_point() + RIGHT * 1.6, "Number"
        )

        self.play(Create(node))
        self.play(Create(in_arrow), Create(out_arrow))
        # TODO(B3): animate "3" entering, "6" leaving. Hold long — it feels slow
        # to you and just right to the viewer.
        self.wait()


class TypedArrows(Scene):
    """Beat 4 — the wires are typed; the wrong things won't connect.

    "You literally can't connect the wrong things together. That's what stops the
    robot from believing nonsense."
    """

    def construct(self):
        producer = Node("pose source", accent=type_color("Pose"))
        producer.add_output("Pose")
        producer.shift(LEFT * 3)

        consumer = Node("wants a scan", accent=type_color("LaserScan"))
        consumer.add_input("LaserScan")
        consumer.shift(RIGHT * 3)

        self.play(FadeIn(producer), FadeIn(consumer))
        # The mismatch beat: Pose out, LaserScan in -> refuse to mate.
        self.play(
            reject_animation(producer.outputs["Pose"], consumer.inputs["LaserScan"])
        )
        # TODO(B4): captions for the type names; then swap consumer to a Pose
        # input and let it click together cleanly.
        self.wait()


class ChainThem(Scene):
    """Beat 5 — chain them; data packets flow. Establishes the "alive" motif.

    "Chain them up — the output of one becomes the input of the next. Now you've
    got a pipeline."
    """

    def construct(self):
        pipe = Pipeline.from_topology(
            nodes={
                "a": {"label": "step one"},
                "b": {"label": "step two"},
                "c": {"label": "step three"},
            },
            edges=[
                ("a", "b", "Number"),
                ("b", "c", "Number"),
            ],
        )
        self.play(Create(pipe))

        # A packet rides each wire in turn — the system breathing.
        for src, dst in (("a", "b"), ("b", "c")):
            packet, anim = pipe.packet_on(src, dst, run_time=0.9)
            self.add(packet)
            self.play(anim)
        # TODO(B5): make packets continuous/looping; light labels on the boxes.
        self.wait()


class RewirePayoff(Scene):
    """Beat 6 + 7 — the boxes were robotics all along, then 'simple != weak'.

    "Same parts. Different wiring. Different robot."
    """

    def construct(self):
        # The real minimal graph from HELIOS_PROJECT_CONTEXT.md.
        pipe = Pipeline.from_topology(
            nodes={
                "sensor":    {"label": "sensor"},
                "estimator": {"label": "estimator", "accent": type_color("Belief"), "compute_load": 0.6},
                "planner":   {"label": "planner", "accent": type_color("Path"), "compute_load": 1.0},
                "control":   {"label": "controller", "accent": type_color("Twist"), "compute_load": 0.1},
            },
            edges=[
                ("sensor", "estimator", "LaserScan"),
                ("estimator", "planner", "Belief"),
                ("planner", "control", "Path"),
            ],
        )
        self.play(Create(pipe))
        # TODO(B6): re-label from the abstract ChainThem boxes; cut to the live
        # DAG overlaid on the cold-open sim footage (open decision: overlay is an
        # engine feature or a post effect).
        # TODO(B7): rewire live — pull the planner, robot follows a fixed path;
        # add a node, new behavior. The one permitted moment of flash.
        self.wait()


# TODO(B8): a FailWiring scene — a valid-but-dumb graph (controller before
# estimator, or a cycle) that maps to the sim's confident wall-crash.
