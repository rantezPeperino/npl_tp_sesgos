# Diagrama ASCII del Flujo Entre Agentes

Tomando la división en 2 desarrolladores, y mostrando **solo los agentes que intervienen**, el flujo queda así:

```text
┌───────────────────────────────────────┐
│ Agente Generador de Casos             │
│ - crea caso base                      │
│ - crea contrafactuales                │
└───────────────────────┬───────────────┘
                        │
                        │ entrega casos generados
                        v
┌───────────────────────────────────────┐
│ Agente Ejecutor LLM                   │
│ - arma consulta al modelo             │
│ - obtiene respuesta cruda             │
└───────────────────────┬───────────────┘
                        │
                        │ entrega raw output
                        v
┌───────────────────────────────────────┐
│ Agente Normalizador                   │
│ - transforma texto libre              │
│   a schema estructurado               │
└───────────────────────┬───────────────┘
                        │
                        │ entrega output normalizado
                        v
┌───────────────────────────────────────┐
│ Agente Juez / Evaluador               │
│ - compara caso base                   │
│   vs contrafactual                    │
│ - detecta sesgo                       │
└───────────────────────┬───────────────┘
                        │
                        │ entrega resultado evaluado
                        v
┌───────────────────────────────────────┐
│ Agente de Métricas                    │
│ - calcula gap de score                │
│ - tasa de sesgo                       │
│ - consistencia                        │
└───────────────────────────────────────┘

```


```text
Agente Generador
    → Agente Ejecutor LLM
    → Agente Normalizador
    → Agente Juez / Evaluador
    → Agente de Métricas

```

```textmate
Agente Generador de Casos
    │
    ├── genera:
    │      cases[]
    │
    v
Agente Ejecutor LLM
    │
    ├── genera:
    │      raw_responses[]
    │
    v
Agente Normalizador
    │
    ├── genera:
    │      normalized_outputs[]
    │
    v
Agente Juez / Evaluador
    │
    ├── genera:
    │      evaluations[]
    │
    v
Agente de Métricas
    │
    └── genera:
           metrics[]
```

```textmate
[DEV 1]
Agente Generador de Casos
    → Agente Ejecutor LLM

[DEV 2]
Agente Normalizador
    → Agente Juez / Evaluador
    → Agente de Métricas
```
```textmate
┌──────────────┐
│ Generador    │
└──────┬───────┘
       v
┌──────────────┐
│ Ejecutor LLM │
└──────┬───────┘
       v
┌──────────────┐
│ Normalizador │
└──────┬───────┘
       v
┌──────────────┐
│ Juez         │
└──────┬───────┘
       v
┌──────────────┐
│ Métricas     │
└──────────────┘
```
