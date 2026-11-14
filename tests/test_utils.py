"""Tests unitarios para las funciones de utils.py."""

from datetime import datetime

import pytest

from utils import (
    formatear_duracion,
    generar_slug,
    obtener_año_actual,
    validar_año,
    validar_correo,
)


@pytest.mark.parametrize(
    "correo",
    ["ana@example.com", "ana.maria+musica@correo.edu.co", "a_b-c@sub-dominio.io"],
)
def test_validar_correo_valido(correo):
    assert validar_correo(correo) is True


@pytest.mark.parametrize(
    "correo",
    ["", "sin-arroba", "a@b", "@example.com", "ana@", "ana @example.com", None, 123],
)
def test_validar_correo_invalido(correo):
    assert validar_correo(correo) is False


@pytest.mark.parametrize(
    "segundos, esperado",
    [(0, "00:00"), (59, "00:59"), (60, "01:00"), (354, "05:54"), (3600, "60:00")],
)
def test_formatear_duracion(segundos, esperado):
    assert formatear_duracion(segundos) == esperado


def test_formatear_duracion_negativa():
    with pytest.raises(ValueError):
        formatear_duracion(-1)


@pytest.mark.parametrize(
    "texto, esperado",
    [
        ("Bohemian Rhapsody", "bohemian-rhapsody"),
        ("  Canción   de Prueba  ", "cancion-de-prueba"),
        ("¡Hola, Mundo!", "hola-mundo"),
        ("AC/DC -- Back in Black", "acdc-back-in-black"),
        ("---", ""),
    ],
)
def test_generar_slug(texto, esperado):
    assert generar_slug(texto) == esperado


def test_obtener_año_actual():
    assert obtener_año_actual() == datetime.now().year


@pytest.mark.parametrize(
    "año, esperado",
    [
        (1899, False),
        (1900, True),
        (1975, True),
        (obtener_año_actual(), True),
        (obtener_año_actual() + 1, False),
    ],
)
def test_validar_año(año, esperado):
    assert validar_año(año) is esperado
