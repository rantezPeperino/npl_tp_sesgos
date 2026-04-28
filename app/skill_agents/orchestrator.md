# Skill — Orchestrator

**Módulo**: [app/orchestrator.py](../app/orchestrator.py)

## Rol

Coordinador central del experimento. Recibe el input mínimo desde la API
(`pedido` + `sesgo_medir` + `model_names?`) y dirige el pipeline completo.
Es el único agente que compone el `ExperimentResult` final y persiste el
resultado en memoria.

## Contrato

```python
def run_experiment(pedido: str, sesgo_medir: str, model_names: List[str]) -> ExperimentResult
def get_experiment_result(experiment_id: str) -> Dict[str, Any]
```

## Flujo (orden estricto)

1. **Health check**: invoca `llm_health.filter_healthy_models(model_names)`.
   Si el resultado es `[]`, **aborta** con `ValueError` (la API lo expone como `422`).
2. **Normalización del prompt**: `prompt_normalizer.normalize_prompt(...)` →
   JSON universal con `experiment_id`, `variation`, `task`, etc.
3. **Construcción del `Experiment`**: `build_experiment_from_payload(...)`.
4. **Generación de casos**: `case_generator.generate_cases(...)` → `[base, counterfactual, negative]`.
5. **Ejecución LLM**: `llm_clients.execute_cases_on_models(cases, experiment, healthy_models)`.
   Cada (modelo, caso) es **una conexión nueva, sin contexto compartido**.
6. **Normalización de respuestas**: `normalizer.normalize_responses(...)` → `CaseOutput[]`.
7. **Control**: `control.evaluate_outputs(outputs, experiment)` → `Dict[model_name, ControlResult]`.
8. **Propagación de bias_detected**: el orquestador setea
   `bias_detected=True` y `bias_category=<dimension>` en los outputs de
   base y contrafactual cuando `comparison.bias_detected`.
9. **Métricas**: `metrics.calculate_metrics_per_model(...)` y `metrics.calculate_global_summary(...)`.
10. **Ensamblado**: arma `ExperimentResult` (sin redundancias) y hace
    `print(report_renderer.render_terminal_report(result))`.
11. **Persistencia en memoria**: `_EXPERIMENTS[experiment_id] = result`.

## Reglas críticas

- Aborta antes de generar casos si no hay LLM disponible (no consume recursos en vano).
- Es el ÚNICO que conoce todos los pasos. Los agentes downstream no se llaman entre sí.
- No duplica datos en la salida (ver schema en [skill_agents/control.md](control.md)).

## Dependencias

- llm_health, prompt_normalizer, case_generator, llm_clients, normalizer, control, metrics, report_renderer.
