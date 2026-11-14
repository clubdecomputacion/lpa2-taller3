"""
Tests para la API de Música.
Pruebas unitarias y de integración usando pytest.
"""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from musica_api.models import Cancion, Favorito, Usuario
from utils import obtener_año_actual

# =============================================================================
# CONFIGURACIÓN DE FIXTURES
# (session y client están en tests/conftest.py)
# =============================================================================


@pytest.fixture(name="usuario_test")
def usuario_test_fixture(session: Session):
    """
    Crea un usuario de prueba en la base de datos.
    """
    usuario = Usuario(nombre="Usuario Test", correo="test@example.com")
    session.add(usuario)
    session.commit()
    session.refresh(usuario)
    return usuario


@pytest.fixture(name="cancion_test")
def cancion_test_fixture(session: Session):
    """
    Crea una cancion de prueba en la base de datos.
    """
    cancion = Cancion(
        titulo="Canción Test",
        artista="Artista Test",
        album="Álbum Test",
        duracion=210,
        año=2020,
        genero="Rock",
    )
    session.add(cancion)
    session.commit()
    session.refresh(cancion)
    return cancion


def datos_cancion(**cambios) -> dict:
    """Payload válido de canción, con campos sobreescribibles."""
    datos = {
        "titulo": "Bohemian Rhapsody",
        "artista": "Queen",
        "album": "A Night at the Opera",
        "duracion": 354,
        "año": 1975,
        "genero": "Rock",
    }
    datos.update(cambios)
    return datos


# =============================================================================
# TESTS DE USUARIOS
# =============================================================================


class TestUsuarios:
    """Tests para los endpoints de usuarios."""

    def test_listar_usuarios(self, client: TestClient, usuario_test: Usuario):
        """Test para GET /api/usuarios"""
        response = client.get("/api/usuarios")

        assert response.status_code == 200
        data = response.json()["items"]
        assert len(data) == 1
        assert data[0]["correo"] == usuario_test.correo

    def test_listar_usuarios_vacio(self, client: TestClient):
        response = client.get("/api/usuarios")

        assert response.status_code == 200
        assert response.json()["items"] == []

    def test_listar_usuarios_paginacion(self, client: TestClient, session: Session):
        for i in range(5):
            session.add(Usuario(nombre=f"U{i}", correo=f"u{i}@example.com"))
        session.commit()

        response = client.get("/api/usuarios", params={"offset": 1, "limit": 2})

        assert response.status_code == 200
        assert [u["nombre"] for u in response.json()["items"]] == ["U1", "U2"]

    def test_crear_usuario(self, client: TestClient):
        """Test para POST /api/usuarios"""
        response = client.post(
            "/api/usuarios", json={"nombre": "Ana", "correo": "Ana@Example.com"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["id"] is not None
        assert data["nombre"] == "Ana"
        assert data["correo"] == "ana@example.com"  # se normaliza a minúsculas
        assert "fecha_registro" in data

    def test_crear_usuario_correo_duplicado(
        self, client: TestClient, usuario_test: Usuario
    ):
        """Test para verificar que no se permiten correos duplicados"""
        response = client.post(
            "/api/usuarios",
            json={"nombre": "Otro", "correo": usuario_test.correo.upper()},
        )

        assert response.status_code == 400
        assert "correo" in response.json()["detail"].lower()

    def test_obtener_usuario(self, client: TestClient, usuario_test: Usuario):
        """Test para GET /api/usuarios/{id}"""
        response = client.get(f"/api/usuarios/{usuario_test.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == usuario_test.id
        assert data["nombre"] == usuario_test.nombre

    def test_obtener_usuario_no_existe(self, client: TestClient):
        """Test para verificar error 404 con usuario inexistente"""
        response = client.get("/api/usuarios/999")

        assert response.status_code == 404

    def test_actualizar_usuario(self, client: TestClient, usuario_test: Usuario):
        """Test para PUT /api/usuarios/{id}"""
        response = client.put(
            f"/api/usuarios/{usuario_test.id}", json={"nombre": "Nombre Nuevo"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["nombre"] == "Nombre Nuevo"
        assert data["correo"] == usuario_test.correo  # no cambia lo no enviado

    def test_actualizar_usuario_correo_de_otro(
        self, client: TestClient, session: Session, usuario_test: Usuario
    ):
        otro = Usuario(nombre="Otro", correo="otro@example.com")
        session.add(otro)
        session.commit()

        response = client.put(
            f"/api/usuarios/{otro.id}", json={"correo": usuario_test.correo}
        )

        assert response.status_code == 400

    def test_actualizar_usuario_mismo_correo(
        self, client: TestClient, usuario_test: Usuario
    ):
        """Reenviar el propio correo no debe contar como duplicado."""
        response = client.put(
            f"/api/usuarios/{usuario_test.id}", json={"correo": usuario_test.correo}
        )

        assert response.status_code == 200

    def test_actualizar_usuario_no_existe(self, client: TestClient):
        response = client.put("/api/usuarios/999", json={"nombre": "X"})

        assert response.status_code == 404

    def test_eliminar_usuario(self, client: TestClient, usuario_test: Usuario):
        """Test para DELETE /api/usuarios/{id}"""
        response = client.delete(f"/api/usuarios/{usuario_test.id}")

        assert response.status_code == 204
        assert client.get(f"/api/usuarios/{usuario_test.id}").status_code == 404

    def test_eliminar_usuario_no_existe(self, client: TestClient):
        response = client.delete("/api/usuarios/999")

        assert response.status_code == 404


# =============================================================================
# TESTS DE CANCIONES
# =============================================================================


class TestCanciones:
    """Tests para los endpoints de canciones."""

    def test_listar_canciones(self, client: TestClient, cancion_test: Cancion):
        """Test para GET /api/canciones"""
        response = client.get("/api/canciones")

        assert response.status_code == 200
        data = response.json()["items"]
        assert len(data) == 1
        assert data[0]["titulo"] == cancion_test.titulo

    def test_crear_cancion(self, client: TestClient):
        """Test para POST /api/canciones"""
        response = client.post("/api/canciones", json=datos_cancion())

        assert response.status_code == 201
        data = response.json()
        assert data["id"] is not None
        assert data["titulo"] == "Bohemian Rhapsody"
        assert data["año"] == 1975
        assert "fecha_creacion" in data

    def test_crear_cancion_sin_album(self, client: TestClient):
        """El álbum es opcional."""
        datos = datos_cancion()
        del datos["album"]

        response = client.post("/api/canciones", json=datos)

        assert response.status_code == 201
        assert response.json()["album"] is None

    def test_obtener_cancion(self, client: TestClient, cancion_test: Cancion):
        """Test para GET /api/canciones/{id}"""
        response = client.get(f"/api/canciones/{cancion_test.id}")

        assert response.status_code == 200
        assert response.json()["artista"] == cancion_test.artista

    def test_obtener_cancion_no_existe(self, client: TestClient):
        response = client.get("/api/canciones/999")

        assert response.status_code == 404

    def test_actualizar_cancion(self, client: TestClient, cancion_test: Cancion):
        """Test para PUT /api/canciones/{id}"""
        response = client.put(
            f"/api/canciones/{cancion_test.id}",
            json={"genero": "Pop", "duracion": 180},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["genero"] == "Pop"
        assert data["duracion"] == 180
        assert data["titulo"] == cancion_test.titulo

    def test_actualizar_cancion_año_invalido(
        self, client: TestClient, cancion_test: Cancion
    ):
        response = client.put(f"/api/canciones/{cancion_test.id}", json={"año": 1800})

        assert response.status_code == 422

    def test_eliminar_cancion(self, client: TestClient, cancion_test: Cancion):
        """Test para DELETE /api/canciones/{id}"""
        response = client.delete(f"/api/canciones/{cancion_test.id}")

        assert response.status_code == 204
        assert client.get(f"/api/canciones/{cancion_test.id}").status_code == 404

    def test_buscar_canciones(self, client: TestClient, cancion_test: Cancion):
        """Test para GET /api/canciones/buscar"""
        # Coincidencia parcial e insensible a mayúsculas
        response = client.get("/api/canciones/buscar", params={"titulo": "canción t"})

        assert response.status_code == 200
        data = response.json()["items"]
        assert len(data) == 1
        assert data[0]["id"] == cancion_test.id

    def test_buscar_canciones_sin_resultados(
        self, client: TestClient, cancion_test: Cancion
    ):
        response = client.get("/api/canciones/buscar", params={"artista": "Nadie"})

        assert response.status_code == 200
        assert response.json()["items"] == []

    def test_buscar_canciones_multiples_filtros(self, client: TestClient):
        """Test para búsqueda con múltiples parámetros"""
        client.post("/api/canciones", json=datos_cancion())
        client.post(
            "/api/canciones",
            json=datos_cancion(titulo="Radio Ga Ga", año=1984, genero="Pop"),
        )
        client.post(
            "/api/canciones",
            json=datos_cancion(titulo="Smells Like Teen Spirit", artista="Nirvana"),
        )

        # Los filtros se combinan con AND
        response = client.get(
            "/api/canciones/buscar", params={"artista": "queen", "genero": "rock"}
        )

        assert response.status_code == 200
        titulos = [c["titulo"] for c in response.json()["items"]]
        assert titulos == ["Bohemian Rhapsody"]


# =============================================================================
# TESTS DE FAVORITOS
# =============================================================================


class TestFavoritos:
    """Tests para los endpoints de favoritos."""

    def test_listar_favoritos(self, client: TestClient):
        """Test para GET /api/favoritos"""
        response = client.get("/api/favoritos")

        assert response.status_code == 200
        assert response.json()["items"] == []

    def test_crear_favorito(
        self, client: TestClient, usuario_test: Usuario, cancion_test: Cancion
    ):
        """Test para POST /api/favoritos"""
        response = client.post(
            "/api/favoritos",
            json={"id_usuario": usuario_test.id, "id_cancion": cancion_test.id},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["id_usuario"] == usuario_test.id
        assert data["id_cancion"] == cancion_test.id
        assert "fecha_marcado" in data

    def test_crear_favorito_usuario_no_existe(
        self, client: TestClient, cancion_test: Cancion
    ):
        response = client.post(
            "/api/favoritos", json={"id_usuario": 999, "id_cancion": cancion_test.id}
        )

        assert response.status_code == 404

    def test_crear_favorito_cancion_no_existe(
        self, client: TestClient, usuario_test: Usuario
    ):
        response = client.post(
            "/api/favoritos", json={"id_usuario": usuario_test.id, "id_cancion": 999}
        )

        assert response.status_code == 404

    def test_crear_favorito_duplicado(
        self, client: TestClient, usuario_test: Usuario, cancion_test: Cancion
    ):
        """Test para verificar que no se permiten favoritos duplicados"""
        payload = {"id_usuario": usuario_test.id, "id_cancion": cancion_test.id}
        client.post("/api/favoritos", json=payload)

        response = client.post("/api/favoritos", json=payload)

        assert response.status_code == 400

    def test_obtener_favorito(
        self,
        client: TestClient,
        session: Session,
        usuario_test: Usuario,
        cancion_test: Cancion,
    ):
        favorito = Favorito(id_usuario=usuario_test.id, id_cancion=cancion_test.id)
        session.add(favorito)
        session.commit()

        response = client.get(f"/api/favoritos/{favorito.id}")

        assert response.status_code == 200
        assert response.json()["id"] == favorito.id
        assert client.get("/api/favoritos/999").status_code == 404

    def test_eliminar_favorito(
        self,
        client: TestClient,
        session: Session,
        usuario_test: Usuario,
        cancion_test: Cancion,
    ):
        """Test para DELETE /api/favoritos/{id}"""
        favorito = Favorito(id_usuario=usuario_test.id, id_cancion=cancion_test.id)
        session.add(favorito)
        session.commit()

        response = client.delete(f"/api/favoritos/{favorito.id}")

        assert response.status_code == 204
        assert session.exec(select(Favorito)).all() == []

    def test_marcar_favorito_usuario(
        self, client: TestClient, usuario_test: Usuario, cancion_test: Cancion
    ):
        """Test para POST /api/usuarios/{id}/favoritos/{id_cancion}"""
        response = client.post(
            f"/api/usuarios/{usuario_test.id}/favoritos/{cancion_test.id}"
        )

        assert response.status_code == 201
        assert response.json()["id_cancion"] == cancion_test.id

    def test_listar_favoritos_usuario(
        self,
        client: TestClient,
        session: Session,
        usuario_test: Usuario,
        cancion_test: Cancion,
    ):
        """Test para GET /api/usuarios/{id}/favoritos"""
        session.add(Favorito(id_usuario=usuario_test.id, id_cancion=cancion_test.id))
        session.commit()

        response = client.get(f"/api/usuarios/{usuario_test.id}/favoritos")

        assert response.status_code == 200
        data = response.json()["items"]
        assert len(data) == 1
        # Incluye los datos de la canción
        assert data[0]["cancion"]["titulo"] == cancion_test.titulo

    def test_listar_favoritos_usuario_no_existe(self, client: TestClient):
        response = client.get("/api/usuarios/999/favoritos")

        assert response.status_code == 404

    def test_eliminar_favorito_usuario(
        self,
        client: TestClient,
        session: Session,
        usuario_test: Usuario,
        cancion_test: Cancion,
    ):
        """Test para DELETE /api/usuarios/{id_usuario}/favoritos/{id_cancion}"""
        session.add(Favorito(id_usuario=usuario_test.id, id_cancion=cancion_test.id))
        session.commit()
        url = f"/api/usuarios/{usuario_test.id}/favoritos/{cancion_test.id}"

        assert client.delete(url).status_code == 204
        assert client.delete(url).status_code == 404

    def test_eliminar_usuario_elimina_sus_favoritos(
        self,
        client: TestClient,
        session: Session,
        usuario_test: Usuario,
        cancion_test: Cancion,
    ):
        session.add(Favorito(id_usuario=usuario_test.id, id_cancion=cancion_test.id))
        session.commit()

        client.delete(f"/api/usuarios/{usuario_test.id}")

        assert client.get("/api/favoritos").json()["items"] == []

    def test_eliminar_cancion_elimina_sus_favoritos(
        self,
        client: TestClient,
        session: Session,
        usuario_test: Usuario,
        cancion_test: Cancion,
    ):
        session.add(Favorito(id_usuario=usuario_test.id, id_cancion=cancion_test.id))
        session.commit()

        client.delete(f"/api/canciones/{cancion_test.id}")

        assert client.get("/api/favoritos").json()["items"] == []


# =============================================================================
# TESTS DE INTEGRACIÓN
# =============================================================================


class TestIntegracion:
    """Tests de integración que prueban flujos completos."""

    def test_flujo_completo(self, client: TestClient):
        """Test que verifica el flujo completo de la aplicación"""
        # 1. Crear usuario
        r = client.post(
            "/api/usuarios", json={"nombre": "Laura", "correo": "laura@example.com"}
        )
        assert r.status_code == 201
        id_usuario = r.json()["id"]

        # 2. Crear canción
        r = client.post("/api/canciones", json=datos_cancion())
        assert r.status_code == 201
        id_cancion = r.json()["id"]

        # 3. Marcar como favorito
        r = client.post(f"/api/usuarios/{id_usuario}/favoritos/{id_cancion}")
        assert r.status_code == 201

        # 4. Verificar que aparece en favoritos del usuario
        r = client.get(f"/api/usuarios/{id_usuario}/favoritos")
        assert r.status_code == 200
        favoritos = r.json()["items"]
        assert len(favoritos) == 1
        assert favoritos[0]["cancion"]["id"] == id_cancion

        # 5. Quitarlo de favoritos
        r = client.delete(f"/api/usuarios/{id_usuario}/favoritos/{id_cancion}")
        assert r.status_code == 204
        favs = client.get(f"/api/usuarios/{id_usuario}/favoritos").json()
        assert favs["items"] == []
        assert favs["total"] == 0

    def test_root_y_health(self, client: TestClient):
        root = client.get("/")
        assert root.status_code == 200
        assert root.json()["documentacion"]["swagger"] == "/docs"

        health = client.get("/health")
        assert health.status_code == 200
        assert health.json()["database"] == "ok"


# =============================================================================
# TESTS DE VALIDACIÓN
# =============================================================================


class TestValidacion:
    """Tests para validaciones de datos."""

    @pytest.mark.parametrize(
        "correo", ["sin-arroba", "a@b", "@example.com", "ana@", "ana @example.com"]
    )
    def test_email_invalido(self, client: TestClient, correo: str):
        """Test para verificar validación de email"""
        response = client.post("/api/usuarios", json={"nombre": "X", "correo": correo})

        assert response.status_code == 422

    def test_email_invalido_al_actualizar(
        self, client: TestClient, usuario_test: Usuario
    ):
        response = client.put(
            f"/api/usuarios/{usuario_test.id}", json={"correo": "no-valido"}
        )

        assert response.status_code == 422

    @pytest.mark.parametrize("año", [1899, obtener_año_actual() + 1])
    def test_año_cancion_invalido(self, client: TestClient, año: int):
        """Test para verificar validación de año"""
        response = client.post("/api/canciones", json=datos_cancion(año=año))

        assert response.status_code == 422

    @pytest.mark.parametrize("año", [1900, obtener_año_actual()])
    def test_año_cancion_limites_validos(self, client: TestClient, año: int):
        response = client.post("/api/canciones", json=datos_cancion(año=año))

        assert response.status_code == 201

    @pytest.mark.parametrize("duracion", [0, -10])
    def test_duracion_invalida(self, client: TestClient, duracion: int):
        response = client.post("/api/canciones", json=datos_cancion(duracion=duracion))

        assert response.status_code == 422

    @pytest.mark.parametrize(
        "campo", ["titulo", "artista", "duracion", "año", "genero"]
    )
    def test_campos_requeridos(self, client: TestClient, campo: str):
        """Test para verificar que los campos requeridos son obligatorios"""
        datos = datos_cancion()
        del datos[campo]

        response = client.post("/api/canciones", json=datos)

        assert response.status_code == 422
        assert response.json()["detail"][0]["loc"] == ["body", campo]

    def test_usuario_campos_requeridos(self, client: TestClient):
        response = client.post("/api/usuarios", json={})

        assert response.status_code == 422
        campos = {e["loc"][-1] for e in response.json()["detail"]}
        assert campos == {"nombre", "correo"}

    def test_nombre_vacio(self, client: TestClient):
        response = client.post(
            "/api/usuarios", json={"nombre": "", "correo": "x@example.com"}
        )

        assert response.status_code == 422
