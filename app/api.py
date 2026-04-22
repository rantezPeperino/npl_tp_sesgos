"""
api.py

CAPA DE EXPOSICIÓN HTTP DEL SISTEMA.
Entrada mínima: { "pedido": "...", "sesgo_medir": "..." }.
El orquestador se encarga del resto (case_id, casos, metadata, reporte).
"""

from dataclasses import asdict
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app import orchestrator


class ExperimentRequest(BaseModel):
    pedido: str = Field(..., min_length=1, description="Texto plano del formulario describiendo el caso a evaluar.")
    sesgo_medir: str = Field(..., min_length=1, description="Dimensión de sesgo a medir (ej. genero, edad, origen).")
    model_names: Optional[List[str]] = None


def create_app() -> FastAPI:
    app = FastAPI(title="tiltDetector", version="0.3.0")

    @app.get("/health")
    def healthcheck():
        return {"status": "ok"}

    @app.post("/experiments/run")
    def run_experiment(request: ExperimentRequest):
        raw_names = request.model_names
        model_names = list(dict.fromkeys(raw_names)) if raw_names else ["mock-llm-a", "mock-llm-b"]
        if not model_names:
            model_names = ["mock-llm-a", "mock-llm-b"]
        try:
            result = orchestrator.run_experiment(
                pedido=request.pedido,
                sesgo_medir=request.sesgo_medir,
                model_names=model_names,
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc))
        return asdict(result)

    @app.get("/experiments/{experiment_id}")
    def get_experiment(experiment_id: str):
        try:
            return orchestrator.get_experiment_result(experiment_id)
        except KeyError:
            raise HTTPException(status_code=404, detail="Experiment not found")

    return app
