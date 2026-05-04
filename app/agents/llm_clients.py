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
import logging
import sys
import time
import uuid
from typing import Any, Dict, List

from app.agents import json_builder, providers
from app.logging_setup import logger
from app.messages import build_prompt_for_case
from app.models import Case, Experiment, LLMResponse


def _log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def _short_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:8]


def _new_call_id() -> str:
    return uuid.uuid4().hex[:8]


def _call_openai(prompt: str, temperature: float, call_id: str, model_id: str, system_prompt: str = "") -> str:
    from app import config
    if not config.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY no configurada")
    from openai import OpenAI  # type: ignore
    client = OpenAI(api_key=config.OPENAI_API_KEY)
    _log(f"[ISOLATION] call={call_id} client_id={id(client):x} provider=openai (cliente nuevo)")
    try:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        kwargs = {
            "model": model_id,
            "messages": messages,
        }
        if temperature != 1.0:
            kwargs["temperature"] = temperature
        try:
            response = client.chat.completions.create(**kwargs)
        except Exception as exc:
            if "temperature" in str(exc):
                _log(f"[LLM] call={call_id} model={model_id} no soporta temperature={temperature}, reintentando sin temperature")
                kwargs.pop("temperature", None)
                response = client.chat.completions.create(**kwargs)
            else:
                raise
        return response.choices[0].message.content or ""
    finally:
        try:
            client.close()
            _log(f"[ISOLATION] call={call_id} client_id={id(client):x} provider=openai (cliente cerrado)")
        except Exception as exc:
            _log(f"[ISOLATION] call={call_id} provider=openai close-error={exc}")


def _call_anthropic(prompt: str, temperature: float, call_id: str, model_id: str, system_prompt: str = "") -> str:
    from app import config
    if not config.ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY no configurada")
    import anthropic  # type: ignore
    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    _log(f"[ISOLATION] call={call_id} client_id={id(client):x} provider=anthropic (cliente nuevo)")
    try:
        create_kwargs = {
            "model": model_id,
            "max_tokens": 512,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system_prompt:
            create_kwargs["system"] = system_prompt
        try:
            message = client.messages.create(**create_kwargs)
            return message.content[0].text
        except Exception as exc:
            # Si el modelo rechaza temperature, reintentar sin él
            if "temperature" in str(exc) and "deprecated" in str(exc).lower():
                _log(f"[LLM] call={call_id} model={model_id} temperature rechazado, reintentando sin temperature")
                logger.warning(f"[ANTHROPIC] model={model_id} no soporta temperature, reintentando sin parámetro")
                create_kwargs.pop("temperature", None)
                message = client.messages.create(**create_kwargs)
                return message.content[0].text
            else:
                raise
    finally:
        try:
            client.close()
            _log(f"[ISOLATION] call={call_id} client_id={id(client):x} provider=anthropic (cliente cerrado)")
        except Exception as exc:
            _log(f"[ISOLATION] call={call_id} provider=anthropic close-error={exc}")


def _call_gemini(prompt: str, temperature: float, call_id: str, model_id: str, system_prompt: str = "") -> str:
    from app import config
    if not config.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY no configurada")
    import google.generativeai as genai  # type: ignore
    genai.configure(api_key=config.GEMINI_API_KEY)
    if system_prompt:
        model = genai.GenerativeModel(model_id, system_instruction=system_prompt)
    else:
        model = genai.GenerativeModel(model_id)
    _log(f"[ISOLATION] call={call_id} client_id={id(model):x} provider=gemini (modelo nuevo)")
    try:
        try:
            response = model.generate_content(
                prompt,
                generation_config={"temperature": temperature},
            )
            return response.text
        except Exception as exc:
            # Si el modelo rechaza temperature, reintentar sin él
            if "temperature" in str(exc).lower():
                _log(f"[LLM] call={call_id} model={model_id} temperature rechazado, reintentando sin temperature")
                logger.warning(f"[GEMINI] model={model_id} no soporta temperature, reintentando sin parámetro")
                response = model.generate_content(prompt)
                return response.text
            else:
                raise
    finally:
        del model
        _log(f"[ISOLATION] call={call_id} provider=gemini (modelo descartado)")


def _call_openrouter(prompt: str, temperature: float, call_id: str, model_id: str, system_prompt: str = "") -> str:
    from app import config
    if not config.OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY no configurada")
    from openai import OpenAI  # type: ignore
    client = OpenAI(
        base_url=config.OPENROUTER_BASE_URL,
        api_key=config.OPENROUTER_API_KEY,
    )
    _log(f"[ISOLATION] call={call_id} client_id={id(client):x} provider=openrouter (cliente nuevo)")
    try:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        kwargs = {
            "model": model_id,
            "messages": messages,
        }
        if temperature != 1.0:
            kwargs["temperature"] = temperature
        try:
            response = client.chat.completions.create(**kwargs)
        except Exception as exc:
            if "temperature" in str(exc):
                _log(f"[LLM] call={call_id} model={model_id} no soporta temperature={temperature}, reintentando sin temperature")
                kwargs.pop("temperature", None)
                response = client.chat.completions.create(**kwargs)
            else:
                raise
        return response.choices[0].message.content or ""
    finally:
        try:
            client.close()
            _log(f"[ISOLATION] call={call_id} client_id={id(client):x} provider=openrouter (cliente cerrado)")
        except Exception as exc:
            _log(f"[ISOLATION] call={call_id} provider=openrouter close-error={exc}")


def _call_deepseek(prompt: str, temperature: float, call_id: str, model_id: str, system_prompt: str = "") -> str:
    from app import config
    if not config.DEEPSEEK_API_KEY:
        raise ValueError("DEEPSEEK_API_KEY no configurada")
    from openai import OpenAI  # type: ignore
    client = OpenAI(
        api_key=config.DEEPSEEK_API_KEY,
        base_url="https://api.deepseek.com",
    )
    _log(f"[ISOLATION] call={call_id} client_id={id(client):x} provider=deepseek (cliente nuevo)")
    try:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        kwargs = {
            "model": model_id,
            "messages": messages,
        }
        if temperature != 1.0:
            kwargs["temperature"] = temperature
        try:
            response = client.chat.completions.create(**kwargs)
        except Exception as exc:
            if "temperature" in str(exc):
                _log(f"[LLM] call={call_id} model={model_id} no soporta temperature={temperature}, reintentando sin temperature")
                kwargs.pop("temperature", None)
                response = client.chat.completions.create(**kwargs)
            else:
                raise
        return response.choices[0].message.content or ""
    finally:
        try:
            client.close()
            _log(f"[ISOLATION] call={call_id} client_id={id(client):x} provider=deepseek (cliente cerrado)")
        except Exception as exc:
            _log(f"[ISOLATION] call={call_id} provider=deepseek close-error={exc}")


def _call_ollama(prompt: str, temperature: float, call_id: str, model_id: str, system_prompt: str = "") -> str:
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
        "model": model_id,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": temperature},
        "context": [],          # ← sin contexto previo
        "keep_alive": 0,        # ← descarga el modelo después
    }
    if system_prompt:
        payload["system"] = system_prompt
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
    "openrouter": _call_openrouter,
    "deepseek": _call_deepseek,
}




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
    if provider == "openrouter":
        return "openrouter.ai"
    if provider == "deepseek":
        return "api.deepseek.com"
    return "?"


def execute_case_on_model(case: Case, experiment: Experiment, model_name: str, system_prompt: str = "") -> LLMResponse:
    from app import config

    provider = providers.resolve_provider(model_name)

    call_fn = _PROVIDERS_CALL.get(provider)
    if call_fn is None:
        raise ValueError(f"Proveedor sin implementación: {provider}")

    # NUEVO: Usar JSON en lugar de prompts en párrafo
    case_json = _build_case_json(case, experiment)
    prompt_json = json.dumps(case_json, ensure_ascii=False, indent=2)

    temperature = float(config.TEMPERATURE)
    call_id = _new_call_id()
    prompt_hash = _short_hash(prompt_json)

    target = _resolve_target(provider)

    _log(
        f"[LLM CALL JSON] call={call_id} provider={provider} model={model_name} "
        f"target={target} case={case.case_id} format=json prompt_sha={prompt_hash}"
    )

    logger.info(f"[LLM CALL JSON] case={case.case_id} model={model_name} provider={provider} format=json")
    logger.debug(f"[JSON ENVIADO] case={case.case_id}\n{prompt_json}")
    if system_prompt:
        logger.debug(f"[SYSTEM PROMPT] case={case.case_id}\n{system_prompt}")

    t0 = time.monotonic()
    raw = call_fn(prompt_json, temperature, call_id, model_name, system_prompt)
    elapsed = time.monotonic() - t0
    _log(
        f"[LLM RESP JSON] call={call_id} provider={provider} model={model_name} "
        f"elapsed={elapsed:.2f}s chars={len(raw)} case={case.case_id}"
    )

    logger.info(f"[LLM RESP JSON] case={case.case_id} model={model_name} elapsed={elapsed:.2f}s")
    logger.debug(f"[RESPUESTA CRUDA] case={case.case_id}\n{raw}")

    return LLMResponse(model_name=model_name, case_id=case.case_id, raw_response=raw, prompt_sent=prompt_json)


def _build_case_json(case: Case, experiment: Experiment) -> Dict[str, Any]:
    """
    Construye el JSON del caso en lugar de un prompt en párrafo.
    Incluye información estructurada para que el LLM analice como JSON.
    """
    case_type = "base"
    if "_counterfactual_" in case.case_id:
        case_type = "counterfactual"
    elif "_negative_" in case.case_id:
        case_type = "negative"

    case_json = {
        "case_id": case.case_id,
        "case_type": case_type,
        "experiment_id": experiment.experiment_id,
        "bias_dimension": experiment.bias_dimension,
        "attribute_context": case.attribute_value,
        "evaluation": {
            "role": experiment.task.role_to_evaluate,
            "question": experiment.task.question,
            "scenario": case.rendered_prompt,
        },
        "constraints": {
            "response_format": "json_strict",
            "required_fields": ["decision", "score", "confidence", "justification"],
            "score_range": {
                "min": experiment.evaluation_constraints.score_scale_min,
                "max": experiment.evaluation_constraints.score_scale_max,
            },
        },
    }

    if case_type == "negative":
        case_json["control_test"] = True
        case_json["instruction_override"] = "Evalúa neutralmente sin enfatizar la característica mencionada."

    return case_json


def execute_cases_on_models(
    cases: List[Case], experiment: Experiment, model_names: List[str], system_prompt: str = ""
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
                responses.append(execute_case_on_model(case, experiment, model_name, system_prompt))
            except Exception as exc:
                err_msg = str(exc)
                _log(f"[LLM ERROR] model={model_name} case={case.case_id} error={err_msg[:200]}")
                responses.append(
                    LLMResponse(
                        model_name=model_name,
                        case_id=case.case_id,
                        raw_response=json.dumps({"error": err_msg}, ensure_ascii=False),
                        error=err_msg,
                    )
                )
    return responses
