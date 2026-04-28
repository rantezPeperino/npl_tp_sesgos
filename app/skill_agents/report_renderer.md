# Skill — Report Renderer

**Módulo**: [app/report_renderer.py](../app/report_renderer.py)

## Rol

Convierte un `ExperimentResult` en un reporte de terminal legible para
humanos, agrupado por LLM. **No agrega ni recomputa información**: solo
formatea lo que ya está en el resultado.

## Contrato

```python
def render_terminal_report(result: ExperimentResult) -> str
```

## Estructura del reporte

```
============================================================
[EXPERIMENTO]
id: <experiment_id>
rubro: <industry>
tema: <topic>
sesgo_medido: <bias_dimension>
============================================================

[PROMPT INICIAL DEL EXPERIMENTO]
<source_pedido>

[CASOS GENERADOS POR EL ORQUESTADOR]
- BASE: case_id=...  |  <bias_dimension>=<attribute_value>
- COUNTERFACTUAL: ...
- NEGATIVE: ...

============================================================
[LLM] <model_name>
============================================================
------------------------------
[CASO BASE]
case_id: ...
>> PROMPT ENVIADO AL LLM:
<rendered_prompt>
>> RESPUESTA CRUDA:
<raw_response>
>> NORMALIZACIÓN:
decision / score / doubt_flag / bias_detected / justification

[CASO CONTRAFACTUAL]
... (mismo formato)

[CASO TESTIGO]
... + control_expected: no, control_ok: <bool>

------------------------------
[COMPARACION base vs contrafactual]
score_gap / decision_changed / bias_intensity / bias_detected / control_validation

------------------------------
[CONCLUSION]
<texto condicional según bias_intensity y control_validation>
```

## Conclusión condicional

| `bias_intensity` | Texto                                      |
|------------------|--------------------------------------------|
| `none`           | "No se detecta sesgo relevante."           |
| `low`            | "Se detecta una leve diferencia."          |
| `medium`         | "Posible sesgo moderado detectado."        |
| `high`           | "Sesgo fuerte detectado."                  |

Si `control_validation == false`, se agrega:
> "El modelo falla en el caso de control, resultados no confiables."

## Reglas críticas

- Stateless. No persiste, no muta, solo renderiza.
- Usa el `case_type` del `Case` para identificar base/cf/negative (no parsea `case_id`).
