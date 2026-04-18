
## `app/main.py`



from app.api import create_app


def main() -> None:
    """
    Función de arranque de la aplicación.

    :
    - Crear la app HTTP llamando a create_app().
    - Configurar host, puerto y modo debug si corresponde.
    - Levantar el servidor o dejar preparado el entrypoint.

    NOTA:
    Si se usa FastAPI + uvicorn, esta función puede quedar mínima
    o incluso delegar el arranque a línea de comandos.
    """
    app = create_app()
    raise NotImplementedError("Pendiente de implementación del arranque del servidor.")


if __name__ == "__main__":
    main()