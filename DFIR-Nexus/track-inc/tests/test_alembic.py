"""
Las migraciones deben coincidir con los modelos y no tocar tablas ajenas.

`alembic revision --autogenerate` comparaba contra toda la base de datos y,
al no haber modelo de `evidences` (tabla del Módulo 1), proponía BORRARLA.
En la base compartida eso habría sido desastroso.
"""

from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

RAIZ = Path(__file__).resolve().parents[1]


@pytest.fixture
def config_temporal(tmp_path):
    url = f"sqlite:///{(tmp_path / 'migraciones.db').as_posix()}"
    cfg = Config(str(RAIZ / "alembic.ini"))
    cfg.set_main_option("script_location", str(RAIZ / "alembic"))
    cfg.set_main_option("sqlalchemy.url", url)
    return cfg, url


def test_modelos_y_migraciones_coinciden_sin_tocar_tablas_ajenas(config_temporal):
    cfg, _ = config_temporal
    command.upgrade(cfg, "head")
    command.check(cfg)  # lanza si autogenerate propondría cambios


def test_usa_la_tabla_de_versiones_del_equipo(config_temporal):
    cfg, url = config_temporal
    command.upgrade(cfg, "head")
    tablas = set(inspect(create_engine(url)).get_table_names())
    assert "alembic_version_tracking" in tablas
    assert "alembic_version" not in tablas
