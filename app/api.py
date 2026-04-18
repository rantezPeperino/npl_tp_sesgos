"""
api.py

CAPA DE EXPOSICIÓN HTTP DEL SISTEMA.

Este módulo representa la puerta de entrada al sistema.
Recibe requests externos, valida el JSON de entrada, invoca el orquestador
y devuelve una respuesta estructurada.

RESPONSABILIDAD DENTRO DEL PROYECTO:
- Exponer endpoints REST.
- Parsear y validar input.
- Llamar al orquestador.
- Traducir resultados internos a respuestas HTTP.

NO DEBE HACER:
- Lógica de negocio profunda.
- Generación de casos directamente.
- Consultas a LLM directamente.
- Evaluación de sesgo directamente.

ENDPOINTS ESPERADOS:
- POST /experiments/run
- GET /experiments/{experiment_id}
- GET /health

QUÉ DEBERÁ HACER EL DEV:
- Elegir framework HTTP.
- Definir request models si usa validación tipada.
- Conectar con orchestrator.py.
- Manejar errores y status codes.
"""

from typing import Any, Dict


def create_app() -> Any:
    """
    Crea y devuelve la aplicación HTTP.

    QUÉ DEBERÁ HACER EL DEV:
    - Instanciar la app web.
    - Registrar endpoints.
    - Conectar handlers con el orquestador.
    - Retornar el objeto app del framework elegido.

    RETURN:
    - Objeto app del framework HTTP.
    """
    raise NotImplementedError("Pendiente de implementación de la aplicación HTTP.")


def run_experiment_endpoint(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Endpoint lógico para ejecutar un experimento.

    INPUT:
    - payload: JSON de entrada con la configuración del experimento.

    OUTPUT:
    - JSON final del sistema con casos, resultados normalizados,
      evaluación y métricas.

    QUÉ DEBERÁ HACER EL DEV:
    - Validar estructura del payload.
    - Convertir el payload a modelos internos si corresponde.
    - Invocar al orquestador para correr el experimento.
    - Devolver el resultado final.

    NOTA:
    En implementación real este comportamiento estará asociado al handler
    del POST /experiments/run.
    """
    raise NotImplementedError("Pendiente de implementación del endpoint de ejecución.")


def get_experiment_result_endpoint(experiment_id: str) -> Dict[str, Any]:
    """
    Endpoint lógico para consultar resultados previamente persistidos.

    INPUT:
    - experiment_id: identificador único del experimento.

    OUTPUT:
    - JSON con el resultado persistido.

    QUÉ DEBERÁ HACER EL DEV:
    - Buscar el experimento en repository.py.
    - Manejar caso no encontrado.
    - Devolver el JSON almacenado.
    """
    raise NotImplementedError("Pendiente de implementación del endpoint de consulta.")


def healthcheck_endpoint() -> Dict[str, str]:
    """
    Endpoint lógico de health check.

    OUTPUT:
    - JSON mínimo que indique que el servicio está operativo.

    EJEMPLO ESPERADO:
    {
        "status": "ok"
    }

    QUÉ DEBERÁ HACER EL DEV:
    - Retornar un estado simple para monitoreo y pruebas rápidas.
    """
    raise NotImplementedError("Pendiente de implementación del health check.")