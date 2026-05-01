"""
main.py

ENTRYPOINT DEL SERVICIO tiltDetector.
Arranque: uvicorn app.main:app --reload
"""

import uvicorn

from app.api.app import create_app

app = create_app()


def main() -> None:
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    main()
