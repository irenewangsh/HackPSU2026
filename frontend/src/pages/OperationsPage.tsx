import { useCallback, useEffect, useState } from "react";
import { fetchOperations, rollbackOp } from "../api";

export function OperationsPage() {
  const [items, setItems] = useState<
    Awaited<ReturnType<typeof fetchOperations>>["items"]
  >([]);
  const [msg, setMsg] = useState("");

  const load = useCallback(() => {
    fetchOperations(60).then((r) => setItems(r.items));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="font-serif text-4xl font-semibold text-forest-900">
            Reversible operations
          </h1>
          <p className="mt-2 font-sans text-forest-700/90">
            File hooks record inverse moves / write restores. Roll back to undo side
            effects inside the sandbox.
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
      {msg && <p className="font-mono text-xs text-sage-800">{msg}</p>}
      <div className="glass-panel overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead className="font-sans text-stone-500">
            <tr>
              <th className="p-3">id</th>
              <th className="p-3">kind</th>
              <th className="p-3">status</th>
              <th className="p-3">detail</th>
              <th className="p-3" />
            </tr>
          </thead>
          <tbody className="divide-y divide-stone-200/60 font-mono text-forest-800">
            {items.map((o) => (
              <tr key={o.id}>
                <td className="p-3">{o.id}</td>
                <td className="p-3 text-sage-800">{o.kind}</td>
                <td className="p-3">{o.status}</td>
                <td className="max-w-xs truncate p-3 text-stone-600">
                  {JSON.stringify(o.detail)}
                </td>
                <td className="p-3">
                  {o.status === "committed" && (
                    <button
                      type="button"
                      className="rounded-lg border border-rose-200/90 bg-rose-50 px-2 py-1 font-sans text-rose-900 hover:bg-rose-100/90"
                      onClick={async () => {
                        try {
                          await rollbackOp(o.id);
                          setMsg(`Rolled back #${o.id}`);
                          load();
                        } catch (e) {
                          setMsg(String(e));
                        }
                      }}
                    >
                      Rollback
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
