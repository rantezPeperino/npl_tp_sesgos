# skill_agents/

Especificación viva de cada agente del sistema. Cada `.md` describe el rol,
contrato, reglas críticas y diferencias con la versión anterior si aplica.

## Pipeline (orden)

```
prompt_normalizer → case_generator → llm_health → llm_clients → normalizer → control → metrics → report_renderer
```

El **orchestrator** invoca a todos en este orden y ensambla el `ExperimentResult` final.

## Skills

| Agente              | Skill                                              |
|---------------------|----------------------------------------------------|
| Orchestrator        | [orchestrator.md](orchestrator.md)                 |
| Prompt Normalizer   | [prompt_normalizer.md](prompt_normalizer.md)       |
| Case Generator      | [case_generator.md](case_generator.md)             |
| LLM Health          | [llm_health.md](llm_health.md)                     |
| LLM Clients         | [llm_clients.md](llm_clients.md)                   |
| Normalizer          | [normalizer.md](normalizer.md)                     |
| Control             | [control.md](control.md)                           |
| Metrics             | [metrics.md](metrics.md)                           |
| Report Renderer     | [report_renderer.md](report_renderer.md)           |

## Schema de salida (sin redundancias)

```
ExperimentResult {
  experiment_id
  metadata { industry, topic, bias_dimension, source_pedido,
             language, temperature, prompt_version }
  cases [
    { case_id, case_type, attribute_value, rendered_prompt }
  ]
  model_results [
    {
      model_name
      outputs [
        { case_id, raw_response, decision, score, doubt_flag,
          justification, bias_detected, bias_category }
      ]
      comparison { score_gap, decision_changed, bias_detected, bias_category }
      metrics { avg_score, bias_rate, consistency_score,
                score_gap, decision_changed, control_validation, bias_intensity }
    }
  ]
  global_summary { total_models, global_bias_rate, max_score_gap,
                   bias_detected_global, control_validation_all_models }
}
```

Eliminados respecto del schema previo: `payload` (duplicaba el input);
`raw_responses[]` y `normalized_outputs[]` separados (ahora unificados en
`outputs[]`); las 3 `comparisons` por modelo (queda solo la principal).
