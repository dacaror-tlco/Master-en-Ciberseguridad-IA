"""
Opciones de emisión: qué anexos entran, qué franja se documenta y en qué
formatos se emite (ver app/modules/reports/opciones.py).

Lo que estos tests vigilan, por orden de importancia:

1. Que las opciones por defecto emitan **exactamente** el informe de antes.
   La personalización no debía cambiar lo que ya se emitía.
2. Que la columna «Ref.» siga resolviendo con cualquier recorte. Es la
   promesa del apartado de metodología, y un filtro es justo lo que puede
   dejar una referencia apuntando a una fila que el informe no imprime.
3. Que lo que se deja fuera se declare en el documento. Un informe recortado
   en silencio engaña sobre su propio alcance.
"""
import json
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

from app.modules.reports import document, repository, service
from app.modules.reports.json_builder import construir_json
from app.modules.reports.opciones import (
    Anexo,
    FormatoInforme,
    OpcionesInforme,
)
from app.modules.shared.models import (
    Case,
    EstadoCaso,
    Evidence,
    OsintResult,
    Severidad,
    TimelineEvent,
    TrackingEvent,
)
from tests.conftest import EMISION_FALSA, NARRATIVA_FALSA, documento_de_prueba

DIA_1 = datetime(2026, 8, 3, 10, 0)
DIA_2 = datetime(2026, 8, 10, 10, 0)


@pytest.fixture
def caso_trazable(db_session):
    """
    Un caso donde **cada** entrada de la cronología apunta a una fila real de
    un anexo, que es la única forma de poder comprobar el invariante de la
    columna «Ref.» cuando se aplican filtros.

    Reparto deliberado: los hechos del día 1 se apoyan en evidencia y OSINT;
    los del día 2, en tracking, uno grave y otro leve. Así una franja temporal,
    una severidad mínima y la exclusión de un anexo recortan cosas distintas.
    """
    caso = Case(
        nombre="Caso trazable",
        estado=EstadoCaso.EN_PROGRESO,
        fecha_creacion=DIA_1 - timedelta(days=1),
        descripcion="Caso con cronología respaldada por los tres anexos",
        responsable="Tester",
    )
    db_session.add(caso)
    db_session.flush()

    evidencia = Evidence(
        case_id=caso.id,
        tipo="correo",
        valor="mensaje.eml",
        fecha_subida=DIA_1,
        observaciones=None,
    )
    osint_malo = OsintResult(
        case_id=caso.id,
        tipo_indicador="dominio",
        valor="malo.example",
        reputacion="maliciosa",
        pais="NL",
        detecciones=12,
        fuente="VirusTotal",
        fecha_consulta=DIA_1,
    )
    osint_limpio = OsintResult(
        case_id=caso.id,
        tipo_indicador="dominio",
        valor="limpio.example",
        reputacion="no consta",
        pais="ES",
        detecciones=0,
        fuente="VirusTotal",
        fecha_consulta=DIA_1,
    )
    tracking_grave = TrackingEvent(
        id="evt-grave",
        case_id=caso.id,
        hora=DIA_2,
        evento="Shell con privilegios de root",
        severidad=Severidad.CRITICA,
        fuente_log="syslog",
        usuario_detectado="root",
    )
    tracking_leve = TrackingEvent(
        id="evt-leve",
        case_id=caso.id,
        hora=DIA_2 + timedelta(hours=1),
        evento="Inicio de sesión fuera de horario",
        severidad=Severidad.BAJA,
        fuente_log="auth.log",
        usuario_detectado="jlopez",
    )
    for fila in (evidencia, osint_malo, osint_limpio, tracking_grave, tracking_leve):
        db_session.add(fila)
    db_session.flush()

    referencias = [
        ("tl-1", DIA_1, Anexo.EVIDENCIAS, evidencia.id),
        ("tl-2", DIA_1 + timedelta(hours=1), Anexo.OSINT, osint_malo.id),
        ("tl-3", DIA_1 + timedelta(hours=2), Anexo.OSINT, osint_limpio.id),
        ("tl-4", DIA_2, Anexo.TRACKING, tracking_grave.id),
        ("tl-5", DIA_2 + timedelta(hours=1), Anexo.TRACKING, tracking_leve.id),
    ]
    for orden, (tl_id, momento, anexo, origen_id) in enumerate(referencias, start=1):
        db_session.add(
            TimelineEvent(
                id=tl_id,
                case_id=caso.id,
                fecha_hora=momento,
                descripcion=f"Hecho {orden}",
                origen_modulo=anexo.value,
                origen_id=origen_id,
                orden=orden,
            )
        )
    db_session.commit()
    db_session.refresh(caso)
    return caso


def _emitir(db_session, caso, opciones=None):
    """
    Compone el documento como lo compone el servicio —recortando primero, y
    pasando al documento solo lo que sobrevive— y lo devuelve en JSON, que es
    el formato inspeccionable.

    No usa `documento_de_prueba` de conftest porque aquella relee los anexos
    enteros de la base de datos, que es justo lo que aquí hay que recortar.
    """
    opciones = opciones or OpcionesInforme()
    seleccion = opciones.aplicar(
        _timeline(db_session, caso),
        _filas(db_session, caso, Evidence),
        _filas(db_session, caso, OsintResult),
        _filas(db_session, caso, TrackingEvent),
    )
    doc = document.construir_documento(
        case=caso,
        timeline_events=seleccion.timeline_events,
        narrativa=NARRATIVA_FALSA,
        generado_por="Ana Pérez",
        version=1,
        generado_el=EMISION_FALSA,
        evidences=seleccion.evidences,
        osint_results=seleccion.osint_results,
        tracking_events=seleccion.tracking_events,
        opciones=opciones,
    )
    return json.loads(construir_json(doc))


def _timeline(db_session, caso):
    return repository.get_timeline_events(db_session, caso.id)


def _filas(db_session, caso, modelo):
    return list(db_session.query(modelo).filter(modelo.case_id == caso.id))


def _secciones(contenido):
    return {s["titulo"]: s for s in contenido["secciones"]}


def _refs(contenido):
    """Los `modulo#id` de la columna «Ref.» de la cronología."""
    cronologia = _secciones(contenido)["5. Cronología de eventos"]
    return [fila[2] for fila in cronologia["tablas"][0]["filas"]]


def _ids_de_anexo(contenido, titulo):
    seccion = _secciones(contenido).get(titulo)
    if seccion is None or not seccion["tablas"]:
        return set()
    return {fila[0] for fila in seccion["tablas"][0]["filas"]}


# --------------------------------------------------------------------------
# 1. Por defecto no cambia nada
# --------------------------------------------------------------------------


def test_sin_opciones_emite_el_mismo_documento_que_antes(db_session, caso_trazable):
    """
    El informe por defecto tiene que ser idéntico al de antes de que existieran
    las opciones. Se compara el documento entero, no un par de campos: es la
    única forma de que un cambio en la declaración de alcance o en el orden de
    los anexos no se cuele sin que nadie se entere.
    """
    sin_opciones = json.loads(construir_json(documento_de_prueba(db_session, caso_trazable)))
    con_defecto = json.loads(
        construir_json(documento_de_prueba(db_session, caso_trazable, opciones=OpcionesInforme()))
    )
    assert sin_opciones == con_defecto


def test_por_defecto_no_declara_alcance_recortado(db_session, caso_trazable):
    contenido = json.loads(construir_json(documento_de_prueba(db_session, caso_trazable)))
    apartado_1 = _secciones(contenido)["1. Objeto y alcance"]
    assert not any("Alcance de esta emisión" in p for p in apartado_1["parrafos"])


def test_opciones_por_defecto_no_recortan_nada(caso_trazable, db_session):
    seleccion = OpcionesInforme().aplicar(
        _timeline(db_session, caso_trazable),
        _filas(db_session, caso_trazable, Evidence),
        _filas(db_session, caso_trazable, OsintResult),
        _filas(db_session, caso_trazable, TrackingEvent),
    )
    assert len(seleccion.timeline_events) == 5
    assert len(seleccion.evidences) == 1
    assert len(seleccion.osint_results) == 2
    assert len(seleccion.tracking_events) == 2


# --------------------------------------------------------------------------
# 2. El invariante de la columna «Ref.»
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "opciones",
    [
        OpcionesInforme(anexos=frozenset({Anexo.EVIDENCIAS})),
        OpcionesInforme(anexos=frozenset({Anexo.TRACKING})),
        OpcionesInforme(anexos=frozenset({Anexo.EVIDENCIAS, Anexo.OSINT})),
        OpcionesInforme(desde=DIA_2),
        OpcionesInforme(hasta=DIA_1 + timedelta(hours=1)),
        OpcionesInforme(severidad_minima=Severidad.ALTA),
        OpcionesInforme(solo_osint_con_detecciones=True),
        OpcionesInforme(
            anexos=frozenset({Anexo.OSINT, Anexo.TRACKING}),
            desde=DIA_1,
            severidad_minima=Severidad.MEDIA,
            solo_osint_con_detecciones=True,
        ),
    ],
)
def test_cada_referencia_sigue_resolviendo_con_cualquier_recorte(
    db_session, caso_trazable, opciones
):
    """
    La promesa del informe —«cualquier afirmación puede contrastarse contra el
    registro del que procede»— no puede depender de qué opciones se elijan.
    Si un filtro deja en la cronología una entrada que apunta a una fila que el
    informe no imprime, el informe miente sobre sí mismo.
    """
    contenido = _emitir(db_session, caso_trazable, opciones)
    ids_por_modulo = {
        Anexo.EVIDENCIAS.value: _ids_de_anexo(
            contenido, "Anexo A — Inventario de evidencias"
        ),
        Anexo.OSINT.value: _ids_de_anexo(
            contenido, "Anexo B — Indicadores consultados en fuentes abiertas"
        ),
        Anexo.TRACKING.value: _ids_de_anexo(
            contenido, "Anexo C — Eventos de análisis post-incidente"
        ),
    }
    for referencia in _refs(contenido):
        modulo, _, origen_id = referencia.partition("#")
        assert origen_id in ids_por_modulo[modulo], (
            f"La cronología cita {referencia} pero ese registro no aparece en su anexo"
        )


def test_excluir_un_anexo_se_lleva_las_entradas_que_se_apoyaban_en_el(
    db_session, caso_trazable
):
    contenido = _emitir(
        db_session,
        caso_trazable,
        OpcionesInforme(anexos=frozenset({Anexo.EVIDENCIAS, Anexo.TRACKING})),
    )
    assert not any(r.startswith("osint#") for r in _refs(contenido))
    # Y los demás hechos siguen ahí: excluir un anexo no vacía el informe.
    assert any(r.startswith("evidences#") for r in _refs(contenido))
    assert any(r.startswith("tracking#") for r in _refs(contenido))


def test_el_anexo_excluido_no_deja_rastro(db_session, caso_trazable):
    """
    Ni título ni «no constan registros»: decir «no constan» de algo que sí
    consta y no se ha impreso sería falso.
    """
    contenido = _emitir(
        db_session, caso_trazable, OpcionesInforme(anexos=frozenset({Anexo.EVIDENCIAS}))
    )
    titulos = set(_secciones(contenido))
    assert "Anexo A — Inventario de evidencias" in titulos
    assert "Anexo B — Indicadores consultados en fuentes abiertas" not in titulos
    assert "Anexo C — Eventos de análisis post-incidente" not in titulos
    volcado = json.dumps(contenido, ensure_ascii=False)
    assert "No constan consultas OSINT" not in volcado


# --------------------------------------------------------------------------
# 3. Los filtros recortan lo que dicen recortar
# --------------------------------------------------------------------------


def test_franja_temporal_recorta_la_cronologia(db_session, caso_trazable):
    contenido = _emitir(db_session, caso_trazable, OpcionesInforme(desde=DIA_2))
    assert _refs(contenido) == ["tracking#evt-grave", "tracking#evt-leve"]


def test_severidad_minima_descarta_los_eventos_leves(db_session, caso_trazable):
    contenido = _emitir(
        db_session, caso_trazable, OpcionesInforme(severidad_minima=Severidad.ALTA)
    )
    assert "tracking#evt-grave" in _refs(contenido)
    assert "tracking#evt-leve" not in _refs(contenido)
    assert _ids_de_anexo(contenido, "Anexo C — Eventos de análisis post-incidente") == {
        "evt-grave"
    }


def test_solo_osint_con_detecciones(db_session, caso_trazable):
    contenido = _emitir(
        db_session, caso_trazable, OpcionesInforme(solo_osint_con_detecciones=True)
    )
    ids = _ids_de_anexo(contenido, "Anexo B — Indicadores consultados en fuentes abiertas")
    assert len(ids) == 1  # El de 0 detecciones se ha quedado fuera.


def test_una_referencia_colgante_se_conserva(db_session, caso_trazable):
    """
    Un `origen_id` que no corresponde a ninguna fila del caso es un dato
    inconsistente de otro módulo, y ya salía así antes. Recortar es cosa de
    las opciones elegidas, no la ocasión de empezar a descartar datos ajenos.
    """
    db_session.add(
        TimelineEvent(
            id="tl-colgante",
            case_id=caso_trazable.id,
            fecha_hora=DIA_2 + timedelta(hours=2),
            descripcion="Apunta a un tracking que no existe",
            origen_modulo="tracking",
            origen_id="evt-fantasma",
            orden=6,
        )
    )
    db_session.commit()

    contenido = _emitir(
        db_session, caso_trazable, OpcionesInforme(severidad_minima=Severidad.ALTA)
    )
    assert "tracking#evt-fantasma" in _refs(contenido)


# --------------------------------------------------------------------------
# 4. El informe declara lo que deja fuera
# --------------------------------------------------------------------------


def test_el_informe_declara_su_alcance_recortado(db_session, caso_trazable):
    contenido = _emitir(
        db_session,
        caso_trazable,
        OpcionesInforme(
            anexos=frozenset({Anexo.EVIDENCIAS, Anexo.TRACKING}),
            desde=DIA_1,
            hasta=DIA_2,
            severidad_minima=Severidad.ALTA,
        ),
    )
    parrafos = " ".join(_secciones(contenido)["1. Objeto y alcance"]["parrafos"])
    assert "Alcance de esta emisión" in parrafos
    assert "2026-08-03" in parrafos and "2026-08-10" in parrafos
    assert "severidad alta o superior" in parrafos
    # Nombra el anexo excluido con el mismo título con el que aparecería.
    assert "Anexo B — Indicadores consultados en fuentes abiertas" in parrafos


def test_elegir_formatos_no_declara_alcance_recortado(db_session, caso_trazable):
    """Emitir en menos soportes no cambia lo que el informe dice."""
    solo_pdf = OpcionesInforme(formatos=frozenset({FormatoInforme.PDF}))
    assert not solo_pdf.hay_recorte
    contenido = _emitir(db_session, caso_trazable, solo_pdf)
    parrafos = " ".join(_secciones(contenido)["1. Objeto y alcance"]["parrafos"])
    assert "Alcance de esta emisión" not in parrafos


# --------------------------------------------------------------------------
# 5. Alcances imposibles
# --------------------------------------------------------------------------


def test_no_se_puede_emitir_sin_ningun_anexo():
    with pytest.raises(ValueError, match="al menos un anexo"):
        OpcionesInforme(anexos=frozenset())


def test_no_se_puede_excluir_el_pdf():
    with pytest.raises(ValueError, match="PDF no se puede excluir"):
        OpcionesInforme(formatos=frozenset({FormatoInforme.HTML}))


def test_franja_invertida():
    with pytest.raises(ValueError, match="invertida"):
        OpcionesInforme(desde=DIA_2, hasta=DIA_1)


# --------------------------------------------------------------------------
# 6. El servicio: formatos emitidos, registro y cronología vacía
# --------------------------------------------------------------------------


def test_solo_se_emiten_los_formatos_elegidos(db_session, caso_trazable, storage_dir):
    opciones = OpcionesInforme(
        formatos=frozenset({FormatoInforme.PDF, FormatoInforme.DOCX})
    )
    with patch(
        "app.modules.reports.ai_narrative.generar_narrativa", return_value=NARRATIVA_FALSA
    ):
        report = service.generate_report(
            db_session,
            case_id=caso_trazable.id,
            generado_por="Tester",
            opciones=opciones,
        )

    # La narrativa de los tests no lleva prompt, así que no se archiva
    # transcripción: lo que queda en el almacén son exactamente los formatos
    # elegidos, sin el .prompt.txt que sí acompaña a una emisión real.
    emitidos = {p.suffix for p in (storage_dir / f"case_{caso_trazable.id}").iterdir()}
    assert emitidos == {".pdf", ".docx"}
    # Y la huella solo cubre lo que existe: no se firma lo que no se ha emitido.
    assert set(report.huellas) == {"pdf", "docx"}


def test_pedir_un_formato_no_emitido_dice_que_no_se_pidio(
    db_session, caso_trazable, storage_dir
):
    with patch(
        "app.modules.reports.ai_narrative.generar_narrativa", return_value=NARRATIVA_FALSA
    ):
        report = service.generate_report(
            db_session,
            case_id=caso_trazable.id,
            generado_por="Tester",
            opciones=OpcionesInforme(formatos=frozenset({FormatoInforme.PDF})),
        )

    with pytest.raises(service.ReportFileMissingError, match="No se pidió al emitirlo"):
        service.get_report_file(db_session, report.id, FormatoInforme.HTML)


def test_el_registro_guarda_las_opciones(db_session, caso_trazable, storage_dir):
    """
    Sin esto, dos informes del mismo caso pueden decir cosas distintas y nada
    explica por qué.
    """
    opciones = OpcionesInforme(
        anexos=frozenset({Anexo.TRACKING}),
        severidad_minima=Severidad.ALTA,
        desde=DIA_2,
    )
    with patch(
        "app.modules.reports.ai_narrative.generar_narrativa", return_value=NARRATIVA_FALSA
    ):
        report = service.generate_report(
            db_session,
            case_id=caso_trazable.id,
            generado_por="Tester",
            opciones=opciones,
        )

    assert report.opciones["anexos"] == ["tracking"]
    assert report.opciones["severidad_minima"] == "alta"
    assert report.opciones["desde"].startswith("2026-08-10")
    assert report.opciones["formatos"] == ["docx", "html", "json", "pdf"]


def test_un_alcance_que_deja_la_cronologia_vacia_no_llega_a_la_ia(
    db_session, caso_trazable, storage_dir
):
    """
    Y se distingue de un caso sin cronología: aquí el arreglo está en la
    petición, y además no se gasta una llamada a la IA para descubrirlo.
    """
    with patch(
        "app.modules.reports.ai_narrative.generar_narrativa"
    ) as generar:
        with pytest.raises(service.EmptySelectionError, match="Amplía la franja"):
            service.generate_report(
                db_session,
                case_id=caso_trazable.id,
                generado_por="Tester",
                opciones=OpcionesInforme(desde=DIA_2 + timedelta(days=365)),
            )
    generar.assert_not_called()


def test_la_ia_solo_ve_los_eventos_que_van_a_salir_impresos(
    db_session, caso_trazable, storage_dir
):
    """
    El prompt numera los eventos [E1], [E2]… y valida que la narrativa no cite
    ninguno inexistente. Si el modelo redactase sobre la cronología entera y el
    documento imprimiese una recortada, esa comprobación daría por buenas
    referencias que el informe no puede respaldar.
    """
    with patch(
        "app.modules.reports.ai_narrative.generar_narrativa", return_value=NARRATIVA_FALSA
    ) as generar:
        service.generate_report(
            db_session,
            case_id=caso_trazable.id,
            generado_por="Tester",
            opciones=OpcionesInforme(desde=DIA_2),
        )

    eventos_vistos = generar.call_args.args[1]
    assert [e.id for e in eventos_vistos] == ["tl-4", "tl-5"]


# --------------------------------------------------------------------------
# 7. Por la API
# --------------------------------------------------------------------------


def test_api_rechaza_un_alcance_imposible(client, caso_trazable):
    respuesta = client.post(
        "/reports/generate",
        json={
            "case_id": caso_trazable.id,
            "generado_por": "Tester",
            "opciones": {"formatos": ["html"]},
        },
    )
    assert respuesta.status_code == 422
    assert "PDF" in json.dumps(respuesta.json(), ensure_ascii=False)


def test_api_acepta_las_opciones(client, db_session, caso_trazable, storage_dir):
    with patch(
        "app.modules.reports.ai_narrative.generar_narrativa", return_value=NARRATIVA_FALSA
    ):
        respuesta = client.post(
            "/reports/generate",
            json={
                "case_id": caso_trazable.id,
                "generado_por": "Tester",
                "opciones": {
                    "anexos": ["tracking"],
                    "formatos": ["pdf", "json"],
                    "desde": "2026-08-10T00:00:00",
                    "severidad_minima": "critica",
                },
            },
        )

    assert respuesta.status_code == 200, respuesta.text
    cuerpo = respuesta.json()
    assert cuerpo["opciones"]["anexos"] == ["tracking"]
    assert cuerpo["opciones"]["formatos"] == ["json", "pdf"]
    assert set(cuerpo["huellas"]) == {"pdf", "json"}


def test_api_dice_que_las_opciones_dejan_la_cronologia_vacia(
    client, caso_trazable, storage_dir
):
    respuesta = client.post(
        "/reports/generate",
        json={
            "case_id": caso_trazable.id,
            "generado_por": "Tester",
            "opciones": {"desde": "2030-01-01T00:00:00"},
        },
    )
    assert respuesta.status_code == 422
    assert "no dejan ningún evento" in respuesta.json()["detail"]
