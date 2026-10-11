"""
conftest.py de los tests. IMPORTANTE: fija DATABASE_URL a un
SQLite temporal ANTES de que cualquier test importe app.core.database
(que lee la variable de entorno en el momento del import), para no
depender de un servidor MySQL real al testear.
"""

import os
import tempfile

_tmp_db_fd, _tmp_db_path = tempfile.mkstemp(suffix=".db")
os.close(_tmp_db_fd)
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp_db_path}"
# La cadena de integridad de los tests va a una carpeta temporal: la
# limpieza de abajo borra sus ficheros, y no debe tocar nunca las cadenas
# reales del módulo.
os.environ["TRACKING_CHAIN_DIR"] = tempfile.mkdtemp(prefix="tracking_chain_tests_")
# Secreto de los JWT, fijado ANTES de importar app.modules.auth.security
# (lo lee en una constante, al importarse). Es ficticio y solo vive en los
# tests: no toca el .env ni se parece al secreto real de Casos. Con el
# valor de ejemplo ("change_me", 9 bytes) pyjwt avisaría de clave corta.
os.environ["JWT_SECRET"] = "solo-para-tests-nunca-un-secreto-real-0123456789abcdef"
# La autenticación se prueba como en producción: obligatoria. El modo
# suelto (TRACKING_AUTH_DESACTIVADA) tiene sus propios tests, que la
# activan y la quitan ellos.
os.environ.pop("TRACKING_AUTH_DESACTIVADA", None)

from contextlib import contextmanager  # noqa: E402
from datetime import datetime, timedelta, timezone  # noqa: E402

import jwt  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import Boolean, Column, Integer, String, Text  # noqa: E402

from app.modules.tracking.chain_integrity import CHAIN_STORAGE_DIR  # noqa: E402
from app.core.database import Base, SessionLocal, engine  # noqa: E402

# fuerza a que el modelo propio de este backend se registre en Base.metadata
from app.modules.tracking import models as _tracking_models  # noqa: E402,F401


class SharedCaseRow(Base):
    """
    `cases` MÍNIMA, solo para estos tests: tracking_events tiene una FK a
    `cases.id` y el test corre contra una SQLite temporal y aislada (no la
    base compartida), así que necesita algo que la satisfaga. Esto NO es
    el modelo de Casos (retirado de este backend al integrar en
    `development`; ver docs/CONTRATOS.md) — es un accesorio de test, vive
    solo aquí y nunca se importa desde app/.

    Incluye `eliminado`, como la tabla real del Módulo 1, para probar que
    Tracking respeta el borrado lógico.
    """
    __tablename__ = "cases"
    # app/modules/tracking/models.py ya registra una referencia mínima a
    # `cases` (solo `id`) para resolver la FK; esta clase la amplía.
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True)
    nombre = Column(String(150), nullable=False)
    estado = Column(String(30), nullable=False, default="abierto")
    responsable = Column(String(100), nullable=False)
    descripcion = Column(Text, nullable=True)
    eliminado = Column(Boolean, nullable=False, default=False)


def crear_caso(nombre: str = "Caso de test", responsable: str = "perito", **extra) -> int:
    """Inserta un caso "ya existente", como lo haría Casos en la base real."""
    with SessionLocal() as db:
        caso = SharedCaseRow(nombre=nombre, responsable=responsable, **extra)
        db.add(caso)
        db.commit()
        return caso.id


def token_de_prueba(*, role: str = "analyst", caduca_en: timedelta = timedelta(hours=1)) -> str:
    """JWT con el mismo contrato que emite Casos: `sub`, `role`, `iat`, `exp`."""
    ahora = datetime.now(timezone.utc)
    payload = {"sub": "1", "role": role, "iat": ahora, "exp": ahora + caduca_en}
    return jwt.encode(payload, os.environ["JWT_SECRET"], algorithm="HS256")


@contextmanager
def cliente(**kwargs):
    """TestClient con un token de analyst ya puesto.

    Desde la Fase 4 los cinco endpoints exigen autenticación, así que un
    cliente sin cabecera solo sirve para probar la propia autenticación
    (eso está en test_auth_tracking.py). El resto de la suite prueba lógica
    de negocio y entra por aquí, para no repetir la cabecera en diez
    ficheros ni olvidarla en el siguiente que se añada.
    """
    from app.main import app  # import diferido: app importa la BD ya configurada arriba

    with TestClient(app, **kwargs) as c:
        c.headers["Authorization"] = f"Bearer {token_de_prueba()}"
        yield c


@pytest.fixture
def client():
    with cliente() as c:
        yield c


@pytest.fixture(autouse=True)
def clean_database_between_tests():
    """Tablas limpias en cada test, y también el store local de la
    cadena de hashes (que vive en ficheros aparte, no en la BD)."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    if CHAIN_STORAGE_DIR.exists():
        for f in CHAIN_STORAGE_DIR.glob("*.db"):
            f.unlink()

    yield
