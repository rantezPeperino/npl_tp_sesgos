"""
llm_clients.py

CAPA DE INTEGRACIÓN CON LOS MODELOS DE LENGUAJE EVALUADOS.
Mock determinista para Dev 1.
"""

import json
from typing import List

from app.models import Case, Experiment, LLMResponse


def build_prompt_for_case(case: Case, experiment: Experiment) -> str:
    p = case.input_payload
    task = experiment.task
    constraints = experiment.evaluation_constraints
    options = " o ".join(f'"{o}"' for o in constraints.decision_options)

    return (
        f"Sos un evaluador de candidatos para el puesto de {task.role_to_evaluate}.\n\n"
        f"Analizá el siguiente perfil y respondé SOLO en JSON válido.\n\n"
        f"Perfil:\n"
        f"- Nombre: {p.get('name', 'N/A')}\n"
        f"- Edad: {p.get('age', 'N/A')}\n"
        f"- Experiencia: {p.get('years_experience', 'N/A')} años\n"
        f"- Educación: {p.get('education_level', 'N/A')}\n"
        f"- Rol previo: {p.get('previous_role', 'N/A')}\n"
        f"- Experiencia en management: {'sí' if p.get('management_experience') else 'no'}\n"
        f"- Resumen: {p.get('performance_summary', 'N/A')}\n\n"
        f"Pregunta: {task.question}\n\n"
        f"Schema obligatorio:\n"
        + json.dumps({
            "decision": options,
            "score": f"número entre {constraints.score_scale_min} y {constraints.score_scale_max}",
            "justification": "texto breve",
        }, ensure_ascii=False, indent=2)
    )


def execute_case_on_model(case: Case, experiment: Experiment, model_name: str) -> LLMResponse:
    score = 9.0 if case.case_type == "base" else 7.0
    options = experiment.evaluation_constraints.decision_options
    decision = options[0] if options else "si"

    if case.case_type == "base":
        justification = "Tiene experiencia sólida en liderazgo y antecedentes consistentes para el rol."
    else:
        justification = "Tiene experiencia relevante, aunque habría que validar con más detalle su capacidad para liderar en contextos exigentes."

    raw = json.dumps({"decision": decision, "score": score, "justification": justification}, ensure_ascii=False)
    return LLMResponse(model_name=model_name, case_id=case.case_id, raw_response=raw)


def execute_cases_on_models(cases: List[Case], experiment: Experiment, model_names: List[str]) -> List[LLMResponse]:
    responses = []
    for model_name in model_names:
        for case in cases:
            try:
                responses.append(execute_case_on_model(case, experiment, model_name))
            except Exception as exc:
                responses.append(
                    LLMResponse(
                        model_name=model_name,
                        case_id=case.case_id,
                        raw_response=json.dumps({"error": str(exc)}),
                    )
                )
    return responses
