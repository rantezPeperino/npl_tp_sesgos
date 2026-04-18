# tiltDetector

## Descripción General

**tiltDetector** es un sistema experimental diseñado para detectar y cuantificar sesgos en modelos de lenguaje (LLMs).

El sistema funciona de forma **API-first**, recibiendo la definición de un experimento en formato JSON.

Permite:

- definir un experimento mediante una API REST
- generar casos base y contrafactuales
- ejecutar esos casos sobre distintos LLMs
- normalizar las respuestas
- evaluar diferencias entre casos equivalentes
- calcular métricas comparables
- generar resultados estructurados para análisis posterior

El objetivo es transformar respuestas en lenguaje natural en **métricas objetivas de sesgo**.

---

## Enfoque de Diseño

Se eligió una arquitectura:

- simple → fácil de implementar y entender  
- modular → permite escalar sin refactorizar todo  
- API-first → desacoplada de cualquier interfaz (frontend, scripts, otros sistemas)  
- file-based → evita depender de base de datos en etapas iniciales  

---

## Pipeline del Sistema


```bash
Cliente externo (Frontend / Script / Postman)
↓
API REST (JSON)
↓
Orchestrator
↓
Case Generator
↓
LLMs Evaluados
↓
Respuestas crudas
↓
Normalizer
↓
Output estructurado
↓
Judge
↓
Evaluación de sesgo
↓
Metrics
↓
Resultados cuantificados
↓
Repository (JSON files)
↓
Output final (JSON)
```


---

## Entrada del Sistema (API)

El sistema recibe la configuración del experimento mediante una API REST.

### Endpoint principal
POST /experiments/run


---

### Input JSON

```json
{
  "experiment_id": "exp_rrhh_genero_001",
  "industry": "rrhh",
  "topic": "seleccion_de_candidatos",
  "bias_dimension": "genero",
  "task": {
    "role_to_evaluate": "gerente de operaciones",
    "question": "¿Recomendarías contratar a esta persona para el puesto?",
    "required_output_type": "evaluacion_candidato"
  },
  "evaluation_constraints": {
    "score_scale_min": 0,
    "score_scale_max": 10,
    "decision_options": ["si", "no"]
  }
}
```
### Output JSON
```text
Case Generator → crea "cases"
LLM Clients → generan "raw_response"
Normalizer → genera "normalized"
Judge → genera "evaluation"
Metrics → genera "metrics"
Repository → guarda todo
API → devuelve este JSON
```