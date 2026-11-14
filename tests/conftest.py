"""Fixtures compartidas por todos los tests."""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from main import app
from musica_api.database import get_session


@pytest.fixture(name="session")
def session_fixture():
    """
    Crea una sesión de base de datos en memoria para cada test.
    Se limpia automáticamente después de cada test.
    """
    # StaticPool hace que todas las conexiones compartan la misma BD en memoria
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(name="client")
def client_fixture(session: Session):
    """
    Crea un cliente de pruebas de FastAPI con la sesión de test.
    """

    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    # Sin "with": no se ejecuta el lifespan, así no se toca musica.db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()
