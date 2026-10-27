"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Background,
  Controls,
  MiniMap,
  ReactFlow,
  useEdgesState,
  useNodesState,
  type Node,
  type Edge,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { api, GraphEdge, GraphNode } from "@/lib/api";

type Props = {
  invId: string;
  filter: string;
  refreshKey?: number;
  onSelectNode: (node: GraphNode | null) => void;
  onSelectEdge: (edge: GraphEdge | null) => void;
};

const nodeColor = (n: GraphNode) => {
  if (n.evidence_type === "document") return "#3dff8a";
  if (n.evidence_type === "inference") return "#6b4cff";
  if (n.evidence_type === "question") return "#ff3d5a";
  return "#8a8a96";
};

export function EvidenceGraph({
  invId,
  filter,
  refreshKey = 0,
  onSelectNode,
  onSelectEdge,
}: Props) {
  const [raw, setRaw] = useState<{ nodes: GraphNode[]; edges: GraphEdge[] }>({
    nodes: [],
    edges: [],
  });
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);

  const load = useCallback(async () => {
    const g = await api.graph(invId);
    setRaw(g);
  }, [invId]);

  useEffect(() => {
    void load();
  }, [load, refreshKey]);

  const filtered = useMemo(() => {
    let ns = raw.nodes;
    if (filter !== "all") {
      ns = ns.filter(
        (n) =>
          n.type === filter ||
          n.evidence_type === filter ||
          (filter === "inference" && n.evidence_type === "inference")
      );
    }
    const ids = new Set(ns.map((n) => n.id));
    const es = raw.edges.filter((e) => ids.has(e.source) && ids.has(e.target));
    return { nodes: ns, edges: es };
  }, [raw, filter]);

  useEffect(() => {
    setNodes(
      filtered.nodes.map((n, i) => ({
        id: n.id,
        position: { x: (i % 4) * 220, y: Math.floor(i / 4) * 100 },
        data: { label: n.label, node: n },
        style: {
          border: `1px solid ${nodeColor(n)}`,
          background: "#141418",
          color: "#e5e5e5",
          fontSize: 11,
          padding: 8,
          maxWidth: 180,
        },
      }))
    );
    setEdges(
      filtered.edges.map((e) => ({
        id: e.id,
        source: e.source,
        target: e.target,
        label: e.label,
        animated: e.evidence_type === "inference",
        data: { edge: e },
        style: {
          stroke: e.is_manual ? "#ff3d5a" : e.evidence_type === "document" ? "#3dff8a" : "#6b4cff",
        },
      }))
    );
  }, [filtered, setNodes, setEdges]);

  return (
    <div className="h-full min-h-[320px] rounded-lg border border-phantom-violet/20 bg-phantom-panel">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={(_, node) => {
          onSelectEdge(null);
          const gn = (node.data as { node: GraphNode }).node;
          onSelectNode(gn);
        }}
        onEdgeClick={(_, edge) => {
          onSelectNode(null);
          const ge = (edge.data as { edge: GraphEdge } | undefined)?.edge;
          if (ge) onSelectEdge(ge);
        }}
        onPaneClick={() => {
          onSelectNode(null);
          onSelectEdge(null);
        }}
        fitView
      >
        <Background color="#333" gap={16} />
        <MiniMap nodeColor={(n) => nodeColor((n.data as { node: GraphNode }).node)} />
        <Controls />
      </ReactFlow>
    </div>
  );
}
