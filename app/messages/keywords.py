"""
messages.keywords

Listados léxicos usados por el normalizer:
- detección de duda en la justificación
- aliases de las llaves del JSON devuelto por el LLM (ES/EN)
"""

from typing import Tuple


DOUBT_KEYWORDS: Tuple[str, ...] = (
    "aunque",
    "habría",
    "dudas",
    "no estoy seguro",
    "podría",
    "quizás",
    "quizas",
    "sin embargo",
    "pero",
)


DECISION_KEYS: Tuple[str, ...] = (
    "decision",
    "decisión",
    "decisión_final",
    "respuesta",
)


SCORE_KEYS: Tuple[str, ...] = (
    "score",
    "puntaje",
    "puntuación",
    "puntuacion",
    "calificacion",
    "calificación",
)


JUSTIFICATION_KEYS: Tuple[str, ...] = (
    "justification",
    "justificación",
    "justificacion",
    "razon",
    "razón",
)
