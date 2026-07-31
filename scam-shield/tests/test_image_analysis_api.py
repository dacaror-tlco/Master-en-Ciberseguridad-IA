from io import BytesIO
from unittest.mock import MagicMock, patch

from PIL import Image


def _make_image_bytes(seed: int, size=(100, 100)) -> bytes:
    img = Image.new("RGB", size)
    px = img.load()
    for x in range(size[0]):
        for y in range(size[1]):
            px[x, y] = ((x + seed) % 256, (y + seed) % 256, (x * y + seed) % 256)
    buf = BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def test_analizar_imagen_nueva_no_da_matches(client):
    data = _make_image_bytes(seed=1)
    response = client.post("/analysis/image", files={"file": ("foto.jpg", data, "image/jpeg")})

    assert response.status_code == 200
    body = response.json()
    assert body["matches"] == []
    assert len(body["perceptual_hash"]) == 16
    assert "Google Images" in body["reverse_search_links"]


def test_imagen_reciclada_se_detecta_como_match(client):
    original = Image.open(BytesIO(_make_image_bytes(seed=7, size=(200, 200))))
    buf = BytesIO()
    original.save(buf, format="JPEG")
    client.post("/analysis/image", files={"file": ("original.jpg", buf.getvalue(), "image/jpeg")})

    cropped = original.resize((160, 160)).crop((5, 5, 155, 155))
    buf2 = BytesIO()
    cropped.save(buf2, format="JPEG")

    response = client.post("/analysis/image", files={"file": ("reciclada.jpg", buf2.getvalue(), "image/jpeg")})
    body = response.json()

    assert len(body["matches"]) == 1
    assert body["matches"][0]["case_id"] == 1
    assert "IMAGE_REUSED_ACROSS_CASES" in [f["code"] for f in body["risk_flags"]]
    assert body["risk_score"] >= 60


def test_imagenes_distintas_no_dan_falso_positivo(client):
    client.post("/analysis/image", files={"file": ("a.jpg", _make_image_bytes(seed=1), "image/jpeg")})
    response = client.post("/analysis/image", files={"file": ("b.jpg", _make_image_bytes(seed=222), "image/jpeg")})

    assert response.json()["matches"] == []


def test_archivo_no_imagen_da_400(client):
    response = client.post("/analysis/image", files={"file": ("nota.txt", b"esto no es una imagen", "text/plain")})
    assert response.status_code == 400


def test_listado_y_detalle_de_casos(client):
    data = _make_image_bytes(seed=1)
    created = client.post("/analysis/image", files={"file": ("foto.jpg", data, "image/jpeg")}).json()

    listado = client.get("/image-cases")
    assert len(listado.json()) == 1

    detalle = client.get(f"/image-cases/{created['id']}")
    assert detalle.status_code == 200
    assert detalle.json()["filename"] == "foto.jpg"


def test_caso_inexistente_da_404(client):
    response = client.get("/image-cases/9999")
    assert response.status_code == 404


# --- Búsqueda inversa (SerpApi) ---

def test_reverse_search_caso_inexistente_da_404(client):
    response = client.post("/analysis/image/9999/reverse-search")
    assert response.status_code == 404


def test_reverse_search_cache_expirada_da_409(client):
    created = client.post("/analysis/image", files={"file": ("foto.jpg", _make_image_bytes(seed=1), "image/jpeg")}).json()
    with patch("app.services.image_cache.get", return_value=None):
        response = client.post(f"/analysis/image/{created['id']}/reverse-search")
    assert response.status_code == 409


def test_reverse_search_sin_api_key_degrada_con_gracia(client):
    created = client.post("/analysis/image", files={"file": ("foto.jpg", _make_image_bytes(seed=1), "image/jpeg")}).json()
    response = client.post(f"/analysis/image/{created['id']}/reverse-search")

    assert response.status_code == 200
    body = response.json()
    assert body["matches"] == []
    assert any("SerpApi" in e for e in body["errors"])
    assert "Google Images" in body["reverse_search_links"]


def test_reverse_search_exitoso_con_serpapi_mockeado(client):
    created = client.post("/analysis/image", files={"file": ("foto.jpg", _make_image_bytes(seed=1), "image/jpeg")}).json()

    serp_resp = MagicMock()
    serp_resp.json.return_value = {
        "image_results": [{"link": "https://otrared.example/perfil", "title": "Perfil", "source": "otrared.example"}]
    }
    serp_resp.raise_for_status.return_value = None

    with patch("app.core.config.settings.serpapi_api_key", "fake-key"), \
         patch("app.core.config.settings.public_base_url", "https://miapp.example.com"), \
         patch("app.services.serpapi_service.requests.get", return_value=serp_resp):
        response = client.post(f"/analysis/image/{created['id']}/reverse-search")

    assert response.status_code == 200
    body = response.json()
    assert len(body["matches"]) == 1
    assert "IMAGE_FOUND_ON_EXTERNAL_PAGES" in [f["code"] for f in body["risk_flags"]]
    assert body["risk_score"] > 0
    assert body["errors"] == []


# --- Búsqueda facial (PimEyes) ---

def test_facial_search_caso_inexistente_da_404(client):
    response = client.post("/analysis/image/9999/facial-search", data={"confirmed_legal_basis": "true"})
    assert response.status_code == 404


def test_facial_search_sin_confirmacion_da_422(client):
    created = client.post("/analysis/image", files={"file": ("foto.jpg", _make_image_bytes(seed=1), "image/jpeg")}).json()
    response = client.post(f"/analysis/image/{created['id']}/facial-search", data={"confirmed_legal_basis": "false"})
    assert response.status_code == 422


def test_facial_search_cache_expirada_da_409(client):
    created = client.post("/analysis/image", files={"file": ("foto.jpg", _make_image_bytes(seed=1), "image/jpeg")}).json()
    with patch("app.services.image_cache.get", return_value=None):
        response = client.post(f"/analysis/image/{created['id']}/facial-search", data={"confirmed_legal_basis": "true"})
    assert response.status_code == 409


def test_facial_search_sin_api_key_degrada_con_gracia(client):
    created = client.post("/analysis/image", files={"file": ("foto.jpg", _make_image_bytes(seed=1), "image/jpeg")}).json()
    response = client.post(
        f"/analysis/image/{created['id']}/facial-search",
        data={"confirmed_legal_basis": "true", "notes": "Caso de prueba"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["matches"] == []
    assert any("PimEyes" in e for e in body["errors"])
    assert body["confirmed_legal_basis"] is True
    assert body["notes"] == "Caso de prueba"


def test_facial_search_exitoso_con_pimeyes_mockeado(client):
    created = client.post("/analysis/image", files={"file": ("foto.jpg", _make_image_bytes(seed=1), "image/jpeg")}).json()

    pim_resp = MagicMock()
    pim_resp.json.return_value = {
        "matches": [{"url": "https://otrared.example/perfil-falso", "page_title": "Perfil falso", "confidence": 0.9}]
    }
    pim_resp.raise_for_status.return_value = None

    with patch("app.core.config.settings.pimeyes_api_key", "fake-key"), \
         patch("app.services.pimeyes_service.requests.post", return_value=pim_resp):
        response = client.post(
            f"/analysis/image/{created['id']}/facial-search",
            data={"confirmed_legal_basis": "true"},
        )

    assert response.status_code == 200
    body = response.json()
    assert len(body["matches"]) == 1
    assert "IMAGE_FACE_FOUND_ELSEWHERE" in [f["code"] for f in body["risk_flags"]]
    assert body["risk_score"] > 0


def test_facial_search_queda_sellada_en_la_cadena_de_integridad(client):
    created = client.post("/analysis/image", files={"file": ("foto.jpg", _make_image_bytes(seed=1), "image/jpeg")}).json()
    client.post(f"/analysis/image/{created['id']}/facial-search", data={"confirmed_legal_basis": "true"})

    verify = client.get("/integrity/verify")
    assert verify.status_code == 200
    assert verify.json()["intact"] is True
