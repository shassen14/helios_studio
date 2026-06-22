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
    FadeOut,
    MovingCameraScene,
    ReplacementTransform,
    Scene,
    Text,
    Write,
)

from helios_manim import (
    STYLE,
    Node,
    Packet,
    Pipeline,
    TypedArrow,
    focus,
    reject_animation,
    reset,
)
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
            node.input_point() + LEFT * STYLE.stub_arrow_len, node.input_point(), "Number"
        )
        out_arrow = TypedArrow(
            node.output_point(), node.output_point() + RIGHT * STYLE.stub_arrow_len, "Number"
        )

        self.play(Create(node))
        self.play(Create(in_arrow), Create(out_arrow))

        # B3: a literal "3" rides in as a typed Number datum; the node doubles
        # it; a "6" rides out. The glyph comes from the type registry, so a
        # Number always reads as a Number wherever it flows. Hold long — it feels
        # slow to you and just right to the viewer.
        three = Packet("Number", value=3)
        three.move_to(in_arrow.get_start())
        self.add(three)
        self.play(three.flow_along(in_arrow))
        six = Packet("Number", value=6).move_to(node.output_point())
        self.play(ReplacementTransform(three, six))  # the "doubling"
        self.play(six.flow_along(out_arrow))
        self.wait()


class TypedArrows(Scene):
    """Beat 4 — the wires are typed; the wrong things won't connect.

    "You literally can't connect the wrong things together. That's what stops the
    robot from believing nonsense."
    """

    def construct(self):
        producer = Node("pose source", accent=type_color("Pose"))
        producer.add_output("Pose")
        producer.shift(LEFT * STYLE.mismatch_gap)

        consumer = Node("wants a scan", accent=type_color("LaserScan"))
        consumer.add_input("LaserScan")
        consumer.shift(RIGHT * STYLE.mismatch_gap)

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


class RewirePayoff(MovingCameraScene):
    """Beat 6 + 7 — the boxes were robotics all along, then 'simple != weak'.

    "Same parts. Different wiring. Different robot."

    A MovingCameraScene so we can show the whole graph zoomed out (it now
    auto-fits the frame — all four nodes on-screen), zoom *into* a part, then
    rewire live.
    """

    def construct(self):
        # The real minimal graph from HELIOS_PROJECT_CONTEXT.md. Auto-fits the
        # frame, so the 4-node chain that used to overflow is fully visible.
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
            direction="TB",
        )
        self.play(Create(pipe))
        self.wait(0.5)

        # B6: zoom into a part — the estimator -> planner heart of the loop.
        self.play(focus(self.camera, [pipe.nodes["estimator"], pipe.nodes["planner"], pipe.nodes["sensor"]]))
        self.wait(0.5)
        self.play(reset(self.camera))

        # B7: rewire live — "pull the planner". Remove the planner (and its
        # wires) and route the estimator straight to the controller (a reflexive
        # robot). Reconnect *before* relaying out: if we relayout with the planner
        # gone but no new wire yet, the controller has no input, ranks as a
        # layer-0 source, and jumps up beside the sensor (a stray triangle) before
        # snapping back. Reconnecting first keeps the chain linear the whole time,
        # so the new wire just draws in and the gap closes vertically.
        planner, dropped = pipe.remove_node("planner")
        new_wire = pipe.connect("estimator", "control", "Belief")
        self.play(FadeOut(planner), *(FadeOut(w) for w in dropped), Create(new_wire))
        self.play(pipe.animate.relayout())
        # TODO(B6): re-label from the abstract ChainThem boxes; cut to the live
        # DAG overlaid on the cold-open sim footage (open decision: overlay is an
        # engine feature or a post effect).
        self.wait()


# TODO(B8): a FailWiring scene — a valid-but-dumb graph (controller before
# estimator, or a cycle) that maps to the sim's confident wall-crash.
