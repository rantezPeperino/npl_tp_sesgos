import { useState } from "react";

export default function LLMStatusBadge({ status, error, onRefresh }) {
  const [open, setOpen] = useState(false);

  const countHealthy = () => {
    let count = 0;
    let total = 0;
    if (status?.local) {
      count += status.local.filter((m) => m.healthy).length;
      total += status.local.length;
    }
    if (status?.remote) {
      for (const models of Object.values(status.remote)) {
        count += models.filter((m) => m.healthy).length;
        total += models.length;
      }
    }
    return { count, total };
  };

  const { count: healthyCount, total: totalModels } = countHealthy();

  return (
    <div className="relative">
      <button
        type="button"
        aria-label="Estado de los modelos"
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
        Modelos ({healthyCount}/{totalModels || "?"})
      </button>

      {open && (
        <div className="absolute right-0 z-20 mt-2 w-96 rounded-lg border border-slate-200 bg-white p-4 shadow-lg">
          <div className="mb-2 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-slate-800">Estado de modelos</h3>
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

          {totalModels === 0 && !error && (
            <p className="text-xs text-slate-500">Sin información todavía…</p>
          )}

          {/* Modelos locales */}
          {status?.local && status.local.length > 0 && (
            <div className="mb-3">
              <h4 className="text-xs font-semibold text-slate-600 uppercase mb-1">Locales</h4>
              <ul className="space-y-1">
                {status.local.map((m) => (
                  <li key={m.id} className="rounded border border-slate-100 p-2">
                    <div className="flex items-center gap-2">
                      <span
                        className={`inline-block h-2.5 w-2.5 rounded-full ${
                          m.healthy ? "bg-emerald-500" : "bg-red-500"
                        }`}
                        aria-hidden
                      />
                      <span className="text-xs font-medium text-slate-800">{m.id}</span>
                      <span className={`ml-auto text-xs ${m.healthy ? "text-emerald-700" : "text-red-700"}`}>
                        {m.healthy ? "ok" : "error"}
                      </span>
                    </div>
                    {!m.healthy && m.detail && (
                      <p className="mt-1 break-words text-xs text-slate-500">{m.detail}</p>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Modelos remotos */}
          {status?.remote && Object.keys(status.remote).length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-slate-600 uppercase mb-1">Remotos</h4>
              {Object.entries(status.remote).map(([provider, models]) => (
                <div key={provider} className="mb-2 last:mb-0">
                  <p className="text-xs text-slate-500 capitalize font-medium mb-1">{provider}</p>
                  <ul className="space-y-1">
                    {models.map((m) => (
                      <li key={m.id} className="rounded border border-slate-100 p-2 bg-slate-50">
                        <div className="flex items-center gap-2">
                          <span
                            className={`inline-block h-2 w-2 rounded-full ${
                              m.healthy ? "bg-emerald-500" : "bg-red-500"
                            }`}
                            aria-hidden
                          />
                          <span className="text-xs font-medium text-slate-800">{m.id}</span>
                          <span className={`ml-auto text-xs ${m.healthy ? "text-emerald-700" : "text-red-700"}`}>
                            {m.healthy ? "ok" : "error"}
                          </span>
                        </div>
                        {!m.healthy && m.detail && (
                          <p className="mt-0.5 break-words text-xs text-slate-500">{m.detail}</p>
                        )}
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
