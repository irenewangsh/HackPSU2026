import { motion } from "framer-motion";
import { Activity, Cpu, Shield } from "lucide-react";
import { useEffect, useState } from "react";
import { TrustRing } from "../components/TrustRing";
import {
  fetchAuthorityTimeline,
  fetchHealth,
  fetchHeatmap,
  fetchNative,
} from "../api";

export function Dashboard() {
  const [health, setHealth] = useState<string[]>([]);
  const [native, setNative] = useState<{ c_library_loaded: boolean } | null>(
    null
  );
  const [lastEnv, setLastEnv] = useState<number | null>(null);
  const [cells, setCells] = useState(0);

  useEffect(() => {
    fetchHealth()
      .then((h) => setHealth(h.layers))
      .catch(() => setHealth([]));
    fetchNative().then(setNative).catch(() => setNative(null));
    fetchAuthorityTimeline(12).then((t) => {
      const v = t.items[0]?.envelope;
      setLastEnv(typeof v === "number" ? v : 0.45);
    });
    fetchHeatmap().then((h) => setCells(h.cells.length));
  }, []);

  return (
    <div className="space-y-10">
      <div className="max-w-2xl">
        <h1 className="font-serif text-4xl font-semibold tracking-tight text-forest-900 md:text-[2.75rem]">
          Mission control
        </h1>
        <p className="mt-4 font-sans text-lg leading-relaxed text-forest-700/90">
          SentinelOS is not “another agent”. It is a{" "}
          <span className="font-medium text-sage-700">supervisory OS layer</span>:
          C path policy, HMAC capability tokens, sandboxed hooks, decaying user
          memory, and reversible ops.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-panel-soft flex flex-col items-center justify-center p-10"
        >
          <TrustRing value={lastEnv ?? 0.42} />
          <p className="mt-5 max-w-[14rem] text-center font-sans text-sm text-forest-600/80">
            Progressive Trust Envelope — last authority event
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.05 }}
          className="glass-panel p-7"
        >
          <div className="mb-4 flex items-center gap-2 font-sans text-sm font-semibold text-forest-900">
            <Cpu className="h-4 w-4 text-sage-600" strokeWidth={1.75} />
            C systems layer
          </div>
          <ul className="list-inside list-disc space-y-2 font-sans text-sm leading-relaxed text-forest-700/90">
            <li>
              <code className="rounded bg-wash-mist/80 px-1 font-mono text-xs text-forest-900">
                sentinel_policy.c
              </code>{" "}
              — <code className="font-mono text-sage-700">realpath(3)</code>, sandbox
              prefix, FNV-1a digest
            </li>
            <li>
              <code className="rounded bg-wash-mist/80 px-1 font-mono text-xs text-forest-900">
                sentinel_fs.c
              </code>{" "}
              — <code className="font-mono text-sage-700">lstat(2)</code> symlink /
              mode bits
            </li>
            <li>
              <code className="rounded bg-wash-mist/80 px-1 font-mono text-xs text-forest-900">
                sentinel_exec.c
              </code>{" "}
              —{" "}
              <code className="font-mono text-sage-700">fork</code>/
              <code className="font-mono text-sage-700">pipe</code>/
              <code className="font-mono text-sage-700">poll</code>/
              <code className="font-mono text-sage-700">execve</code>,{" "}
              <code className="font-mono text-sage-700">setrlimit(RLIMIT_CPU)</code>
            </li>
          </ul>
          <div
            className={`mt-5 inline-flex rounded-full px-3 py-1.5 font-mono text-xs ${
              native?.c_library_loaded
                ? "border border-sage-300/80 bg-sage-100/90 text-sage-800"
                : "border border-amber-200/90 bg-amber-50/95 text-amber-900"
            }`}
          >
            {native?.c_library_loaded ? "libsentinel loaded" : "Python fallback"}
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="glass-panel p-7"
        >
          <div className="mb-4 flex items-center gap-2 font-sans text-sm font-semibold text-forest-900">
            <Activity className="h-4 w-4 text-violet-700/80" />
            Live signals
          </div>
          <p className="font-sans text-sm text-forest-700/90">
            Heatmap buckets active:{" "}
            <span className="font-mono font-semibold text-forest-900">{cells}</span>
          </p>
          <ul className="mt-4 space-y-2 font-sans text-xs text-forest-600/85">
            {health.slice(0, 6).map((l) => (
              <li key={l} className="flex items-center gap-2">
                <Shield className="h-3 w-3 text-sage-500" strokeWidth={1.75} />
                {l}
              </li>
            ))}
          </ul>
        </motion.div>
      </div>
    </div>
  );
}
