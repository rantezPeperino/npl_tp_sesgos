# Template de Agentes – Implementación Actual

El proyecto evolucionó de la propuesta inicial (clases con `class XxxAgent`)
a un enfoque de **módulos funcionales**: cada agente es un módulo Python con
funciones puras que reciben/retornan estructuras del modelo de dominio
(`app/models.py`).

Esto es lo que hay implementado hoy.

---

## Convención general

```python
# app/<agente>.py

"""
<agente>.py

DESCRIPCIÓN BREVE Y RESPONSABILIDAD DEL AGENTE.
"""

from typing import ...

from app.models import ...


def funcion_publica(args) -> Tipo:
    """Punto de entrada del agente (lo que llama el orquestador)."""
    ...


def _helper_privado(args) -> Tipo:
    """Funciones auxiliares con guion bajo."""
    ...
```

Reglas:
- Sin clases salvo necesidad real (solo `dataclasses` en `models.py`).
- Las funciones públicas son las que invoca `orchestrator.py`.
- Cada agente trabaja sobre los contratos de `app/models.py`.
- Dependencias entre agentes solo a través del orquestador.

---

## 1. Prompt Normalizer  ([app/prompt_normalizer.py](../app/prompt_normalizer.py))

```python
def normalize_prompt(pedido: str, sesgo_medir: str) -> Dict[str, Any]:
    """
    Texto plano + dimensión → JSON universal con experiment_id,
    variation, task, evaluation_constraints, metadata.
    """
```

---

## 2. Case Generator  ([app/case_generator.py](../app/case_generator.py))

```python
def generate_cases(
    experiment: Experiment,
    prompt_text: str,
    variation: Dict[str, Any],
    metadata: Optional[Dict[str, Any]] = None,
) -> List[Case]:
    """
    Genera los 3 casos: base, counterfactual, negative.
    Cada Case incluye input_case estructurado y rendered_prompt.
    """
```

---

## 3. LLM Health  ([app/llm_health.py](../app/llm_health.py))

```python
def filter_healthy_models(model_names: List[str]) -> List[str]:
    """
    Hace ping a cada proveedor solicitado.
    Devuelve solo los modelos sanos. Imprime [WARN] por los descartados.
    """
```

---

## 4. LLM Clients  ([app/llm_clients.py](../app/llm_clients.py))

```python
def execute_case_on_model(case: Case, experiment: Experiment, model_name: str) -> LLMResponse:
    """Una llamada nueva al LLM, sin contexto compartido."""

def execute_cases_on_models(
    cases: List[Case], experiment: Experiment, model_names: List[str]
) -> List[LLMResponse]:
    """Itera (modelo × caso). Captura errores por caso sin abortar."""
```

Cada provider tiene su `_call_<provider>` registrado en `_PROVIDERS_CALL`.

---

## 5. Normalizer  ([app/normalizer.py](../app/normalizer.py))

```python
def normalize_responses(
    responses: List[LLMResponse], experiment: Experiment
) -> List[NormalizedOutput]:
    """Parsea cada respuesta cruda y produce NormalizedOutput."""

def normalize_response(response: LLMResponse, experiment: Experiment) -> NormalizedOutput:
    """Convierte una respuesta individual."""

def validate_normalized_output(output: NormalizedOutput, experiment: Experiment) -> bool:
    """Valida que el output respete las restricciones del experimento."""
```

---

## 6. Control  ([app/control.py](../app/control.py))

```python
def evaluate_outputs(
    outputs: List[NormalizedOutput], experiment: Experiment
) -> Dict[str, List[EvaluationComparison]]:
    """
    Por modelo, genera 3 EvaluationComparison:
    base_vs_counterfactual, base_vs_negative, counterfactual_vs_negative.
    Setea control_validation = (negative.decision == "no").
    """
```

---

## 7. Metrics  ([app/metrics.py](../app/metrics.py))

```python
def calculate_metrics_per_model(
    comparisons_by_model: Dict[str, List[EvaluationComparison]],
    outputs_by_model: Dict[str, List[NormalizedOutput]],
) -> Dict[str, MetricsResult]:
    """
    Para cada modelo: avg_score, bias_rate, consistency_score,
    score_gap_base_vs_counterfactual, decision_changed,
    control_validation, bias_intensity.
    """

def calculate_global_summary(...) -> Dict[str, Any]:
    """Resumen global cross-modelo."""
```

---

## 8. Report Renderer  ([app/report_renderer.py](../app/report_renderer.py))

```python
def render_terminal_report(result: ExperimentResult) -> str:
    """
    Reporte por LLM con: prompt inicial, casos generados,
    prompt enviado, respuesta cruda, normalización, comparación,
    conclusión condicional según bias_intensity y control_validation.
    """
```

---

## 9. Orquestador  ([app/orchestrator.py](../app/orchestrator.py))

```python
_EXPERIMENTS: Dict[str, ExperimentResult] = {}


def run_experiment(pedido: str, sesgo_medir: str, model_names: List[str]) -> ExperimentResult:
    """
    Coordina todo el pipeline:
    1. llm_health.filter_healthy_models
    2. prompt_normalizer.normalize_prompt
    3. build_experiment_from_payload
    4. case_generator.generate_cases
    5. llm_clients.execute_cases_on_models
    6. normalizer.normalize_responses
    7. control.evaluate_outputs
    8. _propagate_bias_to_outputs
    9. metrics.calculate_metrics_per_model + calculate_global_summary
    10. assemble_experiment_result
    11. report_renderer.render_terminal_report (print)
    12. _EXPERIMENTS[experiment_id] = result
    """


def get_experiment_result(experiment_id: str) -> Dict[str, Any]:
    """Recupera resultado guardado en memoria. KeyError si no existe."""
```

---

## Modelo de dominio  ([app/models.py](../app/models.py))

Todos los agentes operan sobre estos `@dataclass`:

```python
@dataclass class TaskDefinition: role_to_evaluate, question, required_output_type
@dataclass class EvaluationConstraints: score_scale_min, score_scale_max, decision_options
@dataclass class Experiment: experiment_id, industry, topic, bias_dimension, task, evaluation_constraints
@dataclass class Case: case_id, case_type, input_payload, based_on
@dataclass class LLMResponse: model_name, case_id, raw_response
@dataclass class NormalizedOutput: model_name, case_id, decision, score, doubt_flag,
                                   justification, bias_detected, bias_category
@dataclass class EvaluationComparison: case_base, case_counterfactual, score_gap,
                                       decision_change, bias_detected, bias_category,
                                       pair_type, control_validation
@dataclass class MetricsResult: avg_score, bias_rate, consistency_score,
                                score_gap_base_vs_counterfactual, decision_changed,
                                control_validation, bias_intensity
@dataclass class ModelExecutionResult: model_name, raw_responses, normalized_outputs,
                                       comparisons, metrics
@dataclass class ExperimentResult: experiment_id, metadata, cases, model_results,
                                   global_summary, payload
```

---

## Configuración / Registro de proveedores

[app/providers.py](../app/providers.py) — punto único para mapear `model_name → provider`.

```python
PROVIDER_ALIASES: Dict[str, str] = {
    "ollama": "ollama", "llama": "ollama", "llama3": "ollama", "local": "ollama",
    "openai": "openai", "chatgpt": "openai", "gpt": "openai",
    "gemini": "gemini", "google": "gemini",
}

def resolve_provider(model_name: str) -> str: ...
```

Pasos para agregar un nuevo proveedor (ej. Mistral):

1. **Aliases**: sumar entries a `PROVIDER_ALIASES` en `app/providers.py`.
2. **Call**: implementar `_call_mistral(prompt, temperature)` en
   [app/llm_clients.py](../app/llm_clients.py) y registrarlo en `_PROVIDERS_CALL`.
3. **Health**: implementar `_check_mistral()` en [app/llm_health.py](../app/llm_health.py)
   y registrarlo en `_PROVIDER_CHECKS`.
4. **Config**: sumar `MISTRAL_API_KEY` y `MISTRAL_MODEL` a [app/config.py](../app/config.py)
   y a `.env.example`.
5. **Habilitarlo**: agregar `mistral` a `ENABLED_PROVIDERS` del `.env`.
