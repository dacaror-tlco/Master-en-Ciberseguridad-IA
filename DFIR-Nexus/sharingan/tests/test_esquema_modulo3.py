"""
Contrato con el esquema **real** de los Módulos 3 y 4, contrastado el
2026-09-02 contra el código de sus ramas.

Mismo criterio que `test_esquema_modulo1.py`: `test_contrato_modulos.py` fija
hasta dónde llega la tolerancia del espejo; esto comprueba que el Módulo 5
funciona contra lo que los otros módulos crean y escriben de verdad. Al
fusionar, el espejo desaparece y estas tablas las crea su dueño.

Los dos módulos entran en el mismo fichero porque el Módulo 4 no tiene esquema
propio que contrastar: no crea `timeline_events`, solo inserta en ella filas
que apuntan a `tracking_events` del Módulo 3. Separarlos dejaría cada mitad
probando algo que la otra hace posible.

## Módulo 3 (`track-inc`)

El DDL de abajo está transcrito literalmente de
`track-inc/alembic/versions/6b5d49c8a514_initial_cases_placeholder_tracking_.py`
(commit `1eeacc1`, 2026-08-31). Sigue la especificación al pie de la letra y
usa `values_callable` en `severidad`, así que guarda `alta` y no `ALTA` — que
es lo que este espejo lee. La lección del Enum `estado` del Módulo 1 no se
repite aquí.

Lo que sí divergía: el espejo declaraba una columna `detalles` (JSON) que su
tabla no tiene. Ver `test_el_espejo_no_declara_columnas_que_el_modulo_3_no_tiene`.

## Módulo 4 (`T1m3-l1n3`)

Su rama tiene el código **en el commit anterior al último**: el último dejó
`backend/modules/timeline/update_timeline.py` en un comentario de relleno. Las
filas que este fichero escribe reproducen su `INSERT` literal, incluido el
prefijo «Tracking: » de la descripción y el `orden` empezando en 1.

Ojo con lo que ese script **no** hace: solo lee `tracking_events`. No proyecta
ni evidencias ni OSINT a la cronología, así que hoy los Anexos A y B nunca
tendrían entradas que los respalden. Eso no es algo que este módulo pueda
arreglar, pero sí conviene que quede fijado por escrito y en un test.
"""
import json
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    create_engine,
    insert,
    select,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.modules.reports import repository
from app.modules.reports.document import construir_documento
from app.modules.reports.json_builder import construir_json
from app.modules.shared.models import Case, EstadoCaso, Severidad, TimelineEvent
from tests.conftest import NARRATIVA_FALSA
from tests.test_esquema_modulo1 import cases_modulo1

# --- DDL del Módulo 3, transcrito de su migración 6b5d49c8a514 ---------------

metadata_modulo3 = MetaData()

# `cases` es del Módulo 1, y la migración del Módulo 3 lo dice en su propia
# cabecera: «La tabla `cases` la crea el Modulo 1 (revision 0001), que es su
# dueno». Aquí hace falta igualmente, porque `tracking_events.case_id` es una
# FK real hacia ella y sin la tabla referenciada no se puede crear el esquema.
#
# Se copia la que ya está transcrita en `test_esquema_modulo1.py` en vez de
# volver a escribirla: dos transcripciones del mismo DDL acabarían divergiendo,
# y entonces uno de los dos ficheros estaría probando contra un Módulo 1 que no
# existe.
cases_modulo1.to_metadata(metadata_modulo3)

tracking_events_modulo3 = Table(
    "tracking_events",
    metadata_modulo3,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("case_id", Integer, ForeignKey("cases.id"), nullable=False),
    Column("hora", DateTime(), nullable=False),
    Column("evento", Text(), nullable=False),
    Column(
        "severidad",
        Enum("baja", "media", "alta", "critica", name="severidad_tracking"),
        nullable=False,
    ),
    Column("fuente_log", String(100), nullable=True),
    Column("usuario_detectado", String(100), nullable=True),
    Index("ix_tracking_events_case_id", "case_id"),
)


@pytest.fixture
def sesion_sobre_esquema_real():
    """
    Base de datos en la que `tracking_events` la crea el DDL del Módulo 3 y el
    resto de tablas las crea este módulo. Es la foto de después de fusionar:
    manda el esquema del dueño de cada tabla.
    """
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    propias = [
        tabla
        for tabla in Base.metadata.sorted_tables
        if tabla.name not in metadata_modulo3.tables
    ]
    Base.metadata.create_all(bind=engine, tables=propias)
    metadata_modulo3.create_all(bind=engine)

    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
def caso(sesion_sobre_esquema_real):
    fila = Case(
        nombre="Intrusión por servicio expuesto",
        estado=EstadoCaso.EN_PROGRESO,
        fecha_creacion=datetime(2026, 8, 31, 9, 0),
        descripcion="Bind shell detectada en un servidor de preproducción",
        responsable="Ana Pérez",
    )
    sesion_sobre_esquema_real.add(fila)
    sesion_sobre_esquema_real.commit()
    return fila


def _insertar_evento_como_el_modulo_3(sesion, case_id, **campos):
    """
    Escribe el evento con el DDL del Módulo 3 y sin pasar por el espejo, que es
    justo lo que ocurrirá en producción: la fila la crea el otro módulo.
    """
    valores = {
        "case_id": case_id,
        "hora": datetime(2026, 8, 31, 16, 20, 15),
        "evento": "Shell de root detectada en bindshell",
        "severidad": "critica",
        "fuente_log": "nc",
        "usuario_detectado": "root",
        **campos,
    }
    resultado = sesion.execute(insert(tracking_events_modulo3).values(**valores))
    sesion.commit()
    return resultado.inserted_primary_key[0]


def _proyectar_a_timeline_como_el_modulo_4(sesion, case_id):
    """
    Reproduce el `INSERT` de `update_timeline.py` (Módulo 4): una entrada de
    cronología por cada `tracking_event` del caso, ordenadas por `hora`, con la
    descripción prefijada y el `orden` empezando en 1.
    """
    filas = sesion.execute(
        select(tracking_events_modulo3)
        .where(tracking_events_modulo3.c.case_id == case_id)
        .order_by(tracking_events_modulo3.c.hora)
    ).mappings().all()

    # El script del Módulo 4 no da `id`: en MySQL la columna autoincrementa.
    # Aquí hay que darlo porque el espejo declara `timeline_events.id` como
    # `IdAjeno` (texto, para admitir los `tl-…` que el Módulo 3 propuso) y un
    # texto no autoincrementa. No es un problema real —el Módulo 5 nunca
    # escribe en esta tabla—, pero sí la razón de que este ayudante numere a
    # mano lo que en producción numera el motor.
    siguiente = sesion.query(TimelineEvent).count()

    for orden, evento in enumerate(filas, start=1):
        sesion.add(
            TimelineEvent(
                id=siguiente + orden,
                case_id=case_id,
                fecha_hora=evento["hora"],
                descripcion=f"Tracking: {evento['evento']}",
                origen_modulo="tracking",
                origen_id=evento["id"],
                orden=orden,
            )
        )
    sesion.commit()
    return len(filas)


# --- El espejo no puede pedir más de lo que hay ------------------------------


def test_el_espejo_no_declara_columnas_que_el_modulo_3_no_tiene():
    """
    Alarma de deriva, y la que ya cazó algo real: el espejo declaraba una
    columna `detalles` (JSON) que el Módulo 3 propuso por escrito y nunca
    llegó a crear. Con ella, cualquier `SELECT` del Anexo C habría fallado con
    «Unknown column» y no se habría generado ningún informe del caso.

    Que la columna fuese nullable no salvaba nada: nullable dice qué puede ir
    dentro de una columna que existe, no si existe.
    """
    reales = set(metadata_modulo3.tables["tracking_events"].columns.keys())
    espejo = set(Base.metadata.tables["tracking_events"].columns.keys())

    sobran = espejo - reales
    assert not sobran, (
        f"El espejo de `tracking_events` declara columnas que el Módulo 3 no "
        f"crea: {sorted(sobran)}. O las añade el Módulo 3, o salen del espejo."
    )


def test_el_espejo_reconoce_todas_las_severidades_que_permite_el_modulo_3():
    """
    La alarma de deriva del Enum. Si el Módulo 3 añade un quinto nivel, salta
    aquí al ejecutar los tests; si no saltara, el fallo aparecería al leer un
    evento con ese nivel —`_missing_` devolvería None y SQLAlchemy lanzaría
    LookupError—, y ese caso no podría generar ningún informe.
    """
    permitidos = set(tracking_events_modulo3.c.severidad.type.enums)
    assert permitidos == {"baja", "media", "alta", "critica"}, (
        "Cambió el ENUM transcrito del Módulo 3; revisar que el espejo lo cubra."
    )

    for valor in permitidos:
        assert Severidad(valor).value == valor


def test_el_esquema_activo_es_el_del_modulo_3_y_no_el_espejo(
    sesion_sobre_esquema_real, caso
):
    """
    Comprobación de que este fichero corre de verdad sobre el DDL del Módulo 3.
    Sin ella, todo lo demás podría estar probando el espejo sin que se notara.

    El discriminante es `evento`: el Módulo 3 la declara NOT NULL y el espejo
    la deja sin restricción explícita. Esa diferencia sí la aplica SQLite, a
    diferencia del ENUM de `severidad`, que sobre SQLite no emite CHECK
    (`sa.Enum` trae `create_constraint=False` en SQLAlchemy 2.x).
    """
    with pytest.raises(IntegrityError):
        _insertar_evento_como_el_modulo_3(
            sesion_sobre_esquema_real, caso.id, evento=None
        )


# --- Lectura de eventos escritos por el Módulo 3 -----------------------------


def test_un_evento_escrito_por_el_modulo_3_se_lee_entero(
    sesion_sobre_esquema_real, caso
):
    sesion = sesion_sobre_esquema_real
    _insertar_evento_como_el_modulo_3(sesion, caso.id)

    evento = repository.get_tracking_events(sesion, caso.id)[0]

    assert evento.severidad is Severidad.CRITICA
    assert evento.evento == "Shell de root detectada en bindshell"
    assert evento.fuente_log == "nc"
    assert evento.usuario_detectado == "root"
    assert evento.hora == datetime(2026, 8, 31, 16, 20, 15)


@pytest.mark.parametrize(
    "escrita, esperada",
    [
        ("baja", Severidad.BAJA),
        ("media", Severidad.MEDIA),
        ("alta", Severidad.ALTA),
        ("critica", Severidad.CRITICA),
    ],
)
def test_las_cuatro_severidades_del_modulo_3_se_leen(
    sesion_sobre_esquema_real, caso, escrita, esperada
):
    """
    Los cuatro valores que su ENUM permite. El Módulo 3 usa `values_callable`,
    así que guarda el valor y no el nombre de miembro; si algún día lo quitara,
    guardaría `ALTA` y esto se caería — que es el fallo exacto que tuvo el
    Módulo 1 y que habría impedido generar cualquier informe.
    """
    sesion = sesion_sobre_esquema_real
    _insertar_evento_como_el_modulo_3(sesion, caso.id, severidad=escrita)

    assert repository.get_tracking_events(sesion, caso.id)[0].severidad is esperada


def test_el_id_entero_del_modulo_3_se_normaliza_a_texto(
    sesion_sobre_esquema_real, caso
):
    """
    `IdAjeno` acepta texto porque el Módulo 3 lo propuso así, pero su tabla
    real usa INTEGER autoincremental. Un entero tiene que seguir cabiendo, y
    llegar a la columna «Ref.» como texto para que no dependa del driver.
    """
    sesion = sesion_sobre_esquema_real
    id_real = _insertar_evento_como_el_modulo_3(sesion, caso.id)

    assert isinstance(id_real, int)
    assert repository.get_tracking_events(sesion, caso.id)[0].id == str(id_real)


# --- La cronología que escribe el Módulo 4 -----------------------------------


def test_la_cronologia_del_modulo_4_referencia_eventos_del_modulo_3(
    sesion_sobre_esquema_real, caso
):
    """
    El cruce que sostiene el informe entero: la columna «Ref.» dice
    `tracking#<id>` y ese id tiene que aparecer como fila del Anexo C.

    El script del Módulo 4 escribe `origen_modulo = 'tracking'` —el nombre de
    la tabla, no el nombre en clave del módulo— y `origen_id` con el entero de
    `tracking_events.id`. Es exactamente lo que este módulo exige desde
    `52c50d8`, así que el contrato se sostiene contra su código real.
    """
    sesion = sesion_sobre_esquema_real
    ids = [
        _insertar_evento_como_el_modulo_3(
            sesion,
            caso.id,
            hora=datetime(2026, 8, 31, 16, 0) + timedelta(minutes=10 * i),
            evento=f"Evento {i} detectado por el agente",
            severidad="alta",
        )
        for i in range(3)
    ]
    assert _proyectar_a_timeline_como_el_modulo_4(sesion, caso.id) == 3

    cronologia = repository.get_timeline_events(sesion, caso.id)
    anexo_c = {e.id for e in repository.get_tracking_events(sesion, caso.id)}

    assert [e.orden for e in cronologia] == [1, 2, 3]
    assert all(e.origen_modulo == "tracking" for e in cronologia)
    assert {e.origen_id for e in cronologia} == {str(i) for i in ids}
    # La promesa del apartado de metodología: toda «Ref.» resuelve en su anexo.
    assert {e.origen_id for e in cronologia} <= anexo_c


def test_se_genera_el_informe_entero_sobre_los_esquemas_de_los_modulos_3_y_4(
    sesion_sobre_esquema_real, caso
):
    """
    Prueba de integración de la fusión: eventos escritos con el DDL del Módulo
    3, cronología proyectada como lo hace el script del Módulo 4, e informe
    compuesto de punta a punta.
    """
    sesion = sesion_sobre_esquema_real
    _insertar_evento_como_el_modulo_3(
        sesion,
        caso.id,
        evento="Escaneo de puertos desde 203.0.113.45",
        severidad="media",
        fuente_log="nmap",
        usuario_detectado=None,
    )
    _insertar_evento_como_el_modulo_3(
        sesion,
        caso.id,
        hora=datetime(2026, 8, 31, 16, 40, 0),
        evento="Shell de root detectada en bindshell",
        severidad="critica",
    )
    _proyectar_a_timeline_como_el_modulo_4(sesion, caso.id)

    registro_osint = repository.get_registro_osint(sesion, caso.id)
    documento = construir_documento(
        case=caso,
        timeline_events=repository.get_timeline_events(sesion, caso.id),
        narrativa=NARRATIVA_FALSA,
        generado_por="Ana Pérez",
        version=1,
        generado_el=datetime(2026, 9, 2, 10, 0, tzinfo=timezone.utc),
        evidences=repository.get_evidences(sesion, caso.id),
        osint_results=registro_osint.indicadores,
        fuente_osint=registro_osint.fuente,
        tracking_events=repository.get_tracking_events(sesion, caso.id),
    )
    texto = json.dumps(json.loads(construir_json(documento)), ensure_ascii=False)

    assert "Shell de root detectada en bindshell" in texto  # llega al Anexo C
    assert "Tracking: Escaneo de puertos" in texto          # y a la cronología
    assert "critica" in texto and "media" in texto
    assert "nmap" in texto
    # La columna que se retiró del espejo no puede reaparecer por ningún lado.
    assert "detalles" not in texto


def test_los_anexos_a_y_b_quedan_vacios_con_la_proyeccion_actual_del_modulo_4(
    sesion_sobre_esquema_real, caso
):
    """
    Deja fijado por escrito un límite que no es de este módulo: el script del
    Módulo 4 solo lee `tracking_events`, así que ni evidencias ni OSINT llegan
    nunca a la cronología. El informe tiene que salir igualmente y declarar
    esos anexos vacíos, no reventar.

    Si el Módulo 4 amplía su script a las tres fuentes que anuncia su mensaje
    de commit, este test se caerá — y eso será una buena noticia que habrá que
    venir a recoger aquí.
    """
    sesion = sesion_sobre_esquema_real
    _insertar_evento_como_el_modulo_3(sesion, caso.id)
    _proyectar_a_timeline_como_el_modulo_4(sesion, caso.id)

    cronologia = repository.get_timeline_events(sesion, caso.id)
    assert {e.origen_modulo for e in cronologia} == {"tracking"}

    registro_osint = repository.get_registro_osint(sesion, caso.id)
    documento = construir_documento(
        case=caso,
        timeline_events=cronologia,
        narrativa=NARRATIVA_FALSA,
        generado_por="Ana Pérez",
        version=1,
        generado_el=datetime(2026, 9, 2, 10, 0, tzinfo=timezone.utc),
        evidences=repository.get_evidences(sesion, caso.id),
        osint_results=registro_osint.indicadores,
        fuente_osint=registro_osint.fuente,
        tracking_events=repository.get_tracking_events(sesion, caso.id),
    )
    texto = json.dumps(json.loads(construir_json(documento)), ensure_ascii=False)

    assert "No constan evidencias registradas" in texto
    assert "No constan consultas OSINT registradas" in texto
