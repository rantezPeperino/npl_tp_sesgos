import { useState } from "react";
import CaseDetailDrawer from "./CaseDetailDrawer.jsx";
import CasesRadarChart from "./CasesRadarChart.jsx";

const INTENSITY_CLASSES = {
  none: "bg-slate-100 text-slate-700 border-slate-200",
  low: "bg-yellow-100 text-yellow-800 border-yellow-200",
  medium: "bg-orange-100 text-orange-800 border-orange-200",
  high: "bg-red-100 text-red-800 border-red-200",
};

const INTENSITY_TEXT = {
  none: "No se detecta sesgo relevante.",
  low: "Se detecta una leve diferencia.",
  medium: "Posible sesgo moderado detectado.",
  high: "Sesgo fuerte detectado.",
};

const ROW_DEFS = [
  { type: "base", label: "Caso base" },
  { type: "counterfactual", label: "Contrafactual" },
  { type: "negative", label: "Testigo" },
];

function findCase(cases, type) {
  return cases?.find((c) => c.case_type === type) || null;
}

function findOutput(outputs, caseId) {
  return outputs?.find((o) => o.case_id === caseId) || null;
}

export default function ModelCard({ modelResult, cases, biasDimension }) {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const metrics = modelResult.metrics || {};
  const intensity = metrics.bias_intensity || "none";
  const scoreGap = Number(metrics.score_gap ?? 0);
  const scoreGapPct = Math.min(100, Math.max(0, (scoreGap / 10) * 100));

  return (
    <article className="space-y-5 rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-lg font-semibold text-slate-800">
            {modelResult.model_name}
          </h3>
          <p className="text-xs text-slate-500">
            Sesgo medido: <span className="font-medium">{biasDimension}</span>
          </p>
        </div>
        <span
          className={`inline-flex items-center rounded-full border px-3 py-1 text-xs font-medium ${INTENSITY_CLASSES[intensity] || INTENSITY_CLASSES.none}`}
        >
          bias_intensity: {intensity}
        </span>
      </header>

      <div className="overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead>
            <tr className="border-b border-slate-200 text-left text-xs uppercase tracking-wide text-slate-500">
              <th className="py-2 pr-3">Caso</th>
              <th className="py-2 pr-3">Valor del sesgo</th>
              <th className="py-2 pr-3">Decisión</th>
              <th className="py-2 pr-3">Score</th>
              <th className="py-2 pr-3">Duda</th>
              <th className="py-2 pr-3">Sesgo</th>
            </tr>
          </thead>
          <tbody>
            {ROW_DEFS.map((row) => {
              const c = findCase(cases, row.type);
              const o = c ? findOutput(modelResult.outputs, c.case_id) : null;
              return (
                <tr key={row.type} className="border-b border-slate-100">
                  <td className="py-2 pr-3 font-medium text-slate-700">{row.label}</td>
                  <td className="py-2 pr-3 text-slate-600">{c?.attribute_value || "—"}</td>
                  <td className="py-2 pr-3 text-slate-600">{o?.decision ?? "—"}</td>
                  <td className="py-2 pr-3 text-slate-600">
                    {typeof o?.score === "number" ? o.score.toFixed(1) : "—"}
                  </td>
                  <td className="py-2 pr-3 text-slate-600">
                    {o ? (o.doubt_flag ? "sí" : "no") : "—"}
                  </td>
                  <td className="py-2 pr-3">
                    {o?.bias_detected ? (
                      <span className="rounded bg-red-100 px-2 py-0.5 text-xs font-medium text-red-700">
                        sí
                      </span>
                    ) : (
                      <span className="text-slate-500">no</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div>
        <div className="mb-1 flex items-center justify-between text-xs text-slate-600">
          <span>score_gap base vs contrafactual</span>
          <span className="font-medium">{scoreGap.toFixed(2)} / 10</span>
        </div>
        <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100">
          <div
            className={`h-full ${
              intensity === "high"
                ? "bg-red-500"
                : intensity === "medium"
                ? "bg-orange-500"
                : intensity === "low"
                ? "bg-yellow-500"
                : "bg-emerald-500"
            }`}
            style={{ width: `${scoreGapPct}%` }}
          />
        </div>
      </div>

      <p className="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-700">
        {INTENSITY_TEXT[intensity] || INTENSITY_TEXT.none}
        {!metrics.control_validation && (
          <>
            {" "}
            <span className="font-medium text-red-700">
              El modelo falla en el caso de control, resultados no confiables.
            </span>
          </>
        )}
      </p>

      <CasesRadarChart modelResult={modelResult} cases={cases} />

      <div>
        <button
          type="button"
          onClick={() => setDrawerOpen(true)}
          className="inline-flex items-center gap-2 rounded-md border border-slate-300 bg-white px-3 py-2 text-sm font-medium text-slate-700 shadow-sm hover:bg-slate-50"
        >
          Ver prompts enviados
        </button>
      </div>

      <CaseDetailDrawer
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        cases={cases}
        modelResult={modelResult}
      />
    </article>
  );
}
