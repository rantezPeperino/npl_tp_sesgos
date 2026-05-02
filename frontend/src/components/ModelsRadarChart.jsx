import {
  Chart as ChartJS,
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend,
} from "chart.js";
import { Radar } from "react-chartjs-2";

ChartJS.register(
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend,
);

const MODEL_COLORS = [
  { bg: "rgba(59,130,246,0.15)", border: "rgb(59,130,246)" },   // blue
  { bg: "rgba(239,68,68,0.15)", border: "rgb(239,68,68)" },     // red
  { bg: "rgba(16,185,129,0.15)", border: "rgb(16,185,129)" },   // emerald
  { bg: "rgba(245,158,11,0.15)", border: "rgb(245,158,11)" },   // amber
  { bg: "rgba(139,92,246,0.15)", border: "rgb(139,92,246)" },   // violet
];

const AXES = [
  {
    label: "Avg Score",
    description: "Promedio de los scores asignados por el modelo en los 3 casos (base, contrafactual, testigo). Escala 0-10.",
  },
  {
    label: "Consistencia",
    description: "1.0 si no se detecta sesgo, 0.0 si se detecta. Refleja si el modelo trata ambos grupos de forma equitativa.",
  },
  {
    label: "Score Gap",
    description: "Diferencia de score entre caso base y contrafactual. Escala 0-10. Menor valor = menos sesgo.",
  },
  {
    label: "Bias Rate",
    description: "Tasa de sesgo. 0 = sin sesgo detectado, 10 = sesgo detectado.",
  },
  {
    label: "Bias Intensity",
    description: "Intensidad del sesgo derivada del score gap y cambio de decisión. none=0, low=2.5, medium=5, high=10.",
  },
];

const LABELS = AXES.map((a) => a.label);

const INTENSITY_VALUE = { none: 0, low: 2.5, medium: 5, high: 10 };

function buildDatasets(modelResults) {
  return modelResults.map((mr, i) => {
    const m = mr.metrics || {};
    const color = MODEL_COLORS[i % MODEL_COLORS.length];
    const avgScore = m.avg_score ?? 0;
    const consistency = (m.consistency_score ?? 0) * 10;
    const scoreGap = m.score_gap ?? 0;
    const biasRate = (m.bias_rate ?? 0) * 10;
    const biasIntensity = INTENSITY_VALUE[m.bias_intensity] ?? 0;

    return {
      label: mr.model_name,
      data: [avgScore, consistency, scoreGap, biasRate, biasIntensity],
      backgroundColor: color.bg,
      borderColor: color.border,
      borderWidth: 2,
      pointBackgroundColor: color.border,
      pointRadius: 3,
    };
  });
}

const OPTIONS = {
  responsive: true,
  maintainAspectRatio: false,
  scales: {
    r: {
      beginAtZero: true,
      min: 0,
      max: 10,
      ticks: { stepSize: 2, backdropColor: "transparent", font: { size: 10 } },
      pointLabels: { font: { size: 12, weight: "500" }, color: "#475569" },
      grid: { color: "rgba(148,163,184,0.25)" },
      angleLines: { color: "rgba(148,163,184,0.25)" },
    },
  },
  plugins: {
    legend: {
      position: "bottom",
      labels: { usePointStyle: true, pointStyle: "circle", padding: 16, font: { size: 12 } },
    },
    tooltip: {
      callbacks: {
        label: (ctx) => `${ctx.dataset.label}: ${ctx.raw.toFixed(1)}`,
      },
    },
  },
};

export default function ModelsRadarChart({ modelResults }) {
  if (!modelResults?.length) return null;

  const data = { labels: LABELS, datasets: buildDatasets(modelResults) };

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <h3 className="mb-4 text-lg font-semibold text-slate-800">
        Comparativa global de modelos
      </h3>
      <div className="flex flex-col items-start gap-6 lg:flex-row">
        <div className="w-full lg:w-1/2" style={{ minHeight: 400 }}>
          <Radar data={data} options={OPTIONS} />
        </div>

        <dl className="w-full space-y-3 lg:w-1/2">
          {AXES.map((axis) => (
            <div key={axis.label} className="rounded-md bg-slate-50 px-3 py-2">
              <dt className="text-sm font-semibold text-slate-700">{axis.label}</dt>
              <dd className="mt-0.5 text-xs leading-relaxed text-slate-500">
                {axis.description}
              </dd>
            </div>
          ))}
        </dl>
      </div>
    </section>
  );
}