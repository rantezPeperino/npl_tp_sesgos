import { useState } from "react";

const TABS = [
  { key: "base", label: "BASE" },
  { key: "counterfactual", label: "CONTRAFACTUAL" },
  { key: "negative", label: "TESTIGO" },
];

function findCase(cases, type) {
  return cases?.find((c) => c.case_type === type) || null;
}

function findOutput(outputs, caseId) {
  return outputs?.find((o) => o.case_id === caseId) || null;
}

function prettyJson(raw) {
  if (!raw) return "(sin respuesta)";
  try {
    return JSON.stringify(JSON.parse(raw), null, 2);
  } catch {
    return raw;
  }
}

export default function CaseDetailDrawer({ open, onClose, cases, modelResult }) {
  const [tab, setTab] = useState("base");

  if (!open) return null;

  const caseObj = findCase(cases, tab);
  const output = caseObj ? findOutput(modelResult?.outputs, caseObj.case_id) : null;

  return (
    <div className="fixed inset-0 z-30 flex">
      <button
        type="button"
        aria-label="Cerrar"
        onClick={onClose}
        className="flex-1 bg-slate-900/40"
      />
      <aside className="flex w-full max-w-3xl flex-col bg-white shadow-2xl sm:w-[640px]">
        <header className="flex items-center justify-between border-b border-slate-200 px-5 py-3">
          <h2 className="text-base font-semibold text-slate-800">
            Prompts enviados — {modelResult?.model_name}
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="rounded-md px-2 py-1 text-sm text-slate-500 hover:bg-slate-100"
            aria-label="Cerrar drawer"
          >
            ✕
          </button>
        </header>

        <nav className="flex border-b border-slate-200 px-5">
          {TABS.map((t) => (
            <button
              key={t.key}
              type="button"
              onClick={() => setTab(t.key)}
              className={`-mb-px border-b-2 px-3 py-2 text-sm font-medium ${
                tab === t.key
                  ? "border-blue-600 text-blue-700"
                  : "border-transparent text-slate-500 hover:text-slate-800"
              }`}
            >
              {t.label}
            </button>
          ))}
        </nav>

        <div className="flex-1 space-y-5 overflow-y-auto px-5 py-4 text-sm">
          {!caseObj ? (
            <p className="text-slate-500">Caso no disponible.</p>
          ) : (
            <>
              <Section title="Prompt enviado al LLM">
                <pre className="whitespace-pre-wrap rounded-md bg-slate-50 p-3 text-xs text-slate-700">
                  {caseObj.rendered_prompt || "(no disponible)"}
                </pre>
              </Section>

              <Section title="Respuesta cruda del modelo">
                <pre className="whitespace-pre-wrap rounded-md bg-slate-900 p-3 text-xs text-slate-100">
                  {prettyJson(output?.raw_response)}
                </pre>
              </Section>

              <Section title="Normalización">
                {output ? (
                  <dl className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
                    <Row label="decision" value={output.decision} />
                    <Row label="score" value={String(output.score)} />
                    <Row label="doubt_flag" value={String(output.doubt_flag)} />
                    <Row
                      label="bias_detected"
                      value={String(output.bias_detected)}
                    />
                    <Row
                      label="bias_category"
                      value={output.bias_category || "—"}
                    />
                    <div className="col-span-2 mt-2">
                      <dt className="text-slate-500">justification</dt>
                      <dd className="mt-1 whitespace-pre-wrap rounded bg-slate-50 p-2 text-slate-800">
                        {output.justification || "(vacía)"}
                      </dd>
                    </div>
                  </dl>
                ) : (
                  <p className="text-slate-500">Sin output para este caso.</p>
                )}
              </Section>
            </>
          )}
        </div>
      </aside>
    </div>
  );
}

function Section({ title, children }) {
  return (
    <section>
      <h3 className="mb-1 text-xs font-semibold uppercase tracking-wide text-slate-500">
        {title}
      </h3>
      {children}
    </section>
  );
}

function Row({ label, value }) {
  return (
    <>
      <dt className="text-slate-500">{label}</dt>
      <dd className="text-slate-800">{value}</dd>
    </>
  );
}
