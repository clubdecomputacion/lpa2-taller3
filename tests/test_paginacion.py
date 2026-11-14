"""Tests de la paginación de los listados."""

from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from musica_api.models import Cancion, Favorito, Usuario
from musica_api.paginacion import LIMITE_MAXIMO, LIMITE_POR_DEFECTO


def crear_canciones(session: Session, n: int, **campos) -> list[Cancion]:
    canciones = [
        Cancion(
            titulo=f"Canción {i:02d}",
            artista=campos.get("artista", "Artista"),
            duracion=200,
            año=2000,
            genero=campos.get("genero", "Rock"),
        )
        for i in range(n)
    ]
    session.add_all(canciones)
    session.commit()
    return canciones


def titulos(response) -> list[str]:
    return [c["titulo"] for c in response.json()["items"]]


class TestFormato:
    def test_estructura_de_la_pagina(self, client: TestClient, session: Session):
        crear_canciones(session, 3)

        response = client.get("/api/canciones")

        assert response.status_code == 200
        data = response.json()
        assert set(data) == {"items", "total", "offset", "limit"}
        assert data["total"] == 3
        assert data["offset"] == 0
        assert data["limit"] == LIMITE_POR_DEFECTO

    def test_listado_vacio(self, client: TestClient):
        data = client.get("/api/canciones").json()

        assert data == {
            "items": [],
            "total": 0,
            "offset": 0,
            "limit": LIMITE_POR_DEFECTO,
        }

    def test_limite_por_defecto(self, client: TestClient, session: Session):
        crear_canciones(session, LIMITE_POR_DEFECTO + 5)

        data = client.get("/api/canciones").json()

        assert len(data["items"]) == LIMITE_POR_DEFECTO
        assert data["total"] == LIMITE_POR_DEFECTO + 5


class TestNavegacion:
    def test_recorrer_todas_las_paginas(self, client: TestClient, session: Session):
        """Recorrer página a página devuelve cada canción una sola vez y en orden."""
        crear_canciones(session, 7)

        vistos = []
        offset = 0
        while True:
            data = client.get(
                "/api/canciones", params={"offset": offset, "limit": 3}
            ).json()
            vistos += [c["titulo"] for c in data["items"]]
            offset += data["limit"]
            if offset >= data["total"]:
                break

        assert vistos == [f"Canción {i:02d}" for i in range(7)]

    def test_ultima_pagina_incompleta(self, client: TestClient, session: Session):
        crear_canciones(session, 7)

        response = client.get("/api/canciones", params={"offset": 6, "limit": 3})

        assert titulos(response) == ["Canción 06"]
        assert response.json()["total"] == 7

    def test_offset_mayor_que_total(self, client: TestClient, session: Session):
        crear_canciones(session, 2)

        data = client.get("/api/canciones", params={"offset": 50}).json()

        assert data["items"] == []
        assert data["total"] == 2


class TestValidacionParametros:
    @pytest.mark.parametrize(
        "params",
        [{"offset": -1}, {"limit": 0}, {"limit": LIMITE_MAXIMO + 1}, {"limit": "x"}],
    )
    @pytest.mark.parametrize(
        "url", ["/api/usuarios", "/api/canciones", "/api/favoritos"]
    )
    def test_parametros_invalidos(self, client: TestClient, url: str, params: dict):
        assert client.get(url, params=params).status_code == 422

    def test_limite_maximo_permitido(self, client: TestClient):
        response = client.get("/api/canciones", params={"limit": LIMITE_MAXIMO})

        assert response.status_code == 200


class TestBusquedaPaginada:
    def test_total_cuenta_solo_los_filtrados(
        self, client: TestClient, session: Session
    ):
        crear_canciones(session, 5, genero="Rock")
        crear_canciones(session, 3, genero="Jazz")

        data = client.get(
            "/api/canciones/buscar", params={"genero": "jazz", "limit": 2}
        ).json()

        assert len(data["items"]) == 2
        assert data["total"] == 3
        assert all(c["genero"] == "Jazz" for c in data["items"])


class TestFavoritosUsuarioPaginados:
    def test_mas_recientes_primero(self, client: TestClient, session: Session):
        usuario = Usuario(nombre="Ana", correo="ana@example.com")
        session.add(usuario)
        canciones = crear_canciones(session, 3)
        ahora = datetime.now(UTC)
        for horas, cancion in zip([3, 1, 2], canciones, strict=True):
            session.add(
                Favorito(
                    id_usuario=usuario.id,
                    id_cancion=cancion.id,
                    fecha_marcado=ahora - timedelta(hours=horas),
                )
            )
        session.commit()

        data = client.get(
            f"/api/usuarios/{usuario.id}/favoritos", params={"limit": 2}
        ).json()

        assert data["total"] == 3
        assert [f["cancion"]["titulo"] for f in data["items"]] == [
            "Canción 01",  # hace 1 hora
            "Canción 02",  # hace 2 horas
        ]
