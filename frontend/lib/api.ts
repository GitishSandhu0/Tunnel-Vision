import type {
  ApiResponse,
  GraphData,
  Recommendation,
  UploadJob,
  UploadResponse,
} from "@/types";
import { createClient as createSupabaseClient } from "@/lib/supabase/client";

const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

async function getAccessToken(): Promise<string | null> {
  if (typeof window === "undefined") {
    return null;
  }

  const supabase = createSupabaseClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();

  return session?.access_token ?? null;
}

// ─── Generic fetch wrapper ────────────────────────────────────────
async function apiFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  const url = `${BACKEND_URL}${path}`;
  const token = await getAccessToken();

  const headers = new Headers(options.headers || {});
  if (!headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  if (token && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  try {
    const res = await fetch(url, {
      ...options,
      headers,
    });

    if (!res.ok) {
      const text = await res.text();
      let message = `HTTP ${res.status}`;
      try {
        const json = JSON.parse(text);
        message = json.detail || json.message || message;
      } catch {
        message = text || message;
      }
      return { error: message };
    }

    const data = await res.json();
    return { data };
  } catch (err) {
    const message = err instanceof Error ? err.message : "Network error";
    return { error: message };
  }
}

// ─── File Upload ──────────────────────────────────────────────────
export async function uploadFile(
  file: File,
  onProgress?: (pct: number) => void
): Promise<ApiResponse<UploadResponse>> {
  const token = await getAccessToken();

  return new Promise((resolve) => {
    const formData = new FormData();
    formData.append("file", file);

    const xhr = new XMLHttpRequest();

    if (onProgress) {
      xhr.upload.addEventListener("progress", (e) => {
        if (e.lengthComputable) {
          onProgress(Math.round((e.loaded / e.total) * 100));
        }
      });
    }

    xhr.addEventListener("load", () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          const data = JSON.parse(xhr.responseText) as UploadResponse;
          resolve({ data });
        } catch {
          resolve({ error: "Invalid response from server" });
        }
      } else {
        let message = `HTTP ${xhr.status}`;
        try {
          const json = JSON.parse(xhr.responseText);
          message = json.detail || json.message || message;
        } catch {
          /* ignore */
        }
        resolve({ error: message });
      }
    });

    xhr.addEventListener("error", () => {
      resolve({ error: "Network error during upload" });
    });

    xhr.open("POST", `${BACKEND_URL}/ingest/upload`);
    if (token) {
      xhr.setRequestHeader("Authorization", `Bearer ${token}`);
    }
    xhr.send(formData);
  });
}

// ─── Graph Data ───────────────────────────────────────────────────
export async function getGraphData(
  userId?: string
): Promise<ApiResponse<GraphData>> {
  void userId;
  return apiFetch<GraphData>("/graph/data");
}

// ─── Recommendations ──────────────────────────────────────────────
export async function getRecommendations(
  userId?: string,
  limit = 10
): Promise<ApiResponse<Recommendation[]>> {
  const params = new URLSearchParams({ limit: String(limit) });
  void userId;
  return apiFetch<Recommendation[]>(`/recommendations?${params.toString()}`);
}

// ─── Job Status ───────────────────────────────────────────────────
export async function getJobStatus(
  jobId: string
): Promise<ApiResponse<UploadJob>> {
  return apiFetch<UploadJob>(`/ingest/status/${encodeURIComponent(jobId)}`);
}

// ─── Health Check ─────────────────────────────────────────────────
export async function healthCheck(): Promise<boolean> {
  try {
    const res = await fetch(`${BACKEND_URL}/health`, {
      signal: AbortSignal.timeout(3000),
    });
    return res.ok;
  } catch {
    return false;
  }
}
