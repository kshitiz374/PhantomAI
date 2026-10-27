const API_BASE =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") || "http://127.0.0.1:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      ...(init?.headers || {}),
    },
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || res.statusText);
  }
  const ct = res.headers.get("content-type") || "";
  if (ct.includes("application/json")) {
    return res.json() as Promise<T>;
  }
  return res.text() as Promise<T>;
}

export type Investigation = {
  id: string;
  title: string;
  description: string | null;
  artifact_count: number;
  clue_count: number;
  unresolved_questions: number;
  active_personality: string;
  status: string;
};

export type Artifact = {
  id: string;
  filename: string;
  content: string;
  summary: string | null;
  imported_at: string;
  tags?: string[];
};

export type Health = {
  status: string;
  model_provider: string;
  model_available: boolean;
  offline_capable: boolean;
};

export const api = {
  health: () => request<Health>("/api/health"),
  listInvestigations: () => request<Investigation[]>("/api/investigations"),
  createInvestigation: (body: Record<string, unknown>) =>
    request<Investigation>("/api/investigations", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  deleteInvestigation: (id: string) =>
    request<{ deleted: boolean }>(`/api/investigations/${id}`, { method: "DELETE" }),
  getArtifacts: (invId: string) =>
    request<Artifact[]>(`/api/investigations/${invId}/artifacts`),
  uploadArtifact: (invId: string, file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    return request<Artifact>(`/api/investigations/${invId}/artifacts`, {
      method: "POST",
      body: fd,
    });
  },
  scan: (invId: string) =>
    request<{ artifacts_processed: number; is_demonstration: boolean }>(
      `/api/investigations/${invId}/scan`,
      { method: "POST" }
    ),
  chat: (invId: string, message: string) =>
    request<{ content: string; source_references: string[]; is_demonstration: boolean }>(
      `/api/investigations/${invId}/chat`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message }),
      }
    ),
  graph: (invId: string) =>
    request<{ nodes: GraphNode[]; edges: GraphEdge[] }>(
      `/api/investigations/${invId}/graph`
    ),
  timeline: (invId: string) => request<TimelineEvent[]>(`/api/investigations/${invId}/timeline`),
  reconstruct: (invId: string) =>
    request<ReconstructReport>(`/api/investigations/${invId}/reconstruct`, {
      method: "POST",
    }),
  export: (invId: string, format: "markdown" | "json") =>
    request<string>(`/api/investigations/${invId}/export?format=${format}`),
  updateModel: (body: Record<string, unknown>) =>
    request("/api/settings/model", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  models: () => request<{ models: unknown[]; active_provider: string }>("/api/models"),
  getArtifact: (id: string) => request<Artifact>(`/api/artifacts/${id}`),
  updateInvestigationSettings: (
    invId: string,
    body: { active_personality?: string; custom_personality?: string }
  ) =>
    request(`/api/investigations/${invId}/settings`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  addRelationship: (
    invId: string,
    body: { source_id: string; target_id: string; explanation?: string }
  ) =>
    request(`/api/investigations/${invId}/relationships`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  deleteRelationship: (relId: string) =>
    request(`/api/relationships/${relId}`, { method: "DELETE" }),
};

export type GraphNode = {
  id: string;
  type: string;
  label: string;
  evidence_type?: string;
  confidence?: number;
  data?: Record<string, unknown>;
};

export type GraphEdge = {
  id: string;
  source: string;
  target: string;
  label: string;
  evidence_type: string;
  confidence: number;
  explanation?: string;
  is_manual?: boolean;
};

export type TimelineEvent = {
  id: string;
  description: string;
  timestamp: string | null;
  evidence_type: string;
  source_references: string[];
  contradictions: string[];
};

export type ReconstructReport = {
  case_summary: string;
  established_evidence: string[];
  connected_clues: string[];
  unresolved_questions: string[];
  competing_theories: string[];
  final_story: string;
  evidence_references: Record<string, string[]>;
  disclaimer: string;
  is_demonstration: boolean;
};
