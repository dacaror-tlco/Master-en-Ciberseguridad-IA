"""
Contrato con el esquema **real** del Módulo 1 (rama `modulo-casos`).

`test_contrato_modulos.py` fija hasta dónde llega la tolerancia del espejo.
Esto comprueba otra cosa: que el Módulo 5 funciona contra el DDL que el Módulo
1 crea de verdad, no contra el espejo que este módulo declara para poder
desarrollarse por separado. Son los tests que, al fusionar, dejan de simular
nada: el espejo desaparece y las tablas las crea su dueño.

La diferencia no es teórica. El espejo y la tabla real ya divergieron una vez
—el Enum `estado`, que SQLAlchemy persistía por nombre (`ABIERTO`) mientras el
Módulo 1 lo escribe por valor (`abierto`)— y con esa divergencia no se podía
generar ningún informe de ningún caso. Coincidir en el nombre de la columna no
basta.

El DDL de abajo está transcrito literalmente de
`modulo-casos/backend/alembic/versions/0001_initial_cases_evidences.py`
(commit `d2fbbea`, 2026-08-10). Si el Módulo 1 lo cambia, hay que traer el
cambio aquí: estos tests dirán entonces si el Módulo 5 sigue pudiendo leerlo,
en vez de descubrirlo el día de la integración.
"""
import json
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    create_engine,
    func,
    insert,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.modules.reports import repository
from app.modules.reports.document import construir_documento
from app.modules.reports.json_builder import construir_json
from app.modules.shared.models import Case, EstadoCaso, TimelineEvent
from tests.conftest import NARRATIVA_FALSA

# --- DDL del Módulo 1, transcrito de su migración 0001 -----------------------

metadata_modulo1 = MetaData()

cases_modulo1 = Table(
    "cases",
    metadata_modulo1,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("nombre", String(150), nullable=False),
    Column(
        "estado",
        Enum("abierto", "en_progreso", "cerrado", "archivado", name="estadocaso"),
        nullable=False,
        server_default="abierto",
    ),
    Column("fecha_creacion", DateTime(), server_default=func.now(), nullable=False),
    Column("descripcion", Text(), nullable=True),
    Column("responsable", String(100), nullable=False),
)

evidences_modulo1 = Table(
    "evidences",
    metadata_modulo1,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column(
        "case_id",
        Integer,
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("tipo", String(50), nullable=False),
    Column("valor", Text(), nullable=False),
    Column("fecha_subida", DateTime(), server_default=func.now(), nullable=False),
    Column("observaciones", Text(), nullable=True),
)


@pytest.fixture
def sesion_sobre_esquema_real():
    """
    Base de datos en la que `cases` y `evidences` las crea el DDL del Módulo 1
    y el resto de tablas las crea este módulo. Es la foto de después de
    fusionar: manda el esquema del dueño de cada tabla.
    """
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    metadata_modulo1.create_all(bind=engine)
    propias = [
        tabla
        for tabla in Base.metadata.sorted_tables
        if tabla.name not in metadata_modulo1.tables
    ]
    Base.metadata.create_all(bind=engine, tables=propias)

    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def _insertar_caso_como_el_modulo_1(sesion, **campos):
    """
    Escribe el caso con el DDL del Módulo 1 y sin pasar por el espejo, que es
    justo lo que ocurrirá en producción: la fila la crea el otro módulo.
    """
    valores = {
        "nombre": "Intrusión en servidor web",
        "estado": "en_progreso",
        "fecha_creacion": datetime(2026, 8, 10, 9, 0),
        "descripcion": "Acceso no autorizado detectado por el SIEM",
        "responsable": "Ana Pérez",
        **campos,
    }
    resultado = sesion.execute(insert(cases_modulo1).values(**valores))
    sesion.commit()
    return resultado.inserted_primary_key[0]


# --- El espejo no puede pedir más de lo que hay ------------------------------


@pytest.mark.parametrize("tabla", ["cases", "evidences"])
def test_el_espejo_no_declara_columnas_que_el_modulo_1_no_tiene(tabla):
    """
    Alarma de deriva. El día que el espejo declare una columna que la tabla
    real no tiene, cualquier SELECT del Módulo 5 falla con «no such column» y
    no se genera ningún informe. Esto lo detecta al ejecutar los tests, no al
    fusionar.
    """
    reales = set(metadata_modulo1.tables[tabla].columns.keys())
    espejo = set(Base.metadata.tables[tabla].columns.keys())

    sobran = espejo - reales
    assert not sobran, (
        f"El espejo de `{tabla}` declara columnas que el Módulo 1 no crea: "
        f"{sorted(sobran)}. O las añade el Módulo 1, o salen del espejo."
    )


# --- Lectura de un caso escrito por el Módulo 1 ------------------------------


def test_un_caso_escrito_por_el_modulo_1_se_lee_entero(sesion_sobre_esquema_real):
    sesion = sesion_sobre_esquema_real
    _insertar_caso_como_el_modulo_1(sesion)

    caso = sesion.query(Case).one()

    assert caso.estado is EstadoCaso.EN_PROGRESO
    assert caso.nombre == "Intrusión en servidor web"
    assert caso.responsable == "Ana Pérez"
    assert caso.descripcion == "Acceso no autorizado detectado por el SIEM"
    assert caso.fecha_creacion == datetime(2026, 8, 10, 9, 0)


@pytest.mark.parametrize(
    "escrito, esperado",
    [
        ("abierto", EstadoCaso.ABIERTO),
        ("en_progreso", EstadoCaso.EN_PROGRESO),
        ("cerrado", EstadoCaso.CERRADO),
        ("archivado", EstadoCaso.ARCHIVADO),
    ],
)
def test_los_cuatro_estados_del_modulo_1_se_leen(
    sesion_sobre_esquema_real, escrito, esperado
):
    """
    Los cuatro valores que el ENUM del Módulo 1 permite. Si mañana añaden un
    quinto, este test seguirá pasando y el de deriva no lo verá: lo que lo
    detecta es que `EstadoCaso._missing_` devuelva None y salte el LookupError
    al leer. Por eso el espejo tolera variantes pero no inventa miembros.
    """
    sesion = sesion_sobre_esquema_real
    _insertar_caso_como_el_modulo_1(sesion, estado=escrito)

    assert sesion.query(Case).one().estado is esperado


def test_el_esquema_activo_es_el_del_modulo_1_y_no_el_espejo(
    sesion_sobre_esquema_real,
):
    """
    Comprobación de que este fichero corre de verdad sobre el DDL del Módulo 1.
    Sin ella, todo lo demás podría estar probando el espejo sin que se notara.

    El discriminante es `responsable`: el Módulo 1 la declara NOT NULL y el
    espejo la deja nullable a propósito (criterio de leer con tolerancia). Esa
    diferencia sí la aplica SQLite.

    No se usa el `estado` para esto aunque sea el candidato obvio: `sa.Enum` en
    SQLAlchemy 2.x trae `create_constraint=False`, así que sobre SQLite no
    emite el CHECK y admitiría cualquier cadena. En MySQL sería una columna
    ENUM nativa y sí rechazaría el valor, pero un test que solo pasa contra
    MySQL no lo ejecuta nadie.
    """
    sesion = sesion_sobre_esquema_real

    with pytest.raises(IntegrityError):
        _insertar_caso_como_el_modulo_1(sesion, responsable=None)


def test_el_espejo_reconoce_todos_los_estados_que_permite_el_modulo_1():
    """
    La alarma de deriva del Enum, que es por donde ya se rompió una vez.

    Si el Módulo 1 añade un quinto estado a su ENUM, aquí salta al ejecutar los
    tests. Si no saltara, el fallo aparecería al leer un caso con ese estado:
    `_missing_` devolvería None, SQLAlchemy lanzaría LookupError y ese caso no
    podría generar ningún informe.
    """
    permitidos = set(cases_modulo1.c.estado.type.enums)
    assert permitidos == {"abierto", "en_progreso", "cerrado", "archivado"}, (
        "Cambió el ENUM transcrito del Módulo 1; revisar que el espejo lo cubra."
    )

    for valor in permitidos:
        assert EstadoCaso(valor).value == valor


# --- El informe completo sobre el esquema real -------------------------------


def test_se_genera_el_informe_entero_sobre_el_esquema_del_modulo_1(
    sesion_sobre_esquema_real,
):
    """
    Prueba de integración de la fusión: caso y evidencias escritos con el DDL
    del Módulo 1, cronología escrita como la entregaría el Módulo 4, y el
    informe compuesto de punta a punta. Es lo más cerca que este módulo puede
    estar de la integración real sin que existan las otras ramas fusionadas.
    """
    sesion = sesion_sobre_esquema_real
    case_id = _insertar_caso_como_el_modulo_1(sesion)

    sesion.execute(
        insert(evidences_modulo1).values(
            case_id=case_id,
            tipo="imagen_disco",
            valor="EV-001 imagen forense del servidor web",
            fecha_subida=datetime(2026, 8, 10, 10, 0),
            observaciones="Adquirida en caliente",
        )
    )

    base = datetime(2026, 8, 10, 11, 0, tzinfo=timezone.utc)
    for i in range(2):
        sesion.add(
            TimelineEvent(
                id=f"tl-{i}",
                case_id=case_id,
                fecha_hora=base + timedelta(hours=i),
                descripcion=f"Evento {i} de la cronología",
                origen_modulo="evidences",
                origen_id=1,
                orden=i,
            )
        )
    sesion.commit()

    caso = sesion.query(Case).one()
    registro_osint = repository.get_registro_osint(sesion, case_id)
    documento = construir_documento(
        case=caso,
        timeline_events=repository.get_timeline_events(sesion, case_id),
        narrativa=NARRATIVA_FALSA,
        generado_por="Ana Pérez",
        version=1,
        generado_el=datetime(2026, 8, 29, 10, 0, tzinfo=timezone.utc),
        evidences=repository.get_evidences(sesion, case_id),
        osint_results=registro_osint.indicadores,
        fuente_osint=registro_osint.fuente,
        tracking_events=repository.get_tracking_events(sesion, case_id),
    )
    contenido = json.loads(construir_json(documento))
    texto = json.dumps(contenido, ensure_ascii=False)

    assert contenido["informe"]["case_nombre"] == "Intrusión en servidor web"
    assert "Ana Pérez" in texto
    assert "EV-001 imagen forense del servidor web" in texto  # llega al Anexo A
    assert "Evento 0 de la cronología" in texto


def test_el_anexo_b_no_rompe_el_informe_aunque_no_haya_osint(
    sesion_sobre_esquema_real,
):
    """
    Al integrar, `osint_results` no la escribe nadie: el Módulo 2 usa 15 tablas
    propias y no proyecta a la tabla de la especificación. El informe tiene que
    salir igualmente, con el anexo declarado vacío, y no reventar.
    """
    sesion = sesion_sobre_esquema_real
    case_id = _insertar_caso_como_el_modulo_1(sesion)
    sesion.add(
        TimelineEvent(
            id="tl-0",
            case_id=case_id,
            fecha_hora=datetime(2026, 8, 10, 11, 0, tzinfo=timezone.utc),
            descripcion="Único evento de la cronología",
            origen_modulo="tracking",
            origen_id=1,
            orden=0,
        )
    )
    sesion.commit()

    caso = sesion.query(Case).one()
    registro_osint = repository.get_registro_osint(sesion, case_id)
    documento = construir_documento(
        case=caso,
        timeline_events=repository.get_timeline_events(sesion, case_id),
        narrativa=NARRATIVA_FALSA,
        generado_por="Ana Pérez",
        version=1,
        generado_el=datetime(2026, 8, 29, 10, 0, tzinfo=timezone.utc),
        evidences=repository.get_evidences(sesion, case_id),
        osint_results=registro_osint.indicadores,
        fuente_osint=registro_osint.fuente,
        tracking_events=repository.get_tracking_events(sesion, case_id),
    )

    contenido = json.loads(construir_json(documento))
    titulos = [s["titulo"] for s in contenido["secciones"]]
    assert any(titulo.startswith("Anexo B") for titulo in titulos)
