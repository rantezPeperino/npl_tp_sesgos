import { Link, Route, Routes } from "react-router-dom";
import LLMStatusBadge from "./components/LLMStatusBadge.jsx";
import { useExperiment } from "./hooks/useExperiment.js";
import Home from "./pages/Home.jsx";
import Results from "./pages/Results.jsx";

export default function App() {
  const exp = useExperiment();

  return (
    <div className="flex min-h-full flex-col">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3 sm:px-6">
          <Link to="/" className="flex items-center gap-2">
            <span className="inline-flex h-8 w-8 items-center justify-center rounded-md bg-blue-600 text-sm font-bold text-white">
              tD
            </span>
            <h1 className="text-lg font-semibold text-slate-900">tiltDetector</h1>
          </Link>
          <LLMStatusBadge
            status={exp.llmStatus}
            error={exp.llmStatusError}
            onRefresh={exp.refreshLlmStatus}
          />
        </div>
      </header>

      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-6 sm:px-6">
        <Routes>
          <Route path="/" element={<Home exp={exp} />} />
          <Route path="/results" element={<Results exp={exp} />} />
          <Route
            path="*"
            element={
              <div className="text-sm text-slate-600">
                Página no encontrada. <Link to="/" className="text-blue-700 hover:underline">Volver al inicio</Link>
              </div>
            }
          />
        </Routes>
      </main>

      <footer className="border-t border-slate-200 bg-white">
        <div className="mx-auto max-w-6xl px-4 py-3 text-xs text-slate-500 sm:px-6">
          tiltDetector — frontend MVP. Backend esperado en localhost:8000.
        </div>
      </footer>
    </div>
  );
}
