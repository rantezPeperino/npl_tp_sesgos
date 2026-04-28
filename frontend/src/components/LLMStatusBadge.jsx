import { useState } from "react";

export default function LLMStatusBadge({ status, error, onRefresh }) {
  const [open, setOpen] = useState(false);
  const checks = status?.checks || [];
  const healthyCount = checks.filter((c) => c.healthy).length;

  return (
    <div className="relative">
      <button
        type="button"
        aria-label="Estado de los LLMs"
        onClick={() => setOpen((v) => !v)}
        className="inline-flex items-center gap-2 rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 shadow-sm hover:bg-slate-50"
      >
        <span className="relative flex h-2.5 w-2.5">
          <span
            className={`relative inline-flex h-2.5 w-2.5 rounded-full ${
              healthyCount > 0 ? "bg-emerald-500" : "bg-red-500"
            }`}
          />
        </span>
        Estado LLMs ({healthyCount}/{checks.length || "?"})
      </button>

      {open && (
        <div className="absolute right-0 z-20 mt-2 w-80 rounded-lg border border-slate-200 bg-white p-4 shadow-lg">
          <div className="mb-2 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-slate-800">Proveedores LLM</h3>
            <button
              type="button"
              onClick={() => {
                onRefresh?.();
              }}
              className="text-xs text-blue-600 hover:underline"
            >
              Refrescar
            </button>
          </div>

          {error && (
            <p className="mb-2 rounded bg-red-50 px-2 py-1 text-xs text-red-700">{error}</p>
          )}

          {checks.length === 0 && !error && (
            <p className="text-xs text-slate-500">Sin información todavía…</p>
          )}

          <ul className="space-y-2">
            {checks.map((c) => (
              <li key={c.provider} className="rounded border border-slate-100 p-2">
                <div className="flex items-center gap-2">
                  <span
                    className={`inline-block h-2.5 w-2.5 rounded-full ${
                      c.healthy ? "bg-emerald-500" : "bg-red-500"
                    }`}
                    aria-hidden
                  />
                  <span className="text-sm font-medium capitalize text-slate-800">
                    {c.provider}
                  </span>
                  <span
                    className={`ml-auto text-xs ${
                      c.healthy ? "text-emerald-700" : "text-red-700"
                    }`}
                  >
                    {c.healthy ? "healthy" : "unhealthy"}
                  </span>
                </div>
                {!c.healthy && c.detail && (
                  <p className="mt-1 break-words text-xs text-slate-500">{c.detail}</p>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
