import { useState, useEffect } from "react";
import { fetchRandomExample } from "../api/tiltApi";

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

function ModelRow({ modelId, provider, enabled, healthy, detail, checked, loading, error, onToggleEnable, onToggleSelect }) {
  const statusBg = !enabled
    ? "bg-slate-100"
    : loading
    ? "bg-blue-50"
    : healthy
    ? "bg-green-50"
    : "bg-red-50";

  const statusText = !enabled
    ? "text-slate-500"
    : loading
    ? "text-blue-700"
    : healthy
    ? "text-green-700"
    : "text-red-700";

  const indicatorColor = !enabled
    ? "bg-slate-400"
    : loading
    ? "bg-blue-500"
    : healthy
    ? "bg-green-500"
    : "bg-red-500";

  const statusLabel = !enabled
    ? "deshabilitado"
    : loading
    ? "verificando..."
    : healthy
    ? "online"
    : "offline";

  return (
    <div className={`flex items-center gap-3 rounded-md border border-slate-200 px-3 py-2 transition ${statusBg}`}>
      {/* Toggle habilitar/deshabilitar */}
      <button
        type="button"
        onClick={onToggleEnable}
        disabled={loading}
        className={`flex-shrink-0 relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
          enabled ? "bg-blue-600" : "bg-slate-300"
        } ${loading ? "opacity-60 cursor-wait" : ""}`}
        title={enabled ? "Desactivar modelo" : "Activar modelo"}
      >
        <span
          className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
            enabled ? "translate-x-6" : "translate-x-1"
          }`}
        />
      </button>

      {/* Nombre del modelo + proveedor */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className={`text-sm font-medium ${statusText}`}>
            {modelId}
          </span>
          {provider && provider !== "ollama" && (
            <span className="text-xs px-2 py-0.5 rounded bg-slate-200 text-slate-600 capitalize">
              {provider}
            </span>
          )}
        </div>
        {error && enabled && (
          <p className="text-xs text-red-600 mt-0.5">{error}</p>
        )}
        {!error && !healthy && enabled && (
          <p className="text-xs text-red-600 mt-0.5">{detail}</p>
        )}
      </div>

      {/* Indicador de estado */}
      <div className="flex items-center gap-2 flex-shrink-0">
        {loading && (
          <svg className="h-3 w-3 animate-spin text-blue-500" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
          </svg>
        )}
        {!loading && (
          <span className={`inline-block h-2.5 w-2.5 rounded-full ${indicatorColor}`} />
        )}
        <span className={`text-xs font-medium ${statusText}`}>
          {statusLabel}
        </span>
      </div>

      {/* Checkbox para incluir en experimento */}
      {enabled && !loading && (
        <input
          type="checkbox"
          checked={checked}
          onChange={onToggleSelect}
          disabled={!healthy}
          className="flex-shrink-0 h-4 w-4 cursor-pointer disabled:cursor-not-allowed"
          title={healthy ? "Incluir en experimento" : "Modelo no disponible"}
        />
      )}
    </div>
  );
}

export default function ExperimentForm({ modelsData, enabledModels, toggleModel, refreshModels, loading, error, onSubmit }) {
  const [pedido, setPedido] = useState("");
  const [sesgo, setSesgo] = useState("genero");
  const [selectedForExperiment, setSelectedForExperiment] = useState(() => new Set());
  const [mitigationAb, setMitigationAb] = useState(false);
  const [validationError, setValidationError] = useState(null);
  const [modelErrors, setModelErrors] = useState({});
  const [modelLoading, setModelLoading] = useState({});
  const [retryTimeouts, setRetryTimeouts] = useState({});

  const buildModelsMap = () => {
    const map = {};
    if (modelsData?.local) {
      for (const m of modelsData.local) {
        map[m.id] = m;
      }
    }
    if (modelsData?.remote) {
      for (const [provider, models] of Object.entries(modelsData.remote)) {
        for (const m of models) {
          map[m.id] = { ...m, provider };
        }
      }
    }
    return map;
  };

  const modelsMap = buildModelsMap();

  const handleToggleModel = (modelId) => {
    const isEnabling = !enabledModels.has(modelId);

    if (isEnabling) {
      setModelErrors((prev) => {
        const next = { ...prev };
        delete next[modelId];
        return next;
      });
      setModelLoading((prev) => ({ ...prev, [modelId]: true }));

      if (retryTimeouts[modelId]) {
        clearTimeout(retryTimeouts[modelId]);
        setRetryTimeouts((prev) => {
          const next = { ...prev };
          delete next[modelId];
          return next;
        });
      }

      refreshModels().then(() => {
        setModelLoading((prev) => {
          const next = { ...prev };
          delete next[modelId];
          return next;
        });

        const modelInfo = modelsMap[modelId];
        if (modelInfo && !modelInfo.healthy) {
          const timeoutId = setTimeout(() => {
            toggleModel(modelId);
            setModelErrors((prev) => ({
              ...prev,
              [modelId]: modelInfo.detail
            }));
            setRetryTimeouts((prev) => {
              const next = { ...prev };
              delete next[modelId];
              return next;
            });
          }, 10000);

          setRetryTimeouts((prev) => ({
            ...prev,
            [modelId]: timeoutId
          }));
        }
      });
    } else {
      if (retryTimeouts[modelId]) {
        clearTimeout(retryTimeouts[modelId]);
        setRetryTimeouts((prev) => {
          const next = { ...prev };
          delete next[modelId];
          return next;
        });
      }
    }

    toggleModel(modelId);
    if (enabledModels.has(modelId)) {
      setSelectedForExperiment((prev) => {
        const next = new Set(prev);
        next.delete(modelId);
        return next;
      });
    }
  };

  const handleToggleSelect = (modelId) => {
    setSelectedForExperiment((prev) => {
      const next = new Set(prev);
      if (next.has(modelId)) {
        next.delete(modelId);
      } else {
        next.add(modelId);
      }
      return next;
    });
  };

  useEffect(() => {
    return () => {
      Object.values(retryTimeouts).forEach(timeout => clearTimeout(timeout));
    };
  }, [retryTimeouts]);

  const getHealthyEnabledModels = () => {
    const healthy = [];
    Object.values(modelsMap).forEach((model) => {
      if (model.healthy && enabledModels.has(model.id)) {
        healthy.push(model.id);
      }
    });
    return healthy;
  };

  const hasOnlineModels = getHealthyEnabledModels().length > 0;
  const isSubmitDisabled = loading || !hasOnlineModels;

  async function handleSubmit(e) {
    e.preventDefault();
    setValidationError(null);

    if (!hasOnlineModels) {
      setValidationError("Necesitás al menos un modelo online habilitado para detectar sesgo.");
      return;
    }

    if (!pedido.trim()) {
      setValidationError("Escribí un pedido (no puede estar vacío).");
      return;
    }
    if (!sesgo) {
      setValidationError("Seleccioná una dimensión de sesgo.");
      return;
    }
    if (selectedForExperiment.size === 0) {
      setValidationError("Seleccioná al menos un modelo.");
      return;
    }

    const finalModels = Array.from(selectedForExperiment).filter((modelId) => {
      const info = modelsMap[modelId];
      return info?.healthy && enabledModels.has(modelId);
    });

    if (finalModels.length === 0) {
      setValidationError("No hay modelos disponibles seleccionados.");
      return;
    }

    try {
      await onSubmit({
        pedido: pedido.trim(),
        sesgo_medir: sesgo,
        model_names: finalModels,
        mitigation_ab: mitigationAb,
      });
    } catch {
      // error se propaga vía hook
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div>
        <div className="mb-1 flex items-center justify-between">
          <label
            htmlFor="pedido"
            className="block text-sm font-medium text-slate-800"
          >
            Pedido (texto libre)
          </label>
          <button
            type="button"
            onClick={async () => {
              try {
                const ex = await fetchRandomExample(sesgo);
                setPedido(ex.pedido);
              } catch (err) {
                setValidationError(
                  err?.message || "No se pudo generar un ejemplo."
                );
              }
            }}
            className="rounded-md border border-slate-300 bg-white px-3 py-1 text-xs font-medium text-slate-700 shadow-sm hover:bg-slate-50"
          >
            Generar ejemplo
          </button>
        </div>
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
        <span className="mb-3 block text-sm font-medium text-slate-800">Modelos a evaluar</span>

        {/* Modelos locales */}
        {modelsData?.local && modelsData.local.length > 0 && (
          <div className="mb-4">
            <h3 className="text-xs font-semibold text-slate-700 mb-2 uppercase">Local</h3>
            <div className="space-y-2">
              {modelsData.local.map((m) => (
                <ModelRow
                  key={m.id}
                  modelId={m.id}
                  provider={m.provider}
                  enabled={enabledModels.has(m.id)}
                  healthy={m.healthy}
                  detail={m.detail}
                  checked={selectedForExperiment.has(m.id)}
                  loading={modelLoading[m.id] || false}
                  error={modelErrors[m.id] || null}
                  onToggleEnable={() => handleToggleModel(m.id)}
                  onToggleSelect={() => handleToggleSelect(m.id)}
                />
              ))}
            </div>
          </div>
        )}

        {/* Modelos remotos */}
        {modelsData?.remote && Object.keys(modelsData.remote).length > 0 && (
          <div className="mb-4">
            <h3 className="text-xs font-semibold text-slate-700 mb-2 uppercase">Remoto</h3>
            <div className="space-y-2">
              {Object.entries(modelsData.remote).flatMap(([provider, models]) =>
                models.map((m) => (
                  <ModelRow
                    key={m.id}
                    modelId={m.id}
                    provider={provider}
                    enabled={enabledModels.has(m.id)}
                    healthy={m.healthy}
                    detail={m.detail}
                    checked={selectedForExperiment.has(m.id)}
                    loading={modelLoading[m.id] || false}
                    error={modelErrors[m.id] || null}
                    onToggleEnable={() => handleToggleModel(m.id)}
                    onToggleSelect={() => handleToggleSelect(m.id)}
                  />
                ))
              )}
            </div>
          </div>
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
          disabled={isSubmitDisabled}
          className="inline-flex items-center gap-2 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-blue-400"
          title={!hasOnlineModels ? "Necesitás al menos un modelo online habilitado" : ""}
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
        {!hasOnlineModels && !loading && (
          <span className="text-xs text-slate-500">
            Habilitá al menos un modelo online para detectar sesgo.
          </span>
        )}
      </div>
    </form>
  );
}
