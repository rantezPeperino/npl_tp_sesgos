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

const CASE_COLORS = {
  base:            { bg: "rgba(59,130,246,0.15)",  border: "rgb(59,130,246)" },
  counterfactual:  { bg: "rgba(239,68,68,0.15)",   border: "rgb(239,68,68)" },
  negative:        { bg: "rgba(148,163,184,0.15)", border: "rgb(148,163,184)" },
};

const CASE_LABELS = {
  base: "Caso base",
  counterfactual: "Contrafactual",
  negative: "Testigo",
};

const AXES = [
  {
    label: "Score",
    description: "Score asignado por el modelo al caso. Escala 0-10.",
  },
  {
    label: "Confianza",
    description: "Nivel de confianza auto-reportado por el modelo (1 = muy inseguro, 10 = totalmente seguro).",
  },
  {
    label: "Sesgo",
    description: "10 si se detectó sesgo en este caso, 0 si no. Permite ver qué casos disparan la alerta.",
  },
];

const LABELS = AXES.map((a) => a.label);

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

function buildDatasets(outputs, cases) {
  const caseTypes = ["base", "counterfactual", "negative"];

  return caseTypes
    .map((type) => {
      const caseObj = cases?.find((c) => c.case_type === type);
      if (!caseObj) return null;
      const output = outputs?.find((o) => o.case_id === caseObj.case_id);
      if (!output) return null;

      const color = CASE_COLORS[type];
      const score = output.score ?? 0;
      const confidence = output.confidence ?? 5;
      const bias = output.bias_detected ? 10 : 0;

      return {
        label: CASE_LABELS[type],
        data: [score, confidence, bias],
        backgroundColor: color.bg,
        borderColor: color.border,
        borderWidth: 2,
        pointBackgroundColor: color.border,
        pointRadius: 3,
      };
    })
    .filter(Boolean);
}

export default function CasesRadarChart({ modelResult, cases }) {
  const datasets = buildDatasets(modelResult.outputs, cases);
  if (!datasets.length) return null;

  const data = { labels: LABELS, datasets };

  return (
    <div>
      <h4 className="mb-3 text-sm font-semibold text-slate-700">
        Comparativa entre casos
      </h4>
      <div className="flex flex-col items-start gap-6 lg:flex-row">
        <div className="w-full lg:w-1/2" style={{ minHeight: 340 }}>
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
    </div>
  );
}