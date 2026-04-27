"""
report_renderer.py

GENERADOR DE REPORTE TIPO TERMINAL.
El reporte se agrupa por LLM y contiene, para cada modelo:
- prompt inicial del experimento (el pedido original)
- los 3 casos generados por el orquestador (rendered prompts enviados al LLM)
- las respuestas crudas del LLM por caso
- la normalización (decision, score, doubt_flag, bias_detected)
- la comparación (score_gap, decision_changed, bias_intensity)
- la conclusión
"""

from typing import List, Optional

from app.models import (
    Case,
    EvaluationComparison,
    ExperimentResult,
    LLMResponse,
    MetricsResult,
    NormalizedOutput,
)


_SEPARATOR = "=" * 60
_SUBSEP = "-" * 60
_DASH = "-" * 30


def _classify(case_id: str) -> str:
    if "_base_" in case_id:
        return "base"
    if "_counterfactual_" in case_id or "_cf_" in case_id:
        return "counterfactual"
    if "_negative_" in case_id:
        return "negative"
    return "unknown"


def _find_case(cases: List[Case], role: str) -> Optional[Case]:
    return next((c for c in cases if _classify(c.case_id) == role), None)


def _find_response(responses: List[LLMResponse], case_id: str) -> Optional[LLMResponse]:
    return next((r for r in responses if r.case_id == case_id), None)


def _find_normalized(outputs: List[NormalizedOutput], case_id: str) -> Optional[NormalizedOutput]:
    return next((o for o in outputs if o.case_id == case_id), None)


def _find_main_comparison(comparisons: List[EvaluationComparison]) -> Optional[EvaluationComparison]:
    return next((c for c in comparisons if c.pair_type == "base_vs_counterfactual"), None)


def _conclusion(metrics: MetricsResult) -> str:
    intensity = metrics.bias_intensity
    if intensity == "none":
        base = "No se detecta sesgo relevante."
    elif intensity == "low":
        base = "Se detecta una leve diferencia."
    elif intensity == "medium":
        base = "Se detecta un posible sesgo moderado."
    else:
        base = "Se detecta un sesgo fuerte."
    if not metrics.control_validation:
        base += " El modelo falla en el caso de control, resultados no confiables."
    return base


def _render_case_block(
    label: str,
    case: Optional[Case],
    response: Optional[LLMResponse],
    normalized: Optional[NormalizedOutput],
) -> str:
    if case is None:
        return f"{_DASH}\n[{label}]\n(no disponible)\n"

    rendered_prompt = case.input_payload.get("rendered_prompt", "")
    raw_response = response.raw_response if response else "(sin respuesta)"

    if normalized is None:
        norm_block = "decision: -\nscore: -\ndoubt_flag: -\nbias_detected: -\njustification: -"
    else:
        norm_block = (
            f"decision: {normalized.decision}\n"
            f"score: {normalized.score}\n"
            f"doubt_flag: {str(normalized.doubt_flag).lower()}\n"
            f"bias_detected: {str(normalized.bias_detected).lower()}\n"
            f"justification: {normalized.justification}"
        )

    return (
        f"{_DASH}\n"
        f"[{label}]\n"
        f"case_id: {case.case_id}\n"
        f"\n>> PROMPT ENVIADO AL LLM:\n{rendered_prompt}\n"
        f"\n>> RESPUESTA CRUDA:\n{raw_response}\n"
        f"\n>> NORMALIZACIÓN:\n{norm_block}\n"
    )


def render_terminal_report(result: ExperimentResult) -> str:
    lines: List[str] = []
    md = result.metadata
    pedido_original = md.get("source_pedido", "")
    bias_dimension = md.get("bias_dimension", "")

    lines.append(_SEPARATOR)
    lines.append("[EXPERIMENTO]")
    lines.append(f"id: {result.experiment_id}")
    lines.append(f"rubro: {md.get('industry', '')}")
    lines.append(f"tema: {md.get('topic', '')}")
    lines.append(f"sesgo_medido: {bias_dimension}")
    lines.append(_SEPARATOR)
    lines.append("")
    lines.append("[PROMPT INICIAL DEL EXPERIMENTO]")
    lines.append(pedido_original)
    lines.append("")
    lines.append("[CASOS GENERADOS POR EL ORQUESTADOR]")
    for case in result.cases:
        role = _classify(case.case_id).upper()
        attribute_value = case.input_payload.get("input_case", {}).get("attributes", {}).get(bias_dimension, "")
        lines.append(f"- {role}: case_id={case.case_id}  |  {bias_dimension}={attribute_value}")
    lines.append("")

    for mr in result.model_results:
        lines.append(_SEPARATOR)
        lines.append(f"[LLM] {mr.model_name}")
        lines.append(_SEPARATOR)

        base_case = _find_case(result.cases, "base")
        cf_case = _find_case(result.cases, "counterfactual")
        neg_case = _find_case(result.cases, "negative")

        base_resp = _find_response(mr.raw_responses, base_case.case_id) if base_case else None
        cf_resp = _find_response(mr.raw_responses, cf_case.case_id) if cf_case else None
        neg_resp = _find_response(mr.raw_responses, neg_case.case_id) if neg_case else None

        base_norm = _find_normalized(mr.normalized_outputs, base_case.case_id) if base_case else None
        cf_norm = _find_normalized(mr.normalized_outputs, cf_case.case_id) if cf_case else None
        neg_norm = _find_normalized(mr.normalized_outputs, neg_case.case_id) if neg_case else None

        lines.append(_render_case_block("CASO BASE", base_case, base_resp, base_norm))
        lines.append(_render_case_block("CASO CONTRAFACTUAL", cf_case, cf_resp, cf_norm))
        lines.append(_render_case_block("CASO TESTIGO", neg_case, neg_resp, neg_norm))

        main = _find_main_comparison(mr.comparisons)
        control_ok = main.control_validation if main else None

        lines.append(_DASH)
        lines.append("[COMPARACION base vs contrafactual]")
        if mr.metrics is not None:
            lines.append(f"score_gap: {mr.metrics.score_gap_base_vs_counterfactual}")
            lines.append(f"decision_changed: {str(mr.metrics.decision_changed).lower()}")
            lines.append(f"bias_intensity: {mr.metrics.bias_intensity}")
            lines.append(f"bias_detected: {str(mr.metrics.bias_rate > 0).lower()}")
            lines.append(f"control_validation: {str(bool(control_ok)).lower()}")
            lines.append("")
            lines.append(_DASH)
            lines.append("[CONCLUSION]")
            lines.append(_conclusion(mr.metrics))
        else:
            lines.append("(métricas no disponibles)")
        lines.append("")

    return "\n".join(lines)
