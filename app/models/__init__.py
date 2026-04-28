"""
app.models

Domain types (dataclasses) del sistema. Re-exporta todos los tipos para
importarlos via `from app.models import X`.
"""

from app.models.experiment import (
    EvaluationConstraints,
    Experiment,
    TaskDefinition,
)
from app.models.cases import Case
from app.models.responses import (
    CaseOutput,
    LLMResponse,
    NormalizedOutput,
)
from app.models.analysis import (
    Comparison,
    ControlResult,
    ExperimentResult,
    MetricsResult,
    ModelExecutionResult,
)

__all__ = [
    "TaskDefinition",
    "EvaluationConstraints",
    "Experiment",
    "Case",
    "LLMResponse",
    "NormalizedOutput",
    "CaseOutput",
    "Comparison",
    "ControlResult",
    "MetricsResult",
    "ModelExecutionResult",
    "ExperimentResult",
]
