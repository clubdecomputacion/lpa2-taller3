"""Endpoints de canciones: /api/canciones"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, col, select

from musica_api.database import get_session
from musica_api.models import Cancion, CancionCreate, CancionRead, CancionUpdate
from musica_api.paginacion import (
    Pagina,
    ParametrosPaginacion,
    paginar,
    parametros_paginacion,
)

router = APIRouter()
logger = logging.getLogger(__name__)


def _obtener_o_404(session: Session, id: int) -> Cancion:
    cancion = session.get(Cancion, id)
    if not cancion:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Canción no encontrada")
    return cancion


@router.get("", response_model=Pagina[CancionRead])
def listar_canciones(
    session: Session = Depends(get_session),
    pag: ParametrosPaginacion = Depends(parametros_paginacion),
):
    return paginar(session, select(Cancion).order_by(Cancion.id), pag)


@router.post("", response_model=CancionRead, status_code=status.HTTP_201_CREATED)
def crear_cancion(datos: CancionCreate, session: Session = Depends(get_session)):
    cancion = Cancion.model_validate(datos)
    session.add(cancion)
    session.commit()
    session.refresh(cancion)
    logger.info("Canción %s creada", cancion.id)
    return cancion


# IMPORTANTE: /buscar debe declararse antes de /{id}, si no FastAPI
# intentaría interpretar "buscar" como un id.
@router.get("/buscar", response_model=Pagina[CancionRead])
def buscar_canciones(
    titulo: str | None = None,
    artista: str | None = None,
    genero: str | None = None,
    session: Session = Depends(get_session),
    pag: ParametrosPaginacion = Depends(parametros_paginacion),
):
    """Búsqueda parcial e insensible a mayúsculas; los filtros se combinan con AND."""
    query = select(Cancion)
    if titulo:
        query = query.where(col(Cancion.titulo).ilike(f"%{titulo}%"))
    if artista:
        query = query.where(col(Cancion.artista).ilike(f"%{artista}%"))
    if genero:
        query = query.where(col(Cancion.genero).ilike(f"%{genero}%"))
    return paginar(session, query.order_by(Cancion.id), pag)


@router.get("/{id}", response_model=CancionRead)
def obtener_cancion(id: int, session: Session = Depends(get_session)):
    return _obtener_o_404(session, id)


@router.put("/{id}", response_model=CancionRead)
def actualizar_cancion(
    id: int, datos: CancionUpdate, session: Session = Depends(get_session)
):
    cancion = _obtener_o_404(session, id)
    cambios = datos.model_dump(exclude_unset=True)
    cancion.sqlmodel_update(cambios)
    session.add(cancion)
    session.commit()
    session.refresh(cancion)
    logger.info("Canción %s actualizada (campos: %s)", id, ", ".join(cambios))
    return cancion


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_cancion(id: int, session: Session = Depends(get_session)):
    cancion = _obtener_o_404(session, id)
    session.delete(cancion)  # sus favoritos se eliminan en cascada
    session.commit()
    logger.info("Canción %s eliminada", id)
