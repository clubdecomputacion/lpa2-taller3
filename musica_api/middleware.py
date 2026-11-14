"""Middleware que registra cada request con su duración y un id de seguimiento."""

import logging
import time
import uuid

from fastapi import Request

logger = logging.getLogger("musica_api.requests")

HEADER_REQUEST_ID = "X-Request-ID"


async def registrar_requests(request: Request, call_next):
    """
    Registra método, ruta, código de estado y duración de cada request.

    Cada request recibe un id (o reutiliza el que envíe el cliente en
    X-Request-ID) que se devuelve en la respuesta y aparece en los logs,
    para poder relacionar un error del frontend con su línea de log.
    """
    request_id = request.headers.get(HEADER_REQUEST_ID) or uuid.uuid4().hex[:12]
    request.state.request_id = request_id
    inicio = time.perf_counter()

    try:
        response = await call_next(request)
    except Exception:
        # El manejador de errores registra el traceback y genera la respuesta 500
        duracion_ms = (time.perf_counter() - inicio) * 1000
        logger.error(
            "%s %s -> 500 (%.1f ms) [%s]",
            request.method,
            request.url.path,
            duracion_ms,
            request_id,
        )
        raise

    duracion_ms = (time.perf_counter() - inicio) * 1000
    nivel = logging.WARNING if response.status_code >= 400 else logging.INFO
    logger.log(
        nivel,
        "%s %s -> %s (%.1f ms) [%s]",
        request.method,
        request.url.path,
        response.status_code,
        duracion_ms,
        request_id,
    )
    response.headers[HEADER_REQUEST_ID] = request_id
    return response
