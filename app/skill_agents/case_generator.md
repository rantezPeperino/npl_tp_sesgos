# Skill — Case Generator

**Módulo**: [app/case_generator.py](../app/case_generator.py)

## Rol

A partir del JSON universal del prompt_normalizer, produce **exactamente 3 casos**:

| case_type        | Rol en el experimento                                                          |
|------------------|--------------------------------------------------------------------------------|
| `base`           | Caso principal con el valor "estándar" del atributo del sesgo.                 |
| `counterfactual` | Idéntico al base pero **solo cambia el atributo del sesgo**.                   |
| `negative`       | Testigo de control: debe ser **rechazado** (`decision == "no"`) por el modelo. |

## Contrato

```python
def generate_cases(
    experiment: Experiment,
    prompt_text: str,
    variation: Dict[str, Any],
) -> List[Case]
```

## Qué produce

Cada `Case` es minimalista — sin duplicar `task`, `evaluation_constraints` ni `metadata`:

```python
@dataclass
class Case:
    case_id: str          # exp_<dim>_<hex>_<case_type>_<slug(value)>
    case_type: str        # base | counterfactual | negative
    attribute_value: str  # ej. "hombre" / "mujer" / "sin especificar género"
    rendered_prompt: str  # texto efectivamente enviado al LLM
    based_on: Optional[str]  # case_id del base (para cf y negative)
```

## Reglas críticas

- Falla si `placeholder` (ej. `{{SESGO}}`) no aparece en `prompt_text`.
- El reemplazo es por sustitución de string — no llama a un LLM.
- Solo un atributo cambia entre `base` y `counterfactual` (la dimensión del sesgo).
- El testigo siempre tiene un valor "neutral / no especificado" para forzar rechazo.

## Por qué Case es minimal

El antiguo `Case.input_payload` duplicaba `task`, `evaluation_constraints`,
`metadata` y `variation` por cada caso. Esos datos viven en el `Experiment`,
así que el caso solo aporta lo único: el prompt renderizado y el valor del
atributo.
