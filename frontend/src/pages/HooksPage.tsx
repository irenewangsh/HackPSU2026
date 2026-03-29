import { useState } from "react";
import { hookBrowser, hookExec, hookFile } from "../api";

const inp =
  "mt-1 w-full rounded-xl border border-stone-200/90 bg-white/95 px-3 py-2.5 font-mono text-sm text-forest-900 shadow-sm outline-none focus:ring-2 focus:ring-sage-400/35";

export function HooksPage() {
  const [file, setFile] = useState({
    action_type: "read_file" as
      | "read_file"
      | "classify_file"
      | "move_file"
      | "rename_file"
      | "delete_file",
    source_path: "demo/a.txt",
    dest_path: "demo/b.txt",
    dry_run: true,
  });
  const [url, setUrl] = useState("https://example.com");
  const [argv, setArgv] = useState("uname -a");
  const [capToken, setCapToken] = useState("");
  const [out, setOut] = useState<string>("");

  return (
    <div className="mx-auto max-w-4xl space-y-10">
      <div>
        <h1 className="font-serif text-4xl font-semibold text-forest-900">OS hooks</h1>
        <p className="mt-3 font-sans text-lg leading-relaxed text-forest-700/90">
          File paths are canonicalized in C and must stay under{" "}
          <code className="rounded-md bg-wash-leaf/90 px-1.5 py-0.5 font-mono text-sm text-sage-800">
            sandbox_workspace/
          </code>
          . Exec uses the native fork/pipe layer when available.
        </p>
      </div>

      <section className="glass-panel space-y-4 p-7">
        <h2 className="font-serif text-xl font-semibold text-forest-900">File hook</h2>
        <label className="font-sans text-xs text-forest-700/85">
          capability_token (required when dry_run=false)
          <input
            className={inp}
            value={capToken}
            onChange={(e) => setCapToken(e.target.value)}
          />
        </label>
        <div className="grid gap-3 md:grid-cols-2">
          <label className="font-sans text-xs text-forest-700/85">
            action
            <select
              className={inp}
              value={file.action_type}
              onChange={(e) =>
                setFile((f) => ({
                  ...f,
                  action_type: e.target.value as typeof file.action_type,
                }))
              }
            >
              <option value="read_file">read_file</option>
              <option value="classify_file">classify_file</option>
              <option value="move_file">move_file</option>
              <option value="rename_file">rename_file</option>
              <option value="delete_file">delete_file</option>
            </select>
          </label>
          <label className="font-sans text-xs text-forest-700/85">
            dry_run
            <select
              className={inp}
              value={file.dry_run ? "yes" : "no"}
              onChange={(e) =>
                setFile((f) => ({ ...f, dry_run: e.target.value === "yes" }))
              }
            >
              <option value="yes">true</option>
              <option value="no">false</option>
            </select>
          </label>
          <label className="font-sans text-xs text-forest-700/85 md:col-span-2">
            source_path (relative to sandbox)
            <input
              className={inp}
              value={file.source_path}
              onChange={(e) => setFile((f) => ({ ...f, source_path: e.target.value }))}
            />
          </label>
          <label className="font-sans text-xs text-forest-700/85 md:col-span-2">
            dest_path (move only)
            <input
              className={inp}
              value={file.dest_path}
              onChange={(e) => setFile((f) => ({ ...f, dest_path: e.target.value }))}
            />
          </label>
        </div>
        <button
          type="button"
          className="rounded-xl border border-sage-300/80 bg-sage-50 px-4 py-2.5 font-sans text-sm font-medium text-sage-900 shadow-sm hover:bg-sage-100/90"
          onClick={async () => {
            const r = await hookFile({
              ...file,
              capability_token: capToken || undefined,
              mime_type: "text/plain",
            });
            setOut(JSON.stringify(r, null, 2));
          }}
        >
          Run file hook
        </button>
      </section>

      <section className="glass-panel space-y-4 p-7">
        <h2 className="font-serif text-xl font-semibold text-forest-900">
          Browser hook
        </h2>
        <input
          className="w-full rounded-xl border border-stone-200/90 bg-white/95 px-3 py-2.5 font-mono text-sm text-forest-900 shadow-sm outline-none focus:ring-2 focus:ring-sage-400/35"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
        />
        <button
          type="button"
          className="rounded-xl border border-violet-200/90 bg-violet-50/95 px-4 py-2.5 font-sans text-sm font-medium text-violet-900 shadow-sm hover:bg-violet-100/90"
          onClick={async () =>
            setOut(
              JSON.stringify(
                await hookBrowser({
                  target_url: url,
                  capability_token: capToken || undefined,
                  automate: false,
                }),
                null,
                2
              )
            )
          }
        >
          Mediate URL
        </button>
      </section>

      <section className="glass-panel space-y-4 p-7">
        <h2 className="font-serif text-xl font-semibold text-forest-900">Exec hook</h2>
        <input
          className="w-full rounded-xl border border-stone-200/90 bg-white/95 px-3 py-2.5 font-mono text-sm text-forest-900 shadow-sm outline-none focus:ring-2 focus:ring-sage-400/35"
          value={argv}
          onChange={(e) => setArgv(e.target.value)}
          placeholder="argv as space-separated"
        />
        <button
          type="button"
          className="rounded-xl border border-amber-200/90 bg-amber-50/95 px-4 py-2.5 font-sans text-sm font-medium text-amber-950 shadow-sm hover:bg-amber-100/90"
          onClick={async () =>
            setOut(
              JSON.stringify(
                await hookExec({
                  argv: argv.trim().split(/\s+/),
                  capability_token: capToken || undefined,
                  prefer_container: true,
                }),
                null,
                2
              )
            )
          }
        >
          Run sandboxed exec
        </button>
      </section>

      <pre className="max-h-[420px] overflow-auto rounded-2xl border border-stone-200/80 bg-white/90 p-5 font-mono text-xs leading-relaxed text-forest-800 shadow-inner">
        {out || "Output appears here."}
      </pre>
    </div>
  );
}
