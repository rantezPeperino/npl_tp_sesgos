"""
providers.py

REGISTRO CENTRAL DE PROVEEDORES LLM.
Punto único para mapear model_name (lo que llega por API) → provider real.

Para AGREGAR un nuevo proveedor:
  1. Sumá los aliases en PROVIDER_ALIASES.
  2. Implementá la función de call en app/llm_clients.py y registrala en _PROVIDERS_CALL.
  3. Implementá el health check en app/llm_health.py y registralo en _PROVIDER_CHECKS.
  4. Sumá las env vars necesarias a app/config.py.

Para HABILITAR / DESHABILITAR un proveedor:
  Editá ENABLED_PROVIDERS en .env (lista separada por comas).

Para SELECCIONAR el modelo a usar dentro del proveedor:
  Editá la variable de entorno correspondiente (OPENAI_MODEL, GEMINI_MODEL,
  OLLAMA_MODEL).
"""

from typing import Dict


PROVIDER_ALIASES: Dict[str, str] = {
    "ollama": "ollama",
    "llama": "ollama",
    "llama3": "ollama",
    "local": "ollama",
    "openai": "openai",
    "chatgpt": "openai",
    "gpt": "openai",
    "gemini": "gemini",
    "google": "gemini",
    "claude": "anthropic",
    "anthropic": "anthropic",
}


def resolve_provider(model_name: str) -> str:
    key = model_name.lower().split("-")[0]
    if key not in PROVIDER_ALIASES:
        raise ValueError(
            f"Modelo no soportado: '{model_name}'. "
            f"Aliases válidos: {sorted(PROVIDER_ALIASES.keys())}"
        )
    return PROVIDER_ALIASES[key]
