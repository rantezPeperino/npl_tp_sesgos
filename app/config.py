"""
config.py

Carga de configuración desde variables de entorno (.env en raíz).
Modelos dinámicos por tipo: LOCAL_MODELS (Ollama) y REMOTE_MODELS_OPENAI/ANTHROPIC/GEMINI/OPENROUTER.
"""

import os
from pathlib import Path
from typing import Dict, List

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

# API keys
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")

# Modelos locales (implícitamente Ollama)
_raw_local = os.getenv("LOCAL_MODELS", "")
LOCAL_MODELS: List[str] = [m.strip() for m in _raw_local.split(",") if m.strip()]

# Modelos remotos por proveedor
_raw_remote_openai = os.getenv("REMOTE_MODELS_OPENAI", "")
REMOTE_MODELS_OPENAI: List[str] = [m.strip() for m in _raw_remote_openai.split(",") if m.strip()]

_raw_remote_anthropic = os.getenv("REMOTE_MODELS_ANTHROPIC", "")
REMOTE_MODELS_ANTHROPIC: List[str] = [m.strip() for m in _raw_remote_anthropic.split(",") if m.strip()]

_raw_remote_gemini = os.getenv("REMOTE_MODELS_GEMINI", "")
REMOTE_MODELS_GEMINI: List[str] = [m.strip() for m in _raw_remote_gemini.split(",") if m.strip()]

_raw_remote_openrouter = os.getenv("REMOTE_MODELS_OPENROUTER", "")
REMOTE_MODELS_OPENROUTER: List[str] = [m.strip() for m in _raw_remote_openrouter.split(",") if m.strip()]

_raw_remote_deepseek = os.getenv("REMOTE_MODELS_DEEPSEEK", "")
REMOTE_MODELS_DEEPSEEK: List[str] = [m.strip() for m in _raw_remote_deepseek.split(",") if m.strip()]

# Mapeo dinámico de modelo_id → proveedor
def get_provider_for_model(model_id: str) -> str:
    """Devuelve el proveedor ('ollama', 'openai', etc.) para un model_id dado."""
    if model_id in LOCAL_MODELS:
        return "ollama"
    if model_id in REMOTE_MODELS_OPENAI:
        return "openai"
    if model_id in REMOTE_MODELS_ANTHROPIC:
        return "anthropic"
    if model_id in REMOTE_MODELS_GEMINI:
        return "gemini"
    if model_id in REMOTE_MODELS_OPENROUTER:
        return "openrouter"
    if model_id in REMOTE_MODELS_DEEPSEEK:
        return "deepseek"
    # Fallback: si contiene '/', probablemente sea openrouter
    if "/" in model_id:
        return "openrouter"
    raise ValueError(f"Modelo '{model_id}' no encontrado en configuración")


# Infraestructura
OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OPENROUTER_BASE_URL: str = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

# Metadatos por defecto del experimento
LANGUAGE: str = os.getenv("LANGUAGE", "es")
TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.2"))
PROMPT_VERSION: str = os.getenv("PROMPT_VERSION", "v1")

SCORE_SCALE_MIN: int = int(os.getenv("SCORE_SCALE_MIN", "0"))
SCORE_SCALE_MAX: int = int(os.getenv("SCORE_SCALE_MAX", "10"))
