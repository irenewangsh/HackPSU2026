import { motion } from "framer-motion";
import { Sparkles } from "lucide-react";
import { useMemo, useState } from "react";
import type {
  ActionType,
  AgentActionRequest,
  MediationResult,
  TaskType,
} from "../api";
import { mediate, sendFeedback } from "../api";

const ACTION_OPTIONS: { value: ActionType; label: string }[] = [
  { value: "read_file", label: "Read file" },
  { value: "classify_file", label: "Classify file" },
  { value: "move_file", label: "Move file" },
  { value: "rename_file", label: "Rename file" },
  { value: "upload_file", label: "Upload file" },
  { value: "run_shell", label: "Run shell" },
  { value: "open_website", label: "Open website" },
  { value: "login", label: "Login" },
  { value: "paste_content", label: "Paste content" },
  { value: "submit_form", label: "Submit form" },
  { value: "make_payment", label: "Make payment" },
  { value: "delete_file", label: "Delete file" },
  { value: "share_data", label: "Share data" },
];

const TASK_OPTIONS: { value: TaskType; label: string }[] = [
  { value: "general", label: "General" },
  { value: "coursework_organizer", label: "Coursework organizer" },
  { value: "financial_assistant", label: "Financial assistant" },
];

export function MediationPage() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<MediationResult | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [form, setForm] = useState<AgentActionRequest>({
    action_type: "move_file",
    task_type: "coursework_organizer",
    target_path: "/Users/demo/Downloads/CMPSC311_notes.pdf",
    mime_type: "application/pdf",
    overwrite: false,
    session_id: "demo-session",
    environment_hint: "home",
    payload_preview: "",
    target_url: "",
    form_field_names: [],
  });

  const category = useMemo(() => {
    if (!result) return "general";
    return result.sensitivity.categories[0] ?? "general";
  }, [result]);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setErr(null);
    try {
      const body: AgentActionRequest = {
        ...form,
        payload_preview: form.payload_preview || undefined,
        target_url: form.target_url || undefined,
        target_path: form.target_path || undefined,
      };
      setResult(await mediate(body));
    } catch (e: unknown) {
      setErr(String(e));
    } finally {
      setLoading(false);
    }
  };

  const field =
    "w-full rounded-xl border border-stone-200/90 bg-white/95 px-3 py-2.5 font-mono text-sm text-forest-900 shadow-sm outline-none ring-sage-400/0 transition placeholder:text-stone-400 focus:ring-2 focus:ring-sage-400/35";

  return (
    <div className="mx-auto max-w-4xl space-y-10">
      <div>
        <h1 className="font-serif text-4xl font-semibold text-forest-900">
          Policy mediation
        </h1>
        <p className="mt-3 font-sans text-lg leading-relaxed text-forest-700/90">
          Structured intents only — outputs capability token + policy digest + C
          native status.
        </p>
      </div>

      <motion.form
        onSubmit={onSubmit}
        className="glass-panel grid gap-4 p-7 md:grid-cols-2"
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <label className="space-y-2 font-sans text-sm md:col-span-2">
          <span className="text-forest-700/85">Task type</span>
          <select
            className={field}
            value={form.task_type}
            onChange={(e) =>
              setForm((f) => ({ ...f, task_type: e.target.value as TaskType }))
            }
          >
            {TASK_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </label>
        <label className="space-y-2 font-sans text-sm md:col-span-2">
          <span className="text-forest-700/85">Action</span>
          <select
            className={field}
            value={form.action_type}
            onChange={(e) =>
              setForm((f) => ({ ...f, action_type: e.target.value as ActionType }))
            }
          >
            {ACTION_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </label>
        <label className="space-y-2 font-sans text-sm md:col-span-2">
          <span className="text-forest-700/85">Target path</span>
          <input
            className={field}
            value={form.target_path || ""}
            onChange={(e) => setForm((f) => ({ ...f, target_path: e.target.value }))}
          />
        </label>
        <label className="space-y-2 font-sans text-sm md:col-span-2">
          <span className="text-forest-700/85">URL</span>
          <input
            className={field}
            value={form.target_url || ""}
            onChange={(e) => setForm((f) => ({ ...f, target_url: e.target.value }))}
          />
        </label>
        <label className="space-y-2 font-sans text-sm md:col-span-2">
          <span className="text-forest-700/85">Payload preview</span>
          <textarea
            rows={3}
            className={`${field} text-xs`}
            value={form.payload_preview || ""}
            onChange={(e) =>
              setForm((f) => ({ ...f, payload_preview: e.target.value }))
            }
          />
        </label>
        <div className="md:col-span-2">
          <button
            type="submit"
            disabled={loading}
            className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-sage-600 to-forest-800 px-6 py-3 font-sans text-sm font-semibold text-paper shadow-lg shadow-sage-900/15 disabled:opacity-50"
          >
            <Sparkles className="h-4 w-4" strokeWidth={1.75} />
            {loading ? "…" : "Run mediation"}
          </button>
          {err && (
            <p className="mt-3 font-mono text-xs text-rose-700">{err}</p>
          )}
        </div>
      </motion.form>

      {result && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-panel space-y-5 p-7"
        >
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              className="rounded-lg border border-sage-300/90 bg-sage-50 px-3 py-1.5 font-sans text-xs font-medium text-sage-900"
              onClick={() =>
                sendFeedback({
                  request_id: result.request_id,
                  outcome: "allow",
                  task_type: (form.task_type || "general") as TaskType,
                  action_type: form.action_type,
                  sensitivity: result.sensitivity.level as
                    | "low"
                    | "medium"
                    | "high"
                    | "critical",
                  scenario_category: category,
                })
              }
            >
              User allowed
            </button>
            <button
              type="button"
              className="rounded-lg border border-amber-300/90 bg-amber-50 px-3 py-1.5 font-sans text-xs font-medium text-amber-900"
              onClick={() =>
                sendFeedback({
                  request_id: result.request_id,
                  outcome: "ask",
                  task_type: (form.task_type || "general") as TaskType,
                  action_type: form.action_type,
                  sensitivity: result.sensitivity.level as
                    | "low"
                    | "medium"
                    | "high"
                    | "critical",
                  scenario_category: category,
                })
              }
            >
              User wanted review
            </button>
            <button
              type="button"
              className="rounded-lg border border-rose-200/90 bg-rose-50 px-3 py-1.5 font-sans text-xs font-medium text-rose-900"
              onClick={() =>
                sendFeedback({
                  request_id: result.request_id,
                  outcome: "deny",
                  task_type: (form.task_type || "general") as TaskType,
                  action_type: form.action_type,
                  sensitivity: result.sensitivity.level as
                    | "low"
                    | "medium"
                    | "high"
                    | "critical",
                  scenario_category: category,
                })
              }
            >
              User denied
            </button>
          </div>
          <div className="grid gap-3 md:grid-cols-4">
            <Mini title="Risk score" value={String(result.risk.risk_score)} />
            <Mini title="Sensitivity" value={result.sensitivity.level} />
            <Mini title="Domain trust" value={result.sensitivity.domain_trust} />
            <Mini title="Decision" value={result.decision.decision} />
          </div>
          <p className="font-sans text-sm leading-relaxed text-forest-800">
            {result.decision.user_message}
          </p>
          <section className="rounded-xl border border-stone-200/70 bg-white/70 p-4">
            <h3 className="font-sans text-sm font-semibold text-forest-900">
              Permissions
            </h3>
            <pre className="mt-2 overflow-x-auto font-mono text-[11px] text-forest-800">
              {JSON.stringify(result.decision.permissions, null, 2)}
            </pre>
          </section>
          <section className="rounded-xl border border-stone-200/70 bg-white/70 p-4">
            <h3 className="font-sans text-sm font-semibold text-forest-900">
              Safety transforms
            </h3>
            <p className="mt-2 font-mono text-xs text-forest-800">
              {result.decision.transforms.join(", ")}
            </p>
          </section>
          <section className="rounded-xl border border-stone-200/70 bg-white/70 p-4">
            <h3 className="font-sans text-sm font-semibold text-forest-900">
              Sensitivity analysis
            </h3>
            <pre className="mt-2 overflow-x-auto font-mono text-[11px] text-forest-800">
              {JSON.stringify(
                {
                  categories: result.sensitivity.categories,
                  signals: result.sensitivity.signals,
                },
                null,
                2
              )}
            </pre>
          </section>
          <section className="rounded-xl border border-stone-200/70 bg-white/70 p-4">
            <h3 className="font-sans text-sm font-semibold text-forest-900">
              Risk rationale
            </h3>
            <pre className="mt-2 overflow-x-auto font-mono text-[11px] text-forest-800">
              {JSON.stringify(result.risk.reasons, null, 2)}
            </pre>
          </section>
          <section className="rounded-xl border border-stone-200/70 bg-white/70 p-4">
            <h3 className="font-sans text-sm font-semibold text-forest-900">
              Masked preview
            </h3>
            <p className="mt-2 whitespace-pre-wrap font-mono text-xs text-forest-800">
              {result.masked_preview || "(none)"}
            </p>
          </section>
          <section className="rounded-xl border border-stone-200/70 bg-white/70 p-4">
            <h3 className="font-sans text-sm font-semibold text-forest-900">
              Preference memory
            </h3>
            <pre className="mt-2 overflow-x-auto font-mono text-[11px] text-forest-800">
              {JSON.stringify(result.preference_memory || {}, null, 2)}
            </pre>
          </section>
          <div className="grid gap-3 md:grid-cols-2">
            <div className="rounded-xl border border-stone-200/80 bg-paper-2/90 p-4 font-mono text-xs text-forest-800">
              <p className="text-stone-500">policy_digest</p>
              <p className="mt-1 break-all text-sage-700">{result.policy_digest}</p>
            </div>
            <div className="rounded-xl border border-stone-200/80 bg-paper-2/90 p-4 font-mono text-xs text-forest-800">
              <p className="text-stone-500">capability_scopes</p>
              <p className="mt-1 text-forest-700">
                {(result.capability_scopes || []).join(", ")}
              </p>
            </div>
          </div>
          <div className="rounded-xl border border-stone-200/70 bg-white/70 p-4 font-mono text-[11px] text-stone-600">
            <p className="text-stone-500">capability_token</p>
            <p className="mt-2 break-all text-forest-800">
              {result.capability_token || "—"}
            </p>
          </div>
        </motion.div>
      )}
    </div>
  );
}

function Mini({ title, value }: { title: string; value: string }) {
  return (
    <div className="rounded-xl border border-stone-200/80 bg-paper-2/90 p-3">
      <p className="font-sans text-[11px] uppercase tracking-wide text-stone-500">
        {title}
      </p>
      <p className="mt-1 font-mono text-sm text-forest-900">{value}</p>
    </div>
  );
}
