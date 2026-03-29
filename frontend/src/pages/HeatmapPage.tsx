import { useEffect, useState } from "react";
import { fetchHeatmap } from "../api";

const BUCKETS = ["low", "med", "high", "crit"];

export function HeatmapPage() {
  const [cells, setCells] = useState<
    {
      action_type: string;
      risk_bucket: number;
      count: number;
      avg_risk: number;
    }[]
  >([]);

  useEffect(() => {
    fetchHeatmap().then((h) => setCells(h.cells));
  }, []);

  const max = Math.max(1, ...cells.map((c) => c.count));

  return (
    <div className="mx-auto max-w-5xl space-y-8">
      <div>
        <h1 className="font-serif text-4xl font-semibold text-forest-900">
          Risk heatmap
        </h1>
        <p className="mt-3 font-sans text-lg text-forest-700/90">
          Density of mediated actions × risk bucket (from authority timeline).
        </p>
      </div>
      <div className="glass-panel overflow-x-auto p-7">
        <table className="w-full border-collapse text-left text-xs">
          <thead>
            <tr className="font-sans text-stone-500">
              <th className="p-2">action_type</th>
              {BUCKETS.map((b, i) => (
                <th key={b} className="p-2 text-center">
                  bucket {i} · {b}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {Array.from(new Set(cells.map((c) => c.action_type))).map((at) => (
              <tr key={at} className="border-t border-stone-200/60">
                <td className="p-2 font-mono text-sage-800">{at}</td>
                {[0, 1, 2, 3].map((b) => {
                  const cell = cells.find(
                    (c) => c.action_type === at && c.risk_bucket === b
                  );
                  const intensity = cell ? cell.count / max : 0;
                  return (
                    <td key={b} className="p-1">
                      <div
                        className="flex h-12 items-center justify-center rounded-xl border border-stone-200/70 font-mono text-forest-900"
                        style={{
                          background: `rgba(74, 124, 98, ${0.06 + intensity * 0.42})`,
                        }}
                        title={cell ? `avg ${cell.avg_risk.toFixed(3)}` : ""}
                      >
                        {cell?.count ?? ""}
                      </div>
                    </td>
                  );
                })}
              </tr>
            ))}
            {!cells.length && (
              <tr>
                <td colSpan={5} className="p-8 text-center font-sans text-stone-500">
                  Run mediations to populate the map.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
