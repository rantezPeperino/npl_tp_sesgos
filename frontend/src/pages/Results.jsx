import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import GlobalSummary from "../components/GlobalSummary.jsx";
import ModelsRadarChart from "../components/ModelsRadarChart.jsx";
import ResultsTabs from "../components/ResultsTabs.jsx";

export default function Results({ exp }) {
  const navigate = useNavigate();

  useEffect(() => {
    if (!exp.result) navigate("/");
  }, [exp.result, navigate]);

  if (!exp.result) return null;

  const { result } = exp;

  function handleNew() {
    exp.reset();
    navigate("/");
  }

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <button
            type="button"
            onClick={handleNew}
            className="mb-2 inline-flex items-center gap-1 text-sm text-blue-700 hover:underline"
          >
            ← Nuevo experimento
          </button>
          <h2 className="text-2xl font-bold text-slate-900">Resultados</h2>
          <p className="text-xs text-slate-500">
            id: <span className="font-mono">{result.experiment_id}</span>
          </p>
          {result.metadata?.source_pedido && (
            <p className="mt-2 max-w-3xl text-sm text-slate-600">
              <span className="font-medium">Pedido:</span>{" "}
              {result.metadata.source_pedido}
            </p>
          )}
        </div>
      </header>

      <GlobalSummary summary={result.global_summary} />

      <ModelsRadarChart modelResults={result.model_results} />

      <ResultsTabs result={result} />
    </div>
  );
}
