"use client";

import { useRef, useCallback, useState, useEffect } from "react";
import dynamic from "next/dynamic";
import { motion, AnimatePresence } from "framer-motion";
import { X, Tag, Link2 } from "lucide-react";
import type { GraphData, GraphNode } from "@/types";

// ForceGraph3D must be loaded client-side only (uses WebGL / Three.js)
const ForceGraph3D = dynamic(
  async () => {
    const mod = await import("react-force-graph");
    return mod.ForceGraph3D;
  },
  { ssr: false }
);

// ─── Color helpers ────────────────────────────────────────────────
function nodeColor(node: GraphNode): string {
  switch (node.type) {
    case "user":
      return "#3b82f6"; // neon blue
    case "bridge":
      return "#8b5cf6"; // neon purple
    case "master":
    default:
      return "#4b5563"; // dim gray
  }
}

function nodeSize(node: GraphNode): number {
  const base = node.type === "user" ? 8 : node.type === "bridge" ? 6 : 4;
  return base + (node.weight || 1) * 1.5;
}

function linkColor(link: { type?: string }): string {
  switch (link.type) {
    case "strong":
      return "rgba(59,130,246,0.6)";
    case "weak":
      return "rgba(99,102,241,0.25)";
    case "inferred":
      return "rgba(139,92,246,0.15)";
    default:
      return "rgba(255,255,255,0.1)";
  }
}

// ─── Tooltip panel ────────────────────────────────────────────────
interface TooltipData {
  node: GraphNode;
  x: number;
  y: number;
}

function NodeTooltip({
  data,
  onClose,
}: {
  data: TooltipData;
  onClose: () => void;
}) {
  const typeLabel: Record<string, string> = {
    user: "Your Knowledge",
    master: "Knowledge Base",
    bridge: "Bridge Concept",
  };

  const typeColor: Record<string, string> = {
    user: "text-blue-400 bg-blue-500/10 border-blue-500/20",
    master: "text-gray-400 bg-gray-500/10 border-gray-500/20",
    bridge: "text-purple-400 bg-purple-500/10 border-purple-500/20",
  };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.9 }}
      transition={{ duration: 0.2 }}
      className="absolute z-20 w-56 glass-strong p-4 pointer-events-auto"
      style={{
        left: Math.min(data.x + 12, window.innerWidth - 240),
        top: Math.min(data.y + 12, window.innerHeight - 160),
      }}
    >
      <div className="flex items-start justify-between mb-3">
        <h3 className="text-sm font-semibold text-white leading-tight pr-2">
          {data.node.label}
        </h3>
        <button
          onClick={onClose}
          className="text-white/30 hover:text-white/70 transition-colors shrink-0"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      </div>

      {data.node.type && (
        <span
          className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full border text-xs mb-3 ${
            typeColor[data.node.type] || typeColor.master
          }`}
        >
          <Tag className="w-3 h-3" />
          {typeLabel[data.node.type] || data.node.type}
        </span>
      )}

      {data.node.description && (
        <p className="text-xs text-white/50 leading-relaxed mb-3">
          {data.node.description}
        </p>
      )}

      {data.node.category && (
        <div className="flex items-center gap-1.5 text-xs text-white/30">
          <Link2 className="w-3 h-3" />
          <span>{data.node.category}</span>
        </div>
      )}
    </motion.div>
  );
}

// ─── Main Component ───────────────────────────────────────────────
interface KnowledgeGraphProps {
  graphData: GraphData;
}

export default function KnowledgeGraph({ graphData }: KnowledgeGraphProps) {
  const fgRef = useRef<{ cameraPosition: (pos: object, look: object, ms: number) => void } | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });
  const [tooltip, setTooltip] = useState<TooltipData | null>(null);

  // Measure container
  useEffect(() => {
    if (!containerRef.current) return;
    const ro = new ResizeObserver((entries) => {
      const entry = entries[0];
      if (entry) {
        setDimensions({
          width: entry.contentRect.width,
          height: entry.contentRect.height,
        });
      }
    });
    ro.observe(containerRef.current);
    return () => ro.disconnect();
  }, []);

  // Camera: start zoomed into user cluster, then zoom out
  const handleEngineStop = useCallback(() => {
    if (!fgRef.current) return;

    // Find user node centroid
    const userNodes = graphData.nodes.filter((n) => n.type === "user");
    if (userNodes.length === 0) return;

    const cx =
      userNodes.reduce((s, n) => s + (n.x || 0), 0) / userNodes.length;
    const cy =
      userNodes.reduce((s, n) => s + (n.y || 0), 0) / userNodes.length;
    const cz =
      userNodes.reduce((s, n) => s + (n.z || 0), 0) / userNodes.length;

    // Zoom in
    fgRef.current.cameraPosition(
      { x: cx, y: cy, z: cz + 80 },
      { x: cx, y: cy, z: cz },
      0
    );

    // Smooth zoom out
    setTimeout(() => {
      if (fgRef.current) {
        fgRef.current.cameraPosition(
          { x: cx, y: cy, z: cz + 400 },
          { x: cx, y: cy, z: cz },
          2500
        );
      }
    }, 600);
  }, [graphData.nodes]);

  const handleNodeClick = useCallback(
    (node: object, event: MouseEvent) => {
      const gNode = node as GraphNode;
      setTooltip({ node: gNode, x: event.clientX, y: event.clientY });
    },
    []
  );

  return (
    <div ref={containerRef} className="relative w-full h-full">
      {/* @ts-expect-error – react-force-graph typings are loose */}
      <ForceGraph3D
        ref={fgRef}
        width={dimensions.width}
        height={dimensions.height}
        graphData={graphData}
        nodeLabel="label"
        nodeColor={(node: object) => nodeColor(node as GraphNode)}
        nodeVal={(node: object) => nodeSize(node as GraphNode)}
        linkColor={(link: object) => linkColor(link as { type?: string })}
        linkWidth={(link: object) => {
          const l = link as { type?: string };
          return l.type === "strong" ? 1.5 : 0.8;
        }}
        linkOpacity={0.6}
        backgroundColor="rgba(0,0,0,0)"
        onEngineStop={handleEngineStop}
        onNodeClick={handleNodeClick}
        enableNodeDrag
        enableNavigationControls
        showNavInfo={false}
        nodeThreeObjectExtend={false}
      />

      {/* Tooltip */}
      <AnimatePresence>
        {tooltip && (
          <NodeTooltip
            data={tooltip}
            onClose={() => setTooltip(null)}
          />
        )}
      </AnimatePresence>

      {/* Legend */}
      <div className="absolute bottom-4 left-4 glass rounded-xl px-4 py-3 text-xs space-y-1.5 pointer-events-none">
        {[
          { color: "bg-blue-500", label: "Your Knowledge" },
          { color: "bg-purple-500", label: "Bridge Concepts" },
          { color: "bg-gray-600", label: "Knowledge Base" },
        ].map(({ color, label }) => (
          <div key={label} className="flex items-center gap-2 text-white/50">
            <span className={`w-2.5 h-2.5 rounded-full ${color}`} />
            {label}
          </div>
        ))}
      </div>
    </div>
  );
}
