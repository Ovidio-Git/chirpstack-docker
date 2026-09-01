from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import Engine, text


class SignalNotFoundError(LookupError):
    """Se genera cuando una estación no tiene señales activas para el payload."""


@dataclass(frozen=True)
class StoredSignal:
    """Contiene el identificador y el nombre de una señal almacenada."""

    idsenal: int
    senal: str


@dataclass(frozen=True)
class StoredReadings:
    """Contiene la estación y las señales almacenadas para un webhook."""

    idestacion: int
    senales: list[StoredSignal]


class StationRepository:
    def __init__(self, motor: Engine):
        """
        Inicializa el repositorio con el motor de base de datos.

        :param motor: El motor utilizado para ejecutar las consultas SQL.
        """
        self.motor = motor

    def ping(self) -> bool:
        """
        Comprueba que la conexión con la base de datos esté disponible.

        :return: True si la consulta de comprobación se ejecuta correctamente.
        :rtype: bool
        """
        with self.motor.connect() as conexion:
            return conexion.execute(text("SELECT 1")).scalar_one() == 1

    def store_data(
        self,
        id_estacion: int,
        datos_estacion: dict[str, float | int],
        fecha_registro: datetime,
    ) -> StoredReadings:
        """
        Almacena las señales activas de una estación y actualiza su último envío.

        :param id_estacion: El valor de `deviceInfo.tags.station_id`.
        :param datos_estacion: Las mediciones decodificadas enviadas en `object`.
        :param fecha_registro: La fecha y hora en que se procesa la lectura.
        :return: La estación y las señales que fueron almacenadas.
        :rtype: StoredReadings
        :raises SignalNotFoundError: Si no hay señales activas coincidentes.
        """
        formato_deseado = "%Y-%m-%d %H:%M:%S"
        fecha_formateada = fecha_registro.strftime(formato_deseado)

        with self.motor.begin() as conexion:
            query = text(
                "SELECT senal,idsenal,activo FROM xtSenales "
                "WHERE idestacion = :value"
            )
            resultado = conexion.execute(
                query,
                {"value": id_estacion},
            ).fetchall()

            id_senal = {
                clave: valor
                for clave, valor, activo in resultado
                if activo == "S"
            }
            datos_insertar = {
                valor: datos_estacion[clave]
                for clave, valor in id_senal.items()
                if clave in datos_estacion
            }

            if not datos_insertar:
                raise SignalNotFoundError(
                    "La estación "
                    f"{id_estacion} no tiene señales activas "
                    "correspondientes al object recibido."
                )

            senales_almacenadas: list[StoredSignal] = []
            for idsenal, valor in datos_insertar.items():
                query = text(
                    "INSERT INTO xtDatos (DateTime, idsenal, Value) "
                    "VALUES (:FechaInicial, :SenalDestino, :NewValue)"
                )
                conexion.execute(
                    query,
                    {
                        "FechaInicial": fecha_formateada,
                        "SenalDestino": idsenal,
                        "NewValue": valor,
                    },
                )
                senales_almacenadas.append(
                    StoredSignal(
                        idsenal=int(idsenal),
                        senal=next(
                            clave
                            for clave, identificador in id_senal.items()
                            if identificador == idsenal
                        ),
                    )
                )

            update_query = text(
                "UPDATE xtEstaciones SET ultimoEnvio = :ultimoenvio "
                "WHERE idestacion = :idestacion"
            )
            actualizacion = conexion.execute(
                update_query,
                {
                    "ultimoenvio": fecha_formateada,
                    "idestacion": id_estacion,
                },
            )

            if actualizacion.rowcount != 1:
                raise RuntimeError(
                    "La actualización no afectó exactamente una estación."
                )

            return StoredReadings(
                idestacion=id_estacion,
                senales=senales_almacenadas,
            )

    def list_readings(self) -> list[dict]:
        """
        Consulta las lecturas almacenadas en la base de datos.

        :return: La lista de lecturas con su señal y estación asociadas.
        :rtype: list[dict]
        """
        with self.motor.connect() as conexion:
            filas = conexion.execute(
                text(
                    "SELECT d.[DateTime] AS recorded_at, "
                    "d.idsenal, d.[Value] AS value, "
                    "s.senal, s.idestacion, "
                    "e.ultimoEnvio AS ultimo_envio "
                    "FROM xtDatos d "
                    "JOIN xtSenales s ON s.idsenal = d.idsenal "
                    "JOIN xtEstaciones e "
                    "ON e.idestacion = s.idestacion "
                    "ORDER BY d.[DateTime] DESC"
                )
            ).mappings().all()
            return [dict(fila) for fila in filas]
