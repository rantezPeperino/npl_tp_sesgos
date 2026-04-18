"""
main.py

ENTRYPOINT DEL SERVICIO tiltDetector.

Este módulo existe para arrancar la aplicación en entorno local,
desarrollo o integración. Su responsabilidad es mínima: construir
la app HTTP y delegar el arranque al servidor elegido.

RESPONSABILIDAD DENTRO DEL SISTEMA:
- Importar create_app() desde api.py.
- Crear la instancia de la app.
- Dejar preparado el punto de arranque del servidor.

QUÉ NO DEBE HACER:
- No debe contener lógica de negocio.
- No debe generar casos.
- No debe invocar manualmente el pipeline del experimento.
- No debe persistir datos.

QUÉ DEBERÁ HACER EL DEV:
- Elegir estrategia de arranque real.
- Si usa FastAPI + uvicorn, decidir si el arranque se hará:
  1. desde código
  2. desde comando CLI
- Mantener este archivo lo más simple posible.
"""

from app.api import create_app


def main() -> None:
    """
    Función de arranque de la aplicación.

    TAREAS ESPERADAS:
    - Crear la app HTTP llamando a create_app().
    - Configurar host, puerto y modo debug si corresponde.
    - Levantar el servidor o dejar preparado el entrypoint.

    NOTA:
    Si se usa FastAPI + uvicorn, esta función puede quedar mínima
    o incluso delegar el arranque a línea de comandos.

    QUÉ DEBERÁ HACER EL DEV:
    - Decidir la forma final de inicialización del servicio.
    """
    app = create_app()
    raise NotImplementedError("Pendiente de implementación del arranque del servidor.")


if __name__ == "__main__":
    main()