import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import DashboardShell from "@/components/dashboard/DashboardShell";
import UploadClient from "@/components/dashboard/UploadClient";

export const metadata = { title: "Upload Data" };

export default async function UploadPage() {
  const supabase = createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/auth/login?next=/dashboard/upload");
  }

  return (
    <DashboardShell user={user} activeRoute="/dashboard/upload">
      <div className="space-y-6 max-w-3xl">
        <div>
          <h1 className="text-2xl font-bold text-white mb-1">Upload Data</h1>
          <p className="text-white/40 text-sm">
            Upload ZIP archives or JSON files. The AI pipeline will extract
            entities and build your knowledge graph automatically.
          </p>
        </div>
        <UploadClient />
      </div>
    </DashboardShell>
  );
}
