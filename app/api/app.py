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

    @app.get("/llm/status")
    def llm_status():
        report: Dict[str, Any] = {
            "enabled_providers": sorted(config.ENABLED_PROVIDERS),
            "default_models": list(config.DEFAULT_MODELS),
            "models": {
                "openai": config.OPENAI_MODEL,
                "gemini": config.GEMINI_MODEL,
                "anthropic": config.ANTHROPIC_MODEL,
                "ollama": config.OLLAMA_MODEL,
                "ollama_base_url": config.OLLAMA_BASE_URL,
            },
            "checks": [],
        }
        seen = set()
        for alias in providers.PROVIDER_ALIASES:
            provider = providers.PROVIDER_ALIASES[alias]
            if provider in seen:
                continue
            seen.add(provider)
            check = llm_health._PROVIDER_CHECKS.get(provider)
            if check is None:
                continue
            ok, detail = check()
            report["checks"].append(
                {"provider": provider, "healthy": ok, "detail": detail}
            )
        return report

    @app.post("/experiments/run")
    def run_experiment(request: ExperimentRequest):
        raw_names = request.model_names
        defaults = config.DEFAULT_MODELS or ["ollama"]
        model_names = list(dict.fromkeys(raw_names)) if raw_names else list(defaults)
        if not model_names:
            model_names = list(defaults)
        try:
            result = orchestrator.run_experiment(
                pedido=request.pedido,
                sesgo_medir=request.sesgo_medir,
                model_names=model_names,
                mitigation_ab=request.mitigation_ab,
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

    @app.get("/examples")
    def list_examples_endpoint(dimension: str | None = None):
        items = example_catalog.list_examples(dimension)
        return {"count": len(items), "examples": items}

    @app.get("/examples/random")
    def random_example_endpoint(dimension: str | None = None):
        try:
            return example_catalog.pick_random(dimension)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc))

    return app
