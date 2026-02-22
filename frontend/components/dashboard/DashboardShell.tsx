"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  LayoutDashboard,
  UploadCloud,
  Network,
  Lightbulb,
  Sparkles,
  LogOut,
  Menu,
  X,
  ChevronRight,
} from "lucide-react";
import { createClient } from "@/lib/supabase/client";
import type { User } from "@supabase/supabase-js";

interface NavItem {
  label: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
}

const NAV_ITEMS: NavItem[] = [
  { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { label: "Upload Data", href: "/dashboard/upload", icon: UploadCloud },
  { label: "Knowledge Graph", href: "/dashboard/graph", icon: Network },
  { label: "Recommendations", href: "/dashboard/recommendations", icon: Lightbulb },
];

interface DashboardShellProps {
  user: User;
  activeRoute: string;
  children: React.ReactNode;
}

export default function DashboardShell({
  user,
  activeRoute,
  children,
}: DashboardShellProps) {
  const router = useRouter();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [loggingOut, setLoggingOut] = useState(false);

  async function handleLogout() {
    setLoggingOut(true);
    const supabase = createClient();
    await supabase.auth.signOut();
    router.push("/");
    router.refresh();
  }

  const Sidebar = ({ mobile = false }: { mobile?: boolean }) => (
    <nav
      className={
        mobile
          ? "flex flex-col h-full"
          : "hidden md:flex flex-col h-full"
      }
    >
      {/* Logo */}
      <div className="flex items-center gap-2.5 px-5 py-5 border-b border-white/10">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shadow-neon shrink-0">
          <Sparkles className="w-4 h-4 text-white" />
        </div>
        <span className="font-bold text-white tracking-tight">
          Tunnel Vision
        </span>
      </div>

      {/* Nav items */}
      <div className="flex-1 overflow-y-auto py-4 px-3 space-y-1">
        {NAV_ITEMS.map((item) => {
          const isActive = activeRoute === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={() => setMobileOpen(false)}
              className={`nav-item ${isActive ? "active" : ""}`}
            >
              <item.icon className="w-4 h-4 shrink-0" />
              <span className="flex-1">{item.label}</span>
              {isActive && (
                <ChevronRight className="w-3 h-3 text-blue-400" />
              )}
            </Link>
          );
        })}
      </div>

      {/* User + logout */}
      <div className="border-t border-white/10 p-3">
        <div className="glass rounded-xl p-3 mb-2">
          <p className="text-xs text-white/40 mb-0.5">Signed in as</p>
          <p className="text-sm text-white/80 font-medium truncate">
            {user.email}
          </p>
        </div>
        <button
          onClick={handleLogout}
          disabled={loggingOut}
          className="nav-item w-full text-red-400/70 hover:text-red-400 hover:bg-red-500/10"
        >
          <LogOut className="w-4 h-4 shrink-0" />
          <span>{loggingOut ? "Signing out…" : "Sign Out"}</span>
        </button>
      </div>
    </nav>
  );

  return (
    <div className="flex h-screen bg-obsidian overflow-hidden">
      {/* ── Desktop Sidebar ─────────────────────────────────── */}
      <aside className="hidden md:block w-60 shrink-0 border-r border-white/10 glass-panel rounded-none">
        <Sidebar />
      </aside>

      {/* ── Mobile Sidebar Overlay ───────────────────────────── */}
      <AnimatePresence>
        {mobileOpen && (
          <>
            <motion.div
              key="overlay"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 z-30 bg-black/60 backdrop-blur-sm md:hidden"
              onClick={() => setMobileOpen(false)}
            />
            <motion.aside
              key="sidebar"
              initial={{ x: "-100%" }}
              animate={{ x: 0 }}
              exit={{ x: "-100%" }}
              transition={{ type: "spring", stiffness: 300, damping: 30 }}
              className="fixed inset-y-0 left-0 z-40 w-64 glass-panel rounded-none md:hidden"
            >
              <Sidebar mobile />
            </motion.aside>
          </>
        )}
      </AnimatePresence>

      {/* ── Main Content ─────────────────────────────────────── */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top bar (mobile) */}
        <header className="md:hidden flex items-center justify-between px-4 py-3 border-b border-white/10 backdrop-blur-xl" style={{ background: "rgba(10,10,15,0.85)" }}>
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center">
              <Sparkles className="w-3.5 h-3.5 text-white" />
            </div>
            <span className="font-bold text-white text-sm">Tunnel Vision</span>
          </div>
          <button
            onClick={() => setMobileOpen((v) => !v)}
            className="p-2 text-white/60 hover:text-white rounded-lg transition-colors"
            aria-label="Toggle menu"
          >
            {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto p-6">
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
          >
            {children}
          </motion.div>
        </main>
      </div>
    </div>
  );
}
