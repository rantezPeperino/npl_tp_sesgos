"""
orchestrator.py

COORDINADOR PRINCIPAL DEL PIPELINE END-TO-END.

Flujo:
1. health check (aborta si no hay LLMs)
2. prompt_normalizer → JSON universal
3. case_generator → 3 casos (base, counterfactual, negative)
4. llm_clients → ejecución independiente por caso
5. normalizer → respuestas estructuradas
6. control → comparación principal + validación de testigo
7. propagación de bias_detected a outputs base/cf
8. metrics → cuantificación
9. ensamblado del ExperimentResult sin redundancias
10. report_renderer (print) + persistencia en memoria
"""

from dataclasses import asdict
from typing import Any, Dict, List

from app.agents import (
    case_generator,
    control,
    llm_clients,
    llm_health,
    metrics,
    normalizer,
    prompt_normalizer,
    report_renderer,
)
from app.models import (
    Case,
    CaseOutput,
    ControlResult,
    EvaluationConstraints,
    Experiment,
    ExperimentResult,
    LLMResponse,
    MetricsResult,
    ModelExecutionResult,
    NormalizedOutput,
    TaskDefinition,
)


_EXPERIMENTS: Dict[str, ExperimentResult] = {}


def build_experiment_from_payload(payload: Dict[str, Any]) -> Experiment:
    task_data = payload["task"]
    constraints_data = payload["evaluation_constraints"]
    return Experiment(
        experiment_id=payload["experiment_id"],
        industry=payload["industry"],
        topic=payload["topic"],
        bias_dimension=payload["bias_dimension"],
        task=TaskDefinition(
            role_to_evaluate=task_data["role_to_evaluate"],
            question=task_data["question"],
            required_output_type=task_data["required_output_type"],
        ),
        evaluation_constraints=EvaluationConstraints(
            score_scale_min=constraints_data["score_scale_min"],
            score_scale_max=constraints_data["score_scale_max"],
            decision_options=constraints_data.get("decision_options", []),
        ),
    )


def run_experiment(pedido: str, sesgo_medir: str, model_names: List[str]) -> ExperimentResult:
    healthy_models = llm_health.filter_healthy_models(model_names)
    if not healthy_models:
        raise ValueError(
            "Ningún LLM está disponible. Se aborta la prueba. "
            "Revisá las API keys y la conectividad antes de reintentar."
        )

    payload = prompt_normalizer.normalize_prompt(pedido, sesgo_medir)
    experiment = build_experiment_from_payload(payload)

    cases = case_generator.generate_cases(
        experiment,
        prompt_text=payload["prompt_text"],
        variation=payload["variation"],
    )

    raw_responses = llm_clients.execute_cases_on_models(cases, experiment, healthy_models)
    normalized_outputs = normalizer.normalize_responses(raw_responses, experiment)

    control_by_model = control.evaluate_outputs(normalized_outputs, experiment)

    _propagate_bias(normalized_outputs, control_by_model, experiment.bias_dimension)

    outputs_by_model: Dict[str, List[NormalizedOutput]] = {}
    for o in normalized_outputs:
        outputs_by_model.setdefault(o.model_name, []).append(o)

    metrics_by_model = metrics.calculate_metrics_per_model(control_by_model, outputs_by_model)
    global_summary = metrics.calculate_global_summary(control_by_model, metrics_by_model)

    result = _assemble_result(
        experiment=experiment,
        cases=cases,
        raw_responses=raw_responses,
        normalized_outputs=normalized_outputs,
        control_by_model=control_by_model,
        metrics_by_model=metrics_by_model,
        global_summary=global_summary,
        source_pedido=payload["metadata"].get("source_pedido", ""),
        language=payload["metadata"].get("language"),
        temperature=payload["metadata"].get("temperature"),
        prompt_version=payload["metadata"].get("prompt_version"),
    )

    _EXPERIMENTS[result.experiment_id] = result

    print(report_renderer.render_terminal_report(result))

    return result


def get_experiment_result(experiment_id: str) -> Dict[str, Any]:
    if experiment_id not in _EXPERIMENTS:
        raise KeyError(experiment_id)
    return asdict(_EXPERIMENTS[experiment_id])


def list_experiment_ids() -> List[str]:
    return list(_EXPERIMENTS.keys())


def _propagate_bias(
    outputs: List[NormalizedOutput],
    control_by_model: Dict[str, ControlResult],
    bias_dimension: str,
) -> None:
    for model_name, ctrl in control_by_model.items():
        if not ctrl.comparison.bias_detected:
            continue
        for o in outputs:
            if o.model_name != model_name:
                continue
            if "_base_" in o.case_id or "_counterfactual_" in o.case_id:
                o.bias_detected = True
                o.bias_category = bias_dimension


def _build_case_outputs(
    model_name: str,
    cases: List[Case],
    raw_responses: List[LLMResponse],
    normalized: List[NormalizedOutput],
) -> List[CaseOutput]:
    raws = {r.case_id: r.raw_response for r in raw_responses if r.model_name == model_name}
    norms = {n.case_id: n for n in normalized if n.model_name == model_name}
    outputs: List[CaseOutput] = []
    for case in cases:
        n = norms.get(case.case_id)
        outputs.append(
            CaseOutput(
                case_id=case.case_id,
                raw_response=raws.get(case.case_id, ""),
                decision=n.decision if n else "",
                score=n.score if n else 0.0,
                doubt_flag=n.doubt_flag if n else False,
                justification=n.justification if n else "",
                bias_detected=n.bias_detected if n else False,
                bias_category=n.bias_category if n else None,
            )
        )
    return outputs


def _assemble_result(
    *,
    experiment: Experiment,
    cases: List[Case],
    raw_responses: List[LLMResponse],
    normalized_outputs: List[NormalizedOutput],
    control_by_model: Dict[str, ControlResult],
    metrics_by_model: Dict[str, MetricsResult],
    global_summary: Dict[str, Any],
    source_pedido: str,
    language: Any,
    temperature: Any,
    prompt_version: Any,
) -> ExperimentResult:
    seen: Dict[str, None] = {}
    for r in raw_responses:
        seen[r.model_name] = None
    unique_model_names = list(seen)

    model_results: List[ModelExecutionResult] = []
    for model_name in unique_model_names:
        outputs = _build_case_outputs(model_name, cases, raw_responses, normalized_outputs)
        ctrl = control_by_model.get(model_name)
        model_results.append(
            ModelExecutionResult(
                model_name=model_name,
                outputs=outputs,
                comparison=ctrl.comparison if ctrl else None,
                metrics=metrics_by_model.get(model_name),
            )
        )

    return ExperimentResult(
        experiment_id=experiment.experiment_id,
        metadata={
            "industry": experiment.industry,
            "topic": experiment.topic,
            "bias_dimension": experiment.bias_dimension,
            "source_pedido": source_pedido,
            "language": language,
            "temperature": temperature,
            "prompt_version": prompt_version,
        },
        cases=cases,
        model_results=model_results,
        global_summary=global_summary,
    )
