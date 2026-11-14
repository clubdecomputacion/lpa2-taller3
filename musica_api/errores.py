"""
Manejadores de errores personalizados.

Registran cada error en el log y delegan en los manejadores por defecto de
FastAPI, para que el formato de las respuestas ({"detail": ...}) no cambie.
"""

import logging

from fastapi import FastAPI, Request, status
from fastapi.exception_handlers import (
    http_exception_handler,
    request_validation_exception_handler,
)
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from musica_api.middleware import HEADER_REQUEST_ID

logger = logging.getLogger("musica_api.errores")


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "-")


async def manejar_http_exception(request: Request, exc: StarletteHTTPException):
    logger.info(
        "HTTP %s en %s %s: %s [%s]",
        exc.status_code,
        request.method,
        request.url.path,
        exc.detail,
        _request_id(request),
    )
    return await http_exception_handler(request, exc)


async def manejar_error_validacion(request: Request, exc: RequestValidationError):
    campos = ", ".join(".".join(str(p) for p in e["loc"]) for e in exc.errors())
    logger.info(
        "Validación fallida en %s %s (campos: %s) [%s]",
        request.method,
        request.url.path,
        campos,
        _request_id(request),
    )
    return await request_validation_exception_handler(request, exc)


async def manejar_error_inesperado(request: Request, exc: Exception):
    """Cualquier excepción no controlada: se registra con traceback y se oculta
    el detalle interno al cliente."""
    request_id = _request_id(request)
    logger.exception(
        "Error no controlado en %s %s [%s]",
        request.method,
        request.url.path,
        request_id,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Error interno del servidor", "request_id": request_id},
        headers={HEADER_REQUEST_ID: request_id},
    )


def registrar_manejadores(app: FastAPI) -> None:
    app.add_exception_handler(StarletteHTTPException, manejar_http_exception)
    app.add_exception_handler(RequestValidationError, manejar_error_validacion)
    app.add_exception_handler(Exception, manejar_error_inesperado)
