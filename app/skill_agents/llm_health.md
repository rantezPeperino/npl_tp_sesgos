# Skill — LLM Health Check

**Módulo**: [app/llm_health.py](../app/llm_health.py)

## Rol

Verifica conectividad con cada LLM solicitado **antes** de iniciar el
experimento. Filtra los modelos sanos y descarta los que fallan.

## Contrato

```python
def filter_healthy_models(model_names: List[str]) -> List[str]
```

## Qué chequea por proveedor

| Proveedor | SDK / endpoint                              | Verificación                                |
|-----------|---------------------------------------------|---------------------------------------------|
| ollama    | HTTP nativo `GET /api/tags`                 | servicio arriba + `OLLAMA_MODEL` descargado |
| openai    | `from openai import OpenAI` + `models.list()` | SDK + key + autenticación válida          |
| gemini    | `genai.list_models()`                       | SDK + key + autenticación válida            |
| anthropic | `client.messages.create(max_tokens=1)`      | SDK + key + autenticación válida            |

## Comportamiento

- Si un modelo falla → log `[WARN]` por stderr con detalle del error y se descarta.
- Si un modelo pasa → log `[OK]` por stdout.
- Si NINGÚN modelo está disponible → devuelve `[]` (el orquestador aborta).
- Cachea el resultado del check **por proveedor** dentro de la misma corrida
  (útil cuando el cliente envía varios aliases del mismo proveedor).

## Reglas críticas

- No es opcional: el orquestador lo invoca SIEMPRE como primer paso.
- No mocks: si el SDK no está instalado, falla con mensaje accionable
  (`"pip install <sdk>"`).
- Mensajes de error apuntan a la solución (ej. `"Iniciá el servicio con: ollama serve"`).

## Cómo agregar un proveedor

1. Implementar `_check_<proveedor>()` aquí.
2. Registrar en `_PROVIDER_CHECKS`.
3. Sumar aliases en [app/providers.py](../app/providers.py).
