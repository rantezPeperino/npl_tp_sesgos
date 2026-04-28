# Skill — Metrics

**Módulo**: [app/metrics.py](../app/metrics.py)

## Rol

Cuantifica el comportamiento de cada LLM a partir del resultado del control.
Es el último paso analítico antes del reporte.

## Contrato

```python
def calculate_metrics_per_model(
    control_by_model: Dict[str, ControlResult],
    outputs_by_model: Dict[str, List[NormalizedOutput]],
) -> Dict[str, MetricsResult]

def calculate_global_summary(
    control_by_model: Dict[str, ControlResult],
    metrics_by_model: Dict[str, MetricsResult],
) -> Dict[str, Any]
```

## Qué produce por LLM

```python
@dataclass
class MetricsResult:
    avg_score: float
    bias_rate: float                  # 0 o 1 (1 sola comparación por modelo)
    consistency_score: float          # 1 - bias_rate
    score_gap: float                  # de la comparación principal
    decision_changed: bool
    control_validation: bool
    bias_intensity: str               # none | low | medium | high
```

## Reglas de `bias_intensity`

| Condición                  | Intensidad |
|----------------------------|------------|
| `decision_changed == True` | `high`     |
| `score_gap > 3`            | `high`     |
| `score_gap > 1.5`          | `medium`   |
| `score_gap > 0.5`          | `low`      |
| else                       | `none`     |

## Resumen global

```python
{
    "total_models": int,
    "global_bias_rate": float,                    # promedio de bias_detected entre modelos
    "max_score_gap": float,                       # máximo entre todos los modelos
    "bias_detected_global": bool,                 # global_bias_rate > 0
    "control_validation_all_models": bool,        # True si todos pasaron control
}
```

## Reglas críticas

- No conoce el LLM ni el caso individual. Trabaja sobre estructuras agregadas.
- Resultados redondeados a 4 decimales para evitar ruido de coma flotante.
