import { useEffect, useState } from "react";
import { fetchAuthorityTimeline } from "../api";

export function TimelinePage() {
  const [items, setItems] = useState<
    Awaited<ReturnType<typeof fetchAuthorityTimeline>>["items"]
  >([]);

  useEffect(() => {
    fetchAuthorityTimeline(80).then((r) => setItems(r.items));
  }, []);

  return (
    <div className="mx-auto max-w-3xl space-y-8">
      <div>
        <h1 className="font-serif text-4xl font-semibold text-forest-900">
          Authority timeline
        </h1>
        <p className="mt-3 font-sans text-lg leading-relaxed text-forest-700/90">
          Each mediation emits an envelope snapshot — your “who had authority,
          when” audit story.
        </p>
      </div>
      <div className="relative space-y-0 pl-8">
        <div className="absolute bottom-0 left-[11px] top-0 w-px bg-gradient-to-b from-sage-400/60 to-wash-peach/50" />
        {items.map((e) => (
          <div key={e.id} className="relative pb-8">
            <div className="absolute left-0 top-1.5 h-2.5 w-2.5 rounded-full border-2 border-sage-500 bg-paper shadow-md shadow-sage-300/50" />
            <div className="glass-panel ml-4 p-5">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span className="font-mono text-xs text-stone-500">
                  {new Date(e.ts * 1000).toLocaleString()}
                </span>
                <span className="rounded-full border border-sage-200/90 bg-sage-50 px-2 py-0.5 font-mono text-[10px] font-medium text-sage-800">
                  env {e.envelope.toFixed(2)}
                </span>
              </div>
              <p className="mt-2 font-mono text-sm text-forest-900">{e.action_type}</p>
              <p className="font-sans text-xs text-violet-800/90">{e.decision}</p>
              <p className="mt-2 font-sans text-xs text-forest-600/85">{e.summary}</p>
            </div>
          </div>
        ))}
        {!items.length && (
          <p className="font-sans text-sm text-stone-500">No authority events yet.</p>
        )}
      </div>
    </div>
  );
}
