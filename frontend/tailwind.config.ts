import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        obsidian: "#0a0a0f",
        midnight: "#0d1117",
        "glass-white": "#ffffff0d",
        "neon-blue": "#3b82f6",
        "neon-purple": "#8b5cf6",
        "neon-cyan": "#06b6d4",
        "surface-1": "#111118",
        "surface-2": "#16161f",
        "border-subtle": "rgba(255,255,255,0.08)",
        "border-strong": "rgba(255,255,255,0.18)",
      },
      fontFamily: {
        geist: ["var(--font-geist)", "Inter", "sans-serif"],
        sans: ["var(--font-geist)", "Inter", "sans-serif"],
      },
      backgroundImage: {
        "grid-pattern":
          "linear-gradient(rgba(59,130,246,0.07) 1px, transparent 1px), linear-gradient(90deg, rgba(59,130,246,0.07) 1px, transparent 1px)",
        "grid-pattern-sm":
          "linear-gradient(rgba(59,130,246,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(59,130,246,0.04) 1px, transparent 1px)",
        "radial-glow":
          "radial-gradient(ellipse 80% 50% at 50% -10%, rgba(59,130,246,0.18) 0%, transparent 60%)",
        "radial-glow-purple":
          "radial-gradient(ellipse 60% 40% at 70% 110%, rgba(139,92,246,0.15) 0%, transparent 60%)",
        "hero-gradient":
          "radial-gradient(ellipse 100% 60% at 50% 0%, rgba(59,130,246,0.12) 0%, transparent 55%), radial-gradient(ellipse 60% 40% at 80% 100%, rgba(139,92,246,0.10) 0%, transparent 55%)",
      },
      backgroundSize: {
        grid: "48px 48px",
        "grid-sm": "24px 24px",
      },
      boxShadow: {
        glass: "0 8px 32px 0 rgba(0,0,0,0.37), inset 0 1px 0 rgba(255,255,255,0.06)",
        "glass-strong":
          "0 16px 48px 0 rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.10)",
        neon: "0 0 20px rgba(59,130,246,0.4), 0 0 60px rgba(59,130,246,0.15)",
        "neon-purple":
          "0 0 20px rgba(139,92,246,0.4), 0 0 60px rgba(139,92,246,0.15)",
        "neon-sm": "0 0 10px rgba(59,130,246,0.5)",
      },
      keyframes: {
        float: {
          "0%, 100%": { transform: "translateY(0px) translateX(0px)" },
          "25%": { transform: "translateY(-12px) translateX(6px)" },
          "50%": { transform: "translateY(-6px) translateX(-4px)" },
          "75%": { transform: "translateY(-18px) translateX(8px)" },
        },
        "float-slow": {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%": { transform: "translateY(-20px)" },
        },
        pulse_glow: {
          "0%, 100%": { opacity: "0.4", transform: "scale(1)" },
          "50%": { opacity: "1", transform: "scale(1.2)" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
        "scan-line": {
          "0%": { transform: "translateY(-100%)" },
          "100%": { transform: "translateY(100vh)" },
        },
        "fade-in-up": {
          "0%": { opacity: "0", transform: "translateY(24px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: {
        float: "float 8s ease-in-out infinite",
        "float-slow": "float-slow 12s ease-in-out infinite",
        pulse_glow: "pulse_glow 3s ease-in-out infinite",
        shimmer: "shimmer 2.5s linear infinite",
        "scan-line": "scan-line 8s linear infinite",
        "fade-in-up": "fade-in-up 0.6s ease-out forwards",
      },
      backdropBlur: {
        xs: "2px",
      },
      borderRadius: {
        "2xl": "1rem",
        "3xl": "1.5rem",
      },
    },
  },
  plugins: [],
};

export default config;
