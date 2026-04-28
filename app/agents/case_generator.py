"""
case_generator.py

AGENTE GENERADOR DE CASOS UNIVERSALES.
Produce 3 Case minimal: base, counterfactual, negative.
"""

from typing import Any, Dict, List

from app.models import Case, Experiment


def generate_cases(
    experiment: Experiment,
    prompt_text: str,
    variation: Dict[str, Any],
) -> List[Case]:
    placeholder = variation["placeholder"]
    if placeholder not in prompt_text:
        raise ValueError(
            f"El placeholder '{placeholder}' no aparece en prompt_text. "
            f"El prompt_normalizer debe inyectarlo antes de generar casos."
        )

    specs = [
        ("base", variation["base_value"]),
        ("counterfactual", variation["counterfactual_value"]),
        ("negative", variation["negative_value"]),
    ]

    cases: List[Case] = []
    base_id = None
    for case_type, value in specs:
        case_id = f"{experiment.experiment_id}_{case_type}_{_slug(str(value))}"
        if case_type == "base":
            base_id = case_id
        rendered = prompt_text.replace(placeholder, str(value))
        cases.append(
            Case(
                case_id=case_id,
                case_type=case_type,
                attribute_value=str(value),
                rendered_prompt=rendered,
                based_on=base_id if case_type != "base" else None,
            )
        )
    return cases


def _slug(value: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in value.strip().lower())[:32] or "x"
