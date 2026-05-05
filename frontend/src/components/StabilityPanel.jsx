const VERDICT_STYLES = {
  significativo: "bg-red-100 text-red-800 border-red-200",
  no_concluyente: "bg-amber-100 text-amber-800 border-amber-200",
  sin_datos: "bg-slate-100 text-slate-700 border-slate-200",
};

const VERDICT_TEXT = {
  significativo:
    "El IC95 de la diferencia base − contrafactual no contiene al cero: hay evidencia estadística de sesgo.",
  no_concluyente:
    "El IC95 de la diferencia incluye al cero: no se puede afirmar que el gap sea sesgo y no ruido del modelo.",
  sin_datos:
    "No se pudieron calcular los estadísticos (faltan respuestas válidas en alguno de los casos).",
};

const CASE_LABEL = {
  base: "Caso base",
  counterfactual: "Contrafactual",
  negative: "Testigo",
};

function fmt(n, digits = 2) {
  if (typeof n !== "number" || Number.isNaN(n)) return "—";
  return n.toFixed(digits);
}

function CIBar({ low, high, mean, min = 0, max = 10 }) {
  if (typeof low !== "number" || typeof high !== "number") return null;
  const span = max - min;
  const pctLow = Math.max(0, Math.min(100, ((low - min) / span) * 100));
  const pctHigh = Math.max(0, Math.min(100, ((high - min) / span) * 100));
  const pctMean = Math.max(0, Math.min(100, ((mean - min) / span) * 100));
  const width = Math.max(1, pctHigh - pctLow);
  return (
    <div className="relative h-2 w-full rounded-full bg-slate-100">
      <div
        className="absolute h-2 rounded-full bg-blue-300"
        style={{ left: `${pctLow}%`, width: `${width}%` }}
      />
      <div
        className="absolute -top-1 h-4 w-0.5 bg-blue-700"
        style={{ left: `calc(${pctMean}% - 1px)` }}
        title={`media: ${fmt(mean)}`}
      />
    </div>
  );
}

export default function StabilityPanel({ stability }) {
  if (!stability) return null;

  const verdict = stability.verdict || "sin_datos";
  const verdictStyle = VERDICT_STYLES[verdict] || VERDICT_STYLES.sin_datos;
  const verdictText = VERDICT_TEXT[verdict] || "";

  const sortedCases = [...(stability.cases || [])].sort((a, b) => {
    const order = { base: 0, counterfactual: 1, negative: 2, unknown: 3 };
    return (order[a.case_type] ?? 99) - (order[b.case_type] ?? 99);
  });

  return (
    <section className="rounded-md border border-slate-200 bg-slate-50/40 p-4">
      <header className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <h4 className="text-sm font-semibold text-slate-800">
          Estabilidad estadística (n_repeats = {stability.n_repeats})
        </h4>
        <span
          className={`inline-flex items-center rounded-full border px-3 py-0.5 text-xs font-medium ${verdictStyle}`}
        >
          {verdict.replace("_", " ")}
        </span>
      </header>

      <div className="overflow-x-auto">
        <table className="min-w-full text-xs">
          <thead>
            <tr className="border-b border-slate-200 text-left uppercase tracking-wide text-slate-500">
              <th className="py-1 pr-3">Caso</th>
              <th className="py-1 pr-3">media ± σ</th>
              <th className="py-1 pr-3">IC95 score</th>
              <th className="py-1 pr-3">decisión modal</th>
              <th className="py-1 pr-3">consistencia</th>
            </tr>
          </thead>
          <tbody>
            {sortedCases.map((c) => (
              <tr key={c.case_id} className="border-b border-slate-100">
                <td className="py-1 pr-3 font-medium text-slate-700">
                  {CASE_LABEL[c.case_type] || c.case_type}
                </td>
                <td className="py-1 pr-3 text-slate-600">
                  {fmt(c.score_mean)} ± {fmt(c.score_stdev)}
                </td>
                <td className="py-1 pr-3 text-slate-600">
                  <div className="flex items-center gap-2">
                    <span className="whitespace-nowrap">
                      [{fmt(c.score_ci95_low)}, {fmt(c.score_ci95_high)}]
                    </span>
                    <div className="min-w-[80px] flex-1">
                      <CIBar
                        low={c.score_ci95_low}
                        high={c.score_ci95_high}
                        mean={c.score_mean}
                      />
                    </div>
                  </div>
                </td>
                <td className="py-1 pr-3 text-slate-600">{c.decision_mode}</td>
                <td className="py-1 pr-3 text-slate-600">
                  {fmt((c.decision_consistency ?? 0) * 100, 0)}%
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {verdict !== "sin_datos" && (
        <div className="mt-3 rounded-md border border-slate-200 bg-white p-3">
          <p className="text-xs text-slate-600">
            Δ base − contrafactual:{" "}
            <span className="font-medium text-slate-800">
              {fmt(stability.delta_mean)}
            </span>
            {"  ·  "}
            IC95:{" "}
            <span className="font-medium text-slate-800">
              [{fmt(stability.delta_ci95_low)}, {fmt(stability.delta_ci95_high)}]
            </span>
          </p>
          <p className="mt-1 text-xs text-slate-700">{verdictText}</p>
        </div>
      )}
      {verdict === "sin_datos" && (
        <p className="mt-3 text-xs text-slate-700">{verdictText}</p>
      )}
    </section>
  );
}
