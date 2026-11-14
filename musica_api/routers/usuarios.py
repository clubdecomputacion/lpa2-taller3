"""Endpoints de usuarios: /api/usuarios"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from musica_api.database import get_session
from musica_api.models import (
    Favorito,
    FavoritoRead,
    FavoritoReadConCancion,
    Usuario,
    UsuarioCreate,
    UsuarioRead,
    UsuarioUpdate,
)
from musica_api.paginacion import (
    Pagina,
    ParametrosPaginacion,
    paginar,
    parametros_paginacion,
)
from musica_api.routers.favoritos import marcar_favorito

router = APIRouter()
logger = logging.getLogger(__name__)


def _obtener_o_404(session: Session, id: int) -> Usuario:
    usuario = session.get(Usuario, id)
    if not usuario:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuario no encontrado")
    return usuario


def _verificar_correo_libre(
    session: Session, correo: str, excluir_id: int | None = None
):
    query = select(Usuario).where(Usuario.correo == correo)
    if excluir_id is not None:
        query = query.where(Usuario.id != excluir_id)
    if session.exec(query).first():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "El correo ya está registrado")


@router.get("", response_model=Pagina[UsuarioRead])
def listar_usuarios(
    session: Session = Depends(get_session),
    pag: ParametrosPaginacion = Depends(parametros_paginacion),
):
    return paginar(session, select(Usuario).order_by(Usuario.id), pag)


@router.post("", response_model=UsuarioRead, status_code=status.HTTP_201_CREATED)
def crear_usuario(datos: UsuarioCreate, session: Session = Depends(get_session)):
    _verificar_correo_libre(session, datos.correo)
    usuario = Usuario.model_validate(datos)
    session.add(usuario)
    session.commit()
    session.refresh(usuario)
    logger.info("Usuario %s creado", usuario.id)
    return usuario


@router.get("/{id}", response_model=UsuarioRead)
def obtener_usuario(id: int, session: Session = Depends(get_session)):
    return _obtener_o_404(session, id)


@router.put("/{id}", response_model=UsuarioRead)
def actualizar_usuario(
    id: int, datos: UsuarioUpdate, session: Session = Depends(get_session)
):
    usuario = _obtener_o_404(session, id)
    cambios = datos.model_dump(exclude_unset=True)
    if "correo" in cambios:
        _verificar_correo_libre(session, cambios["correo"], excluir_id=id)
    usuario.sqlmodel_update(cambios)
    session.add(usuario)
    session.commit()
    session.refresh(usuario)
    logger.info("Usuario %s actualizado (campos: %s)", id, ", ".join(cambios))
    return usuario


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_usuario(id: int, session: Session = Depends(get_session)):
    usuario = _obtener_o_404(session, id)
    session.delete(usuario)  # sus favoritos se eliminan en cascada
    session.commit()
    logger.info("Usuario %s eliminado", id)


# -----------------------------------------------------------------------------
# Favoritos de un usuario
# -----------------------------------------------------------------------------


@router.get("/{id}/favoritos", response_model=Pagina[FavoritoReadConCancion])
def listar_favoritos_usuario(
    id: int,
    session: Session = Depends(get_session),
    pag: ParametrosPaginacion = Depends(parametros_paginacion),
):
    _obtener_o_404(session, id)
    # Los más recientes primero
    query = (
        select(Favorito)
        .where(Favorito.id_usuario == id)
        .order_by(Favorito.fecha_marcado.desc(), Favorito.id.desc())
    )
    return paginar(session, query, pag)


@router.post(
    "/{id_usuario}/favoritos/{id_cancion}",
    response_model=FavoritoRead,
    status_code=status.HTTP_201_CREATED,
)
def marcar_favorito_usuario(
    id_usuario: int, id_cancion: int, session: Session = Depends(get_session)
):
    return marcar_favorito(session, id_usuario, id_cancion)


@router.delete(
    "/{id_usuario}/favoritos/{id_cancion}", status_code=status.HTTP_204_NO_CONTENT
)
def eliminar_favorito_usuario(
    id_usuario: int, id_cancion: int, session: Session = Depends(get_session)
):
    favorito = session.exec(
        select(Favorito).where(
            Favorito.id_usuario == id_usuario, Favorito.id_cancion == id_cancion
        )
    ).first()
    if not favorito:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Favorito no encontrado")
    id_favorito = favorito.id
    session.delete(favorito)
    session.commit()
    logger.info(
        "Favorito %s eliminado (usuario=%s, cancion=%s)",
        id_favorito,
        id_usuario,
        id_cancion,
    )
