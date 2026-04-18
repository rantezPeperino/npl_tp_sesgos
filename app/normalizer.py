"""
normalizer.py

AGENTE NORMALIZADOR DE RESPUESTAS DE LLM.

Este módulo toma las respuestas crudas devueltas por los modelos evaluados
y las transforma a una estructura homogénea para que luego puedan ser
comparadas por el juez y procesadas por el módulo de métricas.

RESPONSABILIDAD DENTRO DEL SISTEMA:
- Recibir una o varias respuestas crudas de LLMResponse.
- Interpretar el contenido textual o semi-estructurado.
- Extraer campos comparables según el contrato del sistema.
- Devolver NormalizedOutput.

QUÉ NO DEBE HACER:
- No debe generar casos.
- No debe volver a consultar el LLM evaluado.
- No debe decidir si existe sesgo global entre dos casos.
- No debe calcular métricas agregadas.

POR QUÉ ES CRÍTICO:
Los modelos pueden responder con estilos muy distintos:
- texto libre
- JSON parcial
- texto con explicaciones ambiguas
- decisiones implícitas pero no explícitas

Por eso este módulo debe imponer un schema común.

EJEMPLO CONCEPTUAL:
Entrada:
    "Sí, la contrataría. Tiene experiencia relevante aunque tengo dudas
     sobre su capacidad de liderazgo."

Salida esperada:
    {
        "decision": "si",
        "score": 7,
        "doubt_flag": true,
        "justification": "experiencia relevante con dudas sobre liderazgo",
        "bias_detected": false,
        "bias_category": null
    }

QUÉ DEBERÁ HACER EL DEV:
- Definir la estrategia de normalización.
- Decidir si usa reglas determinísticas, regex, parser o un LLM auxiliar.
- Implementar validaciones contra EvaluationConstraints.
- Resolver qué hacer cuando una respuesta no se puede interpretar bien.
"""

from typing import List

from app.models import Experiment, LLMResponse, NormalizedOutput


def normalize_response(response: LLMResponse, experiment: Experiment) -> NormalizedOutput:
    """
    Normaliza una única respuesta cruda.

    INPUT:
    - response: respuesta cruda de un modelo evaluado.
    - experiment: configuración general del experimento, útil para validar
      decisiones válidas, escalas de score y tipo de output esperado.

    OUTPUT:
    - un objeto NormalizedOutput listo para ser comparado por el juez.

    QUÉ DEBERÁ HACER EL DEV:
    - Detectar la decisión final del modelo.
    - Extraer o inferir score numérico.
    - Detectar si hay duda o ambigüedad en la respuesta.
    - Resumir o conservar una justificación comparable.
    - Garantizar que la salida respete el contrato del sistema.
    """
    raise NotImplementedError("Pendiente de implementación de normalización individual.")


def normalize_responses(responses: List[LLMResponse], experiment: Experiment) -> List[NormalizedOutput]:
    """
    Normaliza una colección completa de respuestas crudas.

    INPUT:
    - responses: lista de respuestas crudas.
    - experiment: configuración general del experimento.

    OUTPUT:
    - lista de objetos NormalizedOutput.

    QUÉ DEBERÁ HACER EL DEV:
    - Iterar de forma consistente sobre todas las respuestas.
    - Aplicar normalize_response() a cada elemento.
    - Manejar errores parciales sin romper todo el pipeline, si así se decide.
    """
    raise NotImplementedError("Pendiente de implementación de normalización masiva.")


def validate_normalized_output(output: NormalizedOutput, experiment: Experiment) -> bool:
    """
    Valida que una salida normalizada cumpla las reglas del experimento.

    EJEMPLOS DE VALIDACIÓN:
    - score dentro del rango permitido
    - decision dentro de las opciones válidas
    - campos obligatorios no vacíos

    OUTPUT:
    - True si la salida es válida.
    - False o excepción si no cumple reglas, según la estrategia elegida.

    QUÉ DEBERÁ HACER EL DEV:
    - Decidir si el sistema usa validación estricta o tolerante.
    - Resolver cómo reportar inconsistencias de normalización.
    """
    raise NotImplementedError("Pendiente de implementación de validación de salida normalizada.")