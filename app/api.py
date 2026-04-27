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

from app import config, llm_health, orchestrator, providers


class ExperimentRequest(BaseModel):
    pedido: str = Field(..., min_length=1, description="Texto plano del formulario describiendo el caso a evaluar.")
    sesgo_medir: str = Field(..., min_length=1, description="Dimensión de sesgo a medir (ej. genero, edad, origen).")
    model_names: Optional[List[str]] = None


def create_app() -> FastAPI:
    app = FastAPI(title="tiltDetector", version="0.3.0")

    @app.get("/health")
    def healthcheck():
        return {"status": "ok"}

    @app.get("/llm/status")
    def llm_status():
        """
        Verifica el estado de cada LLM habilitado.
        Útil para confirmar que los modelos están operativos antes de
        enviar un experimento. NO devuelve respuestas mock — si un proveedor
        falla, lo reporta como `unhealthy`.
        """
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
            report["checks"].append({
                "provider": provider,
                "healthy": ok,
                "detail": detail,
            })
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
