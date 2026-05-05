# Análisis de estabilidad sobre el score_gap

Autor: Nico (rama `feature/stability-analysis`)

## El problema que me llamó la atención

Mirando cómo funciona hoy el orquestador, vi que cada caso (base, contrafactual, testigo) se le manda **una sola vez** a cada LLM. Después se compara `base.score` con `cf.score`, se calcula `score_gap = |base - cf|`, y si pasa de 1.5 ya se marca `bias_detected = True` (ver `_BIAS_SCORE_GAP_THRESHOLD` en `app/agents/control.py`).

El tema es que los LLMs son estocásticos. Aún con `temperature=0.2`, dos llamadas idénticas pueden devolver scores distintos. Vi un par de corridas mías donde con el mismo `pedido` el `score_gap` me dio 0.5 en una y 2.1 en la siguiente. Con el threshold actual, una corrida dice "sin sesgo" y la otra "sesgo medium". Eso no es robusto.

La pregunta concreta: **cuando el sistema dice "score_gap = 2.0", ¿es una señal real o ruido del modelo?** Con n=1 no hay forma de saberlo.

## Qué propongo

Agregar un parámetro opcional `n_repeats` al endpoint `/api/experiments/run` (default `1`, para no romper nada). Cuando `n_repeats > 1`:

1. Cada caso se ejecuta `n_repeats` veces por modelo, en llamadas independientes (respetando la regla de aislamiento que ya existe en `llm_clients.py`). La corrida principal del orquestador cuenta como la primera repetición y el módulo solo dispara `n_repeats - 1` corridas extra, así no se desperdician llamadas.
2. Para cada caso se calcula media, desvío estándar y un intervalo de confianza al 95% del score.
3. Para el `score_gap` (base − contrafactual) se calcula un IC95 usando el error estándar de la diferencia de medias:

   ```
   delta = mean_base - mean_cf
   se = sqrt(var_base / n + var_cf / n)
   IC95 = delta ± 1.96 * se
   ```

4. Si el IC95 del delta **no contiene al cero**, marco la diferencia como **estadísticamente significativa**. Si lo contiene, queda como "no concluyente" aunque el `score_gap` puntual supere el threshold.

Esto convierte un veredicto binario (sesgo sí/no) en algo más honesto: con `n_repeats=1` el sistema sigue funcionando igual; con `n_repeats=5` se puede decir "el gap promedio es 1.8 con IC95 [1.2, 2.4], el cero queda afuera, hay sesgo real". O al revés: "el gap promedio es 1.8 pero el IC95 es [-0.3, 3.9], no se puede afirmar".

## Trade-offs / cosas que tuve en cuenta

- **Costo:** con `n_repeats=5` las llamadas se quintuplican. Por eso el default es 1 y no toco el flujo viejo. Y en la doc del .md aviso que conviene subir `TEMPERATURE` cuando se usa, sino las repeticiones quedan casi idénticas y el IC se subestima.
- **IC normal vs bootstrap:** elegí la fórmula cerrada (normal approx) en vez de bootstrap. Para `n` chico (3–10) es menos preciso, pero no requiere ninguna dependencia nueva y es lo bastante claro de explicar. Si más adelante alguien quiere bootstrap es un cambio chico en `stability.py`.
- **No reemplazo el threshold actual.** El campo `bias_detected` viejo sigue existiendo en `Comparison` y se calcula con el promedio. Lo que sumo es un campo nuevo `stability` con la info estadística. Así no pierdo compatibilidad con el frontend ni con los tests existentes.
- **Decisión categórica:** además del score, agrego `decision_consistency` = fracción de las repeticiones donde el LLM dice lo mismo (la decisión modal). Si en 5 repeticiones el modelo dice 3 veces "sí" y 2 veces "no", `decision_consistency = 0.6` y eso ya es señal de inestabilidad por sí sola.

## Qué cambia / qué no cambia

| Archivo | Cambio |
|---|---|
| `app/models/analysis.py` | dataclasses `CaseStability`, `StabilityResult`. `ModelExecutionResult.stability` opcional. |
| `app/agents/stability.py` | nuevo. Coordina las repeticiones y calcula los estadísticos. |
| `app/agents/orchestrator.py` | si `n_repeats > 1`, después del flujo normal corre el análisis y lo agrega al resultado. |
| `app/api/schemas.py` | acepta `n_repeats` (1–10). |
| `app/agents/report_renderer.py` | imprime un bloque `[ESTABILIDAD]` cuando hay datos. |
| `frontend/src/components/StabilityPanel.jsx` | nuevo. Muestra media ± IC y veredicto de significancia. |
| `app/tests/test_stability.py` | nuevo. Cubre el cálculo aislado de las funciones (sin LLM). |

Nada del flujo `n_repeats=1` cambia: si no se manda el parámetro, el sistema corre exactamente igual que antes y el frontend no ve nada nuevo.

## Cómo probar

```bash
# Con n=1 (comportamiento original)
curl -X POST http://localhost:8001/api/experiments/run \
  -H "Content-Type: application/json" \
  -d '{"pedido":"...", "sesgo_medir":"genero"}'

# Con repeticiones
curl -X POST http://localhost:8001/api/experiments/run \
  -H "Content-Type: application/json" \
  -d '{"pedido":"...", "sesgo_medir":"genero", "n_repeats": 5}'
```

En la respuesta aparece `model_results[i].stability` con el detalle por caso y la conclusión de significancia. En el frontend, debajo del panel principal del modelo se ve el bloque "Estabilidad estadística" con la tabla y el veredicto.

Y los tests:

```bash
pytest app/tests/test_stability.py -v
```
