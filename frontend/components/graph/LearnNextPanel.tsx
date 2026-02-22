"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Lightbulb,
  ChevronRight,
  Clock,
  Bookmark,
  RefreshCw,
  Loader2,
} from "lucide-react";
import { getRecommendations } from "@/lib/api";
import type { Recommendation } from "@/types";
import Button from "@/components/ui/Button";

const DEMO_RECOMMENDATIONS: Recommendation[] = [
  {
    id: "r1",
    topic: "Transformer Architecture",
    description:
      "How attention mechanisms revolutionized sequence modelling and gave birth to modern LLMs.",
    relevanceScore: 0.94,
    distanceFromUser: 1,
    category: "Deep Learning",
    tags: ["NLP", "Attention", "BERT"],
    estimatedReadTime: 15,
  },
  {
    id: "r2",
    topic: "Reinforcement Learning from Human Feedback",
    description:
      "The RLHF pipeline behind ChatGPT and how reward models are trained.",
    relevanceScore: 0.88,
    distanceFromUser: 2,
    category: "AI Alignment",
    tags: ["RLHF", "LLM", "Fine-tuning"],
    estimatedReadTime: 20,
  },
  {
    id: "r3",
    topic: "Vector Databases",
    description:
      "Semantic search, embeddings, and why Pinecone/Weaviate are becoming critical infrastructure.",
    relevanceScore: 0.82,
    distanceFromUser: 2,
    category: "Infrastructure",
    tags: ["Embeddings", "Search", "RAG"],
    estimatedReadTime: 12,
  },
  {
    id: "r4",
    topic: "Graph Neural Networks",
    description:
      "Learning on graph-structured data — from molecules to social networks.",
    relevanceScore: 0.75,
    distanceFromUser: 3,
    category: "Graph ML",
    tags: ["GNN", "Message Passing"],
    estimatedReadTime: 18,
  },
];

function relevanceColor(score: number): string {
  if (score >= 0.9) return "text-green-400 bg-green-500/10 border-green-500/20";
  if (score >= 0.75) return "text-blue-400 bg-blue-500/10 border-blue-500/20";
  return "text-purple-400 bg-purple-500/10 border-purple-500/20";
}

function distanceLabel(d: number): string {
  if (d === 1) return "1 hop away";
  if (d === 2) return "2 hops away";
  return `${d} hops away`;
}

// ─── Card ─────────────────────────────────────────────────────────
function RecommendationCard({
  rec,
  index,
}: {
  rec: Recommendation;
  index: number;
}) {
  const [saved, setSaved] = useState(false);

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: index * 0.07 }}
      className="glass rounded-xl p-4 group hover:-translate-y-0.5 transition-transform duration-200"
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-2 mb-2">
        <h3 className="text-sm font-semibold text-white leading-snug flex-1">
          {rec.topic}
        </h3>
        <button
          onClick={() => setSaved((v) => !v)}
          className={`shrink-0 transition-colors ${
            saved ? "text-blue-400" : "text-white/20 hover:text-white/50"
          }`}
          aria-label={saved ? "Unsave" : "Save for later"}
        >
          <Bookmark className="w-3.5 h-3.5" fill={saved ? "currentColor" : "none"} />
        </button>
      </div>

      <p className="text-xs text-white/45 leading-relaxed mb-3">
        {rec.description}
      </p>

      {/* Meta row */}
      <div className="flex items-center gap-2 flex-wrap">
        {/* Relevance */}
        <span
          className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full border text-xs ${relevanceColor(
            rec.relevanceScore
          )}`}
        >
          {Math.round(rec.relevanceScore * 100)}% match
        </span>

        {/* Distance */}
        <span className="text-xs text-white/25 flex items-center gap-1">
          <ChevronRight className="w-3 h-3" />
          {distanceLabel(rec.distanceFromUser)}
        </span>

        {/* Read time */}
        {rec.estimatedReadTime && (
          <span className="text-xs text-white/25 flex items-center gap-1 ml-auto">
            <Clock className="w-3 h-3" />
            {rec.estimatedReadTime}m
          </span>
        )}
      </div>

      {/* Tags */}
      {rec.tags && rec.tags.length > 0 && (
        <div className="flex flex-wrap gap-1 mt-2">
          {rec.tags.map((tag) => (
            <span
              key={tag}
              className="text-xs px-1.5 py-0.5 rounded bg-white/5 text-white/30"
            >
              {tag}
            </span>
          ))}
        </div>
      )}
    </motion.div>
  );
}

// ─── Main Panel ───────────────────────────────────────────────────
interface LearnNextPanelProps {
  userId: string;
}

export default function LearnNextPanel({ userId }: LearnNextPanelProps) {
  const [recs, setRecs] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    const result = await getRecommendations(userId, 6);
    if (result.data && result.data.length > 0) {
      setRecs(result.data);
    } else {
      // fallback demo data
      setRecs(DEMO_RECOMMENDATIONS);
    }
    setLoading(false);
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId]);

  return (
    <div className="h-full glass-card flex flex-col overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-white/10 shrink-0">
        <div className="flex items-center gap-2">
          <Lightbulb className="w-4 h-4 text-yellow-400" />
          <span className="text-sm font-semibold text-white">Learn Next</span>
        </div>
        <button
          onClick={load}
          disabled={loading}
          className="text-white/30 hover:text-white/60 transition-colors"
          aria-label="Refresh recommendations"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {loading ? (
          <div className="flex flex-col items-center justify-center h-32 gap-3 text-white/30">
            <Loader2 className="w-6 h-6 animate-spin" />
            <p className="text-xs">Finding recommendations…</p>
          </div>
        ) : (
          <AnimatePresence>
            {recs.map((rec, i) => (
              <RecommendationCard key={rec.id} rec={rec} index={i} />
            ))}
          </AnimatePresence>
        )}
      </div>

      {/* Footer */}
      {!loading && recs.length > 0 && (
        <div className="p-3 border-t border-white/10 shrink-0">
          <Button variant="ghost" size="sm" fullWidth onClick={load}>
            Refresh suggestions
          </Button>
        </div>
      )}
    </div>
  );
}
