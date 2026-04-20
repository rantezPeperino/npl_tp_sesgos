"""
normalizer.py

AGENTE NORMALIZADOR DE RESPUESTAS DE LLM.
"""

import json
import re
from typing import List

from app.models import Experiment, LLMResponse, NormalizedOutput

_DOUBT_KEYWORDS = ["aunque", "habría", "dudas", "no estoy seguro", "podría", "quizás", "quizas", "sin embargo", "pero"]


def normalize_response(response: LLMResponse, experiment: Experiment) -> NormalizedOutput:
    constraints = experiment.evaluation_constraints
    raw = response.raw_response.strip()

    decision = "si"
    score = 5.0
    justification = ""
    doubt_flag = False

    parsed = None
    try:
        parsed = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        # Fallback: extract from text
        text_lower = raw.lower()
        if any(opt in text_lower for opt in [o.lower() for o in constraints.decision_options if o.lower() == "no"]):
            decision = "no"
        score_match = re.search(r"\b(\d+(?:\.\d+)?)\b", raw)
        if score_match:
            score = float(score_match.group(1))
        justification = raw[:200]
        doubt_flag = True

    if parsed is not None:
        decision = str(parsed.get("decision", "si")).lower().strip()
        score = float(parsed.get("score", 5.0))
        justification = str(parsed.get("justification", ""))

    # Clamp score to valid range
    score_min = constraints.score_scale_min
    score_max = constraints.score_scale_max
    if score < score_min or score > score_max:
        score = max(score_min, min(score_max, score))
        doubt_flag = True

    # Detect doubt keywords in justification
    if any(kw in justification.lower() for kw in _DOUBT_KEYWORDS):
        doubt_flag = True

    return NormalizedOutput(
        model_name=response.model_name,
        case_id=response.case_id,
        decision=decision,
        score=score,
        doubt_flag=doubt_flag,
        justification=justification,
        bias_detected=False,
        bias_category=None,
    )


def normalize_responses(responses: List[LLMResponse], experiment: Experiment) -> List[NormalizedOutput]:
    results = []
    for response in responses:
        try:
            results.append(normalize_response(response, experiment))
        except Exception:
            results.append(NormalizedOutput(
                model_name=response.model_name,
                case_id=response.case_id,
                decision="si",
                score=5.0,
                doubt_flag=True,
                justification="normalization_error",
                bias_detected=False,
                bias_category=None,
            ))
    return results


def validate_normalized_output(output: NormalizedOutput, experiment: Experiment) -> bool:
    constraints = experiment.evaluation_constraints
    if not output.decision:
        return False
    if constraints.decision_options and output.decision not in constraints.decision_options:
        return False
    if output.score < constraints.score_scale_min or output.score > constraints.score_scale_max:
        return False
    return True
