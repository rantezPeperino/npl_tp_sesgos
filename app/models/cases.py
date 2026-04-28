"""
models.cases

Caso individual del experimento (base / counterfactual / negative).
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Case:
    """
    Caso individual del experimento. Minimal: NO duplica task, constraints
    ni metadata (eso vive en el Experiment). Solo guarda lo único de cada
    caso: el prompt renderizado y el valor del atributo del sesgo.
    """
    case_id: str
    case_type: str  # base | counterfactual | negative
    attribute_value: str
    rendered_prompt: str
    based_on: Optional[str] = None
