import { useCallback, useEffect, useState } from "react";
import { getModels, runExperiment } from "../api/tiltApi";

const STORAGE_KEY = "tiltdetector:lastResult";
const ENABLED_MODELS_KEY = "tiltdetector:enabledModels";

export function useExperiment() {
  const [result, setResult] = useState(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [modelsData, setModelsData] = useState(null);
  const [modelsError, setModelsError] = useState(null);
  const [enabledModels, setEnabledModels] = useState(() => {
    try {
      const raw = localStorage.getItem(ENABLED_MODELS_KEY);
      return raw ? new Set(JSON.parse(raw)) : new Set();
    } catch {
      return new Set();
    }
  });

  const refreshModels = useCallback(async () => {
    try {
      const data = await getModels();
      setModelsData(data);
      setModelsError(null);
    } catch (err) {
      setModelsError(err.message || "No se pudieron obtener los modelos");
    }
  }, []);

  const toggleModel = useCallback((modelId) => {
    setEnabledModels((prev) => {
      const updated = new Set(prev);
      if (updated.has(modelId)) {
        updated.delete(modelId);
      } else {
        updated.add(modelId);
      }
      localStorage.setItem(ENABLED_MODELS_KEY, JSON.stringify(Array.from(updated)));
      return updated;
    });
  }, []);

  useEffect(() => {
    refreshModels();
  }, [refreshModels]);

  const submit = useCallback(async ({ pedido, sesgo_medir, model_names, mitigation_ab = false }) => {
    setLoading(true);
    setError(null);
    try {
      const data = await runExperiment({ pedido, sesgo_medir, model_names, mitigation_ab });
      setResult(data);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
      return data;
    } catch (err) {
      setError(err.message || "Error inesperado al correr el experimento");
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const reset = useCallback(() => {
    setResult(null);
    setError(null);
    localStorage.removeItem(STORAGE_KEY);
  }, []);

  return {
    result,
    loading,
    error,
    modelsData,
    modelsError,
    enabledModels,
    toggleModel,
    refreshModels,
    submit,
    reset,
  };
}
