"""`Pipeline` — lay out nodes and wire them from a topology description.

The payoff Mobject: a script describes *topology* (which node feeds which, over
what type), not pixel positions. SERIES_PLAN.md flags this as the seam where the
long-game "emit the real DAG from helios_runtime -> render" plugs in later: feed
`from_topology` a dict that came from Helios's JSON export instead of a literal.
"""

from __future__ import annotations

from manim import RIGHT, VGroup

from .node import Node
from .packet import Packet
from .port import TypedArrow


class Pipeline(VGroup):
    """A laid-out, wired graph of :class:`Node`s.

    Built via :meth:`from_topology`. Keeps handles to nodes and wires so scenes
    can animate flow, highlight a path, or rewire (Beat 7) without re-deriving
    geometry.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.nodes: dict[str, Node] = {}
        self.wires: list[TypedArrow] = []

    @classmethod
    def from_topology(cls, nodes: dict, edges: list[tuple], node_buff: float = 1.6) -> "Pipeline":
        """Build a left-to-right pipeline.

        Parameters
        ----------
        nodes:
            ``{node_id: {"label": str, "accent": color?, "compute_load": float?}}``.
            Declaration order sets left-to-right placement (good enough for the
            linear chains of episodes 1-6; TODO: layered layout for SLAM loops).
        edges:
            ``[(src_id, dst_id, type_name), ...]``. Each edge adds an output port
            to src, an input port to dst, and a typed wire between them.
        """
        self = cls()

        # 1) Build + place nodes in declaration order.
        for node_id, spec in nodes.items():
            node = Node(
                spec["label"],
                accent=spec.get("accent"),
                compute_load=spec.get("compute_load", 0.0),
            ) if spec.get("accent") else Node(
                spec["label"],
                compute_load=spec.get("compute_load", 0.0),
            )
            self.nodes[node_id] = node
        VGroup(*self.nodes.values()).arrange(RIGHT, buff=node_buff)
        for node in self.nodes.values():
            self.add(node)

        # 2) Add ports + wires from edges (after placement so geometry is final).
        for src_id, dst_id, type_name in edges:
            src, dst = self.nodes[src_id], self.nodes[dst_id]
            out_port = src.add_output(type_name, key=f"{dst_id}:{type_name}")
            in_port = dst.add_input(type_name, key=f"{src_id}:{type_name}")
            wire = TypedArrow.connect(out_port, in_port)
            wire._edge = (src_id, dst_id, type_name)
            self.wires.append(wire)
            self.add(wire)

        return self

    # --- animation helpers -------------------------------------------------
    def wire_between(self, src_id: str, dst_id: str) -> TypedArrow | None:
        for w in self.wires:
            if getattr(w, "_edge", (None,))[0:2] == (src_id, dst_id):
                return w
        return None

    def packet_on(self, src_id: str, dst_id: str, run_time: float = 1.0):
        """Return ``(packet, animation)`` for a datum flowing src -> dst.

        Caller does ``self.add(packet); self.play(anim)``.
        """
        wire = self.wire_between(src_id, dst_id)
        if wire is None:
            raise KeyError(f"no wire {src_id} -> {dst_id}")
        packet = Packet(wire.type_name)
        packet.move_to(wire.get_start())
        return packet, packet.flow_along(wire, run_time=run_time)
