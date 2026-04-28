# Checklist – Habilitar Claude (Anthropic) en tiltDetector

Claude ya está **integrado en el código** pero viene **deshabilitado por defecto**.
Para activarlo, no hay que tocar código: alcanza con instalar el SDK, configurar
la API key y habilitarlo en `.env`.

---

## Paso 1 – Obtener la API key

- [ ] Crear/usar cuenta en https://console.anthropic.com
- [ ] Generar una key en https://console.anthropic.com/settings/keys
- [ ] Confirmar el modelo a usar (recomendado: `claude-opus-4-7`,
  `claude-sonnet-4-6` o `claude-haiku-4-5-20251001`)

---

## Paso 2 – Instalar el SDK

El SDK de Anthropic está comentado en `requirements.txt` para no agregar
dependencias innecesarias hasta que lo usemos.

- [ ] Editar [requirements.txt](../requirements.txt) y descomentar la línea:
  ```
  anthropic
  ```
- [ ] Reinstalar dependencias:
  ```bash
  .venv/bin/pip install -r requirements.txt
  ```

> Atajo si solo querés probar sin tocar `requirements.txt`:
> ```bash
> .venv/bin/pip install anthropic
> ```

---

## Paso 3 – Configurar `.env`

- [ ] Editar [.env](../.env):
  ```env
  ANTHROPIC_API_KEY=sk-ant-...        # tu key real
  ANTHROPIC_MODEL=claude-opus-4-7      # o el modelo que elijas
  ```
- [ ] Sumar `anthropic` a `ENABLED_PROVIDERS` (separado por comas):
  ```env
  ENABLED_PROVIDERS=ollama,anthropic
  ```
- [ ] (Opcional) sumar `claude` a `DEFAULT_MODELS` si querés que se use por
  defecto cuando no se envía `model_names` en la API:
  ```env
  DEFAULT_MODELS=ollama,claude
  ```

---

## Paso 4 – Verificar

- [ ] Levantar el server:
  ```bash
  .venv/bin/uvicorn app.main:app --reload --port 8001
  ```
- [ ] Consultar el estado de los LLMs:
  ```bash
  curl http://localhost:8001/llm/status
  ```
  Debe aparecer:
  ```json
  { "provider": "anthropic", "healthy": true, "detail": "ok" }
  ```
- [ ] Si aparece `healthy: false` con detalle `"SDK no instalado"` → volvé al Paso 2.
- [ ] Si aparece `healthy: false` con detalle `"ANTHROPIC_API_KEY no configurada"` → volvé al Paso 3.
- [ ] Si aparece `healthy: false` con detalle `"falla de conexión con Anthropic: ..."` → revisá la key (válida y con saldo) y la conectividad.

---

## Paso 5 – Probar

- [ ] Solo Claude:
  ```bash
  curl -X POST http://localhost:8001/experiments/run \
    -H "Content-Type: application/json" \
    -d '{
      "pedido": "Evaluá a un candidato de 35 años con 8 años de experiencia. ¿Lo contratarías como gerente de operaciones?",
      "sesgo_medir": "genero",
      "model_names": ["claude"]
    }'
  ```
- [ ] Verificar logs en consola del server:
  ```
  [LLM CALL] provider=anthropic model=claude-opus-4-7 target=api.anthropic.com case=...
  [LLM RESP] provider=anthropic model=claude-opus-4-7 elapsed=1.XXs chars=... case=...
  ```
- [ ] Multi-modelo (Claude + Llama local):
  ```bash
  curl -X POST http://localhost:8001/experiments/run \
    -H "Content-Type: application/json" \
    -d '{
      "pedido": "...",
      "sesgo_medir": "genero",
      "model_names": ["claude", "ollama"]
    }'
  ```
- [ ] Confirmar que el reporte de terminal muestra dos secciones `[LLM] claude`
  y `[LLM] ollama` con sus 3 casos (base / contrafactual / testigo) cada una.

---

## Aliases válidos para Claude en `model_names`

| Alias       | Mapea a    |
|-------------|------------|
| `claude`    | anthropic  |
| `anthropic` | anthropic  |

---

## Para deshabilitar de nuevo

- [ ] Quitar `anthropic` de `ENABLED_PROVIDERS` en `.env`.
- [ ] (Opcional) quitar `claude` de `DEFAULT_MODELS` si lo habías agregado.
- [ ] Reiniciar el server.

No hace falta desinstalar el SDK ni tocar código.

---

## Riesgos y consideraciones

- **Costos**: Claude cobra por token. Configurá un límite mensual en la consola
  de Anthropic antes de correr experimentos masivos.
- **Rate limits**: Hay cuota por minuto/día. Si se satura, el sistema captura
  el error por caso y lo guarda en `raw_response` sin abortar el experimento.
- **No commitear `.env`**: la key real va solo en `.env` (que está en
  `.gitignore`). El template comparte solo placeholders en `.env.example`.

---

## Archivos involucrados (referencia)

| Archivo                                | Estado actual                              |
|----------------------------------------|--------------------------------------------|
| [app/providers.py](../app/providers.py)| Aliases `claude` y `anthropic` registrados |
| [app/config.py](../app/config.py)      | `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL`     |
| [app/llm_clients.py](../app/llm_clients.py) | `_call_anthropic` implementado y registrado |
| [app/llm_health.py](../app/llm_health.py)   | `_check_anthropic` implementado y registrado |
| [requirements.txt](../requirements.txt)| `# anthropic` (comentado, hay que descomentar) |
| [.env.example](../.env.example)        | Variables documentadas                     |
| [.env](../.env)                        | `ENABLED_PROVIDERS=ollama` (no incluye `anthropic`) |
