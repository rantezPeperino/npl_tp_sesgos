"""
llm_health.py

HEALTH CHECK DE LOS LLM ANTES DE CORRER EL EXPERIMENTO.
Para cada model_name solicitado:
- verifica que el SDK / servicio del proveedor esté disponible
- verifica que la API key esté configurada (si aplica)
- hace un ping mínimo para validar conectividad

Si un modelo falla, emite un warning por stderr y se lo descarta.
Si todos fallan, devuelve la lista vacía y el orquestador aborta.

Para agregar un proveedor: ver app/agents/providers.py.
"""

import sys
from typing import List, Tuple

from app import config
from app.agents import providers


def _print_warn(msg: str) -> None:
    print(f"[WARN] {msg}", file=sys.stderr, flush=True)


def _check_openai() -> Tuple[bool, str]:
    if "openai" not in config.ENABLED_PROVIDERS:
        return False, "openai no está en ENABLED_PROVIDERS"
    if not config.OPENAI_API_KEY:
        return False, "OPENAI_API_KEY no configurada"
    try:
        from openai import OpenAI  # type: ignore
    except ImportError as exc:
        return False, f"SDK no instalado ({exc}). Instalá: pip install openai"
    try:
        client = OpenAI(api_key=config.OPENAI_API_KEY)
        list(client.models.list())[:1]
        return True, "ok"
    except Exception as exc:
        return False, f"falla de conexión con OpenAI: {exc}"


def _check_gemini() -> Tuple[bool, str]:
    if "gemini" not in config.ENABLED_PROVIDERS:
        return False, "gemini no está en ENABLED_PROVIDERS"
    if not config.GEMINI_API_KEY:
        return False, "GEMINI_API_KEY no configurada"
    try:
        import google.generativeai as genai  # type: ignore
    except ImportError as exc:
        return False, f"SDK no instalado ({exc}). Instalá: pip install google-generativeai"
    try:
        genai.configure(api_key=config.GEMINI_API_KEY)
        next(iter(genai.list_models()))
        return True, "ok"
    except Exception as exc:
        return False, f"falla de conexión con Gemini: {exc}"


def _check_anthropic() -> Tuple[bool, str]:
    if "anthropic" not in config.ENABLED_PROVIDERS:
        return False, "anthropic no está en ENABLED_PROVIDERS"
    if not config.ANTHROPIC_API_KEY:
        return False, "ANTHROPIC_API_KEY no configurada"
    try:
        import anthropic  # type: ignore
    except ImportError as exc:
        return False, f"SDK no instalado ({exc}). Instalá: pip install anthropic"
    try:
        client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        client.messages.create(
            model=config.ANTHROPIC_MODEL,
            max_tokens=1,
            messages=[{"role": "user", "content": "ping"}],
        )
        return True, "ok"
    except Exception as exc:
        return False, f"falla de conexión con Anthropic: {exc}"


def _check_openrouter() -> Tuple[bool, str]:
    if "openrouter" not in config.ENABLED_PROVIDERS:
        return False, "openrouter no está en ENABLED_PROVIDERS"
    if not config.OPENROUTER_API_KEY:
        return False, "OPENROUTER_API_KEY no configurada"
    try:
        from openai import OpenAI  # type: ignore
    except ImportError as exc:
        return False, f"SDK no instalado ({exc}). Instalá: pip install openai"
    try:
        client = OpenAI(
            api_key=config.OPENROUTER_API_KEY,
            base_url=config.OPENROUTER_BASE_URL,
        )
        list(client.models.list())[:1]
        return True, "ok"
    except Exception as exc:
        return False, f"falla de conexión con OpenRouter: {exc}"


def _check_ollama() -> Tuple[bool, str]:
    if "ollama" not in config.ENABLED_PROVIDERS:
        return False, "ollama no está en ENABLED_PROVIDERS"
    import json
    import urllib.request
    base = config.OLLAMA_BASE_URL.rstrip("/")
    try:
        with urllib.request.urlopen(f"{base}/api/tags", timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as exc:
        return False, (
            f"Ollama no responde en {base} ({exc}). "
            f"Iniciá el servicio con: ollama serve"
        )
    available = [m.get("name", "") for m in data.get("models", [])]
    target = config.OLLAMA_MODEL
    if not any(m == target or m.startswith(f"{target}:") for m in available):
        return False, (
            f"el modelo '{target}' no está descargado en Ollama "
            f"(disponibles: {available or 'ninguno'}). "
            f"Descargalo con: ollama pull {target}"
        )
    return True, "ok"


_PROVIDER_CHECKS = {
    "openai": _check_openai,
    "gemini": _check_gemini,
    "ollama": _check_ollama,
    "anthropic": _check_anthropic,
    "openrouter": _check_openrouter,
}


def filter_healthy_models(model_names: List[str]) -> List[str]:
    """
    Devuelve solo los modelos que pasaron el health check.
    Imprime warnings por los descartados.
    """
    healthy: List[str] = []
    cache: dict = {}

    for model_name in model_names:
        try:
            provider = providers.resolve_provider(model_name)
        except ValueError as exc:
            _print_warn(f"{exc}. Modelo '{model_name}' descartado.")
            continue

        if provider not in cache:
            check = _PROVIDER_CHECKS.get(provider)
            cache[provider] = check() if check else (False, "proveedor sin health check")

        ok, detail = cache[provider]
        if ok:
            healthy.append(model_name)
            print(f"[OK] {model_name} ({provider}) listo.", flush=True)
        else:
            _print_warn(f"{model_name} ({provider}) no disponible: {detail}. Se omite.")

    return healthy
