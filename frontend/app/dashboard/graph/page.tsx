import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import DashboardShell from "@/components/dashboard/DashboardShell";
import GraphPageClient from "@/components/dashboard/GraphPageClient";

export const metadata = { title: "Knowledge Graph" };

export default async function GraphPage() {
  const supabase = createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/auth/login?next=/dashboard/graph");
  }

  return (
    <DashboardShell user={user} activeRoute="/dashboard/graph">
      <GraphPageClient userId={user.id} />
    </DashboardShell>
  );
}
