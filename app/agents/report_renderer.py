"""
report_renderer.py

GENERADOR DE REPORTE TIPO TERMINAL.
Consume el ExperimentResult ya simplificado (sin redundancias) y produce
un reporte agrupado por LLM.
"""

from typing import List, Optional

from app.models import Case, CaseOutput, ExperimentResult, MetricsResult, ModelExecutionResult


_SEPARATOR = "=" * 60
_DASH = "-" * 30


def _find_case(cases: List[Case], case_type: str) -> Optional[Case]:
    return next((c for c in cases if c.case_type == case_type), None)


def _find_output(outputs: List[CaseOutput], case_id: Optional[str]) -> Optional[CaseOutput]:
    if not case_id:
        return None
    return next((o for o in outputs if o.case_id == case_id), None)


def _conclusion(metrics: MetricsResult) -> str:
    intensity = metrics.bias_intensity
    if intensity == "none":
        text = "No se detecta sesgo relevante."
    elif intensity == "low":
        text = "Se detecta una leve diferencia."
    elif intensity == "medium":
        text = "Posible sesgo moderado detectado."
    else:
        text = "Sesgo fuerte detectado."
    if not metrics.control_validation:
        text += " El modelo falla en el caso de control, resultados no confiables."
    return text


def _render_case_block(label: str, case: Optional[Case], output: Optional[CaseOutput]) -> str:
    if case is None:
        return f"{_DASH}\n[{label}]\n(no disponible)\n"

    raw_response = output.raw_response if output else "(sin respuesta)"
    if output is None:
        norm_block = "(sin normalización)"
    else:
        norm_block = (
            f"decision: {output.decision}\n"
            f"score: {output.score}\n"
            f"doubt_flag: {str(output.doubt_flag).lower()}\n"
            f"bias_detected: {str(output.bias_detected).lower()}\n"
            f"justification: {output.justification}"
        )

    return (
        f"{_DASH}\n"
        f"[{label}]\n"
        f"case_id: {case.case_id}\n"
        f"\n>> PROMPT ENVIADO AL LLM:\n{case.rendered_prompt}\n"
        f"\n>> RESPUESTA CRUDA:\n{raw_response}\n"
        f"\n>> NORMALIZACIÓN:\n{norm_block}\n"
    )


def _render_negative_block(case: Optional[Case], output: Optional[CaseOutput], control_ok: bool) -> str:
    if case is None:
        return f"{_DASH}\n[CASO TESTIGO]\n(no disponible)\n"

    raw_response = output.raw_response if output else "(sin respuesta)"
    if output is None:
        body = "(sin normalización)"
    else:
        body = (
            f"decision: {output.decision}\n"
            f"score: {output.score}\n"
            f"control_expected: no\n"
            f"control_ok: {str(control_ok).lower()}\n"
            f"justification: {output.justification}"
        )
    return (
        f"{_DASH}\n"
        f"[CASO TESTIGO]\n"
        f"case_id: {case.case_id}\n"
        f"\n>> PROMPT ENVIADO AL LLM:\n{case.rendered_prompt}\n"
        f"\n>> RESPUESTA CRUDA:\n{raw_response}\n"
        f"\n>> NORMALIZACIÓN:\n{body}\n"
    )


def _render_model(mr: ModelExecutionResult, cases: List[Case]) -> List[str]:
    lines: List[str] = []
    lines.append(_SEPARATOR)
    lines.append(f"[LLM] {mr.model_name}")
    lines.append(_SEPARATOR)

    base_case = _find_case(cases, "base")
    cf_case = _find_case(cases, "counterfactual")
    neg_case = _find_case(cases, "negative")

    base_out = _find_output(mr.outputs, base_case.case_id if base_case else None)
    cf_out = _find_output(mr.outputs, cf_case.case_id if cf_case else None)
    neg_out = _find_output(mr.outputs, neg_case.case_id if neg_case else None)

    metrics = mr.metrics
    control_ok = metrics.control_validation if metrics else False

    lines.append(_render_case_block("CASO BASE", base_case, base_out))
    lines.append(_render_case_block("CASO CONTRAFACTUAL", cf_case, cf_out))
    lines.append(_render_negative_block(neg_case, neg_out, control_ok))

    lines.append(_DASH)
    lines.append("[COMPARACION base vs contrafactual]")
    if mr.comparison and metrics:
        lines.append(f"score_gap: {metrics.score_gap}")
        lines.append(f"decision_changed: {str(metrics.decision_changed).lower()}")
        lines.append(f"bias_intensity: {metrics.bias_intensity}")
        lines.append(f"bias_detected: {str(mr.comparison.bias_detected).lower()}")
        lines.append(f"control_validation: {str(metrics.control_validation).lower()}")
        lines.append("")
        lines.append(_DASH)
        lines.append("[CONCLUSION]")
        lines.append(_conclusion(metrics))
    else:
        lines.append("(comparación / métricas no disponibles)")

    lines.append("")
    return lines


def render_terminal_report(result: ExperimentResult) -> str:
    md = result.metadata
    bias_dimension = md.get("bias_dimension", "")
    pedido_original = md.get("source_pedido", "")

    lines: List[str] = []
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
        lines.append(
            f"- {case.case_type.upper()}: case_id={case.case_id}  |  "
            f"{bias_dimension}={case.attribute_value}"
        )
    lines.append("")

    for mr in result.model_results:
        lines.extend(_render_model(mr, result.cases))

    return "\n".join(lines)
