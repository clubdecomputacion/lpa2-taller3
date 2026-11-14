"""
Paginación de listados.

Todos los listados devuelven una `Pagina` con los elementos de la página
y el total de resultados, para que el frontend pueda calcular el número de
páginas:

    GET /api/canciones?offset=20&limit=10
    {"items": [...], "total": 57, "offset": 20, "limit": 10}
"""

from dataclasses import dataclass
from typing import Any

from fastapi import Query
from pydantic import BaseModel, Field
from sqlmodel import Session, func, select
from sqlmodel.sql.expression import SelectOfScalar

LIMITE_POR_DEFECTO = 20
LIMITE_MAXIMO = 100


class Pagina[T](BaseModel):
    items: list[T]
    total: int = Field(description="Total de resultados (sin paginar)")
    offset: int = Field(description="Elementos omitidos antes de esta página")
    limit: int = Field(description="Tamaño máximo de la página")


@dataclass
class ParametrosPaginacion:
    offset: int
    limit: int


def parametros_paginacion(
    offset: int = Query(0, ge=0, description="Número de elementos a omitir"),
    limit: int = Query(
        LIMITE_POR_DEFECTO,
        ge=1,
        le=LIMITE_MAXIMO,
        description=f"Elementos por página (máximo {LIMITE_MAXIMO})",
    ),
) -> ParametrosPaginacion:
    """Dependencia de FastAPI con los parámetros de paginación validados."""
    return ParametrosPaginacion(offset=offset, limit=limit)


def paginar(
    session: Session, query: SelectOfScalar, params: ParametrosPaginacion
) -> dict[str, Any]:
    """
    Ejecuta `query` paginada y cuenta el total de resultados.

    El total se calcula sobre la misma consulta (con sus filtros), así
    también funciona con búsquedas.
    """
    total = session.exec(select(func.count()).select_from(query.subquery())).one()
    items = session.exec(query.offset(params.offset).limit(params.limit)).all()
    return {
        "items": items,
        "total": total,
        "offset": params.offset,
        "limit": params.limit,
    }
