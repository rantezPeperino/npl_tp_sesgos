"""
models.experiment

Configuración del experimento: tarea, restricciones de evaluación y metadata.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class TaskDefinition:
    role_to_evaluate: str
    question: str
    required_output_type: str


@dataclass
class EvaluationConstraints:
    score_scale_min: int
    score_scale_max: int
    decision_options: List[str] = field(default_factory=list)


@dataclass
class Experiment:
    experiment_id: str
    industry: str
    topic: str
    bias_dimension: str
    task: TaskDefinition
    evaluation_constraints: EvaluationConstraints
