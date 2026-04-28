"""
app.api

Capa HTTP del sistema (FastAPI). Solo expone endpoints — la lógica vive
en app/agents/.
"""

from app.api.app import create_app
from app.api.schemas import ExperimentRequest

__all__ = ["create_app", "ExperimentRequest"]
