"use client";

import { motion, HTMLMotionProps } from "framer-motion";
import React from "react";
// Minimal className combiner – avoids adding clsx to deps
function clsx(...classes: (string | undefined | null | false)[]): string {
  return classes.filter(Boolean).join(" ");
}

type Variant = "primary" | "secondary" | "ghost" | "danger";
type Size = "sm" | "md" | "lg";

interface ButtonProps extends Omit<HTMLMotionProps<"button">, "children"> {
  variant?: Variant;
  size?: Size;
  loading?: boolean;
  icon?: React.ReactNode;
  iconPosition?: "left" | "right";
  children: React.ReactNode;
  fullWidth?: boolean;
}

const variantStyles: Record<Variant, string> = {
  primary: [
    "relative overflow-hidden font-semibold text-white",
    "bg-gradient-to-r from-blue-500 to-indigo-600",
    "border border-blue-400/30",
    "shadow-[0_0_20px_rgba(59,130,246,0.35)]",
    "hover:shadow-[0_0_30px_rgba(59,130,246,0.6),0_0_60px_rgba(59,130,246,0.2)]",
    "hover:from-blue-400 hover:to-indigo-500",
    "transition-all duration-300",
  ].join(" "),

  secondary: [
    "relative overflow-hidden font-semibold text-white/80 hover:text-white",
    "backdrop-blur-xl bg-white/5 hover:bg-white/10",
    "border border-white/10 hover:border-white/20",
    "shadow-[0_8px_32px_rgba(0,0,0,0.37)]",
    "transition-all duration-300",
  ].join(" "),

  ghost: [
    "font-medium text-white/60 hover:text-white",
    "bg-transparent hover:bg-white/5",
    "border border-transparent hover:border-white/10",
    "transition-all duration-200",
  ].join(" "),

  danger: [
    "relative overflow-hidden font-semibold text-white",
    "bg-gradient-to-r from-red-500 to-rose-600",
    "border border-red-400/30",
    "shadow-[0_0_20px_rgba(239,68,68,0.25)]",
    "hover:shadow-[0_0_30px_rgba(239,68,68,0.5)]",
    "transition-all duration-300",
  ].join(" "),
};

const sizeStyles: Record<Size, string> = {
  sm: "px-4 py-2 text-xs rounded-lg gap-1.5",
  md: "px-6 py-3 text-sm rounded-xl gap-2",
  lg: "px-8 py-4 text-base rounded-xl gap-2.5",
};

export default function Button({
  variant = "primary",
  size = "md",
  loading = false,
  icon,
  iconPosition = "left",
  children,
  fullWidth = false,
  className,
  disabled,
  ...props
}: ButtonProps) {
  const isDisabled = disabled || loading;

  return (
    <motion.button
      whileHover={isDisabled ? undefined : { y: -1 }}
      whileTap={isDisabled ? undefined : { y: 0, scale: 0.98 }}
      disabled={isDisabled}
      className={clsx(
        "inline-flex items-center justify-center select-none cursor-pointer",
        variantStyles[variant],
        sizeStyles[size],
        fullWidth && "w-full",
        isDisabled && "opacity-50 cursor-not-allowed pointer-events-none",
        className
      )}
      {...props}
    >
      {/* Shimmer overlay for primary */}
      {variant === "primary" && !isDisabled && (
        <span
          className="absolute inset-0 -translate-x-full animate-[shimmer_2.5s_linear_infinite] bg-gradient-to-r from-transparent via-white/10 to-transparent"
          aria-hidden="true"
        />
      )}

      {loading ? (
        <>
          <Spinner size={size} />
          <span>Loading…</span>
        </>
      ) : (
        <>
          {icon && iconPosition === "left" && (
            <span className="shrink-0">{icon}</span>
          )}
          <span>{children}</span>
          {icon && iconPosition === "right" && (
            <span className="shrink-0">{icon}</span>
          )}
        </>
      )}
    </motion.button>
  );
}

function Spinner({ size }: { size: Size }) {
  const s = size === "sm" ? 14 : size === "lg" ? 20 : 16;
  return (
    <svg
      width={s}
      height={s}
      viewBox="0 0 24 24"
      fill="none"
      className="animate-spin shrink-0"
      aria-hidden="true"
    >
      <circle
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="3"
        strokeOpacity="0.25"
      />
      <path
        d="M12 2a10 10 0 0 1 10 10"
        stroke="currentColor"
        strokeWidth="3"
        strokeLinecap="round"
      />
    </svg>
  );
}
