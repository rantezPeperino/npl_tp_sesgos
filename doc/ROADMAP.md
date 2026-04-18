```textmate
# División Conceptual del Trabajo en Paralelo

La idea es dividir el desarrollo en dos flujos que puedan avanzar en paralelo, pero con un punto de integración claro.

- **Dev 1** se enfoca en la parte de **entrada + ejecución del experimento**
- **Dev 2** se enfoca en la parte de **interpretación + evaluación del resultado**

---

## Vista General

```text
                    tiltDetector
                         |
     -------------------------------------------------
     |                                               |
     |                                               |
     v                                               v

+-----------------------------+         +-----------------------------+
| DEV 1                       |         | DEV 2                       |
| Entrada + Ejecución         |         | Normalización + Evaluación  |
+-----------------------------+         +-----------------------------+
| - API                       |         | - Normalizer                |
| - Models base               |         | - Judge                     |
| - Case Generator            |         | - Metrics                   |
| - LLM Clients               |         | - Output final JSON         |
| - Repository (raw)          |         | - Repository (processed)    |
| - Orchestrator (parte 1)    |         | - Orchestrator (parte 2)    |
+-----------------------------+         +-----------------------------+
     |                                               |
     |                                               |
     ------------------- Punto de Integración -------------------
                             |
                             v
              Contratos JSON compartidos entre módulos
              
              
  


```


```textmate
Cliente externo
    |
    v
 API REST
    |
    v
 [DEV 1]
    |
    |--> recibe JSON de entrada
    |--> valida estructura
    |--> genera casos base y contrafactuales
    |--> consulta LLMs evaluados
    |--> guarda respuestas crudas
    |
    v
  RAW OUTPUT
    |
    |========== handoff entre Dev 1 y Dev 2 ==========
    |
    v
 [DEV 2]
    |
    |--> normaliza respuestas
    |--> compara casos equivalentes
    |--> detecta sesgo
    |--> calcula métricas
    |--> arma JSON final de salida
    |--> guarda resultados procesados
    |
    v
 Response JSON final

```

```textmate
┌─────────────────────────────────────────────────────────────────────┐
│ DEV 1: ARMAR Y EJECUTAR EL EXPERIMENTO                             │
├─────────────────────────────────────────────────────────────────────┤
│ 1. Recibir JSON desde la API                                       │
│ 2. Validar y mapear input a modelos internos                       │
│ 3. Generar casos base y contrafactuales                            │
│ 4. Preparar prompts / requests para los LLMs evaluados             │
│ 5. Ejecutar consultas sobre los modelos                            │
│ 6. Guardar respuestas crudas                                       │
│ 7. Entregar raw output al siguiente tramo                          │
└─────────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────┐
│ DEV 2: INTERPRETAR Y EVALUAR EL EXPERIMENTO                        │
├─────────────────────────────────────────────────────────────────────┤
│ 1. Recibir raw output de los LLMs                                  │
│ 2. Normalizar respuestas a un schema común                         │
│ 3. Comparar casos base vs contrafactuales                          │
│ 4. Detectar si hay sesgo                                           │
│ 5. Clasificar categoría de sesgo                                   │
│ 6. Calcular métricas                                               │
│ 7. Construir salida JSON final                                     │
│ 8. Guardar resultados procesados                                   │
└─────────────────────────────────────────────────────────────────────┘

```