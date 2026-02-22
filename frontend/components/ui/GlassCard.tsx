"use client";

import { motion, HTMLMotionProps } from "framer-motion";
import React from "react";
// Minimal className combiner – avoids adding clsx to deps
function clsx(...classes: (string | undefined | null | false)[]): string {
  return classes.filter(Boolean).join(" ");
}

type Variant = "default" | "strong" | "highlight" | "danger";

interface GlassCardProps extends HTMLMotionProps<"div"> {
  variant?: Variant;
  glow?: "blue" | "purple" | "none";
  children: React.ReactNode;
  padding?: "none" | "sm" | "md" | "lg";
  animate?: boolean;
}

const variantClasses: Record<Variant, string> = {
  default: [
    "backdrop-blur-xl rounded-2xl border",
    "bg-gradient-to-br from-white/[7%] to-white/[3%]",
    "border-white/10",
    "shadow-[0_8px_32px_rgba(0,0,0,0.4),inset_0_1px_0_rgba(255,255,255,0.06)]",
  ].join(" "),

  strong: [
    "backdrop-blur-2xl rounded-2xl border",
    "bg-gradient-to-br from-white/10 to-white/5",
    "border-white/20",
    "shadow-[0_16px_48px_rgba(0,0,0,0.5),inset_0_1px_0_rgba(255,255,255,0.10)]",
  ].join(" "),

  highlight: [
    "backdrop-blur-2xl rounded-2xl border",
    "bg-gradient-to-br from-blue-500/10 to-indigo-500/5",
    "border-blue-500/25",
    "shadow-[0_16px_48px_rgba(59,130,246,0.15),inset_0_1px_0_rgba(255,255,255,0.08)]",
  ].join(" "),

  danger: [
    "backdrop-blur-xl rounded-2xl border",
    "bg-gradient-to-br from-red-500/10 to-rose-500/5",
    "border-red-500/25",
    "shadow-[0_8px_32px_rgba(239,68,68,0.15)]",
  ].join(" "),
};

const glowClasses: Record<"blue" | "purple" | "none", string> = {
  blue: "shadow-[0_0_40px_rgba(59,130,246,0.15),0_16px_48px_rgba(0,0,0,0.5)]",
  purple:
    "shadow-[0_0_40px_rgba(139,92,246,0.15),0_16px_48px_rgba(0,0,0,0.5)]",
  none: "",
};

const paddingClasses = {
  none: "",
  sm: "p-4",
  md: "p-6",
  lg: "p-8",
};

export default function GlassCard({
  variant = "default",
  glow = "none",
  padding = "md",
  animate: shouldAnimate = false,
  children,
  className,
  ...props
}: GlassCardProps) {
  const classes = clsx(
    variantClasses[variant],
    glow !== "none" && glowClasses[glow],
    paddingClasses[padding],
    className
  );

  if (shouldAnimate) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: "easeOut" }}
        className={classes}
        {...props}
      >
        {children}
      </motion.div>
    );
  }

  return (
    <motion.div className={classes} {...props}>
      {children}
    </motion.div>
  );
}
