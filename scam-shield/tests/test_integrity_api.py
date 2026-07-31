"""
Tests de la cadena de custodia. Usan `client.test_engine` (ver
conftest.py) para simular manipulación DIRECTA de la base de datos, sin
pasar por la API — exactamente el escenario que la cadena de custodia
tiene que detectar.
"""
from unittest.mock import patch

from sqlalchemy import text


def _create_two_domain_cases(client, old_whois, old_ssl):
    with patch("app.services.whois_service.get_whois_info", return_value=old_whois), \
         patch("app.services.ssl_service.get_ssl_info", return_value=old_ssl):
        id1 = client.post("/analysis/domain", json={"domain": "uno.com"}).json()["id"]
        id2 = client.post("/analysis/domain", json={"domain": "dos.com"}).json()["id"]
    return id1, id2


def test_cadena_vacia_se_reporta_como_tal(client):
    response = client.get("/integrity/verify")
    assert response.status_code == 200
    data = response.json()
    assert data["intact"] is True
    assert data["total_entries"] == 0


def test_cada_analisis_anade_un_eslabon(client, old_whois, old_ssl):
    _create_two_domain_cases(client, old_whois, old_ssl)

    ledger = client.get("/integrity/ledger").json()
    assert len(ledger) == 2
    assert ledger[0]["case_type"] == "domain"
    assert ledger[0]["case_id"] == 1
    assert ledger[1]["case_id"] == 2


def test_cadena_encadena_los_eslabones_correctamente(client, old_whois, old_ssl):
    _create_two_domain_cases(client, old_whois, old_ssl)
    ledger = client.get("/integrity/ledger").json()

    assert ledger[0]["previous_chain_hash"] == "0" * 64  # el primer eslabón encadena con el "génesis"
    assert ledger[1]["previous_chain_hash"] == ledger[0]["chain_hash"]  # el segundo, con el hash del primero


def test_cadena_integra_tras_analisis_normales(client, old_whois, old_ssl):
    _create_two_domain_cases(client, old_whois, old_ssl)
    response = client.get("/integrity/verify")
    assert response.json()["intact"] is True


def test_manipular_un_caso_directamente_en_la_bd_se_detecta(client, old_whois, old_ssl):
    _create_two_domain_cases(client, old_whois, old_ssl)

    # Manipulación DIRECTA en la base de datos, sin pasar por la API —
    # exactamente lo que la cadena de custodia tiene que detectar.
    with client.test_engine.connect() as conn:
        conn.execute(text("UPDATE cases SET risk_score = 999 WHERE id = 1"))
        conn.commit()

    response = client.get("/integrity/verify")
    data = response.json()
    assert data["intact"] is False
    assert data["broken_at_entry_id"] == 1


def test_manipular_el_segundo_caso_no_afecta_al_primero(client, old_whois, old_ssl):
    _create_two_domain_cases(client, old_whois, old_ssl)

    with client.test_engine.connect() as conn:
        conn.execute(text("UPDATE cases SET risk_score = 999 WHERE id = 2"))
        conn.commit()

    response = client.get("/integrity/verify")
    data = response.json()
    assert data["intact"] is False
    assert data["broken_at_entry_id"] == 2  # se detecta justo en el eslabón afectado, no antes


def test_manipular_el_propio_libro_de_registro_tambien_se_detecta(client, old_whois, old_ssl):
    """Si alguien toca directamente la tabla integrity_ledger (no el caso), también debe detectarse."""
    _create_two_domain_cases(client, old_whois, old_ssl)

    with client.test_engine.connect() as conn:
        conn.execute(text("UPDATE integrity_ledger SET evidence_hash = 'hash-falso' WHERE id = 1"))
        conn.commit()

    response = client.get("/integrity/verify")
    assert response.json()["intact"] is False


def test_email_e_imagen_no_dan_falso_positivo_por_el_hash_informativo(client, old_whois):
    """
    El hash del contenido original (raw_email_sha256 / raw_file_sha256) es
    solo informativo y no participa en la cadena — verificar no debe
    fallar por su culpa, aunque no se pueda reconstruir.
    """
    raw_email = "From: a@ejemplo.com\nSubject: prueba\nDate: Wed, 09 Jul 2026 10:00:00 +0000\n\nCuerpo.\n"
    with patch("app.api.routes.email_analysis.whois_service.get_whois_info", return_value=old_whois):
        files = {"file": ("test.eml", raw_email.encode(), "message/rfc822")}
        client.post("/analysis/email/file", files=files)

    from io import BytesIO
    from PIL import Image
    img = Image.new("RGB", (50, 50), color=(1, 2, 3))
    buf = BytesIO()
    img.save(buf, format="JPEG")
    client.post("/analysis/image", files={"file": ("foto.jpg", buf.getvalue(), "image/jpeg")})

    response = client.get("/integrity/verify")
    data = response.json()
    assert data["intact"] is True
    assert data["total_entries"] == 2


def test_certificado_de_un_caso_concreto(client, old_whois, old_ssl):
    id1, _ = _create_two_domain_cases(client, old_whois, old_ssl)

    response = client.get(f"/integrity/case/domain/{id1}")
    assert response.status_code == 200
    data = response.json()
    assert data["case_type"] == "domain"
    assert data["case_id"] == id1
    assert len(data["evidence_hash"]) == 64  # sha256 en hex


def test_certificado_de_caso_inexistente_da_404(client):
    response = client.get("/integrity/case/domain/9999")
    assert response.status_code == 404
