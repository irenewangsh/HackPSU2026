import { useEffect, useState } from "react";
import {
  fetchProfile,
  forgetNow,
  patchProfile,
  resetPrefs,
} from "../api";

export function ProfilePage() {
  const [p, setP] = useState({
    risk_aversion: 0.45,
    forgetting_lambda_per_hour: 0.015,
    last_forget_wallclock: 0,
  });

  useEffect(() => {
    fetchProfile().then(setP);
  }, []);

  return (
    <div className="mx-auto max-w-lg space-y-8">
      <div>
        <h1 className="font-serif text-4xl font-semibold text-forest-900">
          User profile
        </h1>
        <p className="mt-3 font-sans text-lg leading-relaxed text-forest-700/90">
          Risk aversion scales trust bias. Forgetting λ controls exponential decay of
          preference weights over time.
        </p>
      </div>
      <div className="glass-panel-soft space-y-6 p-7">
        <label className="block font-sans text-sm text-forest-700/85">
          risk_aversion (0–1)
          <input
            type="range"
            min={0}
            max={1}
            step={0.01}
            value={p.risk_aversion}
            onChange={async (e) => {
              const v = parseFloat(e.target.value);
              setP((x) => ({ ...x, risk_aversion: v }));
              await patchProfile({ risk_aversion: v });
            }}
            className="mt-2 w-full accent-sage-600"
          />
          <span className="font-mono text-sage-800">{p.risk_aversion.toFixed(2)}</span>
        </label>
        <label className="block font-sans text-sm text-forest-700/85">
          forgetting_lambda_per_hour
          <input
            type="range"
            min={0}
            max={0.2}
            step={0.001}
            value={p.forgetting_lambda_per_hour}
            onChange={async (e) => {
              const v = parseFloat(e.target.value);
              setP((x) => ({ ...x, forgetting_lambda_per_hour: v }));
              await patchProfile({ forgetting_lambda_per_hour: v });
            }}
            className="mt-2 w-full accent-violet-500"
          />
          <span className="font-mono text-violet-900">
            {p.forgetting_lambda_per_hour.toFixed(4)}
          </span>
        </label>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            className="rounded-xl border border-sage-300/80 bg-sage-50 px-4 py-2 font-sans text-sm font-medium text-sage-900 hover:bg-sage-100/90"
            onClick={async () => {
              await forgetNow();
              const np = await fetchProfile();
              setP(np);
            }}
          >
            Run forgetting pass now
          </button>
          <button
            type="button"
            className="rounded-xl border border-stone-200/90 bg-white/90 px-4 py-2 font-sans text-sm text-forest-800 hover:bg-stone-50"
            onClick={async () => {
              await resetPrefs(null);
            }}
          >
            Reset prefs
          </button>
        </div>
      </div>
    </div>
  );
}
