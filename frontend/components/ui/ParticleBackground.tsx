"use client";

import { motion } from "framer-motion";
import React, { useMemo } from "react";

interface Particle {
  id: number;
  x: number;
  y: number;
  size: number;
  duration: number;
  delay: number;
  color: string;
  blur: number;
}

const COLORS = [
  "rgba(59,130,246,0.8)",
  "rgba(99,102,241,0.8)",
  "rgba(139,92,246,0.7)",
  "rgba(59,130,246,0.5)",
  "rgba(6,182,212,0.7)",
  "rgba(255,255,255,0.4)",
];

function seededRandom(seed: number) {
  const x = Math.sin(seed + 1) * 10000;
  return x - Math.floor(x);
}

export default function ParticleBackground({ count = 40 }: { count?: number }) {
  const particles = useMemo<Particle[]>(() => {
    return Array.from({ length: count }, (_, i) => ({
      id: i,
      x: seededRandom(i * 3) * 100,
      y: seededRandom(i * 7) * 100,
      size: seededRandom(i * 11) * 4 + 1.5,
      duration: seededRandom(i * 13) * 12 + 8,
      delay: seededRandom(i * 17) * -20,
      color: COLORS[Math.floor(seededRandom(i * 19) * COLORS.length)],
      blur: seededRandom(i * 23) < 0.4 ? 2 : 0,
    }));
  }, [count]);

  return (
    <div
      className="pointer-events-none fixed inset-0 overflow-hidden"
      aria-hidden="true"
    >
      {particles.map((p) => (
        <motion.div
          key={p.id}
          className="absolute rounded-full"
          style={{
            left: `${p.x}%`,
            top: `${p.y}%`,
            width: p.size,
            height: p.size,
            background: p.color,
            boxShadow: `0 0 ${p.size * 3}px ${p.color}, 0 0 ${p.size * 6}px ${p.color}`,
            filter: p.blur ? `blur(${p.blur}px)` : undefined,
          }}
          animate={{
            y: [0, -(seededRandom(p.id * 31) * 60 + 20), 0],
            x: [
              0,
              (seededRandom(p.id * 37) - 0.5) * 40,
              (seededRandom(p.id * 41) - 0.5) * 20,
              0,
            ],
            opacity: [
              seededRandom(p.id * 43) * 0.4 + 0.2,
              seededRandom(p.id * 47) * 0.5 + 0.5,
              seededRandom(p.id * 53) * 0.3 + 0.1,
              seededRandom(p.id * 59) * 0.4 + 0.2,
            ],
            scale: [1, seededRandom(p.id * 61) * 0.4 + 0.9, 1],
          }}
          transition={{
            duration: p.duration,
            delay: p.delay,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />
      ))}

      {/* Larger ambient blobs */}
      {[0, 1, 2].map((i) => (
        <motion.div
          key={`blob-${i}`}
          className="absolute rounded-full"
          style={{
            left: `${[15, 70, 45][i]}%`,
            top: `${[20, 60, 80][i]}%`,
            width: [200, 150, 180][i],
            height: [200, 150, 180][i],
            background: [
              "radial-gradient(circle, rgba(59,130,246,0.06) 0%, transparent 70%)",
              "radial-gradient(circle, rgba(139,92,246,0.06) 0%, transparent 70%)",
              "radial-gradient(circle, rgba(6,182,212,0.04) 0%, transparent 70%)",
            ][i],
            transform: "translate(-50%, -50%)",
          }}
          animate={{
            scale: [1, 1.3, 1],
            opacity: [0.5, 1, 0.5],
          }}
          transition={{
            duration: [18, 22, 15][i],
            delay: [0, -7, -12][i],
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />
      ))}
    </div>
  );
}
