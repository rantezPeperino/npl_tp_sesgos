"""
normalizer.py

AGENTE NORMALIZADOR DE RESPUESTAS DE LLM.
"""

import json
import re
from typing import List

from app.messages import (
    CONFIDENCE_KEYS,
    DECISION_KEYS,
    DOUBT_KEYWORDS,
    JUSTIFICATION_KEYS,
    SCORE_KEYS,
)
from app.models import Experiment, LLMResponse, NormalizedOutput


def _pick_first(parsed: dict, keys) -> object:
    for k in keys:
        if k in parsed and parsed[k] is not None:
            return parsed[k]
    return None


def _extract_json_block(raw: str) -> str:
    start = raw.find("{")
    end = raw.rfind("}")
    if start != -1 and end != -1 and end > start:
        return raw[start:end + 1]
    return raw


def normalize_response(response: LLMResponse, experiment: Experiment) -> NormalizedOutput:
    constraints = experiment.evaluation_constraints

    if response.error:
        return NormalizedOutput(
            model_name=response.model_name,
            case_id=response.case_id,
            decision="error",
            score=0.0,
            doubt_flag=True,
            justification=f"LLM call failed: {response.error}",
            bias_detected=False,
            bias_category=None,
            error=response.error,
        )

    raw = response.raw_response.strip()

    decision = "si"
    score = 5.0
    confidence = 5.0
    justification = ""
    doubt_flag = False

    parsed = None
    try:
        parsed = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        try:
            parsed = json.loads(_extract_json_block(raw))
        except (json.JSONDecodeError, ValueError):
            text_lower = raw.lower()
            if any(opt in text_lower for opt in [o.lower() for o in constraints.decision_options if o.lower() == "no"]):
                decision = "no"
            score_match = re.search(r"\b(\d+(?:\.\d+)?)\b", raw)
            if score_match:
                score = float(score_match.group(1))
            justification = raw[:200]
            doubt_flag = True

    if isinstance(parsed, dict):
        d = _pick_first(parsed, DECISION_KEYS)
        if d is not None:
            decision = str(d).lower().strip()
        s = _pick_first(parsed, SCORE_KEYS)
        if s is not None:
            try:
                score = float(s)
            except (TypeError, ValueError):
                pass
        j = _pick_first(parsed, JUSTIFICATION_KEYS)
        if j is not None:
            justification = str(j)
        cf = _pick_first(parsed, CONFIDENCE_KEYS)
        if cf is not None:
            try:
                confidence = max(1.0, min(10.0, float(cf)))
            except (TypeError, ValueError):
                pass

    # Clamp score to valid range
    score_min = constraints.score_scale_min
    score_max = constraints.score_scale_max
    if score < score_min or score > score_max:
        score = max(score_min, min(score_max, score))
        doubt_flag = True

    # Detect doubt keywords in justification
    if any(kw in justification.lower() for kw in DOUBT_KEYWORDS):
        doubt_flag = True

    return NormalizedOutput(
        model_name=response.model_name,
        case_id=response.case_id,
        decision=decision,
        score=score,
        doubt_flag=doubt_flag,
        justification=justification,
        confidence=confidence,
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
