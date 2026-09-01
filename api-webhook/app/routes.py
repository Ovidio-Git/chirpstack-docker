import logging
from functools import lru_cache

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status as estado_http,
)
from sqlalchemy.exc import SQLAlchemyError

from app.database import create_database_engine
from app.models import LoRaWANUplink
from app.repository import (
    SignalNotFoundError,
    StationRepository,
)
from app.service import HomologationService


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()


@lru_cache
def get_repository() -> StationRepository:
    """
    Obtiene el repositorio compartido para acceder a la base de datos.

    :return: El repositorio de estaciones y señales.
    :rtype: StationRepository
    """
    return StationRepository(create_database_engine())


@router.get("/health")
def health(repositorio_datos=Depends(get_repository)):
    """
    Comprueba que la API puede comunicarse con la base de datos.

    :param repositorio_datos: El repositorio inyectado para validar la conexión.
    :return: El estado de disponibilidad de la API.
    :rtype: dict
    """
    try:
        if not repositorio_datos.ping():
            raise HTTPException(
                status_code=503,
                detail="La base de datos no está disponible.",
            )
        return {"status": "ok"}
    except HTTPException:
        raise
    except SQLAlchemyError as error:
        logger.exception("Error al comprobar la base de datos.")
        raise HTTPException(
            status_code=503,
            detail="La base de datos no está disponible.",
        ) from error
    except Exception as error:
        logger.exception("Error inesperado al comprobar la API.")
        raise HTTPException(
            status_code=500,
            detail="Ocurrió un error interno al comprobar la API.",
        ) from error


@router.post(
    "/webhooks/lorawan",
    status_code=estado_http.HTTP_201_CREATED,
)
def receive_lorawan_uplink(
    mensaje: LoRaWANUplink,
    repositorio_datos=Depends(get_repository),
):
    """
    Recibe y homologa un evento decodificado del servidor LoRaWAN.

    :param mensaje: El mensaje enviado por el servidor LoRaWAN.
    :param repositorio_datos: El repositorio utilizado para almacenar las señales.
    :return: El resultado de la homologación y los identificadores asociados.
    :rtype: dict
    """
    try:
        resultado = HomologationService(repositorio_datos).process(mensaje)
    except SignalNotFoundError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except SQLAlchemyError as error:
        logger.exception(
            "Error de base de datos para devEUI=%s deduplicationId=%s.",
            mensaje.informacion_dispositivo.dev_eui,
            mensaje.id_deduplicacion,
        )
        raise HTTPException(
            status_code=503,
            detail="La base de datos no está disponible.",
        ) from error
    except Exception as error:
        logger.exception(
            "Error inesperado al procesar devEUI=%s deduplicationId=%s.",
            mensaje.informacion_dispositivo.dev_eui,
            mensaje.id_deduplicacion,
        )
        raise HTTPException(
            status_code=500,
            detail="Ocurrió un error interno al procesar el evento LoRaWAN.",
        ) from error

    logger.info(
        "Lecturas almacenadas station_id=%s devEUI=%s "
        "deduplicationId=%s fechaOrigen=%s.",
        mensaje.informacion_dispositivo.etiquetas.id_estacion,
        mensaje.informacion_dispositivo.dev_eui,
        mensaje.id_deduplicacion,
        mensaje.fecha_recepcion.isoformat(),
    )
    return {
        "status": "stored",
        "devEUI": resultado.dev_eui,
        "stationId": mensaje.informacion_dispositivo.etiquetas.id_estacion,
        "idestacion": resultado.lecturas.idestacion,
        "storedSignals": [
            {"idsenal": senal.idsenal, "signal": senal.senal}
            for senal in resultado.lecturas.senales
        ],
        "recordedAt": resultado.fecha_registro,
    }


@router.get("/readings")
def readings(repositorio_datos=Depends(get_repository)):
    """
    Consulta las lecturas almacenadas.

    :param repositorio_datos: El repositorio utilizado para consultar las lecturas.
    :return: La colección de lecturas registradas.
    :rtype: dict
    """
    try:
        return {"items": repositorio_datos.list_readings()}
    except SQLAlchemyError as error:
        logger.exception("Error al consultar las lecturas.")
        raise HTTPException(
            status_code=503,
            detail="La base de datos no está disponible.",
        ) from error
    except Exception as error:
        logger.exception("Error inesperado al consultar las lecturas.")
        raise HTTPException(
            status_code=500,
            detail="Ocurrió un error interno al consultar las lecturas.",
        ) from error
