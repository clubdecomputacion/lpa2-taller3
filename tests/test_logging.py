"""Tests del sistema de logging: middleware, manejadores de errores y configuración."""

import logging

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from main import app
from musica_api.config import Settings
from musica_api.database import get_session
from musica_api.logging_config import configurar_logging


def mensajes(caplog, logger: str) -> list[str]:
    return [r.getMessage() for r in caplog.records if r.name == logger]


# =============================================================================
# MIDDLEWARE DE REQUESTS
# =============================================================================


class TestMiddlewareRequests:
    def test_registra_request_exitoso(self, client: TestClient, caplog):
        caplog.set_level(logging.INFO, logger="musica_api")

        response = client.get("/api/usuarios")

        assert response.status_code == 200
        [linea] = mensajes(caplog, "musica_api.requests")
        assert "GET /api/usuarios -> 200" in linea
        assert "ms)" in linea

    def test_devuelve_request_id(self, client: TestClient, caplog):
        caplog.set_level(logging.INFO, logger="musica_api")

        response = client.get("/health")

        request_id = response.headers["X-Request-ID"]
        assert len(request_id) == 12
        assert request_id in mensajes(caplog, "musica_api.requests")[0]

    def test_reutiliza_request_id_del_cliente(self, client: TestClient, caplog):
        caplog.set_level(logging.INFO, logger="musica_api")

        response = client.get("/health", headers={"X-Request-ID": "frontend-123"})

        assert response.headers["X-Request-ID"] == "frontend-123"
        assert "[frontend-123]" in mensajes(caplog, "musica_api.requests")[0]

    def test_errores_4xx_se_registran_como_warning(self, client: TestClient, caplog):
        caplog.set_level(logging.INFO, logger="musica_api")

        client.get("/api/usuarios/999")

        [registro] = [r for r in caplog.records if r.name == "musica_api.requests"]
        assert registro.levelno == logging.WARNING
        assert "-> 404" in registro.getMessage()


# =============================================================================
# MANEJADORES DE ERRORES
# =============================================================================


class TestManejadoresErrores:
    def test_http_exception_mantiene_formato(self, client: TestClient, caplog):
        caplog.set_level(logging.INFO, logger="musica_api")

        response = client.get("/api/usuarios/999")

        assert response.status_code == 404
        assert response.json() == {"detail": "Usuario no encontrado"}
        [linea] = mensajes(caplog, "musica_api.errores")
        assert "HTTP 404" in linea
        assert "Usuario no encontrado" in linea

    def test_error_validacion_registra_campos(self, client: TestClient, caplog):
        caplog.set_level(logging.INFO, logger="musica_api")

        response = client.post("/api/usuarios", json={"nombre": "X"})

        assert response.status_code == 422
        assert response.json()["detail"][0]["loc"] == ["body", "correo"]
        [linea] = mensajes(caplog, "musica_api.errores")
        assert "body.correo" in linea

    def test_error_inesperado_devuelve_500_con_request_id(self, caplog):
        def sesion_rota():
            raise RuntimeError("la base de datos explotó")

        app.dependency_overrides[get_session] = sesion_rota
        try:
            client = TestClient(app, raise_server_exceptions=False)
            response = client.get("/api/usuarios")
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 500
        data = response.json()
        # No se filtra el detalle interno al cliente
        assert data["detail"] == "Error interno del servidor"
        assert "explotó" not in response.text
        assert data["request_id"] == response.headers["X-Request-ID"]

        [registro] = [r for r in caplog.records if r.name == "musica_api.errores"]
        assert registro.levelno == logging.ERROR
        assert registro.exc_info is not None  # incluye el traceback
        assert data["request_id"] in registro.getMessage()


# =============================================================================
# LOGS DE LOS ROUTERS
# =============================================================================


class TestLogsRouters:
    def test_crear_usuario_registra_id_sin_datos_personales(
        self, client: TestClient, caplog
    ):
        caplog.set_level(logging.INFO, logger="musica_api")

        r = client.post(
            "/api/usuarios", json={"nombre": "Ana", "correo": "ana@example.com"}
        )

        [linea] = mensajes(caplog, "musica_api.routers.usuarios")
        assert linea == f"Usuario {r.json()['id']} creado"
        assert "ana@example.com" not in caplog.text

    def test_actualizar_cancion_registra_campos(self, client: TestClient, caplog):
        r = client.post(
            "/api/canciones",
            json={
                "titulo": "T",
                "artista": "A",
                "duracion": 100,
                "año": 2000,
                "genero": "Pop",
            },
        )
        id_cancion = r.json()["id"]
        caplog.set_level(logging.INFO, logger="musica_api")
        caplog.clear()  # descartar el log de la creación

        client.put(f"/api/canciones/{id_cancion}", json={"genero": "Rock"})

        assert mensajes(caplog, "musica_api.routers.canciones") == [
            f"Canción {id_cancion} actualizada (campos: genero)"
        ]


# =============================================================================
# CONFIGURACIÓN
# =============================================================================


class TestConfiguracion:
    def test_log_level_se_normaliza(self):
        assert Settings(log_level="debug").log_level == "DEBUG"

    def test_log_level_invalido(self):
        with pytest.raises(ValidationError):
            Settings(log_level="MUCHO")

    def test_escribe_en_archivo(self, tmp_path):
        archivo = tmp_path / "logs" / "api.log"
        try:
            configurar_logging("INFO", str(archivo))
            logging.getLogger("musica_api.test").info("mensaje de prueba")
            logging.getLogger("musica_api.test").debug("no debe aparecer")
        finally:
            # Restaurar la configuración (y cerrar el archivo, necesario en Windows)
            configurar_logging("INFO")

        contenido = archivo.read_text(encoding="utf-8")
        assert "INFO     | musica_api.test | mensaje de prueba" in contenido
        assert "no debe aparecer" not in contenido
