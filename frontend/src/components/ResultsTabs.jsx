import { useEffect, useState } from "react";
import ModelCard from "./ModelCard.jsx";

export default function ResultsTabs({ result }) {
  const modelResults = result?.model_results || [];
  const [active, setActive] = useState(modelResults[0]?.model_name || null);

  useEffect(() => {
    if (!active && modelResults[0]) setActive(modelResults[0].model_name);
  }, [modelResults, active]);

  if (modelResults.length === 0) {
    return (
      <p className="rounded-md border border-slate-200 bg-white p-4 text-sm text-slate-600">
        Ningún modelo devolvió resultados.
      </p>
    );
  }

  const activeModel = modelResults.find((m) => m.model_name === active) || modelResults[0];

  return (
    <section className="space-y-4">
      <nav className="flex flex-wrap gap-2 border-b border-slate-200">
        {modelResults.map((m) => (
          <button
            key={m.model_name}
            type="button"
            onClick={() => setActive(m.model_name)}
            className={`-mb-px border-b-2 px-3 py-2 text-sm font-medium ${
              active === m.model_name
                ? "border-blue-600 text-blue-700"
                : "border-transparent text-slate-500 hover:text-slate-800"
            }`}
          >
            {m.model_name}
          </button>
        ))}
      </nav>

      <ModelCard
        modelResult={activeModel}
        cases={result.cases}
        biasDimension={result.metadata?.bias_dimension}
      />
    </section>
  );
}
