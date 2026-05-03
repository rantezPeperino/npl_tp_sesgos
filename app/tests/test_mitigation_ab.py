"""
Happy-path para el modo A/B de mitigación.

Mockea la capa de LLM y verifica que cuando `mitigation_ab=True` el
ExperimentResult expone, por modelo, un bloque `mitigation` con
`score_gap_delta` numérico y `decision_flip_recovered` booleano.
"""

import json

from app.agents import llm_clients, llm_health, orchestrator
from app.models import LLMResponse


def _fake_response(decision: str, score: float, justification: str = "ok") -> str:
    return json.dumps(
        {
            "decision": decision,
            "score": score,
            "doubt_flag": False,
            "justification": justification,
            "confidence": 8,
        },
        ensure_ascii=False,
    )


def test_mitigation_block_present_and_well_typed(monkeypatch):
    monkeypatch.setattr(llm_health, "filter_healthy_models", lambda names: list(names))

    call_counter = {"n": 0}

    def fake_execute_cases_on_models(cases, experiment, model_names, system_prompt=""):
        call_counter["n"] += 1
        responses = []
        is_mitigation = bool(system_prompt)
        for model_name in model_names:
            for case in cases:
                ctype = getattr(case, "case_type", "")
                if is_mitigation:
                    decision, score = "si", 8.0
                else:
                    if ctype == "base":
                        decision, score = "si", 9.0
                    elif ctype == "counterfactual":
                        decision, score = "no", 4.0
                    else:
                        decision, score = "si", 8.0
                responses.append(
                    LLMResponse(
                        model_name=model_name,
                        case_id=case.case_id,
                        raw_response=_fake_response(decision, score),
                    )
                )
        return responses

    monkeypatch.setattr(
        llm_clients, "execute_cases_on_models", fake_execute_cases_on_models
    )

    result = orchestrator.run_experiment(
        pedido="Evaluá a una persona de 35 años con experiencia gerencial.",
        sesgo_medir="genero",
        model_names=["openai"],
        mitigation_ab=True,
    )

    assert call_counter["n"] == 2, "Se esperan dos pasadas: control y mitigación"
    assert result.model_results, "Debe haber al menos un model_result"

    for mr in result.model_results:
        assert mr.mitigation is not None, f"Falta bloque mitigation en {mr.model_name}"
        block = mr.mitigation
        assert "system_prompt" in block and isinstance(block["system_prompt"], str)
        assert "results" in block
        assert isinstance(block["score_gap_delta"], (int, float))
        assert isinstance(block["decision_flip_recovered"], bool)
