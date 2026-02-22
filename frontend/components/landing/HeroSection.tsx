"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import {
  BrainCircuit,
  UploadCloud,
  Network,
  Sparkles,
  ArrowRight,
  ChevronRight,
} from "lucide-react";
import ParticleBackground from "@/components/ui/ParticleBackground";
import GlassCard from "@/components/ui/GlassCard";
import Button from "@/components/ui/Button";

// ─── Feature card data ───────────────────────────────────────────
const features = [
  {
    icon: UploadCloud,
    title: "Upload Your Data",
    description:
      "Drop in your notes, articles, bookmarks, or any JSON/ZIP archive. Our AI parses it all automatically.",
    color: "text-blue-400",
    glow: "rgba(59,130,246,0.2)",
    border: "rgba(59,130,246,0.15)",
  },
  {
    icon: BrainCircuit,
    title: "AI Analysis",
    description:
      "Deep-learning pipelines extract entities, concepts, and relationships—building a semantic fingerprint of your knowledge.",
    color: "text-purple-400",
    glow: "rgba(139,92,246,0.2)",
    border: "rgba(139,92,246,0.15)",
  },
  {
    icon: Network,
    title: "Knowledge Graph",
    description:
      "Visualize the living web of everything you know and the vast unexplored territory waiting to be discovered.",
    color: "text-cyan-400",
    glow: "rgba(6,182,212,0.2)",
    border: "rgba(6,182,212,0.15)",
  },
];

// ─── Stagger variants ─────────────────────────────────────────────
const container = {
  hidden: {},
  show: { transition: { staggerChildren: 0.12 } },
};

const fadeUp = {
  hidden: { opacity: 0, y: 28 },
  show: { opacity: 1, y: 0, transition: { duration: 0.65, ease: "easeOut" } },
};

export default function HeroSection() {
  return (
    <>
      {/* ── Hero ────────────────────────────────────────────────── */}
      <section className="relative min-h-screen flex flex-col overflow-hidden bg-obsidian">
        {/* Grid background */}
        <div className="absolute inset-0 bg-grid opacity-60" aria-hidden />

        {/* Radial glow overlays */}
        <div
          className="absolute inset-0 pointer-events-none"
          style={{
            background:
              "radial-gradient(ellipse 80% 50% at 50% -5%, rgba(59,130,246,0.18) 0%, transparent 60%)",
          }}
          aria-hidden
        />
        <div
          className="absolute inset-0 pointer-events-none"
          style={{
            background:
              "radial-gradient(ellipse 60% 40% at 80% 110%, rgba(139,92,246,0.12) 0%, transparent 60%)",
          }}
          aria-hidden
        />

        {/* Floating particles */}
        <ParticleBackground count={45} />

        {/* ── Navbar ───────────────────────────────────────────── */}
        <nav className="relative z-10 flex items-center justify-between px-6 py-5 max-w-7xl mx-auto w-full">
          <motion.div
            initial={{ opacity: 0, x: -16 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5 }}
            className="flex items-center gap-2"
          >
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shadow-neon">
              <Sparkles className="w-4 h-4 text-white" />
            </div>
            <span className="font-bold text-lg text-white tracking-tight">
              Tunnel Vision
            </span>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, x: 16 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="flex items-center gap-3"
          >
            <Link
              href="/auth/login"
              className="px-4 py-2 text-sm text-white/70 hover:text-white transition-colors duration-200 font-medium"
            >
              Log In
            </Link>
            <Link href="/auth/signup">
              <Button size="sm" variant="primary">
                Sign Up
              </Button>
            </Link>
          </motion.div>
        </nav>

        {/* ── Hero Content ─────────────────────────────────────── */}
        <div className="relative z-10 flex-1 flex items-center justify-center px-4 pb-20">
          <motion.div
            variants={container}
            initial="hidden"
            animate="show"
            className="max-w-4xl mx-auto text-center"
          >
            {/* Badge */}
            <motion.div variants={fadeUp} className="flex justify-center mb-6">
              <span className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full glass text-xs font-semibold text-blue-300 border-blue-500/20">
                <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse_glow" />
                AI-Powered Knowledge Mapping
              </span>
            </motion.div>

            {/* Main heading */}
            <motion.h1
              variants={fadeUp}
              className="text-5xl sm:text-6xl md:text-7xl font-extrabold tracking-tight mb-6 leading-none"
            >
              <span className="text-white">Tunnel</span>{" "}
              <span
                className="bg-gradient-to-r from-blue-400 via-indigo-400 to-purple-400 bg-clip-text text-transparent glow-text"
              >
                Vision
              </span>
            </motion.h1>

            {/* Tagline */}
            <motion.p
              variants={fadeUp}
              className="text-xl sm:text-2xl text-white/50 mb-4 font-light tracking-wide"
            >
              Map your mind.{" "}
              <span className="text-white/80 font-medium">
                Explore the unknown.
              </span>
            </motion.p>

            <motion.p
              variants={fadeUp}
              className="text-base text-white/40 mb-10 max-w-xl mx-auto"
            >
              Upload your notes, articles and bookmarks. Watch as AI weaves
              them into a living knowledge graph—then shows you exactly what
              to explore next.
            </motion.p>

            {/* CTA Buttons */}
            <motion.div
              variants={fadeUp}
              className="flex flex-wrap items-center justify-center gap-4"
            >
              <Link href="/auth/signup">
                <Button
                  variant="primary"
                  size="lg"
                  icon={<ArrowRight className="w-5 h-5" />}
                  iconPosition="right"
                >
                  Get Started Free
                </Button>
              </Link>
              <a href="#features">
                <Button variant="secondary" size="lg">
                  Learn More
                </Button>
              </a>
            </motion.div>

            {/* Hero glassmorphic card */}
            <motion.div
              variants={fadeUp}
              className="mt-16 mx-auto max-w-2xl"
            >
              <GlassCard variant="strong" padding="lg" glow="blue">
                <div className="grid grid-cols-3 divide-x divide-white/10">
                  {[
                    { label: "Nodes Mapped", value: "10M+" },
                    { label: "Knowledge Links", value: "50M+" },
                    { label: "Avg. Discovery", value: "4.2×" },
                  ].map(({ label, value }) => (
                    <div key={label} className="px-4 py-2 text-center">
                      <div className="text-2xl font-bold text-white mb-1">
                        {value}
                      </div>
                      <div className="text-xs text-white/40">{label}</div>
                    </div>
                  ))}
                </div>
              </GlassCard>
            </motion.div>
          </motion.div>
        </div>

        {/* Scroll hint */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.5 }}
          className="absolute bottom-8 left-1/2 -translate-x-1/2 flex flex-col items-center gap-1 text-white/30 text-xs"
          aria-hidden
        >
          <ChevronRight className="w-4 h-4 rotate-90" />
        </motion.div>
      </section>

      {/* ── Features Section ─────────────────────────────────────── */}
      <section
        id="features"
        className="relative bg-midnight py-24 px-4 overflow-hidden"
      >
        <div className="absolute inset-0 bg-grid-sm opacity-30" aria-hidden />

        <div className="max-w-6xl mx-auto relative z-10">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="text-center mb-16"
          >
            <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
              Everything you need to{" "}
              <span className="bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                think better
              </span>
            </h2>
            <p className="text-white/50 max-w-xl mx-auto">
              Three powerful stages that transform raw information into
              actionable knowledge.
            </p>
          </motion.div>

          <motion.div
            variants={container}
            initial="hidden"
            whileInView="show"
            viewport={{ once: true, margin: "-80px" }}
            className="grid md:grid-cols-3 gap-6"
          >
            {features.map((feat) => (
              <motion.div key={feat.title} variants={fadeUp}>
                <div
                  className="h-full backdrop-blur-xl rounded-2xl border p-6 transition-all duration-300 hover:-translate-y-1 group"
                  style={{
                    background: `radial-gradient(ellipse 80% 60% at 50% -10%, ${feat.glow} 0%, transparent 70%), rgba(255,255,255,0.03)`,
                    borderColor: feat.border,
                    boxShadow: `0 8px 32px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.05)`,
                  }}
                >
                  <div
                    className="w-12 h-12 rounded-xl flex items-center justify-center mb-4 transition-transform duration-300 group-hover:scale-110"
                    style={{ background: feat.glow }}
                  >
                    <feat.icon className={`w-6 h-6 ${feat.color}`} />
                  </div>
                  <h3 className="text-lg font-semibold text-white mb-2">
                    {feat.title}
                  </h3>
                  <p className="text-sm text-white/50 leading-relaxed">
                    {feat.description}
                  </p>
                </div>
              </motion.div>
            ))}
          </motion.div>

          {/* Bottom CTA */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="mt-16 text-center"
          >
            <Link href="/auth/signup">
              <Button variant="primary" size="lg">
                Start Mapping Your Knowledge
              </Button>
            </Link>
          </motion.div>
        </div>
      </section>

      {/* ── Footer ───────────────────────────────────────────────── */}
      <footer className="bg-obsidian border-t border-white/5 py-8 px-4">
        <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2 text-white/40 text-sm">
            <Sparkles className="w-4 h-4" />
            <span>© 2024 Tunnel Vision. All rights reserved.</span>
          </div>
          <div className="flex gap-6 text-sm text-white/30">
            <a href="#" className="hover:text-white/60 transition-colors">
              Privacy
            </a>
            <a href="#" className="hover:text-white/60 transition-colors">
              Terms
            </a>
            <a href="#" className="hover:text-white/60 transition-colors">
              Contact
            </a>
          </div>
        </div>
      </footer>
    </>
  );
}
