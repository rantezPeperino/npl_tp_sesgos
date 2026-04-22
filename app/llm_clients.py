"""
llm_clients.py

CAPA DE INTEGRACIÓN CON LOS MODELOS DE LENGUAJE EVALUADOS.
Soporta: openai (habilitado), anthropic y gemini (deshabilitados por ahora).
Fallback a mock determinista si el proveedor no está habilitado.
"""

import json
from typing import List

from app.models import Case, Experiment, LLMResponse


_OPENAI_PROVIDER = "openai"
_ANTHROPIC_PROVIDER = "anthropic"
_GEMINI_PROVIDER = "gemini"

_MODEL_PROVIDER_MAP = {
    "chatgpt": _OPENAI_PROVIDER,
    "openai": _OPENAI_PROVIDER,
    "gpt": _OPENAI_PROVIDER,
    "claude": _ANTHROPIC_PROVIDER,
    "anthropic": _ANTHROPIC_PROVIDER,
    "gemini": _GEMINI_PROVIDER,
    "google": _GEMINI_PROVIDER,
}


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


def _resolve_provider(model_name: str) -> str:
    key = model_name.lower().split("-")[0]
    return _MODEL_PROVIDER_MAP.get(key, "mock")


def _call_openai(prompt: str, model: str, api_key: str, temperature: float = 0.0) -> str:
    from openai import OpenAI  # type: ignore
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
    )
    return response.choices[0].message.content or ""


def _call_anthropic(prompt: str, api_key: str) -> str:
    import anthropic  # type: ignore
    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


def _call_gemini(prompt: str, api_key: str) -> str:
    import google.generativeai as genai  # type: ignore
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content(prompt)
    return response.text


def _mock_response(case: Case, experiment: Experiment) -> str:
    options = experiment.evaluation_constraints.decision_options
    default_yes = options[0] if options else "si"
    default_no = options[1] if len(options) > 1 else default_yes

    if case.case_type == "base":
        score, decision = 9.0, default_yes
        justification = "Perfil sólido y consistente con el criterio evaluado."
    elif case.case_type == "counterfactual":
        score, decision = 7.0, default_yes
        justification = "Perfil con condiciones similares, aunque habría que validar con más detalle."
    else:
        score, decision = 5.0, default_no
        justification = "Información insuficiente o no aplica al criterio evaluado."
    return json.dumps({"decision": decision, "score": score, "justification": justification}, ensure_ascii=False)


def execute_case_on_model(case: Case, experiment: Experiment, model_name: str) -> LLMResponse:
    from app import config

    provider = _resolve_provider(model_name)
    prompt = build_prompt_for_case(case, experiment)
    temperature = float(case.input_payload.get("metadata", {}).get("temperature", 0.0))
    raw: str

    if provider == _OPENAI_PROVIDER and _OPENAI_PROVIDER in config.ENABLED_PROVIDERS:
        raw = _call_openai(prompt, config.OPENAI_MODEL, config.OPENAI_API_KEY, temperature=temperature)
    elif provider == _ANTHROPIC_PROVIDER and _ANTHROPIC_PROVIDER in config.ENABLED_PROVIDERS:
        raw = _call_anthropic(prompt, config.ANTHROPIC_API_KEY)
    elif provider == _GEMINI_PROVIDER and _GEMINI_PROVIDER in config.ENABLED_PROVIDERS:
        raw = _call_gemini(prompt, config.GEMINI_API_KEY)
    else:
        raw = _mock_response(case, experiment)

    return LLMResponse(model_name=model_name, case_id=case.case_id, raw_response=raw)


def execute_cases_on_models(cases: List[Case], experiment: Experiment, model_names: List[str]) -> List[LLMResponse]:
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
                        raw_response=json.dumps({"error": str(exc)}),
                    )
                )
    return responses
