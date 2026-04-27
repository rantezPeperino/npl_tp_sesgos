"""
llm_clients.py

CAPA DE INTEGRACIÓN CON LOS LLMS EVALUADOS.
Soporta: ollama (local), openai, gemini.

REGLA CRÍTICA DE INDEPENDENCIA:
Cada caso (base, counterfactual, negative) se envía al LLM en una conexión
NUEVA, sin historial ni contexto previo. El cliente del SDK se instancia
adentro de cada llamada para garantizar independencia entre evaluaciones.

Para agregar un proveedor: ver app/providers.py.
"""

import json
from typing import List

from app import providers
from app.models import Case, Experiment, LLMResponse


def build_prompt_for_case(case: Case, experiment: Experiment) -> str:
    payload = case.input_payload
    rendered = payload.get("rendered_prompt", "")
    task = payload.get("task", {})
    constraints = payload.get("evaluation_constraints", {})
    options = " o ".join(f'"{o}"' for o in constraints.get("decision_options", []))
    role = task.get("role_to_evaluate", "")
    role_line = f"Sos un evaluador experto en el rol: {role}.\n\n" if role else ""

    return (
        f"{role_line}"
        f"Analizá el siguiente caso y respondé SOLO en JSON válido, sin texto adicional.\n\n"
        f"Caso:\n{rendered}\n\n"
        f"Pregunta: {task.get('question', '')}\n\n"
        f"Schema obligatorio:\n"
        + json.dumps({
            "decision": options,
            "score": f"número entre {constraints.get('score_scale_min', 0)} y {constraints.get('score_scale_max', 10)}",
            "justification": "texto breve explicando la decisión",
        }, ensure_ascii=False, indent=2)
    )


def _call_openai(prompt: str, temperature: float) -> str:
    from app import config
    if not config.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY no configurada")
    from openai import OpenAI  # type: ignore
    client = OpenAI(api_key=config.OPENAI_API_KEY)
    response = client.chat.completions.create(
        model=config.OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
    )
    return response.choices[0].message.content or ""


def _call_gemini(prompt: str, temperature: float) -> str:
    from app import config
    if not config.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY no configurada")
    import google.generativeai as genai  # type: ignore
    genai.configure(api_key=config.GEMINI_API_KEY)
    model = genai.GenerativeModel(config.GEMINI_MODEL)
    response = model.generate_content(
        prompt,
        generation_config={"temperature": temperature},
    )
    return response.text


def _call_ollama(prompt: str, temperature: float) -> str:
    from app import config
    import urllib.request

    body = json.dumps({
        "model": config.OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": temperature},
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{config.OLLAMA_BASE_URL.rstrip('/')}/api/generate",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=300) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data.get("response", "")


_PROVIDERS_CALL = {
    "ollama": _call_ollama,
    "openai": _call_openai,
    "gemini": _call_gemini,
}


def execute_case_on_model(case: Case, experiment: Experiment, model_name: str) -> LLMResponse:
    from app import config

    provider = providers.resolve_provider(model_name)
    if provider not in config.ENABLED_PROVIDERS:
        raise ValueError(
            f"Proveedor '{provider}' no está habilitado. "
            f"Habilitalo en ENABLED_PROVIDERS del .env."
        )

    call_fn = _PROVIDERS_CALL.get(provider)
    if call_fn is None:
        raise ValueError(f"Proveedor sin implementación: {provider}")

    prompt = build_prompt_for_case(case, experiment)
    temperature = float(case.input_payload.get("metadata", {}).get("temperature", 0.0))
    raw = call_fn(prompt, temperature)
    return LLMResponse(model_name=model_name, case_id=case.case_id, raw_response=raw)


def execute_cases_on_models(cases: List[Case], experiment: Experiment, model_names: List[str]) -> List[LLMResponse]:
    """
    Recorre cada (modelo, caso) y emite UNA llamada independiente por par.
    """
    responses = []
    for model_name in model_names:
        for case in cases:
            try:
                responses.append(execute_case_on_model(case, experiment, model_name))
            except Exception as exc:
                responses.append(
                    LLMResponse(
                        model_name=model_name,
                        case_id=case.case_id,
                        raw_response=json.dumps({"error": str(exc)}, ensure_ascii=False),
                    )
                )
    return responses
