# Skill — Normalizer

**Módulo**: [app/normalizer.py](../app/normalizer.py)

## Rol

Toma las respuestas crudas del LLM y produce un schema estructurado y
comparable. Le agrega los metadatos necesarios para que el control y las
métricas puedan trabajar.

## Contrato

```python
def normalize_responses(responses: List[LLMResponse], experiment: Experiment) -> List[NormalizedOutput]
def normalize_response(response: LLMResponse, experiment: Experiment) -> NormalizedOutput
def validate_normalized_output(output: NormalizedOutput, experiment: Experiment) -> bool
```

## Qué produce

```python
@dataclass
class NormalizedOutput:
    model_name: str
    case_id: str
    decision: str
    score: float
    doubt_flag: bool
    justification: str
    bias_detected: bool       # se llena después en el orquestador
    bias_category: Optional[str]
```

## Pasos del parser

1. **JSON estricto**: intenta `json.loads(raw)`.
2. **JSON embebido**: si falla, busca el primer `{` y último `}` y reintenta.
3. **Fallback texto**: regex para extraer un número como score, busca la
   palabra "no" entre las opciones permitidas, deja `doubt_flag=True`.

## Tolerancia a llaves en español/inglés

| Concepto      | Llaves aceptadas                                                                  |
|---------------|-----------------------------------------------------------------------------------|
| decisión      | `decision`, `decisión`, `decisión_final`, `respuesta`                             |
| score         | `score`, `puntaje`, `puntuación`, `puntuacion`, `calificacion`, `calificación`    |
| justificación | `justification`, `justificación`, `justificacion`, `razon`, `razón`               |

## Detección de duda (`doubt_flag`)

Se activa cuando la justificación contiene alguna keyword:
`aunque, habría, dudas, no estoy seguro, podría, quizás, sin embargo, pero`.

## Normalización del score

- Castea a `float`.
- Si está fuera del rango `[score_scale_min, score_scale_max]`, lo recorta y
  setea `doubt_flag=True`.

## Reglas críticas

- No detecta sesgo (eso es trabajo del control).
- No emite warnings: si una respuesta no parsea, deja `decision="si"` y
  `score=5.0` con `doubt_flag=True` y `justification` con el raw recortado.
