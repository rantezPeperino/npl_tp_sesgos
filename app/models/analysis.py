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
class CaseStability:
    """Estadísticos de un caso ejecutado n_repeats veces para un mismo modelo."""
    case_id: str
    case_type: str  # base | counterfactual | negative
    n_repeats: int
    scores: List[float]
    decisions: List[str]
    score_mean: float
    score_stdev: float
    score_ci95_low: float
    score_ci95_high: float
    decision_mode: str
    decision_consistency: float  # fracción de repeticiones que comparten la decisión modal


@dataclass
class StabilityResult:
    """
    Resultado del análisis de estabilidad por modelo.

    Si el IC95 de delta NO contiene al cero, la diferencia entre base y
    contrafactual se considera estadísticamente significativa.
    """
    n_repeats: int
    cases: List[CaseStability] = field(default_factory=list)
    delta_mean: float = 0.0           # mean_base - mean_cf (signed)
    delta_stdev: float = 0.0          # SE de la diferencia
    delta_ci95_low: float = 0.0
    delta_ci95_high: float = 0.0
    score_gap_mean: float = 0.0       # |delta_mean|
    significant: bool = False         # IC95 no contiene 0
    verdict: str = "no_concluyente"   # significativo | no_concluyente | sin_datos


@dataclass
class ModelExecutionResult:
    model_name: str
    outputs: List[CaseOutput] = field(default_factory=list)
    comparison: Optional[Comparison] = None
    metrics: Optional[MetricsResult] = None
    mitigation: Optional[Dict[str, Any]] = None
    stability: Optional[StabilityResult] = None


@dataclass
class ExperimentResult:
    experiment_id: str
    metadata: Dict[str, Any]
    cases: List[Case] = field(default_factory=list)
    model_results: List[ModelExecutionResult] = field(default_factory=list)
    global_summary: Dict[str, Any] = field(default_factory=dict)
