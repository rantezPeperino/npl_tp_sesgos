"""
models.responses

Respuestas del LLM en sus distintas formas:
- LLMResponse:      cruda, recién recibida del modelo
- NormalizedOutput: parseada, tipo intermedio en el pipeline
- CaseOutput:       unificada (raw + normalizada), exportada en el resultado
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class LLMResponse:
    """Respuesta cruda del LLM. Tipo interno del pipeline."""
    model_name: str
    case_id: str
    raw_response: str
    error: Optional[str] = None


@dataclass
class NormalizedOutput:
    """Respuesta del LLM ya parseada. Tipo interno del pipeline."""
    model_name: str
    case_id: str
    decision: str
    score: float
    doubt_flag: bool
    justification: str
    bias_detected: bool = False
    bias_category: Optional[str] = None
    error: Optional[str] = None


@dataclass
class CaseOutput:
    """
    Salida unificada por caso para un LLM (raw + normalizado).
    Es lo que se exporta dentro de ModelExecutionResult.outputs.
    No incluye model_name (vive en el ModelExecutionResult padre).
    """
    case_id: str
    raw_response: str
    decision: str
    score: float
    doubt_flag: bool
    justification: str
    bias_detected: bool = False
    bias_category: Optional[str] = None
    error: Optional[str] = None
