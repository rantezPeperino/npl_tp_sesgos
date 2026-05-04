"""
llm_health.py

HEALTH CHECK DE MODELOS ESPECÍFICOS.
Para cada model_id solicitado:
- valida que el proveedor sea reconocido
- verifica que el SDK / servicio esté disponible
- verifica que la API key esté configurada (si aplica)
- hace un ping mínimo para validar conectividad

Estructura de respuesta: {"local": [...], "remote": {"openai": [...], ...}}
Cada modelo incluye: id, provider, healthy, detail
"""

import json
import subprocess
import sys
import urllib.request
from typing import Any, Dict, List, Tuple

from app import config
from app.agents import providers


def _print_warn(msg: str) -> None:
    print(f"[WARN] {msg}", file=sys.stderr, flush=True)


def _check_openai(model_id: str) -> Tuple[bool, str]:
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
        return False, f"falla de conexión: {str(exc)[:100]}"


def _check_gemini(model_id: str) -> Tuple[bool, str]:
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
        return False, f"falla de conexión: {str(exc)[:100]}"


def _check_anthropic(model_id: str) -> Tuple[bool, str]:
    if not config.ANTHROPIC_API_KEY:
        return False, "ANTHROPIC_API_KEY no configurada"
    try:
        import anthropic  # type: ignore
    except ImportError as exc:
        return False, f"SDK no instalado ({exc}). Instalá: pip install anthropic"
    try:
        client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        client.messages.create(
            model=model_id,
            max_tokens=1,
            messages=[{"role": "user", "content": "ping"}],
        )
        return True, "ok"
    except Exception as exc:
        return False, f"falla de conexión: {str(exc)[:100]}"


def _check_openrouter(model_id: str) -> Tuple[bool, str]:
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
        return False, f"falla de conexión: {str(exc)[:100]}"


def _check_ollama(model_id: str) -> Tuple[bool, str]:
    # Verificar que Ollama esté respondiendo
    base = config.OLLAMA_BASE_URL.rstrip("/")
    try:
        with urllib.request.urlopen(f"{base}/api/tags", timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as exc:
        return False, (
            f"Ollama no responde en {base}. "
            f"Iniciá con: ollama serve"
        )

    # Verificar que el modelo esté descargado
    available = [m.get("name", "") for m in data.get("models", [])]
    if not any(m == model_id or m.startswith(f"{model_id}:") for m in available):
        return False, f"modelo '{model_id}' no descargado"

    # Verificar que el modelo esté CORRIENDO (via ollama ps)
    try:
        result = subprocess.run(
            ["ollama", "ps"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            return False, "ollama ps fallo"

        # Parsear output: primera línea es header, resto son modelos
        lines = result.stdout.strip().split("\n")
        if len(lines) <= 1:
            # Solo header o vacío → ningún modelo corriendo
            return False, "modelo no está corriendo"

        # Extraer nombres de modelos en ejecución (primer campo de cada línea)
        running = []
        for line in lines[1:]:
            parts = line.split()
            if parts:
                running.append(parts[0])

        # Verificar si nuestro model_id está en la lista de corriendo
        if model_id in running or any(m.startswith(f"{model_id}:") for m in running):
            return True, "corriendo"
        else:
            return False, "modelo no está corriendo"

    except subprocess.TimeoutExpired:
        return False, "ollama ps timeout"
    except FileNotFoundError:
        return False, "ollama no instalado"
    except Exception as exc:
        return False, f"error al verificar: {str(exc)[:50]}"


_PROVIDER_CHECKS = {
    "openai": _check_openai,
    "gemini": _check_gemini,
    "ollama": _check_ollama,
    "anthropic": _check_anthropic,
    "openrouter": _check_openrouter,
}


def get_models_health() -> Dict[str, Any]:
    """
    Devuelve el health status de todos los modelos configurados.
    Estructura:
    {
      "local": [
        {"id": "llama3.3:70b", "provider": "ollama", "healthy": true, "detail": "ok"},
        ...
      ],
      "remote": {
        "openai": [
          {"id": "gpt-4o-mini", "healthy": false, "detail": "OPENAI_API_KEY no configurada"},
          ...
        ],
        ...
      }
    }
    """
    result: Dict[str, Any] = {"local": [], "remote": {}}

    # Health check para modelos locales
    for model_id in config.LOCAL_MODELS:
        ok, detail = _check_ollama(model_id)
        result["local"].append({
            "id": model_id,
            "provider": "ollama",
            "healthy": ok,
            "detail": detail,
        })

    # Health check para modelos remotos por proveedor
    for model_id in config.REMOTE_MODELS_OPENAI:
        ok, detail = _check_openai(model_id)
        if "openai" not in result["remote"]:
            result["remote"]["openai"] = []
        result["remote"]["openai"].append({
            "id": model_id,
            "healthy": ok,
            "detail": detail,
        })

    for model_id in config.REMOTE_MODELS_ANTHROPIC:
        ok, detail = _check_anthropic(model_id)
        if "anthropic" not in result["remote"]:
            result["remote"]["anthropic"] = []
        result["remote"]["anthropic"].append({
            "id": model_id,
            "healthy": ok,
            "detail": detail,
        })

    for model_id in config.REMOTE_MODELS_GEMINI:
        ok, detail = _check_gemini(model_id)
        if "gemini" not in result["remote"]:
            result["remote"]["gemini"] = []
        result["remote"]["gemini"].append({
            "id": model_id,
            "healthy": ok,
            "detail": detail,
        })

    for model_id in config.REMOTE_MODELS_OPENROUTER:
        ok, detail = _check_openrouter(model_id)
        if "openrouter" not in result["remote"]:
            result["remote"]["openrouter"] = []
        result["remote"]["openrouter"].append({
            "id": model_id,
            "healthy": ok,
            "detail": detail,
        })

    return result


def filter_healthy_models(model_names: List[str]) -> List[str]:
    """
    Devuelve solo los modelos que pasaron el health check.
    Imprime warnings por los descartados.
    """
    healthy: List[str] = []
    models_health = get_models_health()

    # Aplanar todos los modelos con su health status
    all_models_map = {}
    for model_info in models_health["local"]:
        all_models_map[model_info["id"]] = model_info

    for provider_models in models_health["remote"].values():
        for model_info in provider_models:
            all_models_map[model_info["id"]] = model_info

    for model_name in model_names:
        if model_name not in all_models_map:
            _print_warn(f"Modelo '{model_name}' no encontrado en configuración. Se omite.")
            continue

        model_info = all_models_map[model_name]
        if model_info["healthy"]:
            healthy.append(model_name)
            print(f"[OK] {model_name} listo.", flush=True)
        else:
            _print_warn(f"{model_name} no disponible: {model_info['detail']}. Se omite.")

    return healthy
