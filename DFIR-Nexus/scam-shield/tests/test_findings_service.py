"""
Tests unitarios del modelo de lectura `osint_findings` (app/modules/osint/findings/).
Llaman a `record_finding` / `list_findings` directamente con una Session real
sobre la base en memoria (fixture `db`, ver conftest.py).
"""
from datetime import datetime, timedelta, timezone

from app.modules.osint.findings import service as findings_service
from app.modules.osint.findings.subjects import REGISTRY, build_headline
from app.modules.osint.ip.models import IpCase


def _ip_case(db, ip="1.2.3.4", score=0, flags=None, case_id=None):
    case = IpCase(
        ip=ip,
        risk_score=score,
        case_id=case_id,
        abuseipdb=None,
        risk_flags=flags or [],
        errors=[],
        analyzed_at=datetime.now(timezone.utc),
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


def test_record_finding_proyecta_los_campos_normalizados(db):
    case = _ip_case(db, ip="9.9.9.9", score=72, case_id=None)

    finding = findings_service.record_finding(db, "ip", case)

    assert finding is not None
    assert finding.case_type == "ip"
    assert finding.source_table == "ip_cases"
    assert finding.source_id == case.id
    assert finding.subject_type == "ip_address"
    assert finding.subject_value == "9.9.9.9"
    assert finding.risk_score == 72
    assert finding.risk_level == "high"  # >= 60
    assert "9.9.9.9" in finding.headline
    assert finding.analyzed_at is not None
    assert finding.details["ip"] == "9.9.9.9"  # payload completo del caso


def test_record_finding_niveles_segun_los_cortes_compartidos(db):
    for score, expected in [(0, "low"), (29, "low"), (30, "medium"), (59, "medium"), (60, "high"), (100, "high")]:
        case = _ip_case(db, ip=f"10.0.0.{score}", score=score)
        finding = findings_service.record_finding(db, "ip", case)
        assert finding.risk_level == expected


def test_record_finding_recorta_y_ordena_las_flags(db):
    flags = [
        {"code": "A", "severity": "low", "description": "a"},
        {"code": "B", "severity": "high", "description": "b"},
        {"code": "C", "severity": "medium", "description": "c"},
        {"code": "D", "severity": "high", "description": "d"},
        {"code": "E", "severity": "low", "description": "e"},
        {"code": "F", "severity": "low", "description": "f"},
    ]
    case = _ip_case(db, score=50, flags=flags)
    finding = findings_service.record_finding(db, "ip", case)

    assert finding.flag_count == 6
    assert len(finding.top_flags) == 5  # recortado
    assert [f["code"] for f in finding.top_flags[:2]] == ["B", "D"]  # las high primero


def test_record_finding_case_type_desconocido_no_crea_fila(db):
    case = _ip_case(db)
    assert findings_service.record_finding(db, "no_existe", case) is None
    assert findings_service.list_findings(db) == []


def test_record_finding_es_auxiliar_no_propaga_excepciones(db):
    class Roto:
        __tablename__ = "roto"
        id = 1
        risk_score = 10
        risk_flags = []
        # sin 'ip' -> subjects lo tolera; forzamos el fallo en otro sitio:
        @property
        def analyzed_at(self):
            raise RuntimeError("boom")

    # No debe lanzar: devuelve None y deja la sesión usable
    assert findings_service.record_finding(db, "ip", Roto()) is None
    assert findings_service.list_findings(db) == []


def test_list_findings_filtra(db):
    old = _ip_case(db, ip="1.1.1.1", score=10)
    findings_service.record_finding(db, "ip", old)
    hi = _ip_case(db, ip="2.2.2.2", score=80, case_id=42)
    findings_service.record_finding(db, "ip", hi)

    assert len(findings_service.list_findings(db)) == 2
    assert len(findings_service.list_findings(db, risk_level="high")) == 1
    assert len(findings_service.list_findings(db, min_risk_score=50)) == 1
    assert len(findings_service.list_findings(db, case_id=42)) == 1
    assert len(findings_service.list_findings(db, subject_value="2.2.2.2")) == 1
    assert len(findings_service.list_findings(db, case_type="domain")) == 0
    future = datetime.now(timezone.utc) + timedelta(days=1)
    assert len(findings_service.list_findings(db, since=future)) == 0


def test_todos_los_case_type_tienen_spec_y_payload():
    """El vocabulario de subjects debe cubrir el mismo case_type que la cadena de integridad."""
    from app.modules.osint.integrity.payloads import REGISTRY as PAYLOAD_REGISTRY

    assert set(REGISTRY) == set(PAYLOAD_REGISTRY)


def test_build_headline_trunca_a_255():
    spec = REGISTRY["domain"]
    headline = build_headline(spec, "x" * 400, "high", 90)
    assert len(headline) == 255
