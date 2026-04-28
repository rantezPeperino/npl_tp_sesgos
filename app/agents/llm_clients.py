"""
llm_clients.py

CAPA DE INTEGRACIÓN CON LOS LLMS EVALUADOS.
Soporta: ollama (local), openai, gemini, anthropic.

REGLA CRÍTICA DE INDEPENDENCIA:
- Cliente NUEVO del SDK por cada llamada (id(client) verificable en logs).
- Cierre EXPLÍCITO al finalizar (try/finally).
- Cero reutilización de contexto / historial entre casos.
- Para Ollama se envía `context: []` explícito en cada request, lo que
  desactiva el reuso de KV cache de conversación previa.

Para auditar el aislamiento ver: app/tools/verify_isolation.py
Para agregar un proveedor: ver app/agents/providers.py.
"""

import hashlib
import json
import sys
import time
import uuid
from typing import List

from app.agents import providers
from app.messages import build_prompt_for_case
from app.models import Case, Experiment, LLMResponse


def _log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def _short_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:8]


def _new_call_id() -> str:
    return uuid.uuid4().hex[:8]


def _call_openai(prompt: str, temperature: float, call_id: str) -> str:
    from app import config
    if not config.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY no configurada")
    from openai import OpenAI  # type: ignore
    client = OpenAI(api_key=config.OPENAI_API_KEY)
    _log(f"[ISOLATION] call={call_id} client_id={id(client):x} provider=openai (cliente nuevo)")
    try:
        response = client.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
        )
        return response.choices[0].message.content or ""
    finally:
        try:
            client.close()
            _log(f"[ISOLATION] call={call_id} client_id={id(client):x} provider=openai (cliente cerrado)")
        except Exception as exc:
            _log(f"[ISOLATION] call={call_id} provider=openai close-error={exc}")


def _call_anthropic(prompt: str, temperature: float, call_id: str) -> str:
    from app import config
    if not config.ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY no configurada")
    import anthropic  # type: ignore
    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    _log(f"[ISOLATION] call={call_id} client_id={id(client):x} provider=anthropic (cliente nuevo)")
    try:
        message = client.messages.create(
            model=config.ANTHROPIC_MODEL,
            max_tokens=512,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text
    finally:
        try:
            client.close()
            _log(f"[ISOLATION] call={call_id} client_id={id(client):x} provider=anthropic (cliente cerrado)")
        except Exception as exc:
            _log(f"[ISOLATION] call={call_id} provider=anthropic close-error={exc}")


def _call_gemini(prompt: str, temperature: float, call_id: str) -> str:
    from app import config
    if not config.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY no configurada")
    import google.generativeai as genai  # type: ignore
    genai.configure(api_key=config.GEMINI_API_KEY)
    model = genai.GenerativeModel(config.GEMINI_MODEL)
    _log(f"[ISOLATION] call={call_id} client_id={id(model):x} provider=gemini (modelo nuevo)")
    try:
        response = model.generate_content(
            prompt,
            generation_config={"temperature": temperature},
        )
        return response.text
    finally:
        del model
        _log(f"[ISOLATION] call={call_id} provider=gemini (modelo descartado)")


def _call_ollama(prompt: str, temperature: float, call_id: str) -> str:
    """
    Llama a Ollama vía HTTP nativo. Garantías de aislamiento:
    - `context: []` explícito → no reusa KV cache de llamadas anteriores
    - `keep_alive: 0` → Ollama unloadea el modelo de la VRAM tras responder
    - `Connection: close` → fuerza cierre del socket TCP
    - urllib.request.urlopen abre socket NUEVO en cada llamada
    """
    from app import config
    import urllib.request

    payload = {
        "model": config.OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": temperature},
        "context": [],          # ← sin contexto previo
        "keep_alive": 0,        # ← descarga el modelo después
    }
    body = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(
        f"{config.OLLAMA_BASE_URL.rstrip('/')}/api/generate",
        data=body,
        headers={"Content-Type": "application/json", "Connection": "close"},
        method="POST",
    )
    _log(
        f"[ISOLATION] call={call_id} provider=ollama (socket nuevo, context=[], keep_alive=0)"
    )
    resp = urllib.request.urlopen(req, timeout=300)
    try:
        sock_id = id(resp)
        _log(f"[ISOLATION] call={call_id} provider=ollama response_id={sock_id:x}")
        data = json.loads(resp.read().decode("utf-8"))
    finally:
        resp.close()
        _log(f"[ISOLATION] call={call_id} provider=ollama (socket cerrado)")
    return data.get("response", "")


_PROVIDERS_CALL = {
    "ollama": _call_ollama,
    "openai": _call_openai,
    "gemini": _call_gemini,
    "anthropic": _call_anthropic,
}


def _resolve_model_id(provider: str) -> str:
    from app import config
    if provider == "ollama":
        return config.OLLAMA_MODEL
    if provider == "openai":
        return config.OPENAI_MODEL
    if provider == "gemini":
        return config.GEMINI_MODEL
    if provider == "anthropic":
        return config.ANTHROPIC_MODEL
    return "?"


def _resolve_target(provider: str) -> str:
    from app import config
    if provider == "ollama":
        return config.OLLAMA_BASE_URL
    if provider == "openai":
        return "api.openai.com"
    if provider == "gemini":
        return "generativelanguage.googleapis.com"
    if provider == "anthropic":
        return "api.anthropic.com"
    return "?"


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
    temperature = float(config.TEMPERATURE)
    call_id = _new_call_id()
    prompt_hash = _short_hash(prompt)

    model_id = _resolve_model_id(provider)
    target = _resolve_target(provider)

    _log(
        f"[LLM CALL] call={call_id} provider={provider} model={model_id} "
        f"target={target} case={case.case_id} prompt_sha={prompt_hash} prompt_len={len(prompt)}"
    )
    t0 = time.monotonic()
    raw = call_fn(prompt, temperature, call_id)
    elapsed = time.monotonic() - t0
    _log(
        f"[LLM RESP] call={call_id} provider={provider} model={model_id} "
        f"elapsed={elapsed:.2f}s chars={len(raw)} resp_sha={_short_hash(raw)} case={case.case_id}"
    )
    return LLMResponse(model_name=model_name, case_id=case.case_id, raw_response=raw)


def execute_cases_on_models(
    cases: List[Case], experiment: Experiment, model_names: List[str]
) -> List[LLMResponse]:
    """
    Recorre cada (modelo, caso) emitiendo UNA llamada nueva por par.
    Cada llamada:
      - usa un cliente SDK nuevo (id distinto en logs)
      - se cierra explícitamente en finally
      - no comparte estado con la anterior
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
