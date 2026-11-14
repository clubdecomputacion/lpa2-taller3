"""
Modelos de datos de la API de Música.

Por cada entidad hay:
- <Entidad>Base: campos comunes con sus validaciones.
- <Entidad>: la tabla (table=True).
- <Entidad>Create / <Entidad>Update: lo que recibe la API (validado por Pydantic).
- <Entidad>Read: lo que devuelve la API.

Nota: SQLModel NO ejecuta validadores en los modelos table=True, por eso
la validación vive en los esquemas Create/Update.
"""

from datetime import UTC, datetime

from pydantic import field_validator
from sqlmodel import Field, Relationship, SQLModel, UniqueConstraint

from utils import obtener_año_actual, validar_año, validar_correo


def ahora_utc() -> datetime:
    return datetime.now(UTC)


# =============================================================================
# VALIDADORES REUTILIZABLES
# =============================================================================


def _validar_correo(v: str | None) -> str | None:
    if v is None:
        return v
    v = v.strip().lower()
    if not validar_correo(v):
        raise ValueError("El correo electrónico no tiene un formato válido")
    return v


def _validar_año(v: int | None) -> int | None:
    if v is not None and not validar_año(v):
        raise ValueError(f"El año debe estar entre 1900 y {obtener_año_actual()}")
    return v


# =============================================================================
# USUARIO
# =============================================================================


class UsuarioBase(SQLModel):
    nombre: str = Field(min_length=1, max_length=100)
    correo: str = Field(max_length=255, unique=True, index=True)


class Usuario(UsuarioBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    fecha_registro: datetime = Field(default_factory=ahora_utc)

    favoritos: list["Favorito"] = Relationship(
        back_populates="usuario", cascade_delete=True
    )


class UsuarioCreate(UsuarioBase):
    @field_validator("correo")
    @classmethod
    def validar_correo(cls, v: str) -> str:
        return _validar_correo(v)


class UsuarioUpdate(SQLModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=100)
    correo: str | None = Field(default=None, max_length=255)

    @field_validator("correo")
    @classmethod
    def validar_correo(cls, v: str | None) -> str | None:
        return _validar_correo(v)


class UsuarioRead(UsuarioBase):
    id: int
    fecha_registro: datetime


# =============================================================================
# CANCIÓN
# =============================================================================


class CancionBase(SQLModel):
    titulo: str = Field(min_length=1, max_length=200, index=True)
    artista: str = Field(min_length=1, max_length=200, index=True)
    album: str | None = Field(default=None, max_length=200)
    duracion: int = Field(gt=0, description="Duración en segundos")
    año: int
    genero: str = Field(min_length=1, max_length=50, index=True)


class Cancion(CancionBase, table=True):
    __tablename__ = "cancion"

    id: int | None = Field(default=None, primary_key=True)
    fecha_creacion: datetime = Field(default_factory=ahora_utc)

    favoritos: list["Favorito"] = Relationship(
        back_populates="cancion", cascade_delete=True
    )


class CancionCreate(CancionBase):
    @field_validator("año")
    @classmethod
    def validar_año(cls, v: int) -> int:
        return _validar_año(v)


class CancionUpdate(SQLModel):
    titulo: str | None = Field(default=None, min_length=1, max_length=200)
    artista: str | None = Field(default=None, min_length=1, max_length=200)
    album: str | None = Field(default=None, max_length=200)
    duracion: int | None = Field(default=None, gt=0)
    año: int | None = None
    genero: str | None = Field(default=None, min_length=1, max_length=50)

    @field_validator("año")
    @classmethod
    def validar_año(cls, v: int | None) -> int | None:
        return _validar_año(v)


class CancionRead(CancionBase):
    id: int
    fecha_creacion: datetime


# =============================================================================
# FAVORITO
# =============================================================================


class FavoritoBase(SQLModel):
    id_usuario: int = Field(foreign_key="usuario.id", ondelete="CASCADE", index=True)
    id_cancion: int = Field(foreign_key="cancion.id", ondelete="CASCADE", index=True)


class Favorito(FavoritoBase, table=True):
    # Un usuario no puede marcar dos veces la misma canción
    __table_args__ = (
        UniqueConstraint("id_usuario", "id_cancion", name="uq_usuario_cancion"),
    )

    id: int | None = Field(default=None, primary_key=True)
    fecha_marcado: datetime = Field(default_factory=ahora_utc)

    usuario: Usuario | None = Relationship(back_populates="favoritos")
    cancion: Cancion | None = Relationship(back_populates="favoritos")


class FavoritoCreate(FavoritoBase):
    pass


class FavoritoRead(FavoritoBase):
    id: int
    fecha_marcado: datetime


class FavoritoReadConCancion(FavoritoRead):
    """Favorito con los datos de la canción, útil para 'mis favoritos'."""

    cancion: CancionRead
