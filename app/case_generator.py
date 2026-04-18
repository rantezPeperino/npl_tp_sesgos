"""
case_generator.py

AGENTE GENERADOR DE CASOS Y CONTRAFACTUALES.

Este módulo se encarga de construir los escenarios experimentales que luego
serán ejecutados sobre los LLMs evaluados.

RESPONSABILIDAD DENTRO DEL SISTEMA:
- Crear uno o más casos base.
- Generar variantes contrafactuales.
- Alterar únicamente el atributo sensible o el conjunto de atributos
  definidos por la lógica del experimento.
- Garantizar comparabilidad entre casos.

EJEMPLO:
Caso base:
- nombre: Juan
- género: masculino
- experiencia: 10

Contrafactual:
- nombre: Juana
- género: femenino
- experiencia: 10

IMPORTANTE:
La lógica de este módulo define la calidad del experimento.
Si cambia más de una variable relevante sin control, la medición de sesgo
pierde validez.

QUÉ DEBERÁ HACER EL DEV:
- Diseñar reglas de generación.
- Decidir si parte de plantillas fijas o de input enriquecido.
- Implementar validaciones para asegurar comparabilidad.
"""

from typing import List

from app.models import Case, Experiment


def generate_cases(experiment: Experiment) -> List[Case]:
    """
    Genera todos los casos necesarios para un experimento.

    INPUT:
    - experiment: configuración general del experimento.

    OUTPUT:
    - lista de casos generados.

    QUÉ DEBERÁ HACER EL DEV:
    - Crear al menos un caso base.
    - Crear sus contrafactuales asociados.
    - Asignar case_id únicos.
    - Etiquetar correctamente base/counterfactual/control si corresponde.
    """
    raise NotImplementedError("Pendiente de implementación de la generación de casos.")


def generate_base_case(experiment: Experiment) -> Case:
    """
    Genera el caso base inicial para el experimento.

    QUÉ DEBERÁ HACER EL DEV:
    - Definir cómo se arma el input base a partir del experimento.
    - Construir el payload del caso.
    """
    raise NotImplementedError("Pendiente de implementación del caso base.")


def generate_counterfactual_cases(base_case: Case, experiment: Experiment) -> List[Case]:
    """
    Genera uno o más contrafactuales a partir de un caso base.

    REGLA GENERAL:
    - cambiar solo la dimensión sensible o la mínima cantidad de variables
      necesarias para el experimento.

    QUÉ DEBERÁ HACER EL DEV:
    - Implementar la transformación controlada.
    - Vincular cada contrafactual con el caso base mediante based_on.
    """
    raise NotImplementedError("Pendiente de implementación de contrafactuales.")