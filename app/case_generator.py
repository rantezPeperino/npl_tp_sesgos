"""
case_generator.py

AGENTE GENERADOR DE CASOS UNIVERSALES.
Entrada: texto plano (prompt_text) + variation con placeholder y 3 valores.
Salida: 3 casos (base, counterfactual, negative) con texto renderizado.
Agnóstico del rubro: sirve para RRHH, salud, justicia, finanzas, educación, etc.
"""

from typing import Any, Dict, List, Optional

from app.models import Case, Experiment


def generate_cases(
    experiment: Experiment,
    prompt_text: str,
    variation: Dict[str, Any],
    metadata: Optional[Dict[str, Any]] = None,
) -> List[Case]:
    placeholder = variation["placeholder"]
    if placeholder not in prompt_text:
        raise ValueError(
            f"El placeholder '{placeholder}' no aparece en prompt_text. "
            f"Insertá el marcador en el texto para que se pueda generar el contrafactual."
        )

    attribute = variation["attribute"]

    specs = [
        ("base", variation["base_value"]),
        ("counterfactual", variation["counterfactual_value"]),
        ("negative", variation["negative_value"]),
    ]

    cases: List[Case] = []
    base_internal_id: Optional[str] = None
    for case_type, value in specs:
        internal_id = f"{experiment.experiment_id}_{case_type}_{_slug(str(value))}"
        if case_type == "base":
            base_internal_id = internal_id
        rendered = prompt_text.replace(placeholder, str(value))
        payload = _build_payload(
            experiment=experiment,
            case_type=case_type,
            internal_id=internal_id,
            rendered_prompt=rendered,
            attribute=attribute,
            value=value,
            placeholder=placeholder,
            metadata=metadata,
        )
        cases.append(
            Case(
                case_id=internal_id,
                case_type=case_type,
                input_payload=payload,
                based_on=base_internal_id if case_type != "base" else None,
            )
        )
    return cases


def _build_payload(
    experiment: Experiment,
    case_type: str,
    internal_id: str,
    rendered_prompt: str,
    attribute: str,
    value: Any,
    placeholder: str,
    metadata: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    return {
        "experiment_id": experiment.experiment_id,
        "case_id": internal_id,
        "case_type": case_type,
        "industry": experiment.industry,
        "topic": experiment.topic,
        "bias_dimension": experiment.bias_dimension,
        "input_case": {
            "entity_id": internal_id,
            "attributes": {
                experiment.bias_dimension: value,
            },
        },
        "rendered_prompt": rendered_prompt,
        "variation": {
            "attribute": attribute,
            "placeholder": placeholder,
            "value": value,
        },
        "task": {
            "role_to_evaluate": experiment.task.role_to_evaluate,
            "question": experiment.task.question,
            "required_output_type": experiment.task.required_output_type,
        },
        "evaluation_constraints": {
            "score_scale_min": experiment.evaluation_constraints.score_scale_min,
            "score_scale_max": experiment.evaluation_constraints.score_scale_max,
            "decision_options": experiment.evaluation_constraints.decision_options,
        },
        "metadata": metadata or {"language": "es", "temperature": 0.2, "prompt_version": "v1"},
    }


def _slug(value: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in value.strip().lower())[:32] or "x"
