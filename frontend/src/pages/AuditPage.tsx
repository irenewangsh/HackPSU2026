import { useCallback, useEffect, useState } from "react";
import { fetchAudit } from "../api";

export function AuditPage() {
  const [items, setItems] = useState<
    Awaited<ReturnType<typeof fetchAudit>>["items"]
  >([]);

  const load = useCallback(() => {
    fetchAudit(80).then((r) => setItems(r.items));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div className="flex justify-between gap-4">
        <div>
          <h1 className="font-serif text-4xl font-semibold text-forest-900">
            Audit log
          </h1>
          <p className="mt-2 font-sans text-forest-700/90">
            Immutable mediation records.
          </p>
        </div>
        <button
          type="button"
          className="font-sans text-xs font-medium text-sage-700 underline decoration-sage-300/80 hover:text-sage-900"
          onClick={() => load()}
        >
          Refresh
        </button>
      </div>
      <div className="glass-panel max-h-[560px] overflow-auto">
        <table className="w-full text-left text-xs">
          <thead className="sticky top-0 bg-paper/95 font-sans text-stone-500 backdrop-blur-sm">
            <tr>
              <th className="p-3">time</th>
              <th className="p-3">action</th>
              <th className="p-3">decision</th>
              <th className="p-3">risk</th>
              <th className="p-3">summary</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-stone-200/60 font-mono text-forest-800">
            {items.map((row) => (
              <tr key={row.id}>
                <td className="p-3 text-stone-500">
                  {new Date(row.ts * 1000).toLocaleString()}
                </td>
                <td className="p-3">{row.action_type}</td>
                <td className="p-3 text-sage-800">{row.decision}</td>
                <td className="p-3">{row.composite_risk.toFixed(3)}</td>
                <td className="max-w-md truncate p-3 text-stone-600">{row.summary}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
