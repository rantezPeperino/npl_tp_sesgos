import { useNavigate } from "react-router-dom";
import ExperimentForm from "../components/ExperimentForm.jsx";

export default function Home({ exp }) {
  const navigate = useNavigate();

  async function handleSubmit(payload) {
    await exp.submit(payload);
    navigate("/results");
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <header>
        <h2 className="text-2xl font-bold text-slate-900">Nuevo experimento</h2>
        <p className="mt-1 text-sm text-slate-600">
          Describí un caso a evaluar y elegí la dimensión de sesgo a medir. El
          sistema construye automáticamente los 3 casos (base, contrafactual,
          testigo) y los envía a los LLMs seleccionados.
        </p>
      </header>

      <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
        <ExperimentForm
          llmStatus={exp.llmStatus}
          loading={exp.loading}
          error={exp.error}
          onSubmit={handleSubmit}
        />
      </div>

      {exp.result && !exp.loading && (
        <div className="rounded-md border border-blue-200 bg-blue-50 px-4 py-3 text-sm text-blue-800">
          Tenés un experimento previo guardado:{" "}
          <button
            type="button"
            onClick={() => navigate("/results")}
            className="font-medium underline hover:text-blue-900"
          >
            ver resultados
          </button>
          .
        </div>
      )}
    </div>
  );
}
