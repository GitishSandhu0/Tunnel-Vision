import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import DashboardShell from "@/components/dashboard/DashboardShell";
import { LayoutDashboard, Files, Network, Lightbulb } from "lucide-react";

export const metadata = { title: "Dashboard" };

export default async function DashboardPage() {
  const supabase = createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/auth/login?next=/dashboard");
  }

  const stats = [
    {
      label: "Uploaded Files",
      value: "0",
      icon: Files,
      color: "text-blue-400",
      bg: "rgba(59,130,246,0.1)",
      border: "rgba(59,130,246,0.2)",
    },
    {
      label: "Entities Extracted",
      value: "0",
      icon: Lightbulb,
      color: "text-purple-400",
      bg: "rgba(139,92,246,0.1)",
      border: "rgba(139,92,246,0.2)",
    },
    {
      label: "Graph Nodes",
      value: "0",
      icon: Network,
      color: "text-cyan-400",
      bg: "rgba(6,182,212,0.1)",
      border: "rgba(6,182,212,0.2)",
    },
    {
      label: "Recommendations",
      value: "0",
      icon: LayoutDashboard,
      color: "text-emerald-400",
      bg: "rgba(52,211,153,0.1)",
      border: "rgba(52,211,153,0.2)",
    },
  ];

  return (
    <DashboardShell user={user} activeRoute="/dashboard">
      <div className="space-y-8">
        {/* Welcome */}
        <div>
          <h1 className="text-2xl font-bold text-white mb-1">
            Welcome back 👋
          </h1>
          <p className="text-white/40 text-sm">{user.email}</p>
        </div>

        {/* Stats grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
          {stats.map((stat) => (
            <div
              key={stat.label}
              className="backdrop-blur-xl rounded-2xl border p-5 transition-all duration-300 hover:-translate-y-0.5"
              style={{
                background: stat.bg,
                borderColor: stat.border,
                boxShadow:
                  "0 8px 32px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.05)",
              }}
            >
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-medium text-white/40 uppercase tracking-wider">
                  {stat.label}
                </span>
                <div
                  className="w-8 h-8 rounded-lg flex items-center justify-center"
                  style={{ background: stat.bg }}
                >
                  <stat.icon className={`w-4 h-4 ${stat.color}`} />
                </div>
              </div>
              <p className="text-3xl font-bold text-white">{stat.value}</p>
            </div>
          ))}
        </div>

        {/* Quick actions */}
        <div className="grid md:grid-cols-2 gap-5">
          <div className="glass-card p-6">
            <h2 className="text-lg font-semibold text-white mb-3">
              Get Started
            </h2>
            <ul className="space-y-3 text-sm text-white/50">
              {[
                { step: "1", text: "Upload your notes or data files", href: "/dashboard/upload" },
                { step: "2", text: "Let AI extract entities and relationships", href: "/dashboard/upload" },
                { step: "3", text: "Explore your knowledge graph", href: "/dashboard/graph" },
              ].map((item) => (
                <li key={item.step} className="flex items-center gap-3">
                  <span className="w-6 h-6 rounded-full bg-blue-500/20 border border-blue-500/30 flex items-center justify-center text-blue-400 font-bold text-xs shrink-0">
                    {item.step}
                  </span>
                  <a
                    href={item.href}
                    className="hover:text-white transition-colors"
                  >
                    {item.text}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          <div className="glass-card p-6">
            <h2 className="text-lg font-semibold text-white mb-3">
              Recent Activity
            </h2>
            <div className="flex flex-col items-center justify-center h-24 text-white/25">
              <Files className="w-8 h-8 mb-2" />
              <p className="text-sm">No activity yet</p>
            </div>
          </div>
        </div>
      </div>
    </DashboardShell>
  );
}
