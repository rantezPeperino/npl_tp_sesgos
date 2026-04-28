"""
prompt_normalizer.py

AGENTE NORMALIZADOR DE PROMPT DE ENTRADA.
Convierte el texto plano + sesgo_medir en un JSON universal normalizado
que el orquestador usa para armar el experimento.
"""

import re
import uuid
from typing import Any, Dict

from app import config
from app.messages import (
    BIAS_PLACEHOLDER,
    DIMENSION_TEMPLATES,
    generic_template,
    inject_bias_placeholder,
)


def normalize_prompt(pedido: str, sesgo_medir: str) -> Dict[str, Any]:
    if not pedido or not pedido.strip():
        raise ValueError("El campo 'pedido' no puede estar vacío.")
    if not sesgo_medir or not sesgo_medir.strip():
        raise ValueError("El campo 'sesgo_medir' no puede estar vacío.")

    dimension = sesgo_medir.strip().lower().replace(" ", "_")
    template = DIMENSION_TEMPLATES.get(dimension, generic_template(dimension))

    pedido_clean = pedido.strip()
    prompt_text = inject_bias_placeholder(pedido_clean)
    question = _extract_question(pedido_clean)

    experiment_id = f"exp_{dimension}_{uuid.uuid4().hex[:8]}"

    return {
        "experiment_id": experiment_id,
        "industry": "generico",
        "topic": "generico",
        "bias_dimension": dimension,
        "prompt_text": prompt_text,
        "variation": {
            "attribute": dimension,
            "placeholder": BIAS_PLACEHOLDER,
            "base_value": template["base"],
            "counterfactual_value": template["counterfactual"],
            "negative_value": template["negative"],
        },
        "task": {
            "role_to_evaluate": "evaluador experto",
            "question": question,
            "required_output_type": "decision_cuantificable",
        },
        "evaluation_constraints": {
            "score_scale_min": config.SCORE_SCALE_MIN,
            "score_scale_max": config.SCORE_SCALE_MAX,
            "decision_options": ["si", "no"],
        },
        "metadata": {
            "language": config.LANGUAGE,
            "temperature": config.TEMPERATURE,
            "prompt_version": config.PROMPT_VERSION,
            "source_pedido": pedido_clean,
        },
    }


def _extract_question(pedido: str) -> str:
    questions = re.findall(r"[¿?][^¿?]*\?", pedido)
    if questions:
        return questions[-1].strip().lstrip("¿").strip()
    return "¿Cuál es tu evaluación del caso presentado?"
