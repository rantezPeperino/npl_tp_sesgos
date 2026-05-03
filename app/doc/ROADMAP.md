# Roadmap del Proyecto – Estado Actual

## División Conceptual del Trabajo

El desarrollo se dividió en dos flujos paralelos con un punto de integración
claro. Ambos están **completos** y operativos.

- **Dev 1**: entrada + ejecución del experimento
- **Dev 2**: interpretación + evaluación del resultado

---

## Vista General

```text
                    tiltDetector
                         │
       ─────────────────────────────────────────────────
       │                                               │
       v                                               v
+───────────────────────────+         +───────────────────────────+
│ DEV 1                     │         │ DEV 2                     │
│ Entrada + Ejecución       │         │ Normalización + Análisis  │
+───────────────────────────+         +───────────────────────────+
│ - API REST (FastAPI)      │         │ - Normalizer              │
│ - Models (dataclasses)    │         │ - Control (3 vías)        │
│ - Prompt Normalizer       │         │ - Metrics extendidas      │
│ - Case Generator          │         │ - Report Renderer         │
│ - LLM Health Check        │         │ - Memoria en proceso      │
│ - LLM Clients             │         │   (_EXPERIMENTS dict)     │
│   (Ollama / OpenAI / Gem) │         │                           │
│ - Orchestrator (control)  │         │ - Orchestrator (parte 2)  │
+───────────────────────────+         +───────────────────────────+
       │                                               │
       └─────────────── Punto de Integración ───────────┘
                              │
                              v
              Contratos en app/models.py (dataclasses)
              Persistencia en memoria, accesible vía
              GET /experiments/{id}
```

---

## Pipeline Cliente → Resultado

```text
Cliente externo (Postman / curl / Frontend)
    │
    │ POST /experiments/run  { pedido, sesgo_medir, model_names? }
    v
┌───────────────────────────────────────────────────────────────┐
│  [DEV 1]                                                      │
│  1. Health check de los LLMs solicitados                      │
│     → si ninguno está disponible, aborta con 422              │
│     → emite [WARN] por los que fallan, sigue con los OK       │
│  2. prompt_normalizer convierte texto plano → JSON universal  │
│     - genera experiment_id                                    │
│     - inyecta placeholder {{SESGO}}                           │
│     - selecciona valores base/cf/negative por dimensión       │
│  3. case_generator produce los 3 Case (base, cf, negative)    │
│     con input_case estructurado y rendered_prompt             │
│  4. llm_clients ejecuta cada caso × cada LLM en una           │
│     conexión nueva, sin contexto compartido                   │
└───────────────────────────────────────────────────────────────┘
                          │
                          │ raw_responses[]
                          v
┌───────────────────────────────────────────────────────────────┐
│  [DEV 2]                                                      │
│  5. normalizer parsea la respuesta y produce                  │
│     NormalizedOutput (decision, score, doubt_flag,            │
│     justification, bias_detected, bias_category)              │
│  6. control compara los 3 casos por modelo:                   │
│     - base vs counterfactual (detección de sesgo)             │
│     - base vs negative (control)                              │
│     - counterfactual vs negative (control)                    │
│     control_validation = (negative.decision == "no")          │
│  7. orchestrator propaga bias_detected a base y cf cuando     │
│     la comparación principal lo detecta                       │
│  8. metrics calcula:                                          │
│     - avg_score, bias_rate, consistency_score                 │
│     - score_gap_base_vs_counterfactual                        │
│     - decision_changed, control_validation                    │
│     - bias_intensity (none / low / medium / high)             │
│  9. report_renderer arma reporte por LLM y se imprime         │
│     en stdout; también queda en el ExperimentResult           │
│ 10. orchestrator guarda el resultado en _EXPERIMENTS[id]      │
└───────────────────────────────────────────────────────────────┘
                          │
                          v
              Response JSON final (ExperimentResult)
              + reporte de terminal
              + GET /experiments/{id} disponible
```

---

## Bloques completados

```text
┌─────────────────────────────────────────────────────────────────────┐
│ DEV 1: ARMAR Y EJECUTAR EL EXPERIMENTO                             │
├─────────────────────────────────────────────────────────────────────┤
│ ✔ Recibir { pedido, sesgo_medir } por API                          │
│ ✔ Validar input (Pydantic)                                         │
│ ✔ Health check de los LLMs antes de iniciar                        │
│ ✔ Normalizar el texto plano a JSON universal                       │
│ ✔ Generar 3 casos: base, contrafactual, testigo negativo           │
│ ✔ Mantener input_case estructurado para trazabilidad               │
│ ✔ Conectividad multi-proveedor: Ollama / OpenAI / Gemini           │
│ ✔ Cada llamada LLM es independiente (sin contexto)                 │
│ ✔ Habilitar / deshabilitar proveedores vía .env                    │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ DEV 2: INTERPRETAR Y EVALUAR EL EXPERIMENTO                        │
├─────────────────────────────────────────────────────────────────────┤
│ ✔ Normalizar respuestas a schema común                             │
│ ✔ doubt_flag detectado por keywords                                │
│ ✔ Comparar base vs counterfactual                                  │
│ ✔ Comparar base vs negative y cf vs negative (control)             │
│ ✔ Control validation (negative.decision == "no")                   │
│ ✔ Propagar bias_detected a outputs involucrados                    │
│ ✔ Métricas extendidas con bias_intensity                           │
│ ✔ Reporte de terminal por LLM                                      │
│ ✔ Persistencia en memoria + GET /experiments/{id}                  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Estado de Proveedores LLM

| Proveedor | Estado     | SDK                       | Modelo default       |
|-----------|------------|---------------------------|----------------------|
| Ollama    | habilitado | nativo HTTP (sin SDK)     | `llama3.2:latest`    |
| OpenAI    | disponible | `openai`                  | `gpt-4.5-preview`    |
| Gemini    | disponible | `google-generativeai`     | `gemini-2.0-flash`   |
| Anthropic | integrado, deshabilitado | `anthropic` (comentado en requirements) | `claude-opus-4-7` |

Para habilitar/deshabilitar: editar `ENABLED_PROVIDERS` en `.env`.
Para habilitar Claude (Anthropic): ver [doc/CLAUDE_CHECKLIST.md](CLAUDE_CHECKLIST.md).
Para agregar un nuevo proveedor: ver [app/providers.py](../app/providers.py).

---

## Pendientes / Próximos pasos

- Migrar `google.generativeai` → `google.genai` (el paquete actual está deprecated).
- Agregar persistencia en archivos (versión actual usa solo memoria).
- Soporte para múltiples bias_dimensions en un mismo experimento.
- Tests automatizados de integración con LLM mock para CI.
- Frontend de consumo (actualmente solo Postman/curl).
- Mitigación A/B por system prompt — ver [MITIGATION_AB.md](MITIGATION_AB.md).
