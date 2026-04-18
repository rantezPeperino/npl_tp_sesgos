"""
orchestrator.py

COORDINADOR PRINCIPAL DEL PIPELINE END-TO-END.

Este módulo conecta todos los componentes del sistema en el orden correcto.
Su responsabilidad no es implementar la lógica profunda de cada agente,
sino invocar cada tramo del flujo y consolidar el resultado final.

RESPONSABILIDAD DENTRO DEL SISTEMA:
- Construir el experimento a partir del payload de entrada.
- Generar casos.
- Ejecutar los casos sobre los LLMs.
- Persistir respuestas crudas.
- Normalizar respuestas.
- Evaluar comparaciones.
- Calcular métricas.
- Persistir resultados finales.
- Devolver el resultado completo a la API.

QUÉ NO DEBE HACER:
- No debe reimplementar la lógica de generación.
- No debe interpretar directamente texto crudo.
- No debe contener fórmulas de métricas.
- No debe exponer endpoints HTTP.

QUÉ DEBERÁ HACER EL DEV:
- Definir claramente el orden de ejecución.
- Decidir qué hacer ante errores parciales.
- Consolidar la estructura final de salida.
"""

from typing import Any, Dict, List

from app.models import (
    EvaluationComparison,
    Experiment,
    ExperimentResult,
    LLMResponse,
    MetricsResult,
    NormalizedOutput,
)


def build_experiment_from_payload(payload: Dict[str, Any]) -> Experiment:
    """
    Convierte el JSON de entrada de la API a un objeto Experiment.

    INPUT:
    - payload: diccionario recibido por API.

    OUTPUT:
    - objeto Experiment.

    QUÉ DEBERÁ HACER EL DEV:
    - mapear estructuras anidadas como task y evaluation_constraints.
    - validar campos mínimos antes de construir el modelo.
    """
    raise NotImplementedError("Pendiente de implementación de mapeo payload -> Experiment.")


def run_experiment(payload: Dict[str, Any], model_names: List[str]) -> ExperimentResult:
    """
    Ejecuta el pipeline completo del sistema.

    FLUJO ESPERADO:
    1. Construir Experiment.
    2. Generar casos.
    3. Ejecutar casos sobre modelos.
    4. Persistir raw responses.
    5. Normalizar respuestas.
    6. Evaluar comparaciones.
    7. Calcular métricas.
    8. Construir resultado final.
    9. Persistir resultado final.
    10. Retornar ExperimentResult.

    INPUT:
    - payload: JSON de entrada.
    - model_names: lista de nombres lógicos de modelos a evaluar.

    OUTPUT:
    - objeto ExperimentResult.

    QUÉ DEBERÁ HACER EL DEV:
    - integrar correctamente los módulos del proyecto.
    - decidir estrategia de logging y manejo de excepciones.
    - garantizar que el resultado sea serializable por la API.
    """
    raise NotImplementedError("Pendiente de implementación del pipeline completo.")


def assemble_experiment_result(
    experiment: Experiment,
    cases: List[Dict[str, Any]],
    raw_responses: List[LLMResponse],
    normalized_outputs: List[NormalizedOutput],
    comparisons_by_model: Dict[str, List[EvaluationComparison]],
    metrics_by_model: Dict[str, MetricsResult],
    global_summary: Dict[str, Any],
) -> ExperimentResult:
    """
    Arma el objeto final de salida del sistema.

    OBJETIVO:
    - consolidar todos los artefactos intermedios en una única estructura
      coherente con el contrato final de la API.

    QUÉ DEBERÁ HACER EL DEV:
    - decidir si guarda payload final ya serializado o estructuras tipadas.
    - mantener compatibilidad con README y con el contrato JSON acordado.
    """
    raise NotImplementedError("Pendiente de implementación del ensamblado del resultado final.")