const API = "";

export type ActionType =
  | "read_file"
  | "classify_file"
  | "move_file"
  | "rename_file"
  | "upload_file"
  | "run_shell"
  | "open_website"
  | "login"
  | "paste_content"
  | "submit_form"
  | "make_payment"
  | "delete_file"
  | "share_data";

export type TaskType =
  | "general"
  | "coursework_organizer"
  | "financial_assistant";

export interface AgentActionRequest {
  action_type: ActionType;
  task_type?: TaskType;
  target_path?: string | null;
  target_url?: string | null;
  mime_type?: string | null;
  payload_preview?: string | null;
  form_field_names?: string[] | null;
  overwrite?: boolean;
  session_id?: string;
  environment_hint?: string | null;
}

export interface MediationResult {
  request_id: string;
  sensitivity: {
    level: string;
    domain_trust: string;
    categories: string[];
    signals: string[];
  };
  risk: {
    action_risk: number;
    data_risk: number;
    risk_score: number;
    composite_score: number;
    reasons: string[];
  };
  trust_envelope: {
    value: number;
    factors: string[];
    shrunk_for: string[];
  };
  decision: {
    decision: string;
    permissions: {
      file_read_write: string;
      execution: string;
      network: string;
      review_required: boolean;
      limited_mode_only: boolean;
    };
    transforms: string[];
    effective_scope: Record<string, unknown>;
    user_message: string;
    expires_in_seconds: number | null;
  };
  masked_preview?: string | null;
  transformed_payload_hint: string | null;
  audit_note: string;
  preference_memory?: {
    key: string;
    task_type: string;
    action_type: string;
    sensitivity: string;
    allow_count: number;
    deny_count: number;
    ask_count: number;
    confidence: number;
    bias: number;
  };
  capability_token?: string | null;
  policy_digest?: string | null;
  capability_scopes?: string[];
  native?: { c_library_loaded?: boolean; library_path?: string | null };
}

export async function mediate(
  body: AgentActionRequest
): Promise<MediationResult> {
  const r = await fetch(`${API}/api/v1/mediate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) {
    const err = await r.json().catch(() => ({}));
    throw new Error(JSON.stringify(err));
  }
  return r.json();
}

export async function fetchHealth(): Promise<{ layers: string[] }> {
  const r = await fetch(`${API}/health`);
  if (!r.ok) throw new Error("health failed");
  return r.json();
}

export async function fetchAudit(limit = 40) {
  const r = await fetch(`${API}/api/v1/audit?limit=${limit}`);
  if (!r.ok) throw new Error("audit failed");
  return r.json() as Promise<{
    items: {
      id: number;
      ts: number;
      action_type: string;
      decision: string;
      composite_risk: number;
      summary: string;
    }[];
  }>;
}

export async function sendFeedback(p: {
  request_id: string;
  accepted?: boolean;
  outcome?: "allow" | "ask" | "deny";
  task_type: TaskType;
  action_type: ActionType;
  sensitivity: "low" | "medium" | "high" | "critical";
  scenario_category: string;
}) {
  const r = await fetch(`${API}/api/v1/feedback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(p),
  });
  if (!r.ok) throw new Error("feedback failed");
  return r.json();
}

export async function fetchPreferenceMemory(limit = 80) {
  const r = await fetch(`${API}/api/v1/analytics/preference-memory?limit=${limit}`);
  if (!r.ok) throw new Error("preference-memory failed");
  return r.json() as Promise<{
    items: {
      key: string;
      task_type: string;
      action_type: string;
      sensitivity: string;
      allow_count: number;
      deny_count: number;
      ask_count: number;
      confidence: number;
      bias: number;
    }[];
  }>;
}

export async function resetPrefs(category: string | null) {
  const r = await fetch(`${API}/api/v1/preferences/reset`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ category }),
  });
  if (!r.ok) throw new Error("reset failed");
  return r.json();
}

export async function trustBias(category: string) {
  const r = await fetch(`${API}/api/v1/trust/${encodeURIComponent(category)}`);
  if (!r.ok) throw new Error("trust failed");
  return r.json() as Promise<{ category: string; bias: number }>;
}

export async function fetchHeatmap() {
  const r = await fetch(`${API}/api/v1/analytics/heatmap`);
  if (!r.ok) throw new Error("heatmap failed");
  return r.json() as Promise<{
    cells: {
      action_type: string;
      risk_bucket: number;
      count: number;
      avg_risk: number;
    }[];
  }>;
}

export async function fetchAuthorityTimeline(limit = 100) {
  const r = await fetch(
    `${API}/api/v1/analytics/authority-timeline?limit=${limit}`
  );
  if (!r.ok) throw new Error("timeline failed");
  return r.json() as Promise<{
    items: {
      id: number;
      ts: number;
      request_id: string;
      action_type: string;
      decision: string;
      composite_risk: number;
      envelope: number;
      summary: string;
    }[];
  }>;
}

export async function fetchOperations(limit = 50) {
  const r = await fetch(`${API}/api/v1/operations?limit=${limit}`);
  if (!r.ok) throw new Error("operations failed");
  return r.json() as Promise<{
    items: {
      id: number;
      ts: number;
      kind: string;
      detail: Record<string, unknown>;
      inverse: Record<string, unknown>;
      status: string;
      request_id: string | null;
    }[];
  }>;
}

export async function rollbackOp(id: number) {
  const r = await fetch(`${API}/api/v1/operations/${id}/rollback`, {
    method: "POST",
  });
  if (!r.ok) {
    const j = await r.json().catch(() => ({}));
    throw new Error(JSON.stringify(j));
  }
  return r.json();
}

export async function fetchProfile() {
  const r = await fetch(`${API}/api/v1/profile`);
  if (!r.ok) throw new Error("profile failed");
  return r.json() as Promise<{
    risk_aversion: number;
    forgetting_lambda_per_hour: number;
    last_forget_wallclock: number;
  }>;
}

export async function patchProfile(body: {
  risk_aversion?: number;
  forgetting_lambda_per_hour?: number;
}) {
  const r = await fetch(`${API}/api/v1/profile`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error("patch profile failed");
  return r.json();
}

export async function forgetNow() {
  const r = await fetch(`${API}/api/v1/profile/forget-now`, { method: "POST" });
  if (!r.ok) throw new Error("forget failed");
  return r.json();
}

export async function hookFile(body: Record<string, unknown>) {
  const r = await fetch(`${API}/api/v1/hooks/file`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) {
    const t = await r.text();
    throw new Error(t);
  }
  return r.json();
}

export async function hookBrowser(body: {
  target_url: string;
  capability_token?: string | null;
  automate?: boolean;
  timeout_sec?: number;
  steps?: Array<Record<string, unknown>>;
}) {
  const r = await fetch(`${API}/api/v1/hooks/browser`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error("browser hook failed");
  return r.json();
}

export async function hookExec(body: {
  argv: string[];
  capability_token?: string | null;
  prefer_container?: boolean;
}) {
  const r = await fetch(`${API}/api/v1/hooks/exec`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error("exec hook failed");
  return r.json();
}

export async function fetchNative() {
  const r = await fetch(`${API}/api/v1/hooks/native`);
  if (!r.ok) throw new Error("native failed");
  return r.json() as Promise<{
    c_library_loaded: boolean;
    library_path: string | null;
  }>;
}
