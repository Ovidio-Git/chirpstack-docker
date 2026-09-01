import os

from sqlalchemy import Engine, create_engine
from sqlalchemy.engine import URL


def create_database_engine() -> Engine:
    """
    Crea el motor de conexión a Microsoft SQL Server.

    Los parámetros de conexión se obtienen de las variables de entorno del
    mismo modo que el producto de referencia: DB_HOST, DB_PORT, DB_USER,
    DB_PASSWORD, DB_DATABASE y DB_DRIVER.

    :return: El motor de SQLAlchemy configurado para SQL Server.
    :rtype: Engine
    :raises ValueError: Si falta un parámetro o el puerto no es válido.
    """
    parametros = {
        "host": os.getenv("DB_HOST"),
        "port": os.getenv("DB_PORT", "1433"),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
        "database": os.getenv("DB_DATABASE"),
        "driver": os.getenv("DB_DRIVER", "ODBC Driver 18 for SQL Server"),
    }

    if not all(parametros.values()):
        raise ValueError(
            "Todos los parámetros de conexión son necesarios para crear "
            "la instancia."
        )

    try:
        puerto = int(str(parametros["port"]))
    except ValueError as error:
        raise ValueError("El puerto de conexión debe ser un número válido.") from error

    url_base_datos = URL.create(
        "mssql+pyodbc",
        username=str(parametros["user"]),
        password=str(parametros["password"]),
        host=str(parametros["host"]),
        port=puerto,
        database=str(parametros["database"]),
        query={
            "driver": str(parametros["driver"]),
            "Encrypt": os.getenv("DB_ENCRYPT", "yes"),
            "TrustServerCertificate": os.getenv(
                "DB_TRUST_SERVER_CERTIFICATE",
                "no",
            ),
        },
    )

    return create_engine(
        url_base_datos,
        pool_pre_ping=True,
        pool_recycle=1800,
    )
