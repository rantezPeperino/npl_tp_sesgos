"""
api.py

CAPA DE EXPOSICIÓN HTTP DEL SISTEMA.
"""

import re
from dataclasses import asdict
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator

from app import orchestrator, repository

_EXPERIMENT_ID_RE = re.compile(r"^[a-zA-Z0-9_\-]{1,100}$")


class ExperimentRequest(BaseModel):
    experiment_id: str = Field(..., min_length=1, max_length=100)
    industry: str
    topic: str
    bias_dimension: str
    task: Dict[str, Any]
    evaluation_constraints: Dict[str, Any]
    model_names: Optional[List[str]] = None

    @field_validator("experiment_id")
    @classmethod
    def validate_experiment_id(cls, v: str) -> str:
        if not _EXPERIMENT_ID_RE.match(v):
            raise ValueError("experiment_id solo puede contener letras, números, guiones y guiones bajos.")
        return v


def create_app() -> FastAPI:
    app = FastAPI(title="tiltDetector", version="0.1.0")

    @app.get("/health")
    def healthcheck():
        return {"status": "ok"}

    @app.post("/experiments/run")
    def run_experiment(request: ExperimentRequest):
        payload = request.model_dump(exclude={"model_names"})
        raw_names = request.model_names
        model_names = list(dict.fromkeys(raw_names)) if raw_names else ["mock-llm-a", "mock-llm-b"]
        if not model_names:
            model_names = ["mock-llm-a", "mock-llm-b"]
        try:
            result = orchestrator.run_experiment(payload, model_names)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc))
        return asdict(result)

    @app.get("/experiments/{experiment_id}")
    def get_experiment(experiment_id: str):
        try:
            return repository.load_experiment_result(experiment_id)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="Experiment not found")

    return app
