"""
orchestrator.py

COORDINADOR PRINCIPAL DEL PIPELINE END-TO-END.
Dev 1: build_experiment → generate_cases → execute_on_models → save_raw → result parcial.
"""

from typing import Any, Dict, List

from app import case_generator, llm_clients, repository
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

    result = assemble_experiment_result(
        experiment=experiment,
        cases=cases,
        raw_responses=raw_responses,
        normalized_outputs=[],
        comparisons_by_model={},
        metrics_by_model={},
        global_summary={"status": "dev1_complete", "pending": "normalization, evaluation, metrics (Dev 2)"},
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
