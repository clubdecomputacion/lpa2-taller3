"""
Configuración de la base de datos.
Crea el engine de SQLModel y provee la dependencia de sesión para los endpoints.
"""

from collections.abc import Generator

from sqlmodel import Session, SQLModel, create_engine

from musica_api.config import get_settings

settings = get_settings()

# SQLite necesita check_same_thread=False porque FastAPI usa varios hilos
connect_args = (
    {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
)

engine = create_engine(settings.database_url, echo=False, connect_args=connect_args)


def create_db_and_tables() -> None:
    """Crea todas las tablas definidas en los modelos, si no existen."""
    # Importar los modelos para registrarlos en SQLModel.metadata
    from musica_api import models  # noqa: F401

    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """Dependencia de FastAPI: abre una sesión por request y la cierra al final."""
    with Session(engine) as session:
        yield session
