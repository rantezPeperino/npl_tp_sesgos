export default function GlobalSummary({ summary }) {
  if (!summary) return null;

  const biasGlobal = !!summary.bias_detected_global;
  const controlOk = !!summary.control_validation_all_models;
  const maxGap =
    typeof summary.max_score_gap === "number"
      ? summary.max_score_gap.toFixed(2)
      : "—";

  return (
    <section className="grid grid-cols-1 gap-4 sm:grid-cols-3">
      <Card
        title="Sesgo detectado"
        value={biasGlobal ? "Sí" : "No"}
        tone={biasGlobal ? "danger" : "success"}
      />
      <Card title="Score gap máximo" value={maxGap} tone="neutral" />
      <Card
        title="Control"
        value={controlOk ? "OK" : "Falla"}
        tone={controlOk ? "success" : "danger"}
      />
    </section>
  );
}

function Card({ title, value, tone }) {
  const tones = {
    success: "border-emerald-200 bg-emerald-50 text-emerald-800",
    danger: "border-red-200 bg-red-50 text-red-800",
    neutral: "border-slate-200 bg-white text-slate-800",
  };
  return (
    <div className={`rounded-lg border p-4 shadow-sm ${tones[tone]}`}>
      <p className="text-xs font-medium uppercase tracking-wide opacity-70">
        {title}
      </p>
      <p className="mt-1 text-2xl font-semibold">{value}</p>
    </div>
  );
}
