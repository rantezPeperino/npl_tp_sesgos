"""
api.schemas

Pydantic models para validar los requests entrantes.
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class ExperimentRequest(BaseModel):
    pedido: str = Field(
        ...,
        min_length=1,
        description="Texto plano del formulario describiendo el caso a evaluar.",
    )
    sesgo_medir: str = Field(
        ...,
        min_length=1,
        description="Dimensión de sesgo a medir (ej. genero, edad, origen).",
    )
    model_names: Optional[List[str]] = None
