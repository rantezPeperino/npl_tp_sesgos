"""
orchestrator.py

COORDINADOR PRINCIPAL DEL PIPELINE END-TO-END.

Flujo:
1. Recibe { pedido, sesgo_medir } desde la API.
2. prompt_normalizer convierte el texto plano en un JSON universal.
3. build_experiment → generate_cases (base, counterfactual, negative).
4. Ejecuta en los LLMs habilitados.
5. normalizer → control → metrics.
6. Ensambla el ExperimentResult y lo guarda en memoria para el reporte final.
"""

from dataclasses import asdict
from typing import Any, Dict, List

from app import case_generator, control, llm_clients, llm_health, metrics, normalizer, prompt_normalizer, report_renderer
from app.models import (
    EvaluationComparison,
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

    normalized_payload = prompt_normalizer.normalize_prompt(pedido, sesgo_medir)

    experiment = build_experiment_from_payload(normalized_payload)

    cases = case_generator.generate_cases(
        experiment,
        prompt_text=normalized_payload["prompt_text"],
        variation=normalized_payload["variation"],
        metadata=normalized_payload["metadata"],
    )

    raw_responses = llm_clients.execute_cases_on_models(cases, experiment, healthy_models)

    normalized_outputs = normalizer.normalize_responses(raw_responses, experiment)

    comparisons_by_model = control.evaluate_outputs(normalized_outputs, experiment)

    _propagate_bias_to_outputs(normalized_outputs, comparisons_by_model, experiment.bias_dimension)

    outputs_by_model = {
        model_name: [o for o in normalized_outputs if o.model_name == model_name]
        for model_name in {o.model_name for o in normalized_outputs}
    }
    metrics_by_model = metrics.calculate_metrics_per_model(comparisons_by_model, outputs_by_model)
    global_summary = metrics.calculate_global_summary(comparisons_by_model, metrics_by_model)

    result = assemble_experiment_result(
        experiment=experiment,
        normalized_payload=normalized_payload,
        cases=cases,
        raw_responses=raw_responses,
        normalized_outputs=normalized_outputs,
        comparisons_by_model=comparisons_by_model,
        metrics_by_model=metrics_by_model,
        global_summary=global_summary,
    )

    _EXPERIMENTS[result.experiment_id] = result

    print(report_renderer.render_terminal_report(result))

    return result


def _propagate_bias_to_outputs(
    outputs: List[NormalizedOutput],
    comparisons_by_model: Dict[str, List[EvaluationComparison]],
    bias_dimension: str,
) -> None:
    for model_name, comparisons in comparisons_by_model.items():
        main = next((c for c in comparisons if c.pair_type == "base_vs_counterfactual"), None)
        if main is None or not main.bias_detected:
            continue
        flagged_ids = {main.case_base, main.case_counterfactual}
        for o in outputs:
            if o.model_name == model_name and o.case_id in flagged_ids:
                o.bias_detected = True
                o.bias_category = bias_dimension


def get_experiment_result(experiment_id: str) -> Dict[str, Any]:
    if experiment_id not in _EXPERIMENTS:
        raise KeyError(experiment_id)
    return asdict(_EXPERIMENTS[experiment_id])


def list_experiment_ids() -> List[str]:
    return list(_EXPERIMENTS.keys())


def assemble_experiment_result(
    experiment: Experiment,
    normalized_payload: Dict[str, Any],
    cases: List[Any],
    raw_responses: List[LLMResponse],
    normalized_outputs: List[NormalizedOutput],
    comparisons_by_model: Dict[str, List[EvaluationComparison]],
    metrics_by_model: Dict[str, MetricsResult],
    global_summary: Dict[str, Any],
) -> ExperimentResult:
    seen: Dict[str, None] = {}
    for r in raw_responses:
        seen[r.model_name] = None
    unique_model_names = list(seen)

    model_results = [
        ModelExecutionResult(
            model_name=model_name,
            raw_responses=[r for r in raw_responses if r.model_name == model_name],
            normalized_outputs=[o for o in normalized_outputs if o.model_name == model_name],
            comparisons=comparisons_by_model.get(model_name, []),
            metrics=metrics_by_model.get(model_name),
        )
        for model_name in unique_model_names
    ]

    return ExperimentResult(
        experiment_id=experiment.experiment_id,
        metadata={
            "industry": experiment.industry,
            "topic": experiment.topic,
            "bias_dimension": experiment.bias_dimension,
            "source_pedido": normalized_payload["metadata"].get("source_pedido", ""),
            "language": normalized_payload["metadata"].get("language"),
            "temperature": normalized_payload["metadata"].get("temperature"),
            "prompt_version": normalized_payload["metadata"].get("prompt_version"),
        },
        cases=cases,
        model_results=model_results,
        global_summary=global_summary,
        payload=normalized_payload,
    )
