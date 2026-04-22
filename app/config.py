"""
config.py

Carga de configuración desde variables de entorno (.env).
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4.5-preview")

_raw_providers = os.getenv("ENABLED_PROVIDERS", "")
ENABLED_PROVIDERS: set = {p.strip() for p in _raw_providers.split(",") if p.strip()}

LANGUAGE: str = os.getenv("LANGUAGE", "es")
TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.2"))
PROMPT_VERSION: str = os.getenv("PROMPT_VERSION", "v1")

SCORE_SCALE_MIN: int = int(os.getenv("SCORE_SCALE_MIN", "0"))
SCORE_SCALE_MAX: int = int(os.getenv("SCORE_SCALE_MAX", "10"))
