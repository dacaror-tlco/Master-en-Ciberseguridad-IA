from unittest.mock import patch

from app.modules.reports.ai_narrative import AIResponseError, AIUnavailableError
from tests.conftest import NARRATIVA_FALSA


def test_generate_report_sin_api_key_da_503(client, case_con_timeline, storage_dir):
    with patch("app.core.config.settings.reports_storage_dir", str(storage_dir)):
        response = client.post(
            "/reports/generate",
            json={"case_id": case_con_timeline.id, "generado_por": "Tester"},
        )
    assert response.status_code == 503


def test_generate_report_case_inexistente(client, storage_dir):
    response = client.post(
        "/reports/generate", json={"case_id": 999, "generado_por": "Tester"}
    )
    assert response.status_code == 404


def test_generate_get_and_download_report(client, case_con_timeline, storage_dir):
    with patch("app.modules.reports.ai_narrative.generar_narrativa", return_value=NARRATIVA_FALSA):
        generate_response = client.post(
            "/reports/generate",
            json={"case_id": case_con_timeline.id, "generado_por": "Tester"},
        )
    assert generate_response.status_code == 200
    report = generate_response.json()
    assert report["version"] == 1
    assert "HALLAZGOS" in report["resumen_ia"]

    get_response = client.get(f"/reports/{report['id']}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == report["id"]

    download_response = client.get(f"/reports/{report['id']}/download")
    assert download_response.status_code == 200
    assert download_response.headers["content-type"] == "application/pdf"

    list_response = client.get(f"/cases/{case_con_timeline.id}/reports")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1


def test_get_report_inexistente(client):
    response = client.get("/reports/999")
    assert response.status_code == 404


def test_download_de_un_pdf_borrado_da_410(client, case_con_timeline, storage_dir):
    """Antes esto reventaba con un 500 al intentar servir un fichero inexistente."""
    with patch("app.modules.reports.ai_narrative.generar_narrativa", return_value=NARRATIVA_FALSA):
        report = client.post(
            "/reports/generate",
            json={"case_id": case_con_timeline.id, "generado_por": "Tester"},
        ).json()

    (storage_dir / f"case_{case_con_timeline.id}" / "report_v1.pdf").unlink()

    response = client.get(f"/reports/{report['id']}/download")
    assert response.status_code == 410


def test_ia_caida_da_503(client, case_con_timeline, storage_dir):
    with patch(
             "app.modules.reports.ai_narrative.generar_narrativa",
             side_effect=AIUnavailableError("Anthropic no responde"),
         ):
        response = client.post(
            "/reports/generate",
            json={"case_id": case_con_timeline.id, "generado_por": "Tester"},
        )
    assert response.status_code == 503


def test_respuesta_ia_inutilizable_da_502(client, case_con_timeline, storage_dir):
    with patch(
             "app.modules.reports.ai_narrative.generar_narrativa",
             side_effect=AIResponseError("narrativa truncada"),
         ):
        response = client.post(
            "/reports/generate",
            json={"case_id": case_con_timeline.id, "generado_por": "Tester"},
        )
    assert response.status_code == 502
