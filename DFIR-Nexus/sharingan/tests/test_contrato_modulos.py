"""
Contrato con los módulos que escriben las tablas que este lee.

El Módulo 5 no es dueño de `cases`, `evidences`, `osint_results`,
`tracking_events` ni `timeline_events`: las lee y las imprime. Dos veces ya un
desajuste minúsculo en esas tablas —el `estado` del Módulo 1, la `severidad`
propuesta por el Módulo 3— habría impedido generar *cualquier* informe.

Estos tests fijan hasta dónde llega la tolerancia del espejo, para que nadie la
recorte sin darse cuenta de lo que se lleva por delante.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from sqlalchemy import text

from app.modules.reports import repository
from app.modules.reports.document import construir_documento
from app.modules.reports.json_builder import construir_json
from app.modules.shared.models import (
    EstadoCaso,
    Severidad,
    TimelineEvent,
    TrackingEvent,
)
from tests.conftest import NARRATIVA_FALSA, documento_de_prueba

FIXTURE_MODULO_3 = (
    Path(__file__).resolve().parent.parent / "fixtures" / "caso_005_bindshell_modulo3.json"
)


# --- Tolerancia ortográfica --------------------------------------------------


@pytest.mark.parametrize(
    "escrito, esperado",
    [
        ("crítica", Severidad.CRITICA),   # lo que propone el Módulo 3
        ("critica", Severidad.CRITICA),   # lo que dice el CLAUDE.md
        ("CRÍTICA", Severidad.CRITICA),
        ("  Critica  ", Severidad.CRITICA),
        ("CRITICA", Severidad.CRITICA),   # nombre del miembro
        ("alta", Severidad.ALTA),
    ],
)
def test_la_severidad_se_lee_escriba_quien_la_escriba(escrito, esperado):
    """Una tilde no puede ser la diferencia entre emitir un informe o no."""
    assert Severidad(escrito) is esperado


@pytest.mark.parametrize(
    "escrito", ["abierto", "ABIERTO", "En_Progreso", "  cerrado "]
)
def test_el_estado_del_caso_tambien_es_tolerante(escrito):
    assert isinstance(EstadoCaso(escrito), EstadoCaso)


def test_una_severidad_inventada_sigue_fallando(db_session):
    """Tolerar variantes no es tragar cualquier cosa: eso ocultaría un error."""
    with pytest.raises(ValueError):
        Severidad("gravísima")


def test_se_lee_una_severidad_con_tilde_escrita_directamente_en_la_tabla(
    db_session, case_con_timeline
):
    """
    La comprobación que importa: la fila la escribe el Módulo 3, no el ORM de
    este módulo. Se inserta con SQL crudo para que nadie normalice por el
    camino, igual que en test_shared_models.
    """
    db_session.execute(
        text(
            "INSERT INTO tracking_events (id, case_id, hora, evento, severidad) "
            "VALUES ('evt-tilde', :caso, '2026-08-20 16:20:15', 'Shell de root', 'crítica')"
        ),
        {"caso": case_con_timeline.id},
    )
    db_session.commit()

    eventos = repository.get_tracking_events(db_session, case_con_timeline.id)
    con_tilde = next(e for e in eventos if e.id == "evt-tilde")

    assert con_tilde.severidad is Severidad.CRITICA
    assert con_tilde.severidad.value == "critica"  # se imprime el valor canónico


# --- Identificadores de texto ------------------------------------------------


def test_los_identificadores_de_texto_llegan_hasta_el_informe(db_session, case_con_timeline):
    """
    El Módulo 3 usa `evt-7f3a9c2e` y `obs-9f2a8b1c`. La columna «Ref.» del
    informe existe para que cualquiera vaya de una afirmación a su registro de
    origen, así que el identificador tiene que sobrevivir literal.
    """
    db_session.add(
        TimelineEvent(
            id="tl-99",
            case_id=case_con_timeline.id,
            fecha_hora=datetime(2026, 8, 20, 16, 20, 15, tzinfo=timezone.utc),
            descripcion="Shell de root detectada en bindshell",
            origen_modulo="tracking",
            origen_id="evt-7f3a9c2e",
            orden=99,
        )
    )
    db_session.commit()

    doc = documento_de_prueba(db_session, case_con_timeline)
    contenido = json.loads(construir_json(doc))
    cronologia = next(s for s in contenido["secciones"] if "Cronología" in s["titulo"])
    referencias = [fila[2] for fila in cronologia["tablas"][0]["filas"]]

    assert "tracking#evt-7f3a9c2e" in referencias


def test_un_identificador_entero_sigue_funcionando(db_session, case_con_timeline):
    """Si el equipo acuerda INTEGER, esto tiene que seguir en pie sin tocar nada."""
    eventos = repository.get_timeline_events(db_session, case_con_timeline.id)

    assert all(isinstance(e.origen_id, str) for e in eventos)
    assert [e.origen_id for e in eventos] == ["0", "1", "2"]


# --- El campo `detalles`, retirado -------------------------------------------


def test_el_espejo_no_declara_detalles():
    """
    El Módulo 3 propuso por escrito una columna `detalles` (JSON) y su tabla
    real no la tiene. Declararla aquí no sería tolerancia sino un fallo
    garantizado: `SELECT` la pediría y MySQL respondería «Unknown column», así
    que ningún informe del caso se generaría.

    Es lo contrario del resto de este fichero. Ahí se fija hasta dónde llega la
    permisividad del espejo *sobre los tipos*; aquí se fija que la
    permisividad no llega a inventarse columnas. Un espejo puede aceptar un
    valor raro en una columna que existe; no puede leer una que no existe.
    """
    assert not hasattr(TrackingEvent, "detalles")
    assert "detalles" not in TrackingEvent.__table__.columns


def test_el_anexo_c_no_cita_una_columna_que_no_existe(db_session, case_con_timeline):
    """El anexo citaba el detalle crudo como almacenado. Ya no lo está."""
    db_session.add(
        TrackingEvent(
            id="evt-7f3a9c2e",
            case_id=case_con_timeline.id,
            hora=datetime(2026, 8, 20, 16, 20, 15, tzinfo=timezone.utc),
            evento="Shell de root detectada en bindshell",
            severidad=Severidad("crítica"),
            fuente_log="nc",
            usuario_detectado="root",
        )
    )
    db_session.commit()

    texto = json.dumps(json.loads(construir_json(documento_de_prueba(db_session, case_con_timeline))))
    assert "detalles" not in texto
    assert "bindshell" in texto  # el evento sí aparece


# --- La fixture del Módulo 3, de punta a punta -------------------------------


def test_el_informe_se_genera_con_el_formato_del_modulo_3(db_session):
    """
    Prueba de integración del contrato: se carga el JSON con el formato que
    propuso el Módulo 3 —ids de texto y severidad con tilde— y se compone el
    informe entero. Si algún día alguien endurece el espejo, esto
    se cae antes que la integración.
    """
    from scripts.load_fixtures import construir_objetos

    caso, hijos = construir_objetos(json.loads(FIXTURE_MODULO_3.read_text(encoding="utf-8")))
    db_session.add(caso)
    db_session.flush()
    for filas in hijos.values():
        for fila in filas:
            fila.case_id = caso.id
            db_session.add(fila)
    db_session.commit()

    registro_osint = repository.get_registro_osint(db_session, caso.id)
    doc = construir_documento(
        case=caso,
        timeline_events=repository.get_timeline_events(db_session, caso.id),
        narrativa=NARRATIVA_FALSA,
        generado_por="Ana Pérez",
        version=1,
        generado_el=datetime(2026, 8, 21, 10, 0, tzinfo=timezone.utc),
        evidences=repository.get_evidences(db_session, caso.id),
        osint_results=registro_osint.indicadores,
        fuente_osint=registro_osint.fuente,
        tracking_events=repository.get_tracking_events(db_session, caso.id),
    )
    contenido = json.loads(construir_json(doc))
    texto = json.dumps(contenido)

    assert contenido["informe"]["case_nombre"].startswith("Intrusión por servicio")
    assert "tracking#evt-7f3a9c2e" in texto      # el id de texto llega a la Ref.
    assert "critica" in texto                    # la tilde se normalizó
    assert "nmap" in texto and "access.log" in texto  # nmap y tráfico web


def test_cada_referencia_de_la_cronologia_resuelve_en_los_anexos(db_session):
    """
    La promesa del apartado de metodologia: «cualquier afirmacion de este
    informe puede contrastarse contra el registro concreto del que procede».
    Eso solo es cierto si el `modulo#id` de la columna «Ref.» aparece de verdad
    como fila del anexo correspondiente.

    No es teorico: al pasar a identificadores de texto, el previsualizador
    renumeraba las filas y el Anexo C decia «2» donde la cronologia decia
    «tracking#evt-7f3a9c2e». Dos tablas del mismo informe nombrando distinto el
    mismo registro.
    """
    from scripts.load_fixtures import construir_objetos

    caso, hijos = construir_objetos(json.loads(FIXTURE_MODULO_3.read_text(encoding="utf-8")))
    db_session.add(caso)
    db_session.flush()
    for filas in hijos.values():
        for fila in filas:
            fila.case_id = caso.id
            db_session.add(fila)
    db_session.commit()

    contenido = json.loads(construir_json(documento_de_prueba(db_session, caso)))
    secciones = {s["titulo"]: s for s in contenido["secciones"]}

    ids_por_anexo = {
        "evidences": {f[0] for f in secciones["Anexo A — Inventario de evidencias"]["tablas"][0]["filas"]},
        "osint": {f[0] for f in secciones["Anexo B — Indicadores consultados en fuentes abiertas"]["tablas"][0]["filas"]},
        "tracking": {f[0] for f in secciones["Anexo C — Eventos de análisis post-incidente"]["tablas"][0]["filas"]},
    }

    referencias = [f[2] for f in secciones["5. Cronología de eventos"]["tablas"][0]["filas"]]
    assert referencias, "la cronologia no puede estar vacia"

    for referencia in referencias:
        modulo, _, identificador = referencia.partition("#")
        assert modulo in ids_por_anexo, f"origen_modulo desconocido: {modulo!r}"
        assert identificador in ids_por_anexo[modulo], (
            f"la referencia {referencia!r} no aparece en el anexo de {modulo}"
        )
