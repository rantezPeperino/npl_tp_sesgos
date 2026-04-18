"""
metrics.py

MÓDULO DE CÁLCULO DE MÉTRICAS.

Este módulo toma las comparaciones producidas por el juez y genera métricas
agregadas que permitan cuantificar el comportamiento de cada modelo y del
experimento completo.

RESPONSABILIDAD DENTRO DEL SISTEMA:
- Calcular métricas por modelo.
- Calcular métricas globales del experimento.
- Convertir evaluaciones individuales en indicadores comparables.

QUÉ NO DEBE HACER:
- No debe interpretar respuestas crudas.
- No debe detectar pares comparables.
- No debe decidir por sí solo si existe sesgo en un par individual.
- No debe exponer HTTP.

EJEMPLOS DE MÉTRICAS POSIBLES:
- avg_score
- bias_rate
- consistency_score
- max_score_gap
- total_comparisons

QUÉ DEBERÁ HACER EL DEV:
- Definir fórmulas concretas.
- Asegurar consistencia entre métricas por modelo y resumen global.
- Decidir cómo tratar faltantes o errores parciales.
"""

from typing import Dict, List

from app.models import EvaluationComparison, MetricsResult, NormalizedOutput


def calculate_model_metrics(
    comparisons: List[EvaluationComparison],
    outputs: List[NormalizedOutput],
) -> MetricsResult:
    """
    Calcula métricas para un único modelo.

    INPUT:
    - comparisons: comparaciones generadas por judge.py para un modelo.
    - outputs: outputs normalizados de ese modelo, útiles por ejemplo para
      promedio de score.

    OUTPUT:
    - objeto MetricsResult.

    QUÉ DEBERÁ HACER EL DEV:
    - definir cómo calcular avg_score.
    - calcular bias_rate como proporción de comparaciones con sesgo detectado.
    - definir consistency_score según reglas del negocio.
    """
    raise NotImplementedError("Pendiente de implementación de métricas por modelo.")


def calculate_metrics_per_model(
    comparisons_by_model: Dict[str, List[EvaluationComparison]],
    outputs_by_model: Dict[str, List[NormalizedOutput]],
) -> Dict[str, MetricsResult]:
    """
    Calcula métricas para todos los modelos evaluados.

    OUTPUT:
    - diccionario:
      {
          "llm_a": MetricsResult(...),
          "llm_b": MetricsResult(...)
      }

    QUÉ DEBERÁ HACER EL DEV:
    - iterar por modelo.
    - llamar calculate_model_metrics() con inputs consistentes.
    """
    raise NotImplementedError("Pendiente de implementación de métricas por modelo en lote.")


def calculate_global_summary(
    comparisons_by_model: Dict[str, List[EvaluationComparison]],
    metrics_by_model: Dict[str, MetricsResult],
) -> Dict[str, float]:
    """
    Calcula un resumen global del experimento.

    EJEMPLOS DE CAMPOS POSIBLES:
    - total_models
    - total_comparisons
    - bias_detected
    - max_score_gap
    - average_bias_rate

    OUTPUT:
    - diccionario simple serializable a JSON.

    QUÉ DEBERÁ HACER EL DEV:
    - decidir qué métricas resumen forman parte del contrato final.
    - asegurar compatibilidad con la salida final del sistema.
    """
    raise NotImplementedError("Pendiente de implementación del resumen global.")