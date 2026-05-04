"""
providers.py

RESOLUCIÓN DINÁMICA DE PROVEEDORES.
Mapea model_id (como llega por API) → provider real consultando la config.

Los modelos se declaran en .env con:
  LOCAL_MODELS=llama3.3:70b,deepseek-r1:32b,...
  REMOTE_MODELS_OPENAI=gpt-4o-mini,gpt-4-turbo,...
  REMOTE_MODELS_ANTHROPIC=...
  REMOTE_MODELS_GEMINI=...
  REMOTE_MODELS_OPENROUTER=...

resolve_provider(model_id) busca en las listas de config y devuelve el provider.
"""


def resolve_provider(model_id: str) -> str:
    """
    Resuelve el proveedor para un model_id concreto.
    Consulta las listas declaradas en config.
    """
    from app import config
    return config.get_provider_for_model(model_id)


def extract_subkey(model_name: str) -> str:
    """
    Para sintaxis "provider:subkey", devuelve la parte después del ':'.
    Si no hay ':', devuelve string vacío.
    Ej: "openrouter:openai/gpt-4o-mini" -> "openai/gpt-4o-mini"
    """
    if ":" in model_name:
        return model_name.split(":", 1)[1].strip()
    return ""
