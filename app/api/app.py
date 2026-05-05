"""
api.app

Factory de la app FastAPI + endpoints.
"""

from dataclasses import asdict
from typing import Any, Dict

from fastapi import FastAPI, HTTPException

from app import config
from app.agents import example_catalog, llm_health, orchestrator, providers
from app.api.schemas import ExperimentRequest


def create_app() -> FastAPI:
    app = FastAPI(title="tiltDetector", version="0.4.0")

    @app.get("/health")
    def healthcheck():
        return {"status": "ok"}

    @app.get("/api/llm/models")
    def get_models():
        return llm_health.get_models_health()

    @app.get("/api/llm/status")
    def llm_status():
        return llm_health.get_models_health()

    @app.post("/api/experiments/run")
    def run_experiment(request: ExperimentRequest):
        raw_names = request.model_names
        defaults = config.LOCAL_MODELS or ["llama3.2"]
        model_names = list(dict.fromkeys(raw_names)) if raw_names else list(defaults)
        if not model_names:
            model_names = list(defaults)
        try:
            result = orchestrator.run_experiment(
                pedido=request.pedido,
                sesgo_medir=request.sesgo_medir,
                model_names=model_names,
                mitigation_ab=request.mitigation_ab,
                n_repeats=request.n_repeats,
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc))
        return asdict(result)

    @app.get("/api/experiments/{experiment_id}")
    def get_experiment(experiment_id: str):
        try:
            return orchestrator.get_experiment_result(experiment_id)
        except KeyError:
            raise HTTPException(status_code=404, detail="Experiment not found")

    @app.get("/api/examples")
    def list_examples_endpoint(dimension: str | None = None):
        items = example_catalog.list_examples(dimension)
        return {"count": len(items), "examples": items}

    @app.get("/api/examples/random")
    def random_example_endpoint(dimension: str | None = None):
        try:
            return example_catalog.pick_random(dimension)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc))

    return app
