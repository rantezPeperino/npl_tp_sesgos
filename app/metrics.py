"""
metrics.py

MÓDULO DE CÁLCULO DE MÉTRICAS.
"""

from typing import Any, Dict, List

from app.models import EvaluationComparison, MetricsResult, NormalizedOutput


def calculate_model_metrics(
    comparisons: List[EvaluationComparison],
    outputs: List[NormalizedOutput],
) -> MetricsResult:
    avg_score = sum(o.score for o in outputs) / len(outputs) if outputs else 0.0
    if comparisons:
        bias_rate = sum(1 for c in comparisons if c.bias_detected) / len(comparisons)
    else:
        bias_rate = 0.0
    consistency_score = 1.0 - bias_rate
    return MetricsResult(avg_score=avg_score, bias_rate=bias_rate, consistency_score=consistency_score)


def calculate_metrics_per_model(
    comparisons_by_model: Dict[str, List[EvaluationComparison]],
    outputs_by_model: Dict[str, List[NormalizedOutput]],
) -> Dict[str, MetricsResult]:
    return {
        model_name: calculate_model_metrics(
            comparisons_by_model.get(model_name, []),
            outputs_by_model.get(model_name, []),
        )
        for model_name in set(list(comparisons_by_model) + list(outputs_by_model))
    }


def calculate_global_summary(
    comparisons_by_model: Dict[str, List[EvaluationComparison]],
    metrics_by_model: Dict[str, MetricsResult],
) -> Dict[str, Any]:
    all_comparisons = [c for comps in comparisons_by_model.values() for c in comps]
    total_comparisons = len(all_comparisons)
    global_bias_rate = (
        sum(1 for c in all_comparisons if c.bias_detected) / total_comparisons
        if total_comparisons else 0.0
    )
    max_score_gap = max((c.score_gap for c in all_comparisons), default=0.0)
    return {
        "total_models": len(metrics_by_model),
        "total_comparisons": total_comparisons,
        "global_bias_rate": round(global_bias_rate, 4),
        "max_score_gap": round(max_score_gap, 4),
        "bias_detected_global": global_bias_rate > 0,
    }
