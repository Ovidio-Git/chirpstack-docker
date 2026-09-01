from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from app.models import LoRaWANUplink
from app.repository import StationRepository, StoredReadings


@dataclass(frozen=True)
class HomologationResult:
    """Contiene el resultado de homologar y almacenar una lectura."""

    dev_eui: str
    fecha_registro: datetime
    lecturas: StoredReadings


class HomologationService:
    def __init__(
        self,
        repositorio: StationRepository,
    ):
        """
        Inicializa el servicio encargado de homologar las lecturas.

        :param repositorio: El repositorio utilizado para almacenar las señales.
        """
        self.repositorio = repositorio

    def process(
        self,
        mensaje: LoRaWANUplink,
    ) -> HomologationResult:
        """
        Almacena las señales decodificadas por el servidor LoRaWAN.

        :param mensaje: El mensaje recibido desde el servidor LoRaWAN.
        :return: El resultado de la homologación realizada.
        :rtype: HomologationResult
        """
        zona_horaria_colombia = ZoneInfo("America/Bogota")
        fecha_proceso = mensaje.fecha_recepcion.astimezone(zona_horaria_colombia)
        dev_eui = mensaje.informacion_dispositivo.dev_eui.lower()
        lecturas = self.repositorio.store_data(
            mensaje.informacion_dispositivo.etiquetas.id_estacion,
            {
                senal: float(valor)
                for senal, valor in mensaje.datos.items()
            },
            fecha_proceso.replace(tzinfo=None),
        )
        return HomologationResult(
            dev_eui=dev_eui,
            fecha_registro=fecha_proceso,
            lecturas=lecturas,
        )
