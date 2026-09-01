from __future__ import annotations

from datetime import datetime
from typing import Annotated

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictFloat,
    StrictInt,
    StringConstraints,
    field_validator,
)
from pydantic_core import PydanticCustomError


DevEUI = Annotated[str, StringConstraints(pattern=r"^[0-9a-fA-F]{16}$")]
NombreSenal = Annotated[str, StringConstraints(min_length=1, max_length=64)]
ValorSenal = StrictFloat | StrictInt


class DeviceTags(BaseModel):
    """Representa los tags configurados para un dispositivo LoRaWAN."""

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    id_estacion: int = Field(alias="station_id", gt=0)


class DeviceInfo(BaseModel):
    """Representa la información del dispositivo enviada por ChirpStack."""

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    dev_eui: DevEUI = Field(alias="devEui")
    etiquetas: DeviceTags = Field(alias="tags")


class LoRaWANUplink(BaseModel):
    """Representa el mensaje recibido desde el servidor LoRaWAN."""

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    id_deduplicacion: str = Field(alias="deduplicationId", min_length=1)
    fecha_recepcion: datetime = Field(alias="time")
    informacion_dispositivo: DeviceInfo = Field(alias="deviceInfo")
    datos: dict[NombreSenal, ValorSenal] = Field(alias="object", min_length=1)

    @field_validator("fecha_recepcion")
    @classmethod
    def require_timezone(cls, valor: datetime) -> datetime:
        """
        Valida que la fecha recibida incluya una zona horaria.

        :param valor: La fecha enviada por el servidor LoRaWAN.
        :return: La misma fecha después de ser validada.
        :rtype: datetime
        :raises PydanticCustomError: Si la fecha no contiene una zona horaria.
        """
        if valor.tzinfo is None or valor.utcoffset() is None:
            raise PydanticCustomError(
                "zona_horaria_requerida",
                "La fecha debe incluir una zona horaria.",
            )
        return valor
