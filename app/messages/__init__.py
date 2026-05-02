"""
app.messages

Plantillas de texto, prompts y constantes léxicas usadas por los agentes.
Mantener los textos separados de la lógica facilita ajustarlos sin tocar
el pipeline.
"""

from app.messages.dimensions import (
    BIAS_PLACEHOLDER,
    DIMENSION_TEMPLATES,
    generic_template,
)
from app.messages.keywords import (
    CONFIDENCE_KEYS,
    DECISION_KEYS,
    DOUBT_KEYWORDS,
    JUSTIFICATION_KEYS,
    SCORE_KEYS,
)
from app.messages.prompts import build_prompt_for_case, inject_bias_placeholder

__all__ = [
    "BIAS_PLACEHOLDER",
    "DIMENSION_TEMPLATES",
    "generic_template",
    "CONFIDENCE_KEYS",
    "DOUBT_KEYWORDS",
    "DECISION_KEYS",
    "SCORE_KEYS",
    "JUSTIFICATION_KEYS",
    "build_prompt_for_case",
    "inject_bias_placeholder",
]
