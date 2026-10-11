"""
Fase 4 — contrato de integración de Informes en `development`.

Estos tests son nuevos (no existían en origin/sharingan) y verifican
exactamente la matriz pedida en la integración: caso inexistente, caso sin
datos secundarios, caso completo con las cuatro fuentes, aislamiento de
OSINT entre casos (sin heurística), persistencia de los campos
obligatorios de `reports`, versionado sin duplicados e integridad (no se
modifican las tablas ajenas).

A diferencia de `tests/conftest.py::case_con_anexos` (que usa
`OsintResult`, la tabla del modelo de datos oficial que nadie ha creado
en la base real), estos tests usan `OsintFinding` sobre una base en la
que `osint_results` NO existe — es el escenario real de `development`/
Aiven, confirmado en las fases anteriores. Reutiliza el patrón de
`tests/test_anexo_b_fuentes.py::_sesion_con`.
"""
import json
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.modules.reports import repository, service
from app.modules.reports.formats import FormatoInforme
from app.modules.reports.osint import FuenteOsint
from app.modules.shared.models import (
    Case,
    Evidence,
    EstadoCaso,
    OsintFinding,
    Severidad,
    TimelineEvent,
    TrackingEvent,
)
from tests.conftest import NARRATIVA_FALSA


def _sesion_sin_osint_results():
    """Misma base que test_anexo_b_fuentes.py::_sesion_con({"osint_results"})."""
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(
        bind=engine,
        tables=[t for t in Base.metadata.sorted_tables if t.name != "osint_results"],
    )
    return sessionmaker(bind=engine)()


def _crear_caso(sesion, nombre="Caso de Fase 4", **kw):
    caso = Case(
        nombre=nombre,
        estado=EstadoCaso.EN_PROGRESO,
        fecha_creacion=datetime.now(timezone.utc) - timedelta(days=1),
        responsable="Tester",
        **kw,
    )
    sesion.add(caso)
    sesion.flush()
    return caso


def _generar(sesion, case_id, tmp_path, generado_por="Ana Pérez"):
    with patch("app.core.config.settings.reports_storage_dir", str(tmp_path)), \
         patch("app.modules.reports.ai_narrative.generar_narrativa", return_value=NARRATIVA_FALSA):
        return service.generate_report(sesion, case_id, generado_por)


def _json_del_informe(sesion, report, tmp_path) -> str:
    with patch("app.core.config.settings.reports_storage_dir", str(tmp_path)):
        _, ruta = service.get_report_file(sesion, report.id, FormatoInforme.JSON)
    return ruta.read_text(encoding="utf-8")


# --- 1. Caso inexistente ---------------------------------------------------


def test_case_id_inexistente_produce_error_controlado_no_500(tmp_path):
    sesion = _sesion_sin_osint_results()

    with pytest.raises(service.CaseNotFoundError):
        _generar(sesion, case_id=99999, tmp_path=tmp_path)

    sesion.close()


def test_case_id_inexistente_via_api_da_404_no_500():
    """A nivel HTTP: CaseNotFoundError se traduce a 404 en routes.py."""
    from fastapi.testclient import TestClient
    from app.core.database import get_db
    from app.main import app
    from tests.conftest import _bearer_token

    sesion = _sesion_sin_osint_results()

    def _override_get_db():
        yield sesion

    app.dependency_overrides[get_db] = _override_get_db
    try:
        with TestClient(app) as client:
            # Fase 4: este backend exige autenticación (ver conftest.client);
            # este test monta su propio TestClient (necesita una sesión de
            # BD distinta de la del fixture) así que adjunta el JWT él mismo.
            client.headers["Authorization"] = f"Bearer {_bearer_token()}"
            r = client.post(
                "/reports/generate",
                json={"case_id": 99999, "generado_por": "Tester"},
            )
        assert r.status_code == 404
        assert r.status_code != 500
    finally:
        app.dependency_overrides.clear()
        sesion.close()


# --- 2. Caso existente sin datos secundarios -------------------------------


def test_caso_sin_evidencias_osint_ni_tracking_genera_informe_con_anexos_vacios(tmp_path):
    """
    Nota de diseño (verificada, no asumida): generate_report SÍ exige que el
    caso tenga al menos un timeline_event (EmptyTimelineError si no —
    comportamiento intencional y ya probado en
    test_reports_service.py::test_generate_report_sin_eventos, con su propio
    fixture caso_002_sin_eventos.json documentando el 422). Timeline es la
    columna vertebral del documento, así que esto no es un dato "secundario"
    en el mismo sentido que evidencias/OSINT/tracking.

    Este test cubre exactamente lo pedido: evidences, osint_findings y
    tracking_events vacíos para un caso que sí tiene cronología (mínimo
    indispensable) — y confirma que el informe se genera igualmente, con
    esos tres anexos vacíos y no como error.
    """
    sesion = _sesion_sin_osint_results()
    caso = _crear_caso(sesion)
    sesion.add(
        TimelineEvent(
            id=1, case_id=caso.id,
            fecha_hora=datetime.now(timezone.utc),
            descripcion="Único evento de cronología del caso",
            origen_modulo="tracking", origen_id=1, orden=1,
        )
    )
    sesion.commit()

    assert repository.get_evidences(sesion, caso.id) == []
    assert repository.get_registro_osint(sesion, caso.id).indicadores == []
    assert repository.get_tracking_events(sesion, caso.id) == []

    report = _generar(sesion, caso.id, tmp_path)

    assert report.case_id == caso.id
    assert report.version == 1
    sesion.close()


# --- 3. Caso completo con las cuatro fuentes -------------------------------


def test_caso_completo_incluye_datos_de_las_cuatro_fuentes(tmp_path):
    sesion = _sesion_sin_osint_results()
    caso = _crear_caso(sesion, nombre="Caso multi-fuente Fase 4")

    sesion.add(Evidence(
        case_id=caso.id, tipo="disco", valor="EV-IMG-0001-imagen-forense",
        fecha_subida=datetime.now(timezone.utc),
    ))
    sesion.add(OsintFinding(
        case_id=caso.id, case_type="domain", source_table="osint_domain_cases",
        source_id=5, subject_type="domain", subject_value="dominio-fase4.example",
        risk_score=80, risk_level="high", headline="Dominio con riesgo alto",
        flag_count=3, analyzed_at=datetime.now(timezone.utc),
    ))
    sesion.add(TrackingEvent(
        id="evt-fase4-1", case_id=caso.id, hora=datetime.now(timezone.utc),
        evento="powershell -EncodedCommand FASE4TRACKING", severidad=Severidad.CRITICA,
    ))
    sesion.add(TimelineEvent(
        id=1, case_id=caso.id, fecha_hora=datetime.now(timezone.utc),
        descripcion="Evento de cronología del caso multi-fuente",
        origen_modulo="tracking", origen_id=1, orden=1,
    ))
    sesion.commit()

    report = _generar(sesion, caso.id, tmp_path)
    contenido = _json_del_informe(sesion, report, tmp_path)

    assert "EV-IMG-0001-imagen-forense" in contenido
    assert "dominio-fase4.example" in contenido
    assert "FASE4TRACKING" in contenido
    sesion.close()


# --- 4. OSINT de otro caso no se filtra por error --------------------------


def test_osint_findings_de_otro_caso_nunca_aparecen_en_el_informe(tmp_path):
    sesion = _sesion_sin_osint_results()
    caso_1 = _crear_caso(sesion, nombre="Caso 1")
    caso_2 = _crear_caso(sesion, nombre="Caso 2")

    sesion.add(TimelineEvent(
        id=1, case_id=caso_1.id, fecha_hora=datetime.now(timezone.utc),
        descripcion="Evento del caso 1", origen_modulo="tracking", origen_id=1, orden=1,
    ))
    sesion.add(OsintFinding(
        case_id=caso_1.id, case_type="domain", source_table="osint_domain_cases",
        source_id=1, subject_type="domain", subject_value="del-caso-uno.example",
        risk_score=50, risk_level="medium", headline="Hallazgo del caso 1",
        flag_count=1, analyzed_at=datetime.now(timezone.utc),
    ))
    sesion.add(OsintFinding(
        case_id=caso_2.id, case_type="domain", source_table="osint_domain_cases",
        source_id=2, subject_type="domain", subject_value="del-caso-dos.example",
        risk_score=90, risk_level="high", headline="Hallazgo del caso 2",
        flag_count=5, analyzed_at=datetime.now(timezone.utc),
    ))
    sesion.commit()

    registro = repository.get_registro_osint(sesion, caso_1.id)
    assert registro.fuente is FuenteOsint.FINDINGS
    assert [i.valor for i in registro.indicadores] == ["del-caso-uno.example"]

    report = _generar(sesion, caso_1.id, tmp_path)
    contenido = _json_del_informe(sesion, report, tmp_path)

    assert "del-caso-uno.example" in contenido
    assert "del-caso-dos.example" not in contenido
    assert "Hallazgo del caso 2" not in contenido
    sesion.close()


# --- 5. Persistencia --------------------------------------------------------


def test_persistencia_de_los_campos_obligatorios_de_reports(tmp_path):
    sesion = _sesion_sin_osint_results()
    caso = _crear_caso(sesion)
    sesion.add(TimelineEvent(
        id=1, case_id=caso.id, fecha_hora=datetime.now(timezone.utc),
        descripcion="Evento", origen_modulo="tracking", origen_id=1, orden=1,
    ))
    sesion.commit()

    report = _generar(sesion, caso.id, tmp_path, generado_por="Perito de Prueba")

    assert report.case_id == caso.id
    assert report.version == 1
    assert report.fecha_generacion is not None
    assert report.archivo_pdf  # ruta no vacía
    assert report.generado_por == "Perito de Prueba"

    # Releído de la base, no del objeto en memoria de la propia inserción.
    releido = repository.get_report(sesion, report.id)
    assert releido is not None
    assert releido.case_id == caso.id
    assert releido.version == 1
    assert releido.archivo_pdf == report.archivo_pdf
    sesion.close()


# --- 6. Versionado -----------------------------------------------------------


def test_dos_informes_del_mismo_caso_no_violan_unique_case_version(tmp_path):
    sesion = _sesion_sin_osint_results()
    caso = _crear_caso(sesion)
    sesion.add(TimelineEvent(
        id=1, case_id=caso.id, fecha_hora=datetime.now(timezone.utc),
        descripcion="Evento", origen_modulo="tracking", origen_id=1, orden=1,
    ))
    sesion.commit()

    r1 = _generar(sesion, caso.id, tmp_path)
    r2 = _generar(sesion, caso.id, tmp_path)

    assert r1.version == 1
    assert r2.version == 2
    assert r1.id != r2.id

    todos = repository.list_reports_for_case(sesion, caso.id)
    versiones = [r.version for r in todos]
    assert versiones == sorted(versiones)
    assert len(versiones) == len(set(versiones))  # sin duplicados
    sesion.close()


def test_la_base_de_datos_rechaza_una_version_duplicada_aunque_la_app_no_lo_impidiera(tmp_path):
    """
    No basta con que el código calcule bien la siguiente versión: la
    restricción UNIQUE(case_id, version) tiene que existir también a nivel
    de base de datos, como red de seguridad ante condiciones de carrera
    (ver repository.reservar_report). Se comprueba insertando directamente,
    sin pasar por next_version().
    """
    sesion = _sesion_sin_osint_results()
    caso = _crear_caso(sesion)
    sesion.commit()

    repository.reservar_report(
        sesion, case_id=caso.id, resumen_ia="x", archivo_pdf="a.pdf",
        generado_por="t", version=1, fecha_generacion=datetime.now(timezone.utc),
    )
    sesion.commit()

    from sqlalchemy.exc import IntegrityError

    with pytest.raises(IntegrityError):
        repository.reservar_report(
            sesion, case_id=caso.id, resumen_ia="y", archivo_pdf="b.pdf",
            generado_por="t", version=1, fecha_generacion=datetime.now(timezone.utc),
        )
        sesion.commit()
    sesion.rollback()
    sesion.close()


# --- 7. Integridad: no se modifican tablas ajenas ---------------------------


def test_generar_informe_no_modifica_las_tablas_de_otros_modulos(tmp_path):
    sesion = _sesion_sin_osint_results()
    caso = _crear_caso(sesion)
    sesion.add(Evidence(
        case_id=caso.id, tipo="disco", valor="EV-INTEGRIDAD",
        fecha_subida=datetime.now(timezone.utc),
    ))
    sesion.add(OsintFinding(
        case_id=caso.id, case_type="domain", source_table="osint_domain_cases",
        source_id=1, subject_type="domain", subject_value="integridad.example",
        risk_score=10, risk_level="low", headline="x", flag_count=0,
        analyzed_at=datetime.now(timezone.utc),
    ))
    sesion.add(TrackingEvent(
        id="evt-integridad", case_id=caso.id, hora=datetime.now(timezone.utc),
        evento="evento de integridad", severidad=Severidad.BAJA,
    ))
    sesion.add(TimelineEvent(
        id=1, case_id=caso.id, fecha_hora=datetime.now(timezone.utc),
        descripcion="Evento", origen_modulo="tracking", origen_id=1, orden=1,
    ))
    sesion.commit()

    def _snapshot():
        # SQL crudo, no `select(Modelo)`: un `select` sobre una entidad ORM
        # devuelve objetos ya cacheados en el identity map de la sesión, así
        # que comparar dos "snapshots" así compararía el mismo objeto en
        # memoria consigo mismo y el test pasaría aunque hubiera mutación
        # real. Con SQL crudo se comparan los valores tal y como quedaron
        # físicamente en la base.
        sesion.expire_all()
        return (
            [tuple(r) for r in sesion.execute(text("SELECT * FROM cases ORDER BY id"))],
            [tuple(r) for r in sesion.execute(text("SELECT * FROM evidences ORDER BY id"))],
            [tuple(r) for r in sesion.execute(text("SELECT * FROM osint_findings ORDER BY id"))],
            [tuple(r) for r in sesion.execute(text("SELECT * FROM tracking_events ORDER BY id"))],
            [tuple(r) for r in sesion.execute(text("SELECT * FROM timeline_events ORDER BY id"))],
        )

    antes = _snapshot()
    _generar(sesion, caso.id, tmp_path)
    despues = _snapshot()

    assert antes == despues
    sesion.close()
