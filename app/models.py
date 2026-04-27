"""
models.py

DEFINICIÓN DE ESTRUCTURAS DE DATOS DEL SISTEMA.

Este módulo centraliza los modelos usados en todo el pipeline.
La intención es que todos los demás módulos trabajen sobre contratos
claros, consistentes y reutilizables.

MODELOS ESPERADOS:
- Experiment
- TaskDefinition
- EvaluationConstraints
- Case
- LLMResponse
- NormalizedOutput
- EvaluationComparison
- MetricsResult
- ModelExecutionResult
- ExperimentResult

QUÉ DEBERÁ HACER EL DEV:
- Elegir estrategia de modelado: dataclasses, pydantic models o clases simples.
- Definir campos obligatorios y opcionales.
- Asegurar serialización/deserialización sencilla a JSON.
- Mantener alineación con el contrato de entrada y salida de la API.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class TaskDefinition:
    """
    Representa la tarea específica a evaluar dentro del experimento.

    EJEMPLOS:
    - rol a evaluar
    - pregunta que se enviará al modelo
    - tipo de salida esperada

    QUÉ DEBERÁ HACER EL DEV:
    - Validar qué campos son obligatorios.
    - Mantener compatibilidad con el JSON de entrada de la API.
    """
    role_to_evaluate: str
    question: str
    required_output_type: str


@dataclass
class EvaluationConstraints:
    """
    Representa restricciones o reglas del experimento.

    EJEMPLOS:
    - score mínimo y máximo
    - decisiones permitidas
    - futuras reglas adicionales

    QUÉ DEBERÁ HACER EL DEV:
    - Usar este modelo para parametrizar normalización y evaluación.
    """
    score_scale_min: int
    score_scale_max: int
    decision_options: List[str] = field(default_factory=list)


@dataclass
class Experiment:
    """
    Representa la configuración general de un experimento completo.

    CONTIENE:
    - metadata del experimento
    - dimensión de sesgo a estudiar
    - definición de tarea
    - restricciones de evaluación

    QUÉ DEBERÁ HACER EL DEV:
    - Mapear el JSON de entrada a esta estructura.
    """
    experiment_id: str
    industry: str
    topic: str
    bias_dimension: str
    task: TaskDefinition
    evaluation_constraints: EvaluationConstraints


@dataclass
class Case:
    """
    Representa un caso individual generado para el experimento.

    TIPOS TÍPICOS:
    - base
    - counterfactual
    - control (si se incorpora en el futuro)

    QUÉ DEBERÁ HACER EL DEV:
    - Definir la estructura interna del input del caso.
    - Poder relacionar contrafactuales con el caso base.
    """
    case_id: str
    case_type: str
    input_payload: Dict[str, Any]
    based_on: Optional[str] = None


@dataclass
class LLMResponse:
    """
    Representa la respuesta cruda devuelta por un LLM evaluado.

    CONTIENE:
    - nombre del modelo
    - identificador del caso
    - respuesta textual original

    QUÉ DEBERÁ HACER EL DEV:
    - Usar este contrato como output de llm_clients.py.
    """
    model_name: str
    case_id: str
    raw_response: str


@dataclass
class NormalizedOutput:
    """
    Representa la versión estructurada de una respuesta cruda.

    CAMPOS TÍPICOS:
    - decision
    - score
    - doubt_flag
    - justification
    - bias_detected
    - bias_category

    QUÉ DEBERÁ HACER EL DEV:
    - Alinear este modelo con lo que produzca normalizer.py.
    """
    model_name: str
    case_id: str
    decision: str
    score: float
    doubt_flag: bool
    justification: str
    bias_detected: bool
    bias_category: Optional[str] = None


@dataclass
class EvaluationComparison:
    """
    Representa una comparación entre dos casos del experimento.
    Los pares posibles son: base_vs_counterfactual, base_vs_negative,
    counterfactual_vs_negative.
    """
    case_base: str
    case_counterfactual: str
    score_gap: float
    decision_change: bool
    bias_detected: bool
    bias_category: Optional[str] = None
    pair_type: str = "base_vs_counterfactual"
    control_validation: Optional[bool] = None


@dataclass
class MetricsResult:
    """
    Representa métricas agregadas calculadas para un modelo o experimento.

    EJEMPLOS:
    - promedio de score
    - tasa de sesgo
    - consistencia

    QUÉ DEBERÁ HACER EL DEV:
    - Expandir esta estructura según las métricas definidas por negocio.
    """
    avg_score: float
    bias_rate: float
    consistency_score: float
    score_gap_base_vs_counterfactual: float = 0.0
    decision_changed: bool = False
    control_validation: bool = True
    bias_intensity: str = "none"


@dataclass
class ModelExecutionResult:
    """
    Representa todo el resultado asociado a un único modelo evaluado.

    CONTIENE:
    - nombre del modelo
    - respuestas crudas del modelo
    - outputs normalizados
    - comparaciones del agente de control
    - métricas calculadas para ese modelo

    QUÉ DEBERÁ HACER EL DEV:
    - Usar esta estructura para consolidar resultados por modelo antes
      de construir el resultado final del experimento.
    """
    model_name: str
    raw_responses: List[LLMResponse] = field(default_factory=list)
    normalized_outputs: List[NormalizedOutput] = field(default_factory=list)
    comparisons: List[EvaluationComparison] = field(default_factory=list)
    metrics: Optional[MetricsResult] = None


@dataclass
class ExperimentResult:
    """
    Representa el output final completo del sistema.

    DEBERÍA CONTENER:
    - metadata
    - casos generados
    - resultados por modelo
    - resumen global
    - payload final opcionalmente ya ensamblado

    QUÉ DEBERÁ HACER EL DEV:
    - Alinear este modelo con la salida final de la API.
    - Decidir si payload se arma siempre o se genera al serializar.
    """
    experiment_id: str
    metadata: Dict[str, Any]
    cases: List[Case] = field(default_factory=list)
    model_results: List[ModelExecutionResult] = field(default_factory=list)
    global_summary: Dict[str, Any] = field(default_factory=dict)
    payload: Dict[str, Any] = field(default_factory=dict)