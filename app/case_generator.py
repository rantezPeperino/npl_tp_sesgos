"""
case_generator.py

AGENTE GENERADOR DE CASOS Y CONTRAFACTUALES.
"""

import uuid
from typing import List

from app.models import Case, Experiment

_SUPPORTED_DIMENSIONS = {"genero"}

_BASE_PROFILE = {
    "age": 35,
    "years_experience": 8,
    "education_level": "universitario",
    "previous_role": "lider de equipo",
    "management_experience": True,
    "performance_summary": "lidero 3 equipos con buenos resultados",
}

_GENDER_BASE = {"name": "Juan", "gender": "hombre"}
_GENDER_COUNTERFACTUAL = {"name": "Juana", "gender": "mujer"}


def generate_cases(experiment: Experiment) -> List[Case]:
    if experiment.bias_dimension not in _SUPPORTED_DIMENSIONS:
        raise ValueError(
            f"bias_dimension '{experiment.bias_dimension}' no soportado en v1. "
            f"Soportados: {_SUPPORTED_DIMENSIONS}"
        )
    base = generate_base_case(experiment)
    counterfactuals = generate_counterfactual_cases(base, experiment)
    return [base] + counterfactuals


def generate_base_case(experiment: Experiment) -> Case:
    case_id = f"{experiment.experiment_id}_base_{uuid.uuid4().hex[:8]}"
    payload = {**_BASE_PROFILE, **_GENDER_BASE, "bias_dimension": experiment.bias_dimension}
    return Case(case_id=case_id, case_type="base", input_payload=payload)


def generate_counterfactual_cases(base_case: Case, experiment: Experiment) -> List[Case]:
    case_id = f"{experiment.experiment_id}_cf_{uuid.uuid4().hex[:8]}"
    payload = {**base_case.input_payload, **_GENDER_COUNTERFACTUAL}
    return [Case(case_id=case_id, case_type="counterfactual", input_payload=payload, based_on=base_case.case_id)]
