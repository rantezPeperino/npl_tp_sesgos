import { useCallback, useEffect, useState } from "react";
import { getLlmStatus, runExperiment } from "../api/tiltApi";

const STORAGE_KEY = "tiltdetector:lastResult";

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
  const [llmStatus, setLlmStatus] = useState(null);
  const [llmStatusError, setLlmStatusError] = useState(null);

  const refreshLlmStatus = useCallback(async () => {
    try {
      const status = await getLlmStatus();
      setLlmStatus(status);
      setLlmStatusError(null);
    } catch (err) {
      setLlmStatusError(err.message || "No se pudo obtener el estado de los LLMs");
    }
  }, []);

  useEffect(() => {
    refreshLlmStatus();
  }, [refreshLlmStatus]);

  const submit = useCallback(async ({ pedido, sesgo_medir, model_names }) => {
    setLoading(true);
    setError(null);
    try {
      const data = await runExperiment({ pedido, sesgo_medir, model_names });
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
    llmStatus,
    llmStatusError,
    refreshLlmStatus,
    submit,
    reset,
  };
}
