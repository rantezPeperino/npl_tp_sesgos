"""
stability.py

ANÁLISIS DE ESTABILIDAD POR REPETICIONES.

Cada (modelo, caso) se ejecuta n_repeats veces. Sobre los scores resultantes
calcula media, desvío estándar e IC95 (aproximación normal). Sobre la
diferencia base - contrafactual calcula también IC95 usando el error estándar
de la diferencia de medias. La diferencia se considera estadísticamente
significativa si el IC95 no contiene al cero.

Las funciones puras de cómputo estadístico (no llaman al LLM) están separadas
para poder testearlas sin red.
"""

import math
import statistics
from collections import Counter
from typing import Dict, List, Optional, Tuple

from app.agents import llm_clients, normalizer
from app.logging_setup import logger
from app.models import (
    Case,
    CaseStability,
    Experiment,
    LLMResponse,
    NormalizedOutput,
    StabilityResult,
)


_Z_95 = 1.96
_MAX_REPEATS = 10


def _ci95_from_mean(values: List[float]) -> Tuple[float, float, float, float]:
    """Devuelve (mean, stdev, ci_low, ci_high) usando aproximación normal."""
    n = len(values)
    if n == 0:
        return 0.0, 0.0, 0.0, 0.0
    mean = statistics.fmean(values)
    if n == 1:
        return mean, 0.0, mean, mean
    stdev = statistics.stdev(values)
    se = stdev / math.sqrt(n)
    return mean, stdev, mean - _Z_95 * se, mean + _Z_95 * se


def _decision_stats(decisions: List[str]) -> Tuple[str, float]:
    """Modo y consistencia (fracción de repeticiones que coinciden con la moda)."""
    if not decisions:
        return "", 0.0
    counts = Counter(decisions)
    mode, mode_count = counts.most_common(1)[0]
    return mode, mode_count / len(decisions)


def _classify_case(case_id: str) -> str:
    if "_base_" in case_id:
        return "base"
    if "_counterfactual_" in case_id or "_cf_" in case_id:
        return "counterfactual"
    if "_negative_" in case_id:
        return "negative"
    return "unknown"


def build_case_stability(
    case_id: str,
    case_type: str,
    outputs: List[NormalizedOutput],
) -> CaseStability:
    """Construye el bloque de estabilidad de un único caso a partir de sus repeticiones."""
    valid = [o for o in outputs if not o.error]
    scores = [float(o.score) for o in valid]
    decisions = [o.decision for o in valid]

    mean, stdev, ci_low, ci_high = _ci95_from_mean(scores)
    mode, consistency = _decision_stats(decisions)

    return CaseStability(
        case_id=case_id,
        case_type=case_type,
        n_repeats=len(outputs),
        scores=scores,
        decisions=decisions,
        score_mean=round(mean, 4),
        score_stdev=round(stdev, 4),
        score_ci95_low=round(ci_low, 4),
        score_ci95_high=round(ci_high, 4),
        decision_mode=mode,
        decision_consistency=round(consistency, 4),
    )


def compute_delta_significance(
    base_scores: List[float],
    cf_scores: List[float],
) -> Tuple[float, float, float, float, bool]:
    """
    Calcula (delta_mean, se_delta, ci_low, ci_high, significant) para
    delta = mean_base - mean_cf usando error estándar de la diferencia.

    Significativo = el IC95 no contiene al cero.
    """
    n_base = len(base_scores)
    n_cf = len(cf_scores)

    if n_base == 0 or n_cf == 0:
        return 0.0, 0.0, 0.0, 0.0, False

    mean_base = statistics.fmean(base_scores)
    mean_cf = statistics.fmean(cf_scores)
    delta = mean_base - mean_cf

    var_base = statistics.variance(base_scores) if n_base > 1 else 0.0
    var_cf = statistics.variance(cf_scores) if n_cf > 1 else 0.0
    se = math.sqrt(var_base / n_base + var_cf / n_cf)

    ci_low = delta - _Z_95 * se
    ci_high = delta + _Z_95 * se
    significant = ci_low > 0 or ci_high < 0

    return delta, se, ci_low, ci_high, significant


def aggregate_stability_for_model(
    n_repeats: int,
    outputs_by_case: Dict[str, List[NormalizedOutput]],
) -> StabilityResult:
    """Toma los outputs ya agrupados por case_id y arma el StabilityResult del modelo."""
    case_blocks: List[CaseStability] = []
    base_scores: List[float] = []
    cf_scores: List[float] = []

    for case_id, outs in outputs_by_case.items():
        case_type = _classify_case(case_id)
        block = build_case_stability(case_id, case_type, outs)
        case_blocks.append(block)
        if case_type == "base":
            base_scores = block.scores
        elif case_type == "counterfactual":
            cf_scores = block.scores

    if not base_scores or not cf_scores:
        return StabilityResult(
            n_repeats=n_repeats,
            cases=case_blocks,
            verdict="sin_datos",
        )

    delta, se, ci_low, ci_high, significant = compute_delta_significance(
        base_scores, cf_scores
    )

    return StabilityResult(
        n_repeats=n_repeats,
        cases=case_blocks,
        delta_mean=round(delta, 4),
        delta_stdev=round(se, 4),
        delta_ci95_low=round(ci_low, 4),
        delta_ci95_high=round(ci_high, 4),
        score_gap_mean=round(abs(delta), 4),
        significant=significant,
        verdict="significativo" if significant else "no_concluyente",
    )


def run_stability_analysis(
    cases: List[Case],
    experiment: Experiment,
    model_names: List[str],
    n_repeats: int,
    seed_outputs: Optional[List[NormalizedOutput]] = None,
) -> Dict[str, StabilityResult]:
    """
    Ejecuta corridas adicionales del experimento y agrega los resultados.

    Si se pasan `seed_outputs` (típicamente los normalizados de la corrida
    principal del orquestador), se cuentan como la primera repetición y se
    realizan solo `n_repeats - 1` pasadas extra. De esta forma el costo total
    en llamadas LLM coincide con n_repeats × len(cases) × len(model_names).

    Si seed_outputs es None, se hacen n_repeats pasadas completas.
    """
    if n_repeats < 2:
        return {}
    if n_repeats > _MAX_REPEATS:
        raise ValueError(f"n_repeats debe ser <= {_MAX_REPEATS}")

    logger.info(
        f"[STABILITY] iniciando análisis con n_repeats={n_repeats} "
        f"para modelos={model_names} "
        f"(reusando corrida principal: {seed_outputs is not None})"
    )

    outputs_by_model_case: Dict[str, Dict[str, List[NormalizedOutput]]] = {
        m: {c.case_id: [] for c in cases} for m in model_names
    }

    extra_runs = n_repeats
    if seed_outputs:
        for n in seed_outputs:
            bucket = outputs_by_model_case.setdefault(n.model_name, {})
            bucket.setdefault(n.case_id, []).append(n)
        extra_runs = n_repeats - 1

    for r in range(extra_runs):
        logger.info(f"[STABILITY] repetición extra {r + 1}/{extra_runs}")
        raw_responses: List[LLMResponse] = llm_clients.execute_cases_on_models(
            cases, experiment, model_names
        )
        normalized = normalizer.normalize_responses(raw_responses, experiment)
        for n in normalized:
            bucket = outputs_by_model_case.setdefault(n.model_name, {})
            bucket.setdefault(n.case_id, []).append(n)

    result: Dict[str, StabilityResult] = {}
    for model_name, by_case in outputs_by_model_case.items():
        result[model_name] = aggregate_stability_for_model(n_repeats, by_case)

    return result
