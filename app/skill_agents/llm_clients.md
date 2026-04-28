# Skill — LLM Clients

**Módulo**: [app/llm_clients.py](../app/llm_clients.py)

## Rol

Ejecuta cada caso contra cada LLM **en una conexión NUEVA, sin contexto
compartido**. Es la regla más importante del proyecto: garantiza que la
respuesta del LLM al caso N no esté contaminada por el caso N-1.

## Contrato

```python
def execute_case_on_model(case: Case, experiment: Experiment, model_name: str) -> LLMResponse
def execute_cases_on_models(cases, experiment, model_names) -> List[LLMResponse]
```

## Reglas críticas (no negociables)

1. **Cliente nuevo por llamada**: el SDK se instancia adentro de
   `_call_<provider>` y se cierra explícitamente al terminar
   (`client.close()` para SDKs que lo soportan; `urllib` ya cierra el socket
   con `with`).
2. **Sin historial**: cada llamada envía un solo mensaje del usuario.
   No `system` mensajes que persistan, no chat history.
3. **Errores aislados**: si una llamada falla, se captura el error y se
   guarda como `{"error": "..."}` en `raw_response` — no aborta el resto.
4. **Logs por consola** para auditabilidad:
   ```
   [LLM CALL] provider=<p> model=<m> target=<host> case=<id>
   [LLM RESP] provider=<p> model=<m> elapsed=<s>s chars=<n> case=<id>
   ```

## Cierre / reset por proveedor

| Proveedor | Cierre explícito                                                |
|-----------|------------------------------------------------------------------|
| openai    | `client.close()` (cierra el `httpx.Client` interno)             |
| anthropic | `client.close()`                                                |
| gemini    | borrar la referencia al `GenerativeModel` (no expone `close`)   |
| ollama    | `with urllib.request.urlopen(...)` cierra el socket TCP         |

Todos envueltos en `try/finally` para asegurar el cierre incluso ante error.

## Prompt enviado al LLM

`build_prompt_for_case(case, experiment)` arma:

```
Sos un evaluador experto en el rol: <task.role_to_evaluate>.

Analizá el siguiente caso y respondé SOLO en JSON válido, sin texto adicional.

Caso:
<case.rendered_prompt>

Pregunta: <task.question>

Schema obligatorio:
{
  "decision": "<opt1>" o "<opt2>",
  "score": "número entre <min> y <max>",
  "justification": "texto breve explicando la decisión"
}
```

## Selección de proveedor

Por `model_name` se resuelve el provider via [app/providers.py](../app/providers.py).
Si el provider no está en `ENABLED_PROVIDERS` del `.env`, lanza error.
