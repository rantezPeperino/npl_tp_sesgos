"""
judge.py

AGENTE JUEZ / EVALUADOR DE SESGO.

Este módulo recibe outputs ya normalizados y compara casos equivalentes
para detectar si existen diferencias potencialmente atribuibles a la
dimensión sensible estudiada.

RESPONSABILIDAD DENTRO DEL SISTEMA:
- Comparar un caso base con uno o más contrafactuales.
- Medir cambios de score y de decisión.
- Determinar si hay evidencia de sesgo.
- Clasificar el tipo de sesgo si corresponde.

QUÉ NO DEBE HACER:
- No debe generar casos.
- No debe consultar directamente a los LLMs evaluados.
- No debe producir métricas agregadas finales del experimento.
- No debe persistir resultados.

POR QUÉ ES CRÍTICO:
Es el componente que transforma outputs normalizados en un juicio
comparativo sobre el comportamiento del modelo.

EJEMPLO CONCEPTUAL:
Caso base:
- decision = "si"
- score = 9

Contrafactual:
- decision = "no"
- score = 6

Posible resultado:
- score_gap = 3
- decision_change = True
- bias_detected = True
- bias_category = "gender"

QUÉ DEBERÁ HACER EL DEV:
- Definir criterios de comparación.
- Parametrizar umbrales de score_gap si corresponde.
- Asegurar que solo se comparen casos equivalentes.
"""

from typing import Dict, List, Tuple

from app.models import EvaluationComparison, Experiment, NormalizedOutput


def group_outputs_by_model(outputs: List[NormalizedOutput]) -> Dict[str, List[NormalizedOutput]]:
    """
    Agrupa los outputs normalizados por modelo.

    OUTPUT:
    - diccionario cuya clave es model_name y cuyo valor es la lista de
      outputs de ese modelo.

    QUÉ DEBERÁ HACER EL DEV:
    - Mantener una estructura útil para evaluación por modelo.
    - Facilitar procesamiento posterior del juez y de métricas.
    """
    raise NotImplementedError("Pendiente de implementación de agrupamiento por modelo.")


def find_comparable_case_pairs(outputs: List[NormalizedOutput], experiment: Experiment) -> List[Tuple[NormalizedOutput, NormalizedOutput]]:
    """
    Identifica pares comparables entre outputs normalizados.

    OBJETIVO:
    - encontrar qué outputs representan un caso base y su contrafactual
      dentro de un mismo modelo.

    OUTPUT:
    - lista de tuplas (base_output, counterfactual_output)

    QUÉ DEBERÁ HACER EL DEV:
    - definir cómo se recupera la relación entre casos.
    - asegurar que los pares sean realmente comparables.
    """
    raise NotImplementedError("Pendiente de implementación de búsqueda de pares comparables.")


def compare_case_pair(
    base_output: NormalizedOutput,
    counterfactual_output: NormalizedOutput,
    experiment: Experiment,
) -> EvaluationComparison:
    """
    Compara un único par de outputs equivalentes.

    INPUT:
    - base_output: salida normalizada del caso base.
    - counterfactual_output: salida normalizada del caso contrafactual.
    - experiment: configuración del experimento.

    OUTPUT:
    - objeto EvaluationComparison.

    QUÉ DEBERÁ HACER EL DEV:
    - calcular score_gap.
    - detectar cambio de decisión.
    - aplicar reglas para decidir bias_detected.
    - clasificar bias_category si corresponde.
    """
    raise NotImplementedError("Pendiente de implementación de comparación individual.")


def evaluate_outputs(outputs: List[NormalizedOutput], experiment: Experiment) -> Dict[str, List[EvaluationComparison]]:
    """
    Evalúa todos los outputs normalizados y devuelve comparaciones por modelo.

    OUTPUT ESPERADO:
    - diccionario:
      {
          "llm_a": [EvaluationComparison, ...],
          "llm_b": [EvaluationComparison, ...]
      }

    QUÉ DEBERÁ HACER EL DEV:
    - agrupar por modelo.
    - encontrar pares comparables.
    - comparar cada par.
    - devolver un resultado homogéneo y fácil de consumir por metrics.py.
    """
    raise NotImplementedError("Pendiente de implementación de evaluación completa.")