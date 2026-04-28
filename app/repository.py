"""
repository.py

CAPA DE PERSISTENCIA BASADA EN ARCHIVOS JSON.
"""

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List

from app.models import ExperimentResult, LLMResponse, NormalizedOutput


BASE_DATA_DIR = Path("data")
INPUT_DIR = BASE_DATA_DIR / "input"
OUTPUT_DIR = BASE_DATA_DIR / "output"
RAW_DIR = OUTPUT_DIR / "raw"
NORMALIZED_DIR = OUTPUT_DIR / "normalized"
EVALUATION_DIR = OUTPUT_DIR / "evaluation"
FINAL_RESULT_DIR = OUTPUT_DIR / "final"


def ensure_directories() -> None:
    for directory in [INPUT_DIR, RAW_DIR, NORMALIZED_DIR, EVALUATION_DIR, FINAL_RESULT_DIR]:
        directory.mkdir(parents=True, exist_ok=True)


def save_input_payload(experiment_id: str, payload: Dict[str, Any]) -> str:
    ensure_directories()
    path = INPUT_DIR / f"{experiment_id}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    return str(path)


def save_raw_responses(experiment_id: str, responses: List[LLMResponse]) -> str:
    ensure_directories()
    path = RAW_DIR / f"{experiment_id}.json"
    path.write_text(json.dumps([asdict(r) for r in responses], ensure_ascii=False, indent=2))
    return str(path)


def save_normalized_outputs(experiment_id: str, outputs: List[NormalizedOutput]) -> str:
    ensure_directories()
    path = NORMALIZED_DIR / f"{experiment_id}.json"
    path.write_text(json.dumps([asdict(o) for o in outputs], ensure_ascii=False, indent=2))
    return str(path)


def save_evaluation_payload(experiment_id: str, payload: Dict[str, Any]) -> str:
    ensure_directories()
    path = EVALUATION_DIR / f"{experiment_id}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    return str(path)


def save_final_result(result: ExperimentResult) -> str:
    ensure_directories()
    path = FINAL_RESULT_DIR / f"{result.experiment_id}.json"
    path.write_text(json.dumps(asdict(result), ensure_ascii=False, indent=2))
    return str(path)


def load_experiment_result(experiment_id: str) -> Dict[str, Any]:
    path = FINAL_RESULT_DIR / f"{experiment_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"Experiment '{experiment_id}' not found.")
    return json.loads(path.read_text())
