from fastapi import FastAPI

from app.routes import router


def create_app() -> FastAPI:
    """
    Crea la aplicación FastAPI e incluye las rutas del webhook.

    :return: La aplicación FastAPI configurada.
    :rtype: FastAPI
    """
    aplicacion = FastAPI(
        title="XRepo LoRaWAN Homologation MVP",
        version="0.3.0",
    )
    aplicacion.include_router(router)
    return aplicacion


app = create_app()
