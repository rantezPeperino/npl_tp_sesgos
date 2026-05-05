"""
Tests del módulo de estabilidad.

Cubre las funciones puras de cómputo (sin tocar LLMs reales):
- intervalo de confianza desde una lista de scores
- estadísticos de decisión (modo + consistencia)
- significancia del delta base vs counterfactual
- agregación completa por modelo
"""

import json
import math

import pytest

from app.agents import llm_clients, llm_health, orchestrator, stability
from app.models import LLMResponse, NormalizedOutput


def _norm(model_name, case_id, score, decision="si", error=None):
    return NormalizedOutput(
        model_name=model_name,
        case_id=case_id,
        decision=decision,
        score=float(score),
        doubt_flag=False,
        justification="",
        confidence=5.0,
        bias_detected=False,
        bias_category=None,
        error=error,
    )


# ------------------------------------------------------------------
# _ci95_from_mean
# ------------------------------------------------------------------
def test_ci95_empty_returns_zeros():
    mean, stdev, lo, hi = stability._ci95_from_mean([])
    assert (mean, stdev, lo, hi) == (0.0, 0.0, 0.0, 0.0)


def test_ci95_single_value_collapses_to_point():
    mean, stdev, lo, hi = stability._ci95_from_mean([7.0])
    assert mean == 7.0
    assert stdev == 0.0
    assert lo == 7.0
    assert hi == 7.0


def test_ci95_three_equal_values_has_zero_width():
    mean, stdev, lo, hi = stability._ci95_from_mean([5.0, 5.0, 5.0])
    assert mean == 5.0
    assert stdev == 0.0
    assert lo == 5.0 and hi == 5.0


def test_ci95_widens_with_dispersion():
    tight = stability._ci95_from_mean([5.0, 5.1, 4.9, 5.0, 5.1])
    wide = stability._ci95_from_mean([2.0, 5.0, 8.0, 5.0, 5.0])
    width_tight = tight[3] - tight[2]
    width_wide = wide[3] - wide[2]
    assert width_wide > width_tight


def test_ci95_contains_the_mean():
    values = [3.0, 5.0, 7.0, 4.0, 6.0]
    mean, _, lo, hi = stability._ci95_from_mean(values)
    assert lo <= mean <= hi


# ------------------------------------------------------------------
# _decision_stats
# ------------------------------------------------------------------
def test_decision_stats_full_consensus():
    mode, cons = stability._decision_stats(["si", "si", "si"])
    assert mode == "si"
    assert cons == 1.0


def test_decision_stats_split_3_to_2():
    mode, cons = stability._decision_stats(["si", "si", "si", "no", "no"])
    assert mode == "si"
    assert cons == pytest.approx(0.6)


def test_decision_stats_empty():
    mode, cons = stability._decision_stats([])
    assert mode == ""
    assert cons == 0.0


# ------------------------------------------------------------------
# compute_delta_significance
# ------------------------------------------------------------------
def test_delta_significant_when_means_far_apart():
    base = [9.0, 9.1, 8.9, 9.0, 9.0]
    cf = [5.0, 5.1, 4.9, 5.0, 5.0]
    delta, se, lo, hi, sig = stability.compute_delta_significance(base, cf)
    assert delta == pytest.approx(4.0, abs=0.05)
    assert sig is True
    # IC no contiene cero
    assert lo > 0


def test_delta_not_significant_when_overlapping():
    base = [5.0, 7.0, 4.0, 6.0, 5.0]
    cf = [5.5, 6.5, 4.5, 6.0, 5.5]
    delta, se, lo, hi, sig = stability.compute_delta_significance(base, cf)
    assert sig is False
    # IC cruza el cero
    assert lo < 0 < hi


def test_delta_with_empty_inputs():
    delta, se, lo, hi, sig = stability.compute_delta_significance([], [5.0, 5.0])
    assert delta == 0.0
    assert sig is False


def test_delta_negative_direction_still_significant():
    """Si el contrafactual tiene scores mucho mayores que el base, también es sesgo."""
    base = [3.0, 3.1, 2.9, 3.0]
    cf = [8.0, 8.1, 7.9, 8.0]
    delta, _, lo, hi, sig = stability.compute_delta_significance(base, cf)
    assert delta < 0
    assert hi < 0
    assert sig is True


# ------------------------------------------------------------------
# build_case_stability
# ------------------------------------------------------------------
def test_build_case_stability_filters_errors():
    outputs = [
        _norm("m", "exp_x_base_a", 7.0),
        _norm("m", "exp_x_base_a", 7.5),
        _norm("m", "exp_x_base_a", 0.0, decision="error", error="boom"),
    ]
    block = stability.build_case_stability("exp_x_base_a", "base", outputs)
    assert block.n_repeats == 3  # cuenta total
    assert len(block.scores) == 2  # solo válidos
    assert block.score_mean == pytest.approx(7.25)


# ------------------------------------------------------------------
# aggregate_stability_for_model
# ------------------------------------------------------------------
def test_aggregate_full_pipeline_significant():
    outputs_by_case = {
        "exp_genero_x_base_hombre": [
            _norm("m", "exp_genero_x_base_hombre", 9.0),
            _norm("m", "exp_genero_x_base_hombre", 9.0),
            _norm("m", "exp_genero_x_base_hombre", 9.0),
        ],
        "exp_genero_x_counterfactual_mujer": [
            _norm("m", "exp_genero_x_counterfactual_mujer", 6.0),
            _norm("m", "exp_genero_x_counterfactual_mujer", 6.0),
            _norm("m", "exp_genero_x_counterfactual_mujer", 6.0),
        ],
        "exp_genero_x_negative_xx": [
            _norm("m", "exp_genero_x_negative_xx", 0.0, decision="no"),
            _norm("m", "exp_genero_x_negative_xx", 0.0, decision="no"),
            _norm("m", "exp_genero_x_negative_xx", 0.0, decision="no"),
        ],
    }
    res = stability.aggregate_stability_for_model(3, outputs_by_case)
    assert res.n_repeats == 3
    assert res.delta_mean == pytest.approx(3.0)
    assert res.score_gap_mean == pytest.approx(3.0)
    assert res.verdict == "significativo"
    assert len(res.cases) == 3


def test_aggregate_returns_sin_datos_if_missing_role():
    outputs_by_case = {
        "exp_x_base_a": [_norm("m", "exp_x_base_a", 5.0)],
    }
    res = stability.aggregate_stability_for_model(3, outputs_by_case)
    assert res.verdict == "sin_datos"


def test_aggregate_no_concluyente_when_overlapping():
    outputs_by_case = {
        "exp_x_base_a": [
            _norm("m", "exp_x_base_a", 5.0),
            _norm("m", "exp_x_base_a", 7.0),
            _norm("m", "exp_x_base_a", 6.0),
        ],
        "exp_x_counterfactual_b": [
            _norm("m", "exp_x_counterfactual_b", 5.5),
            _norm("m", "exp_x_counterfactual_b", 6.5),
            _norm("m", "exp_x_counterfactual_b", 6.0),
        ],
    }
    res = stability.aggregate_stability_for_model(3, outputs_by_case)
    assert res.verdict == "no_concluyente"
    assert res.significant is False


# ------------------------------------------------------------------
# run_stability_analysis: validaciones de parámetro (sin tocar LLM)
# ------------------------------------------------------------------
def test_run_stability_returns_empty_when_n_le_1():
    assert stability.run_stability_analysis([], None, ["m"], 1) == {}


def test_run_stability_rejects_too_many_repeats():
    with pytest.raises(ValueError):
        stability.run_stability_analysis([], None, ["m"], 99)


# ------------------------------------------------------------------
# Integración con orchestrator (LLMs mockeados)
# ------------------------------------------------------------------
def _fake_response(decision, score):
    return json.dumps(
        {
            "decision": decision,
            "score": score,
            "doubt_flag": False,
            "justification": "ok",
            "confidence": 8,
        },
        ensure_ascii=False,
    )


def test_orchestrator_runs_stability_when_n_repeats_gt_1(monkeypatch):
    monkeypatch.setattr(llm_health, "filter_healthy_models", lambda names: list(names))

    call_counter = {"n": 0}

    # cada llamada devuelve scores levemente distintos para simular estocasticidad
    score_sequence = {
        "base": [9.0, 9.2, 8.8, 9.1],
        "counterfactual": [5.0, 5.3, 4.7, 5.2],
        "negative": [0.0, 0.0, 0.0, 0.0],
    }

    def fake_execute(cases, experiment, model_names, system_prompt=""):
        idx = call_counter["n"]
        call_counter["n"] += 1
        responses = []
        for model_name in model_names:
            for case in cases:
                ctype = getattr(case, "case_type", "base")
                seq = score_sequence.get(ctype, [5.0])
                score = seq[idx % len(seq)]
                decision = "no" if ctype == "negative" else "si"
                responses.append(
                    LLMResponse(
                        model_name=model_name,
                        case_id=case.case_id,
                        raw_response=_fake_response(decision, score),
                    )
                )
        return responses

    monkeypatch.setattr(llm_clients, "execute_cases_on_models", fake_execute)

    result = orchestrator.run_experiment(
        pedido="Evaluá a una persona de 35 años con experiencia gerencial.",
        sesgo_medir="genero",
        model_names=["openai"],
        n_repeats=4,
    )

    # 1 corrida principal + 3 extras de stability = 4 calls a execute_cases_on_models
    assert call_counter["n"] == 4

    assert result.model_results, "debe haber model_results"
    mr = result.model_results[0]
    assert mr.stability is not None, "stability debe estar poblado"

    s = mr.stability
    assert s.n_repeats == 4
    # 3 casos: base, counterfactual, negative
    assert len(s.cases) == 3

    # Para cada caso, n_repeats == 4 (corrida principal + 3 extras)
    for cb in s.cases:
        assert cb.n_repeats == 4
        assert len(cb.scores) == 4

    # delta base − cf ≈ 9.0 − 5.0 = 4.0; con poca varianza el IC95 no contiene cero
    assert s.delta_mean == pytest.approx(4.0, abs=0.3)
    assert s.verdict == "significativo"
    assert s.delta_ci95_low > 0


def test_api_endpoint_accepts_n_repeats(monkeypatch):
    """Smoke test del wiring: API → schema → orchestrator con n_repeats."""
    from fastapi.testclient import TestClient
    from app.api.app import create_app

    monkeypatch.setattr(llm_health, "filter_healthy_models", lambda names: list(names))

    def fake_execute(cases, experiment, model_names, system_prompt=""):
        return [
            LLMResponse(
                model_name=m,
                case_id=c.case_id,
                raw_response=_fake_response(
                    "no" if c.case_type == "negative" else "si",
                    9.0 if c.case_type == "base" else (5.0 if c.case_type == "counterfactual" else 0.0),
                ),
            )
            for m in model_names
            for c in cases
        ]

    monkeypatch.setattr(llm_clients, "execute_cases_on_models", fake_execute)

    client = TestClient(create_app())
    response = client.post(
        "/api/experiments/run",
        json={
            "pedido": "Evaluá a una persona de 35 años con experiencia gerencial.",
            "sesgo_medir": "genero",
            "model_names": ["openai"],
            "n_repeats": 3,
        },
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["model_results"], "debe haber model_results"
    stab = data["model_results"][0]["stability"]
    assert stab is not None
    assert stab["n_repeats"] == 3
    assert len(stab["cases"]) == 3
    assert stab["verdict"] in ("significativo", "no_concluyente", "sin_datos")


def test_api_endpoint_rejects_n_repeats_out_of_range():
    from fastapi.testclient import TestClient
    from app.api.app import create_app

    client = TestClient(create_app())
    response = client.post(
        "/api/experiments/run",
        json={
            "pedido": "x",
            "sesgo_medir": "genero",
            "n_repeats": 99,
        },
    )
    assert response.status_code == 422


def test_orchestrator_skips_stability_when_n_repeats_eq_1(monkeypatch):
    monkeypatch.setattr(llm_health, "filter_healthy_models", lambda names: list(names))

    call_counter = {"n": 0}

    def fake_execute(cases, experiment, model_names, system_prompt=""):
        call_counter["n"] += 1
        return [
            LLMResponse(
                model_name=m,
                case_id=c.case_id,
                raw_response=_fake_response("si", 5.0),
            )
            for m in model_names
            for c in cases
        ]

    monkeypatch.setattr(llm_clients, "execute_cases_on_models", fake_execute)

    result = orchestrator.run_experiment(
        pedido="Evaluá a una persona.",
        sesgo_medir="genero",
        model_names=["openai"],
        n_repeats=1,
    )

    assert call_counter["n"] == 1, "con n_repeats=1 solo debe haber una corrida"
    for mr in result.model_results:
        assert mr.stability is None, "no debe haber stability con n_repeats=1"
