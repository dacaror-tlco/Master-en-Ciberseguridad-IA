"""
Compatibilidad del espejo de solo lectura (`app/modules/shared/models.py`)
con las tablas que escriben realmente los otros módulos.

El Módulo 1 (rama `modulo-casos`) declara `cases.estado` como
`Enum(..., values_callable=...)`, es decir guarda el **valor** del Enum
(`abierto`), igual que la especificación del proyecto. Por defecto SQLAlchemy
guardaría y buscaría por **nombre de miembro** (`ABIERTO`), así que sin
`values_callable` el Módulo 5 no puede leer una fila escrita por el Módulo 1.

Estos tests insertan filas con SQL crudo, tal y como quedan en la base de datos
compartida, en lugar de crearlas con el propio ORM: crearlas con el ORM usaría
la misma convención en escritura y lectura y no detectaría el desajuste.
"""
from sqlalchemy import text

from app.modules.shared.models import Case, EstadoCaso, Severidad, TrackingEvent

from .conftest import TestingSessionLocal, engine


def test_lee_estado_escrito_por_modulo_1():
    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO cases "
                "(id, nombre, estado, fecha_creacion, descripcion, responsable) "
                "VALUES (1, 'Caso del Módulo 1', 'abierto', "
                "'2026-08-15 10:00:00', 'Alta desde Módulo 1', 'Perito')"
            )
        )

    session = TestingSessionLocal()
    try:
        caso = session.get(Case, 1)
        assert caso.estado is EstadoCaso.ABIERTO
    finally:
        session.close()


def test_lee_severidad_escrita_por_modulo_3():
    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO cases "
                "(id, nombre, estado, fecha_creacion, descripcion, responsable) "
                "VALUES (1, 'Caso', 'en_progreso', '2026-08-15 10:00:00', '', 'Perito')"
            )
        )
        conn.execute(
            text(
                "INSERT INTO tracking_events "
                "(id, case_id, hora, evento, severidad, fuente_log, usuario_detectado) "
                "VALUES (1, 1, '2026-08-15 11:00:00', 'Acceso no autorizado', "
                "'critica', 'auth.log', 'www-data')"
            )
        )

    session = TestingSessionLocal()
    try:
        evento = session.get(TrackingEvent, 1)
        assert evento.severidad is Severidad.CRITICA
    finally:
        session.close()


def test_el_orm_persiste_el_valor_no_el_nombre(db_session, case_con_timeline):
    """La escritura tiene que ser simétrica: un caso creado por el ORM debe
    quedar en la base de datos como lo dejaría el Módulo 1."""
    guardado = db_session.execute(
        text("SELECT estado FROM cases WHERE id = :id"),
        {"id": case_con_timeline.id},
    ).scalar_one()

    assert guardado == "en_progreso"
