"""
repository.py

CAPA DE PERSISTENCIA BASADA EN ARCHIVOS JSON.

Este módulo abstrae la lectura y escritura de datos en disco.
En esta primera versión del sistema se eligió persistencia simple en archivos
para evitar complejidad innecesaria de base de datos.

RESPONSABILIDAD DENTRO DEL SISTEMA:
- Guardar inputs, respuestas crudas y resultados procesados.
- Recuperar resultados por experiment_id.
- Organizar rutas y nombres de archivos de salida.

QUÉ NO DEBE HACER:
- No debe decidir lógica de negocio.
- No debe construir métricas.
- No debe generar casos.
- No debe exponer endpoints HTTP.

ESTRATEGIA RECOMENDADA:
- usar archivos JSON
- separar raw, normalized, evaluation, final_result
- mantener trazabilidad por experiment_id

QUÉ DEBERÁ HACER EL DEV:
- definir layout de carpetas final.
- asegurar serialización segura de dataclasses o modelos.
- decidir si sobreescribe, versiona o agrega timestamp.
"""

from pathlib import Path
from typing import Any, Dict, List

from app.models import ExperimentResult, LLMResponse, NormalizedOutput


BASE_DATA_DIR = Path("data")
INPUT_DIR = BASE_DATA_DIR / "input"
OUTPUT_DIR = BASE_DATA_DIR / "output"
RAW_DIR = OUTPUT_DIR / "raw"
NORMALIZED_DIR = OUTPUT_DIR / "normalized"
EVALUATION_DIR = OUTPUT_DIR / "evaluation"
FINAL_RESULT_DIR = OUTPUT_DIR / "final"


def ensure_directories() -> None:
    """
    Crea las carpetas necesarias de persistencia si no existen.

    QUÉ DEBERÁ HACER EL DEV:
    - crear directorios base del proyecto.
    - decidir si esta inicialización se hace al arranque o bajo demanda.
    """
    raise NotImplementedError("Pendiente de implementación de creación de directorios.")


def save_input_payload(experiment_id: str, payload: Dict[str, Any]) -> str:
    """
    Guarda el payload original recibido por la API.

    OUTPUT:
    - ruta o identificador del archivo guardado.

    QUÉ DEBERÁ HACER EL DEV:
    - serializar correctamente el diccionario.
    - decidir convención de nombres.
    """
    raise NotImplementedError("Pendiente de implementación de guardado de input.")


def save_raw_responses(experiment_id: str, responses: List[LLMResponse]) -> str:
    """
    Guarda las respuestas crudas devueltas por los modelos.

    OUTPUT:
    - ruta o identificador del archivo guardado.

    QUÉ DEBERÁ HACER EL DEV:
    - convertir LLMResponse a JSON serializable.
    - persistir de forma trazable por experimento.
    """
    raise NotImplementedError("Pendiente de implementación de guardado de raw responses.")


def save_normalized_outputs(experiment_id: str, outputs: List[NormalizedOutput]) -> str:
    """
    Guarda outputs normalizados.

    OUTPUT:
    - ruta o identificador del archivo guardado.

    QUÉ DEBERÁ HACER EL DEV:
    - serializar NormalizedOutput.
    - usar un layout consistente con el resto de la persistencia.
    """
    raise NotImplementedError("Pendiente de implementación de guardado de normalizados.")


def save_evaluation_payload(experiment_id: str, payload: Dict[str, Any]) -> str:
    """
    Guarda el resultado intermedio de evaluación producido por el juez y métricas.

    OUTPUT:
    - ruta o identificador del archivo guardado.

    QUÉ DEBERÁ HACER EL DEV:
    - decidir el nivel de granularidad de este artefacto intermedio.
    """
    raise NotImplementedError("Pendiente de implementación de guardado de evaluación.")


def save_final_result(result: ExperimentResult) -> str:
    """
    Guarda el resultado final completo del experimento.

    OUTPUT:
    - ruta o identificador del archivo guardado.

    QUÉ DEBERÁ HACER EL DEV:
    - serializar el objeto final.
    - alinear el formato con lo que luego devolverá la API.
    """
    raise NotImplementedError("Pendiente de implementación de guardado final.")


def load_experiment_result(experiment_id: str) -> Dict[str, Any]:
    """
    Recupera un resultado final previamente persistido.

    INPUT:
    - experiment_id: identificador único del experimento.

    OUTPUT:
    - diccionario con el resultado final, listo para ser devuelto por la API.

    QUÉ DEBERÁ HACER EL DEV:
    - localizar el archivo correcto.
    - manejar archivo inexistente.
    - retornar una estructura JSON-compatible.
    """
    raise NotImplementedError("Pendiente de implementación de carga de resultado final.")