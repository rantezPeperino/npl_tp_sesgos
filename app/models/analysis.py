"""
models.analysis

Resultados del análisis: comparación del control, métricas y resultado final
del experimento.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.models.cases import Case
from app.models.responses import CaseOutput


@dataclass
class Comparison:
    """Única comparación principal: base vs counterfactual."""
    score_gap: float
    decision_changed: bool
    bias_detected: bool
    bias_category: Optional[str] = None


@dataclass
class ControlResult:
    """Output del agente de control para un LLM."""
    comparison: Comparison
    control_validation: bool


@dataclass
class MetricsResult:
    avg_score: float
    bias_rate: float
    consistency_score: float
    score_gap: float
    decision_changed: bool
    control_validation: bool
    bias_intensity: str  # none | low | medium | high


@dataclass
class ModelExecutionResult:
    model_name: str
    outputs: List[CaseOutput] = field(default_factory=list)
    comparison: Optional[Comparison] = None
    metrics: Optional[MetricsResult] = None


@dataclass
class ExperimentResult:
    experiment_id: str
    metadata: Dict[str, Any]
    cases: List[Case] = field(default_factory=list)
    model_results: List[ModelExecutionResult] = field(default_factory=list)
    global_summary: Dict[str, Any] = field(default_factory=dict)
