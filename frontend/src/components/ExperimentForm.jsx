import { useEffect, useMemo, useState } from "react";

const SESGO_OPTIONS = [
  "genero",
  "edad",
  "origen",
  "etnia",
  "religion",
  "discapacidad",
  "orientacion_sexual",
  "nivel_socioeconomico",
];

const ALL_PROVIDERS = ["ollama", "openai", "gemini", "anthropic"];

export default function ExperimentForm({ llmStatus, loading, error, onSubmit }) {
  const [pedido, setPedido] = useState("");
  const [sesgo, setSesgo] = useState("genero");
  const [selectedModels, setSelectedModels] = useState(() => new Set());
  const [mitigationAb, setMitigationAb] = useState(false);
  const [validationError, setValidationError] = useState(null);

  const providerHealth = useMemo(() => {
    const map = {};
    for (const c of llmStatus?.checks || []) {
      map[c.provider] = c;
    }
    return map;
  }, [llmStatus]);

  useEffect(() => {
    if (!llmStatus) return;
    const healthy = (llmStatus.checks || [])
      .filter((c) => c.healthy)
      .map((c) => c.provider);
    if (selectedModels.size === 0 && healthy.length > 0) {
      setSelectedModels(new Set(healthy));
    }
  }, [llmStatus]);

  function toggleModel(name) {
    setSelectedModels((prev) => {
      const next = new Set(prev);
      if (next.has(name)) next.delete(name);
      else next.add(name);
      return next;
    });
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setValidationError(null);

    if (!pedido.trim()) {
      setValidationError("Escribí un pedido (no puede estar vacío).");
      return;
    }
    if (!sesgo) {
      setValidationError("Seleccioná una dimensión de sesgo.");
      return;
    }
    if (selectedModels.size === 0) {
      setValidationError("Seleccioná al menos un modelo.");
      return;
    }

    try {
      await onSubmit({
        pedido: pedido.trim(),
        sesgo_medir: sesgo,
        model_names: Array.from(selectedModels),
        mitigation_ab: mitigationAb,
      });
    } catch {
      // el error se propaga vía hook.error
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div>
        <label
          htmlFor="pedido"
          className="mb-1 block text-sm font-medium text-slate-800"
        >
          Pedido (texto libre)
        </label>
        <textarea
          id="pedido"
          value={pedido}
          onChange={(e) => setPedido(e.target.value)}
          rows={6}
          placeholder="Ej: Evaluá a un candidato de 35 años con 8 años de experiencia. ¿Lo contratarías como gerente de operaciones?"
          className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
        />
        <p className="mt-1 text-xs text-slate-500">
          Describí el caso a evaluar. El sistema construirá automáticamente los 3
          casos de comparación (base, contrafactual, testigo).
        </p>
      </div>

      <div>
        <label
          htmlFor="sesgo"
          className="mb-1 block text-sm font-medium text-slate-800"
        >
          Sesgo a medir
        </label>
        <select
          id="sesgo"
          value={sesgo}
          onChange={(e) => setSesgo(e.target.value)}
          className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
        >
          {SESGO_OPTIONS.map((opt) => (
            <option key={opt} value={opt}>
              {opt}
            </option>
          ))}
        </select>
      </div>

      <div>
        <span className="mb-2 block text-sm font-medium text-slate-800">Modelos a evaluar</span>
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
          {ALL_PROVIDERS.map((p) => {
            const health = providerHealth[p];
            const healthy = !!health?.healthy;
            const detail = health?.detail || "Estado desconocido";
            const checked = selectedModels.has(p);
            return (
              <label
                key={p}
                title={!healthy ? detail : "healthy"}
                className={`flex cursor-pointer items-center gap-2 rounded-md border px-3 py-2 text-sm shadow-sm transition ${
                  !healthy
                    ? "cursor-not-allowed border-slate-200 bg-slate-50 text-slate-400"
                    : checked
                    ? "border-blue-500 bg-blue-50 text-blue-800"
                    : "border-slate-300 bg-white text-slate-800 hover:bg-slate-50"
                }`}
              >
                <input
                  type="checkbox"
                  className="h-4 w-4"
                  disabled={!healthy}
                  checked={checked}
                  onChange={() => toggleModel(p)}
                  aria-label={`Modelo ${p}`}
                />
                <span className="capitalize">{p}</span>
                <span
                  aria-hidden
                  className={`ml-auto inline-block h-2 w-2 rounded-full ${
                    healthy ? "bg-emerald-500" : "bg-red-500"
                  }`}
                />
              </label>
            );
          })}
        </div>
        {llmStatus?.enabled_providers && (
          <p className="mt-1 text-xs text-slate-500">
            Habilitados en backend: {llmStatus.enabled_providers.join(", ") || "ninguno"}
          </p>
        )}
      </div>

      <div>
        <label className="flex cursor-pointer items-start gap-2 rounded-md border border-slate-300 bg-white px-3 py-2 text-sm shadow-sm hover:bg-slate-50">
          <input
            type="checkbox"
            className="mt-0.5 h-4 w-4"
            checked={mitigationAb}
            onChange={(e) => setMitigationAb(e.target.checked)}
            aria-label="Comparar con mitigación (A/B)"
          />
          <span>
            <span className="font-medium text-slate-800">Comparar con mitigación (A/B)</span>
            <span className="block text-xs text-slate-500">
              Corre cada caso dos veces: control vs. con system prompt de fairness. Duplica el costo en tokens.
            </span>
          </span>
        </label>
      </div>

      {(validationError || error) && (
        <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {validationError || error}
        </div>
      )}

      <div className="flex items-center gap-3">
        <button
          type="submit"
          disabled={loading}
          className="inline-flex items-center gap-2 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-blue-400"
        >
          {loading ? (
            <>
              <svg
                className="h-4 w-4 animate-spin"
                viewBox="0 0 24 24"
                fill="none"
                aria-hidden
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
                />
              </svg>
              Evaluando casos en los modelos...
            </>
          ) : (
            "Detectar sesgo"
          )}
        </button>
        {loading && (
          <span className="text-xs text-slate-500">
            Esto puede tardar 10–30 segundos según los modelos seleccionados.
          </span>
        )}
      </div>
    </form>
  );
}
