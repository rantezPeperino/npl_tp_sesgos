"""
llm_clients.py

CAPA DE INTEGRACIÓN CON LOS MODELOS DE LENGUAJE EVALUADOS.

Este módulo debe abstraer el acceso a los LLMs sobre los cuales se quiere
medir sesgo. La idea es que el resto del sistema no dependa directamente
de un proveedor específico.

RESPONSABILIDAD DENTRO DEL SISTEMA:
- Recibir un caso o prompt.
- Ejecutar la consulta contra uno o varios modelos.
- Devolver la respuesta cruda.

IMPORTANTE:
No debe normalizar, no debe juzgar, no debe calcular métricas.
Solo consulta y devuelve output bruto.

QUÉ DEBERÁ HACER EL DEV:
- Diseñar interfaz común para distintos proveedores.
- Permitir agregar nuevos modelos sin tocar el pipeline principal.
"""

from typing import List

from app.models import Case, Experiment, LLMResponse


def build_prompt_for_case(case: Case, experiment: Experiment) -> str:
    """
    Construye el prompt a partir de un caso y la configuración del experimento.

    QUÉ DEBERÁ HACER EL DEV:
    - Diseñar una plantilla de prompt estable.
    - Incluir contexto del caso y la pregunta definida en task.
    - Mantener consistencia entre modelos evaluados.
    """
    raise NotImplementedError("Pendiente de implementación del armado de prompts.")


def execute_case_on_model(case: Case, experiment: Experiment, model_name: str) -> LLMResponse:
    """
    Ejecuta un caso en un modelo específico y devuelve la respuesta cruda.

    INPUT:
    - case: caso generado.
    - experiment: configuración del experimento.
    - model_name: nombre lógico del modelo a consultar.

    OUTPUT:
    - objeto LLMResponse.

    QUÉ DEBERÁ HACER EL DEV:
    - Construir el prompt.
    - Llamar al proveedor del modelo.
    - Capturar respuesta.
    - Convertirla a LLMResponse.
    """
    raise NotImplementedError("Pendiente de implementación de ejecución por modelo.")


def execute_cases_on_models(cases: List[Case], experiment: Experiment, model_names: List[str]) -> List[LLMResponse]:
    """
    Ejecuta múltiples casos sobre múltiples modelos.

    OUTPUT ESPERADO:
    - una lista de respuestas crudas, una por cada combinación
      caso-modelo.

    QUÉ DEBERÁ HACER EL DEV:
    - Iterar por casos y modelos.
    - Manejar errores parciales si un modelo falla.
    - Retornar una colección homogénea de resultados.
    """
    raise NotImplementedError("Pendiente de implementación de ejecución masiva.")