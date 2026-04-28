"""
verify_isolation.py

Herramienta de auditoría: dispara N llamadas independientes contra un mismo
LLM y muestra:
  - id() del cliente SDK por llamada (deben ser TODOS distintos)
  - latencia por llamada
  - hash de la respuesta (si todas son iguales con temperature>0 hay reuso de
    contexto / cache; si difieren, las llamadas son independientes)
  - tiempo entre llamadas (sin solapamiento)

Uso:
  .venv/bin/python -m app.tools.verify_isolation [modelo] [n_calls]

Ejemplos:
  .venv/bin/python -m app.tools.verify_isolation ollama 3
  .venv/bin/python -m app.tools.verify_isolation openai 5
"""

import hashlib
import sys
import time

from app.agents import llm_clients


def _short_hash(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:12]


def main() -> int:
    model_name = sys.argv[1] if len(sys.argv) > 1 else "ollama"
    n_calls = int(sys.argv[2]) if len(sys.argv) > 2 else 3

    prompt = (
        "Respondé SOLO en JSON válido con el siguiente formato exacto:\n"
        '{"score": <número entre 0 y 10>, "msg": "una sola oración"}\n\n'
        "Caso: Evaluá el riesgo crediticio de una persona con ingresos estables. "
        "Asigná un score y comentá en una sola oración."
    )

    provider = llm_clients.providers.resolve_provider(model_name)
    call_fn = llm_clients._PROVIDERS_CALL[provider]

    print(f"=== verify_isolation: provider={provider} model_name={model_name} n_calls={n_calls} ===\n")
    print(f"Prompt (idéntico en cada llamada):\n{prompt}\n")
    print("---")

    results = []
    for i in range(n_calls):
        call_id = llm_clients._new_call_id()
        t0 = time.monotonic()
        raw = call_fn(prompt, 0.7, call_id)
        elapsed = time.monotonic() - t0
        results.append(
            {
                "i": i,
                "call_id": call_id,
                "elapsed": elapsed,
                "resp_sha": _short_hash(raw),
                "raw": raw,
            }
        )
        print(
            f"\n--- llamada {i + 1}/{n_calls} ---\n"
            f"call_id   : {call_id}\n"
            f"elapsed   : {elapsed:.2f}s\n"
            f"resp_sha  : {_short_hash(raw)}\n"
            f"raw[:200] : {raw[:200]}"
        )

    print("\n\n=== RESUMEN ===")
    unique_hashes = {r["resp_sha"] for r in results}
    print(f"Llamadas              : {n_calls}")
    print(f"Hashes únicos resp    : {len(unique_hashes)}")
    if len(unique_hashes) == 1:
        print(
            "AVISO: todas las respuestas son idénticas. Con temperature=0.7 esto\n"
            "puede ser legítimo (modelo determinista) o indicar reuso de contexto.\n"
            "Probá con temperature=1.0 para confirmar variabilidad."
        )
    else:
        print(
            f"OK: hay {len(unique_hashes)} respuestas distintas → cada llamada es\n"
            "una inferencia independiente sin contexto compartido."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
