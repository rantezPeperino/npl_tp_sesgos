"""
config.py

Carga de configuración desde variables de entorno (.env).
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

# API keys
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")

# Modelos por proveedor
OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4.5-preview")
GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-opus-4-7")
OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3")
OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OPENROUTER_MODEL: str = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
OPENROUTER_BASE_URL: str = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

# Proveedores habilitados (separados por coma): ollama, openai, gemini
_raw_providers = os.getenv("ENABLED_PROVIDERS", "")
ENABLED_PROVIDERS: set = {p.strip() for p in _raw_providers.split(",") if p.strip()}

# Default model_names cuando el cliente no envía ninguno
_raw_default_models = os.getenv("DEFAULT_MODELS", "ollama")
DEFAULT_MODELS: list = [m.strip() for m in _raw_default_models.split(",") if m.strip()]

# Metadatos por defecto del experimento
LANGUAGE: str = os.getenv("LANGUAGE", "es")
TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.2"))
PROMPT_VERSION: str = os.getenv("PROMPT_VERSION", "v1")

SCORE_SCALE_MIN: int = int(os.getenv("SCORE_SCALE_MIN", "0"))
SCORE_SCALE_MAX: int = int(os.getenv("SCORE_SCALE_MAX", "10"))
