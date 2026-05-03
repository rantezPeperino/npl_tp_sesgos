const BASE = "/api";

async function handleJson(res) {
  const contentType = res.headers.get("content-type") || "";
  const body = contentType.includes("application/json")
    ? await res.json().catch(() => null)
    : await res.text();
  if (!res.ok) {
    const detail =
      (body && body.detail) ||
      (typeof body === "string" ? body : JSON.stringify(body));
    const err = new Error(detail || `HTTP ${res.status}`);
    err.status = res.status;
    err.body = body;
    throw err;
  }
  return body;
}

export async function runExperiment({ pedido, sesgo_medir, model_names }) {
  const res = await fetch(`${BASE}/experiments/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ pedido, sesgo_medir, model_names }),
  });
  return handleJson(res);
}

export async function getExperiment(experimentId) {
  const res = await fetch(`${BASE}/experiments/${experimentId}`);
  return handleJson(res);
}

export async function getLlmStatus() {
  const res = await fetch(`${BASE}/llm/status`);
  return handleJson(res);
}

export async function getHealth() {
  const res = await fetch(`${BASE}/health`);
  return handleJson(res);
}

export async function fetchRandomExample(dimension) {
  const qs = dimension ? `?dimension=${encodeURIComponent(dimension)}` : "";
  const res = await fetch(`${BASE}/examples/random${qs}`);
  return handleJson(res);
}
