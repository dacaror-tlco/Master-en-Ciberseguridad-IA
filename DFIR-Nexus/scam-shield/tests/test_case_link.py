"""
PATCH /osint-cases/{case_type}/{id}/vinculacion — vincular/cambiar/
desvincular el caso de Nexus asociado a una investigación OSINT.

`db` es una Session directa sobre el mismo engine SQLite en memoria que
usa `client` (ver conftest.py): se usa para sembrar investigaciones y
casos sin pasar por los endpoints de análisis (creación no es lo que
prueba este fichero) y para comprobar el estado persistido tras cada
llamada.
"""
from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from app.core.config import settings
from app.modules.osint.cnmv.models import CnmvCheckCase
from app.modules.osint.domain.models import Case as DomainCase
from app.modules.osint.email.models import EmailCase
from app.modules.osint.findings.models import OsintFinding
from app.modules.osint.image.models import ImageCase
from app.modules.osint.ip.models import IpCase
from app.modules.osint.phone.models import PhoneCase
from app.modules.osint.typosquatting.models import TyposquattingCase
from app.modules.osint.wallet.models import WalletCase
from tests.conftest import SharedCaseRow

NOW = datetime.now(timezone.utc)


def _crear_caso(db, id=10, eliminado=False):
    caso = SharedCaseRow(id=id, nombre=f"Caso {id}", eliminado=eliminado)
    db.add(caso)
    db.commit()
    return caso


def _crear_ip(db, **overrides):
    kwargs = dict(ip="1.2.3.4", risk_score=0, analyzed_at=NOW)
    kwargs.update(overrides)
    inv = IpCase(**kwargs)
    db.add(inv)
    db.commit()
    db.refresh(inv)
    return inv


# --- escenarios principales (tipo de referencia: ip) ------------------------


def test_investigacion_sin_caso_por_defecto_en_el_listado(client, db):
    inv = _crear_ip(db)
    item = next(i for i in client.get("/ip-cases").json() if i["id"] == inv.id)
    assert item["case_id"] is None


def test_vinculacion_null_a_caso(client, db):
    _crear_caso(db, id=10)
    inv = _crear_ip(db)
    r = client.patch(f"/osint-cases/ip/{inv.id}/vinculacion", json={"case_id": 10})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["cambiado"] is True
    assert body["case_id"] == 10


def test_cambio_de_caso_a_otro(client, db):
    _crear_caso(db, id=10)
    _crear_caso(db, id=20)
    inv = _crear_ip(db, case_id=10)
    r = client.patch(f"/osint-cases/ip/{inv.id}/vinculacion", json={"case_id": 20})
    assert r.status_code == 200
    assert r.json()["case_id"] == 20


def test_desvinculacion(client, db):
    _crear_caso(db, id=10)
    inv = _crear_ip(db, case_id=10)
    r = client.patch(f"/osint-cases/ip/{inv.id}/vinculacion", json={"case_id": None})
    assert r.status_code == 200
    assert r.json()["case_id"] is None


def test_mismo_case_id_es_no_op(client, db):
    _crear_caso(db, id=10)
    inv = _crear_ip(db, case_id=10)
    with patch("app.modules.osint.case_link.audit_client.requests.post") as mock_post:
        r = client.patch(f"/osint-cases/ip/{inv.id}/vinculacion", json={"case_id": 10})
    assert r.status_code == 200
    body = r.json()
    assert body["cambiado"] is False
    assert body["auditoria_registrada"] is None
    mock_post.assert_not_called()


def test_persistencia_correcta_en_la_tabla_origen(client, db):
    _crear_caso(db, id=10)
    inv = _crear_ip(db)
    client.patch(f"/osint-cases/ip/{inv.id}/vinculacion", json={"case_id": 10})
    db.expire_all()
    assert db.get(IpCase, inv.id).case_id == 10


def test_persistencia_correcta_en_osint_findings(client, db):
    _crear_caso(db, id=10)
    inv = _crear_ip(db)
    db.add(
        OsintFinding(
            case_type="ip", source_table="ip_cases", source_id=inv.id, case_id=None,
            subject_type="ip_address", subject_value=inv.ip, risk_score=0, risk_level="low",
            headline="IP 1.2.3.4 — RIESGO BAJO (0)", flag_count=0, top_flags=[], details={},
            analyzed_at=NOW,
        )
    )
    db.commit()

    client.patch(f"/osint-cases/ip/{inv.id}/vinculacion", json={"case_id": 10})

    db.expire_all()
    finding = db.query(OsintFinding).filter_by(case_type="ip", source_id=inv.id).first()
    assert finding.case_id == 10


def test_no_falla_si_no_existe_finding_para_la_investigacion(client, db):
    """record_finding puede haber fallado en su momento (es auxiliar) — no
    debe impedir vincular la investigación en sí."""
    _crear_caso(db, id=10)
    inv = _crear_ip(db)
    r = client.patch(f"/osint-cases/ip/{inv.id}/vinculacion", json={"case_id": 10})
    assert r.status_code == 200


def test_investigacion_inexistente_da_404(client, db):
    _crear_caso(db, id=10)
    r = client.patch("/osint-cases/ip/999999/vinculacion", json={"case_id": 10})
    assert r.status_code == 404


def test_tipo_de_investigacion_desconocido_da_404(client, db):
    r = client.patch("/osint-cases/no-existe/1/vinculacion", json={"case_id": None})
    assert r.status_code == 404


def test_caso_destino_inexistente_da_error_controlado_y_no_persiste_nada(client, db):
    inv = _crear_ip(db)
    r = client.patch(f"/osint-cases/ip/{inv.id}/vinculacion", json={"case_id": 999999})
    assert r.status_code == 404
    db.expire_all()
    assert db.get(IpCase, inv.id).case_id is None


def test_caso_destino_eliminado_se_trata_como_no_disponible(client, db):
    _crear_caso(db, id=10, eliminado=True)
    inv = _crear_ip(db)
    r = client.patch(f"/osint-cases/ip/{inv.id}/vinculacion", json={"case_id": 10})
    assert r.status_code == 404


# --- auditoría ---------------------------------------------------------


def test_auditoria_se_registra_en_cada_cambio_real(client, db):
    _crear_caso(db, id=10)
    inv = _crear_ip(db)
    with patch("app.modules.osint.case_link.audit_client.requests.post") as mock_post:
        mock_post.return_value.raise_for_status.return_value = None
        r = client.patch(f"/osint-cases/ip/{inv.id}/vinculacion", json={"case_id": 10})

    assert r.status_code == 200
    assert r.json()["auditoria_registrada"] is True
    mock_post.assert_called_once()
    payload = mock_post.call_args.kwargs["json"]
    assert payload["case_type"] == "ip"
    assert payload["source_id"] == inv.id
    assert payload["case_anterior"] is None
    assert payload["case_nuevo"] == 10
    # Fase 4: el body ya no lleva `actor` — Casos lo resuelve él mismo a
    # partir del JWT reenviado (ver más abajo), no de un dato del body.
    assert "actor" not in payload


def test_auditoria_envia_service_token_y_reenvia_el_jwt_del_usuario(client, db):
    """Fase 4 — mecanismo OSINT->Cases: X-Service-Token autentica la
    llamada como procedente de este backend; Authorization es el MISMO
    JWT que trajo la petición entrante (inyectado por el `client`
    autenticado de conftest.py), reenviado tal cual para que Casos pueda
    resolver el `actor` real."""
    _crear_caso(db, id=10)
    inv = _crear_ip(db)
    with patch("app.modules.osint.case_link.audit_client.requests.post") as mock_post:
        mock_post.return_value.raise_for_status.return_value = None
        client.patch(f"/osint-cases/ip/{inv.id}/vinculacion", json={"case_id": 10})

    headers = mock_post.call_args.kwargs["headers"]
    assert headers["X-Service-Token"] == settings.osint_audit_service_token
    assert headers["Authorization"] == client.headers["Authorization"]


def test_auditoria_distingue_los_tres_escenarios(client, db):
    _crear_caso(db, id=10)
    _crear_caso(db, id=20)
    inv = _crear_ip(db)

    with patch("app.modules.osint.case_link.audit_client.requests.post") as mock_post:
        mock_post.return_value.raise_for_status.return_value = None
        client.patch(f"/osint-cases/ip/{inv.id}/vinculacion", json={"case_id": 10})  # NULL -> 10
        client.patch(f"/osint-cases/ip/{inv.id}/vinculacion", json={"case_id": 20})  # 10 -> 20
        client.patch(f"/osint-cases/ip/{inv.id}/vinculacion", json={"case_id": None})  # 20 -> NULL

    llamadas = [c.kwargs["json"] for c in mock_post.call_args_list]
    assert [(c["case_anterior"], c["case_nuevo"]) for c in llamadas] == [
        (None, 10),
        (10, 20),
        (20, None),
    ]


def test_fallo_de_auditoria_no_deshace_el_cambio_y_se_reporta(client, db):
    _crear_caso(db, id=10)
    inv = _crear_ip(db)
    with patch(
        "app.modules.osint.case_link.audit_client.requests.post",
        side_effect=ConnectionError("Casos no disponible"),
    ):
        r = client.patch(f"/osint-cases/ip/{inv.id}/vinculacion", json={"case_id": 10})

    assert r.status_code == 200  # el cambio en OSINT no se deshace por un fallo ajeno
    body = r.json()
    assert body["case_id"] == 10
    assert body["auditoria_registrada"] is False
    assert body["auditoria_error"]

    db.expire_all()
    assert db.get(IpCase, inv.id).case_id == 10  # persistido de verdad, no solo en la respuesta


# --- funcionamiento genérico para los 8 tipos -------------------------------


@pytest.mark.parametrize(
    "case_type,modelo,kwargs",
    [
        ("domain", DomainCase, dict(domain="ejemplo.com", risk_score=0, analyzed_at=NOW)),
        ("email", EmailCase, dict(risk_score=0, headers={}, analyzed_at=NOW)),
        ("wallet", WalletCase, dict(chain="ETH", address="0xabc", risk_score=0, wallet={}, analyzed_at=NOW)),
        ("typosquatting", TyposquattingCase, dict(domain="ejemplo.com", risk_score=0, analyzed_at=NOW)),
        ("phone", PhoneCase, dict(raw_phone="+34600000000", risk_score=0, analyzed_at=NOW)),
        ("cnmv", CnmvCheckCase, dict(query="Entidad X", risk_score=0, analyzed_at=NOW)),
        ("image", ImageCase, dict(perceptual_hash="abc123", risk_score=0, analyzed_at=NOW)),
        ("ip", IpCase, dict(ip="1.2.3.4", risk_score=0, analyzed_at=NOW)),
    ],
)
def test_endpoint_generico_funciona_para_los_8_tipos(client, db, case_type, modelo, kwargs):
    _crear_caso(db, id=10)
    inv = modelo(**kwargs)
    db.add(inv)
    db.commit()
    db.refresh(inv)

    r = client.patch(f"/osint-cases/{case_type}/{inv.id}/vinculacion", json={"case_id": 10})
    assert r.status_code == 200, r.text
    assert r.json()["case_id"] == 10

    r = client.patch(f"/osint-cases/{case_type}/{inv.id}/vinculacion", json={"case_id": None})
    assert r.status_code == 200
    assert r.json()["case_id"] is None
