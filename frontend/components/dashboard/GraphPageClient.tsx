"use client";

import { useState, useEffect } from "react";
import dynamic from "next/dynamic";
import { motion } from "framer-motion";
import { Network, RefreshCw, AlertCircle } from "lucide-react";
import { getGraphData } from "@/lib/api";
import type { GraphData } from "@/types";
import Button from "@/components/ui/Button";
import LearnNextPanel from "@/components/graph/LearnNextPanel";

// Dynamic import – react-force-graph uses browser APIs and Three.js
const KnowledgeGraph = dynamic(
  () => import("@/components/graph/KnowledgeGraph"),
  {
    ssr: false,
    loading: () => (
      <div className="flex flex-col items-center justify-center h-full gap-4 text-white/30">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
        >
          <Network className="w-10 h-10" />
        </motion.div>
        <p className="text-sm">Initialising 3D renderer…</p>
      </div>
    ),
  }
);

interface GraphPageClientProps {
  userId: string;
}

export default function GraphPageClient({ userId }: GraphPageClientProps) {
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showPanel, setShowPanel] = useState(true);

  async function loadGraph() {
    setLoading(true);
    setError(null);

    const result = await getGraphData(userId);
    if (result.error) {
      setError(result.error);
    } else if (result.data) {
      setGraphData(result.data);
    } else {
      // Provide demo data if backend not available
      setGraphData({
        nodes: [
          { id: "u1", label: "Your Knowledge", type: "user", weight: 5 },
          { id: "u2", label: "Machine Learning", type: "user", weight: 4 },
          { id: "u3", label: "Neural Networks", type: "user", weight: 3 },
          { id: "m1", label: "Deep Learning", type: "master", weight: 2 },
          { id: "m2", label: "Computer Vision", type: "master", weight: 2 },
          { id: "m3", label: "NLP", type: "master", weight: 2 },
          { id: "m4", label: "Reinforcement Learning", type: "master", weight: 1 },
          { id: "m5", label: "Transformers", type: "master", weight: 2 },
          { id: "b1", label: "Data Science", type: "bridge", weight: 3 },
        ],
        links: [
          { source: "u1", target: "u2", type: "strong" },
          { source: "u1", target: "u3", type: "strong" },
          { source: "u2", target: "m1", type: "weak" },
          { source: "u3", target: "m1", type: "strong" },
          { source: "m1", target: "m2", type: "weak" },
          { source: "m1", target: "m3", type: "weak" },
          { source: "m3", target: "m5", type: "weak" },
          { source: "m1", target: "m4", type: "inferred" },
          { source: "b1", target: "u2", type: "weak" },
          { source: "b1", target: "m2", type: "weak" },
        ],
      });
    }

    setLoading(false);
  }

  useEffect(() => {
    loadGraph();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId]);

  return (
    <div className="space-y-4 h-full">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white mb-1">
            Knowledge Graph
          </h1>
          <p className="text-white/40 text-sm">
            Blue nodes = your knowledge · Gray nodes = unexplored territory
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setShowPanel((v) => !v)}
          >
            {showPanel ? "Hide" : "Show"} Recommendations
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={loadGraph}
            icon={<RefreshCw className="w-4 h-4" />}
          >
            Refresh
          </Button>
        </div>
      </div>

      {/* Main layout */}
      <div className="flex gap-4" style={{ height: "calc(100vh - 220px)" }}>
        {/* Graph canvas */}
        <div className="flex-1 glass-card overflow-hidden relative">
          {loading ? (
            <div className="flex flex-col items-center justify-center h-full gap-4 text-white/30">
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
              >
                <Network className="w-10 h-10" />
              </motion.div>
              <p className="text-sm">Loading knowledge graph…</p>
            </div>
          ) : error ? (
            <div className="flex flex-col items-center justify-center h-full gap-3 text-white/50 px-8 text-center">
              <AlertCircle className="w-10 h-10 text-red-400/60" />
              <p className="text-sm">{error}</p>
              <Button variant="secondary" size="sm" onClick={loadGraph}>
                Retry
              </Button>
            </div>
          ) : graphData ? (
            <KnowledgeGraph graphData={graphData} />
          ) : null}
        </div>

        {/* Recommendations panel */}
        {showPanel && (
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
            className="w-72 shrink-0"
          >
            <LearnNextPanel userId={userId} />
          </motion.div>
        )}
      </div>
    </div>
  );
}
