"""`Pipeline` — lay out nodes and wire them from a topology description.

The payoff Mobject: a script describes *topology* (which node feeds which, over
what type), not pixel positions. SERIES_PLAN.md flags this as the seam where the
long-game "emit the real DAG from helios_runtime -> render" plugs in later: feed
`from_topology` a dict that came from Helios's JSON export instead of a literal.

Two structural guarantees beyond the skeleton:

* **Auto-fit** — :meth:`fit_to_frame` scales the whole graph so nothing falls
  off-screen at *any* node count (the 4-node graph used to overflow the frame).
* **Live edits** — :meth:`connect`/:meth:`disconnect`/:meth:`add_node`/
  :meth:`remove_node`/:meth:`relayout` mutate the graph *in place* on persistent
  submobjects, so Beat-7 rewires animate via ``self.play(pipe.animate.relayout())``.
"""

from __future__ import annotations

import numpy as np
from manim import ORIGIN, VGroup, config

from .node import Node
from .packet import Packet
from .port import TypedArrow
from .style import STYLE


class Pipeline(VGroup):
    """A laid-out, wired graph of :class:`Node`s.

    Built via :meth:`from_topology`. Keeps handles to nodes and wires so scenes
    can animate flow, highlight a path, or rewire (Beat 7) without re-deriving
    geometry.
    """

    def __init__(self, direction: str = "LR", **kwargs):
        super().__init__(**kwargs)
        self.nodes: dict[str, Node] = {}
        self.wires: list[TypedArrow] = []
        self._node_buff = STYLE.node_buff
        self.direction = direction  # "LR" (left->right) | "TB" (top->down tree)

    # --- construction ------------------------------------------------------
    @classmethod
    def from_topology(
        cls,
        nodes: dict,
        edges: list[tuple],
        direction: str = "LR",
        node_buff: float = STYLE.node_buff,
        fit: bool = True,
    ) -> "Pipeline":
        """Build a wired graph laid out by layer (Sugiyama-style rank).

        Parameters
        ----------
        nodes:
            ``{node_id: {"label": str, "accent": color?, "compute_load": float?}}``.
            Declaration order sets the *cross-axis* order of siblings within a
            layer (top->bottom for LR, left->right for TB).
        edges:
            ``[(src_id, dst_id, type_name), ...]``. Each edge adds an output port
            to src, an input port to dst, and a typed wire between them. Edges
            also define the layering: a node's layer is the longest path from any
            source, so a node always sits one layer past its deepest input.
        direction:
            ``"LR"`` lays layers out left-to-right (a linked-list chain);
            ``"TB"`` lays them top-to-bottom (a tree). Drives both node placement
            and which edges the ports sit on.
        node_buff:
            Gap between adjacent *layers* before any auto-fit scaling.
        fit:
            When True (default) scale the finished graph to fit the frame so no
            node renders off-screen regardless of count. Pass ``fit=False`` to
            keep raw coordinates (e.g. when composing into a larger layout).

        The build runs in ordered passes so multi-port nodes are laid out before
        wiring: (1) create + arrange nodes by layer, (2) register all ports,
        (3) lay out ports, (4) wire from final port centres, (5) optional fit.
        """
        self = cls(direction=direction)
        self._node_buff = node_buff

        # 1) Create nodes, then place them by layer derived from the edges.
        for node_id, spec in nodes.items():
            self.nodes[node_id] = self._make_node(spec)
        self._arrange_nodes([(s, d) for s, d, _ in edges])
        for node in self.nodes.values():
            self.add(node)

        # 2) Register every edge's ports (create + store, no wiring yet).
        for src_id, dst_id, type_name in edges:
            src, dst = self.nodes[src_id], self.nodes[dst_id]
            src.add_output(type_name, key=f"{dst_id}:{type_name}")
            dst.add_input(type_name, key=f"{src_id}:{type_name}")

        # 3) Lay out all ports now that every node knows its full port set.
        for node in self.nodes.values():
            node.layout_ports()

        # 4) Wire from the now-final port centres.
        for src_id, dst_id, type_name in edges:
            self._build_wire(src_id, dst_id, type_name)

        # 5) Auto-fit so nothing overflows the frame.
        if fit:
            self.fit_to_frame()

        return self

    def _make_node(self, spec: dict) -> Node:
        return Node(
            spec["label"],
            accent=spec.get("accent", STYLE.node_default_accent),
            compute_load=spec.get("compute_load", 0.0),
            flow=self.direction,
        )

    def _rank_nodes(self, edges: list[tuple]) -> dict[str, int]:
        """Longest-path layer for each node (0 for sources).

        Plain Kahn topological pass: a node's layer is one past the deepest of
        its predecessors, so it always renders downstream of everything feeding
        it. Nodes left unranked by a cycle (SLAM loops) stay at layer 0 — TODO:
        break back-edges before ranking so feedback loops layer cleanly.
        """
        succ = {n: [] for n in self.nodes}
        indeg = {n: 0 for n in self.nodes}
        for src, dst in edges:
            if src in succ and dst in indeg:
                succ[src].append(dst)
                indeg[dst] += 1
        layer = {n: 0 for n in self.nodes}
        queue = [n for n in self.nodes if indeg[n] == 0]
        while queue:
            n = queue.pop(0)
            for m in succ[n]:
                layer[m] = max(layer[m], layer[n] + 1)
                indeg[m] -= 1
                if indeg[m] == 0:
                    queue.append(m)
        return layer

    def _arrange_nodes(self, edges: list[tuple] | None = None):
        """Place nodes in layers along the flow axis, siblings on the cross axis.

        ``edges`` is the ``(src, dst)`` list to rank by; when omitted it is
        recovered from the live wires so :meth:`relayout` re-layers correctly
        after edits. Each layer is centred on the cross axis so a small layer
        aligns to the middle of a larger one.
        """
        if not self.nodes:
            return
        if edges is None:
            edges = [w._edge[:2] for w in self.wires]
        layer = self._rank_nodes(edges)

        # Group node ids by layer, preserving declaration order within a layer.
        buckets: dict[int, list[str]] = {}
        for node_id in self.nodes:
            buckets.setdefault(layer[node_id], []).append(node_id)

        if self.direction == "TB":
            flow_step = STYLE.node_height + self._node_buff
            cross_step = STYLE.node_width + STYLE.cross_buff
        else:
            flow_step = STYLE.node_width + self._node_buff
            cross_step = STYLE.node_height + STYLE.cross_buff

        for lvl, ids in buckets.items():
            # Centre the layer; first declared sibling goes top (LR) / left (TB).
            offsets = (np.arange(len(ids)) - (len(ids) - 1) / 2) * cross_step
            for node_id, off in zip(ids, offsets):
                if self.direction == "TB":
                    self.nodes[node_id].move_to([off, -lvl * flow_step, 0.0])
                else:
                    self.nodes[node_id].move_to([lvl * flow_step, -off, 0.0])

    def _build_wire(self, src_id: str, dst_id: str, type_name: str) -> TypedArrow:
        src, dst = self.nodes[src_id], self.nodes[dst_id]
        out_port = src.outputs[f"{dst_id}:{type_name}"]
        in_port = dst.inputs[f"{src_id}:{type_name}"]
        wire = TypedArrow.connect(out_port, in_port)
        wire._edge = (src_id, dst_id, type_name)
        self.wires.append(wire)
        self.add(wire)
        return wire

    # --- fit / layout ------------------------------------------------------
    def fit_to_frame(self, margin: float = STYLE.frame_margin) -> "Pipeline":
        """Scale the whole graph to fit the frame (aspect-preserving), centred.

        The generic fix for off-screen nodes at any count: shrink by the
        limiting ratio so both width and height clear the margin, then centre.
        Only scales *down* — a graph already inside the frame is left at 1:1.
        """
        if not self.submobjects:
            return self
        max_w = config.frame_width - 2 * margin
        max_h = config.frame_height - 2 * margin
        if self.width > max_w or self.height > max_h:
            ratio = min(max_w / self.width, max_h / self.height)
            self.scale(ratio)
        self.move_to(ORIGIN)
        return self

    def relayout(self, fit: bool = True) -> "Pipeline":
        """Re-derive geometry in place after an edit (animatable).

        Re-arranges nodes, re-distributes ports, moves existing wire mobjects to
        their new endpoints, and optionally re-fits. Because positions are
        mutated on the *same* persistent submobjects, Beat-7 rewires animate with
        ``self.play(pipe.animate.relayout())``.
        """
        self._arrange_nodes()
        for node in self.nodes.values():
            node.layout_ports()
        self._refresh_wires()
        if fit:
            self.fit_to_frame()
        return self

    def _refresh_wires(self):
        """Move each existing wire mobject onto its current port endpoints."""
        for wire in self.wires:
            src_id, dst_id, type_name = wire._edge
            out_port = self.nodes[src_id].outputs[f"{dst_id}:{type_name}"]
            in_port = self.nodes[dst_id].inputs[f"{src_id}:{type_name}"]
            wire.put_start_and_end_on(out_port.get_center(), in_port.get_center())

    # --- edit API ----------------------------------------------------------
    # Each mutator returns the affected mobject(s) so the caller animates them
    # (Create the new wire, FadeOut the removed one, etc.).
    def add_node(self, node_id: str, spec: dict) -> Node:
        """Add a disconnected node. Caller re-fits/relayouts to place it."""
        node = self._make_node(spec)
        self.nodes[node_id] = node
        self.add(node)
        return node

    def remove_node(self, node_id: str):
        """Remove a node and every wire/port incident to it.

        Returns ``(node, removed_wires)`` so the caller can FadeOut the lot.
        """
        node = self.nodes[node_id]
        removed = [w for w in self.wires if node_id in w._edge[:2]]
        for wire in removed:
            self._drop_wire(wire)
        self.nodes.pop(node_id)
        if node in self.submobjects:
            self.remove(node)
        return node, removed

    def connect(self, src_id: str, dst_id: str, type_name: str) -> TypedArrow:
        """Wire two existing nodes; relayout both ends. Returns the new wire."""
        src, dst = self.nodes[src_id], self.nodes[dst_id]
        src.add_output(type_name, key=f"{dst_id}:{type_name}")
        dst.add_input(type_name, key=f"{src_id}:{type_name}")
        wire = self._build_wire(src_id, dst_id, type_name)
        self._refresh_wires()
        return wire

    def disconnect(self, src_id: str, dst_id: str) -> TypedArrow | None:
        """Remove the wire src -> dst plus the ports it used. Returns the wire."""
        wire = self.wire_between(src_id, dst_id)
        if wire is None:
            return None
        self._drop_wire(wire)
        self.nodes[src_id].layout_ports()
        self.nodes[dst_id].layout_ports()
        self._refresh_wires()
        return wire

    def _drop_wire(self, wire: TypedArrow):
        """Detach a wire mobject and the two ports it connected."""
        src_id, dst_id, type_name = wire._edge
        self.nodes[src_id].remove_port(f"{dst_id}:{type_name}", "out")
        self.nodes[dst_id].remove_port(f"{src_id}:{type_name}", "in")
        if wire in self.wires:
            self.wires.remove(wire)
        if wire in self.submobjects:
            self.remove(wire)

    # --- animation helpers -------------------------------------------------
    def wire_between(self, src_id: str, dst_id: str) -> TypedArrow | None:
        for w in self.wires:
            if getattr(w, "_edge", (None,))[0:2] == (src_id, dst_id):
                return w
        return None

    def packet_on(self, src_id: str, dst_id: str, run_time: float | None = None):
        """Return ``(packet, animation)`` for a datum flowing src -> dst.

        Caller does ``self.add(packet); self.play(anim)``.
        """
        wire = self.wire_between(src_id, dst_id)
        if wire is None:
            raise KeyError(f"no wire {src_id} -> {dst_id}")
        packet = Packet(wire.type_name)
        packet.move_to(wire.get_start())
        rt = run_time if run_time is not None else STYLE.packet_run_time
        return packet, packet.flow_along(wire, run_time=rt)
