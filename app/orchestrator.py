"""
orchestrator.py

COORDINADOR PRINCIPAL DEL PIPELINE END-TO-END.
Dev 1: build_experiment → generate_cases → execute_on_models → save_raw → result parcial.
"""

from typing import Any, Dict, List

from app import case_generator, judge, llm_clients, metrics, normalizer, repository
from app.models import (
    EvaluationComparison,
    Experiment,
    EvaluationConstraints,
    ExperimentResult,
    LLMResponse,
    MetricsResult,
    ModelExecutionResult,
    NormalizedOutput,
    TaskDefinition,
)


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


def run_experiment(payload: Dict[str, Any], model_names: List[str]) -> ExperimentResult:
    experiment = build_experiment_from_payload(payload)

    repository.save_input_payload(experiment.experiment_id, payload)

    cases = case_generator.generate_cases(experiment)

    raw_responses = llm_clients.execute_cases_on_models(cases, experiment, model_names)

    repository.save_raw_responses(experiment.experiment_id, raw_responses)

    # Dev 2: normalize → evaluate → metrics
    normalized_outputs = normalizer.normalize_responses(raw_responses, experiment)
    repository.save_normalized_outputs(experiment.experiment_id, normalized_outputs)

    comparisons_by_model = judge.evaluate_outputs(normalized_outputs, experiment)
    from dataclasses import asdict as _asdict
    repository.save_evaluation_payload(
        experiment.experiment_id,
        {model: [_asdict(c) for c in comps] for model, comps in comparisons_by_model.items()},
    )

    outputs_by_model = {
        model_name: [o for o in normalized_outputs if o.model_name == model_name]
        for model_name in {o.model_name for o in normalized_outputs}
    }
    metrics_by_model = metrics.calculate_metrics_per_model(comparisons_by_model, outputs_by_model)
    global_summary = metrics.calculate_global_summary(comparisons_by_model, metrics_by_model)

    result = assemble_experiment_result(
        experiment=experiment,
        cases=cases,
        raw_responses=raw_responses,
        normalized_outputs=normalized_outputs,
        comparisons_by_model=comparisons_by_model,
        metrics_by_model=metrics_by_model,
        global_summary=global_summary,
    )

    repository.save_final_result(result)
    return result


def assemble_experiment_result(
    experiment: Experiment,
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
        },
        cases=cases,
        model_results=model_results,
        global_summary=global_summary,
        payload={},
    )
