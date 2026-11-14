"""
Configuración del sistema de logging de la API.

Todos los loggers de la aplicación cuelgan de "musica_api" (p. ej.
"musica_api.requests", "musica_api.routers.usuarios"), así que basta con
configurar ese logger para controlar el nivel y los destinos de todos.
"""

import logging
from logging.config import dictConfig
from pathlib import Path

FORMATO = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
FORMATO_FECHA = "%Y-%m-%d %H:%M:%S"


def configurar_logging(nivel: str = "INFO", archivo: str | None = None) -> None:
    """
    Configura los logs de la aplicación.

    Args:
        nivel: nivel mínimo (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        archivo: si se indica, además de la consola se escribe en un archivo
            rotativo (1 MB por archivo, se guardan los 5 más recientes).
    """
    handlers: dict[str, dict] = {
        "consola": {
            "class": "logging.StreamHandler",
            "formatter": "estandar",
        },
    }
    if archivo:
        Path(archivo).parent.mkdir(parents=True, exist_ok=True)
        handlers["archivo"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "estandar",
            "filename": archivo,
            "maxBytes": 1_000_000,
            "backupCount": 5,
            "encoding": "utf-8",
        }

    dictConfig(
        {
            "version": 1,
            # No desactivar los loggers de uvicorn/sqlalchemy ya creados
            "disable_existing_loggers": False,
            "formatters": {
                "estandar": {"format": FORMATO, "datefmt": FORMATO_FECHA},
            },
            "handlers": handlers,
            "loggers": {
                "musica_api": {
                    "level": nivel,
                    "handlers": list(handlers),
                    # Propagar permite que pytest (caplog) capture los logs
                    "propagate": True,
                },
            },
        }
    )
    logging.getLogger("musica_api").debug(
        "Logging configurado (nivel=%s, archivo=%s)", nivel, archivo
    )
