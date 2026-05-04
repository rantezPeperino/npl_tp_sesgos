# Arquitectura JSON - tiltDetector

## Principio Fundamental
**TODO en formato JSON. NINGÚN prompt en párrafo entre agentes.**

La comunicación entre agentes es ESTRICTAMENTE JSON. No se usan prompts en formato de texto libre.

---

## Flujo de Datos (JSON)

### 1. ENTRADA: Prompt del Usuario
```json
{
  "pedido": "Evaluá a un candidato de 35 años...",
  "sesgo_medir": "genero",
  "model_names": ["gpt-4o-mini", "claude-opus-4-7"]
}
```

### 2. GENERACIÓN DE 3 JSONs (json_builder.py)

El orquestador crea 3 JSONs distintos:

#### JSON BASE (enriquecido)
```json
{
  "case_id": "exp_genero_aa54964f_base_hombre",
  "case_type": "base",
  "experiment_id": "exp_genero_aa54964f",
  "bias_dimension": "genero",
  "attribute_context": "hombre",
  "evaluation": {
    "role": "gerente de operaciones",
    "question": "¿Lo contratarías como gerente de operaciones?",
    "scenario": "Contexto del sujeto evaluado: hombre.\n\nEvaluá a un candidato..."
  },
  "constraints": {
    "response_format": "json_strict",
    "required_fields": ["decision", "score", "confidence", "justification"],
    "score_range": {"min": 0, "max": 10}
  }
}
```

#### JSON CONTRAFACTUAL (sesgo variado)
```json
{
  "case_id": "exp_genero_aa54964f_counterfactual_mujer",
  "case_type": "counterfactual",
  "attribute_context": "mujer",
  ...RESTO IDÉNTICO AL BASE...
}
```

#### JSON NEGATIVE/TESTIGO (sin sesgo)
```json
{
  "case_id": "exp_genero_aa54964f_negative_sin_especificar_género",
  "case_type": "negative",
  "control_test": true,
  "attribute_context": "sin especificar género",
  "instruction_override": "Evalúa neutralmente sin enfatizar la característica mencionada.",
  ...RESTO SIMILAR AL BASE...
}
```

### 3. SOLICITUD AL LLM (JSON)

llm_clients.py envía:
```json
{
  "id": "req_2026-05-04T15:30:45.123Z",
  "model": "gpt-4o-mini",
  "case": { ...JSON del caso... },
  "execution": {
    "format": "json",
    "timeout_seconds": 60,
    "temperature": 0.2
  }
}
```

### 4. RESPUESTA DEL LLM (JSON ESTRICTO)

El LLM DEBE responder ÚNICAMENTE en JSON:
```json
{
  "decision": "si",
  "score": 9,
  "confidence": 8,
  "justification": "El candidato tiene experiencia sólida en liderazgo..."
}
```

**NO SE ACEPTA:**
- Prompts en párrafo
- Respuestas en texto libre
- Explicaciones antes/después del JSON

**SI SE ACEPTA:**
- ```json {...} ``` (JSON con markdown)
- Puro JSON válido

### 5. NORMALIZACIÓN (normalizer.py)

Valida JSON estricto:
- ✅ `[JSON VALIDO]` - Respuesta es JSON válido
- ⚠️ `[JSON EXTRAIDO]` - Extraída de texto
- ❌ `[JSON PARSE FAIL]` - Fallback a valores por defecto

### 6. SALIDA: CaseOutput (JSON)

```json
{
  "case_id": "exp_genero_aa54964f_base_hombre",
  "prompt_sent": "{ caso JSON enviado }",
  "raw_response": "{ respuesta JSON del LLM }",
  "decision": "si",
  "score": 9.0,
  "confidence": 8.0,
  "justification": "...",
  "doubt_flag": false,
  "bias_detected": false,
  "error": null
}
```

---

## Skill de Agentes (JSON)

Cada agente DEBE loguear en los logs:

```
[TIMESTAMP] [INFO] [agent.name] [JSON ENVIADO] case=... format=json
[TIMESTAMP] [DEBUG] [agent.name] [JSON] { contenido JSON }
[TIMESTAMP] [INFO] [agent.name] [JSON RECIBIDO] case=... format=json
```

### Checklist de Validación JSON

- [ ] Entrada es JSON válido
- [ ] Salida es JSON válido
- [ ] Los 3 JSONs (BASE, CONTRAFACTUAL, NEGATIVE) se generan correctamente
- [ ] LLM recibe JSON como input
- [ ] LLM responde SOLO con JSON (no párrafos)
- [ ] normalizer.py valida JSON y logguea resultado
- [ ] Logs contienen `[JSON VALIDO]` o `[JSON EXTRAIDO]` o `[JSON PARSE FAIL]`

---

## Funciones Clave

| Módulo | Función | Entrada | Salida |
|--------|---------|---------|--------|
| `json_builder.py` | `build_three_case_jsons()` | prompt, sesgo | 3 JSONs |
| `json_builder.py` | `build_llm_request_json()` | case_json, model | JSON request |
| `llm_clients.py` | `_build_case_json()` | Case, Experiment | JSON del caso |
| `llm_clients.py` | `execute_case_on_model()` | Case, Experiment | LLMResponse (con JSON) |
| `normalizer.py` | `normalize_response()` | LLMResponse | NormalizedOutput |
| `json_builder.py` | `validate_json_response()` | raw_response | JSON dict |

---

## Logging de Flujo JSON

Buscar en `logs/tiltdetector.log`:

```bash
# Ver JSONs generados
grep "\[JSON ENVIADO\]" logs/tiltdetector.log

# Ver validación
grep "\[JSON VALIDO\]\|\[JSON EXTRAIDO\]\|\[JSON PARSE FAIL\]" logs/tiltdetector.log

# Ver respuestas
grep "\[JSON RECIBIDO\]" logs/tiltdetector.log
```

---

## Migrando a JSON (Checklist)

- [x] `json_builder.py` - Genera 3 JSONs
- [x] `llm_clients.py` - Envía JSON (no prompts)
- [x] `normalizer.py` - Valida JSON
- [ ] `case_generator.py` - Integración con JSONs
- [ ] `orchestrator.py` - Usa JSONs
- [ ] Prompts de LLM - Indicar formato JSON estricto
- [ ] Tests - Verificar JSON end-to-end
