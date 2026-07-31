from unittest.mock import MagicMock, patch

import pytest

from app.services import cnmv_registry_service


@pytest.fixture(autouse=True)
def _no_real_cnmv_registry_lookup():
    """
    Anula (sobreescribiendo por nombre) el autouse global de conftest.py
    que mockea `search_registered_entities` — aquí es precisamente la
    función real la que se quiere probar.
    """
    yield

_GET_PAGE = """
<html><body><form>
<input type="hidden" name="__VIEWSTATE" value="fake-viewstate" />
<input type="hidden" name="__VIEWSTATEGENERATOR" value="fake-generator" />
<input type="hidden" name="__EVENTVALIDATION" value="fake-validation" />
</form></body></html>
"""

_POST_WITH_RESULTS = """
<html><body>
<p class="titcont">Han sido encontrados: 2 resultados</p>
<select name="ctl00$ContentPrincipal$wuc_Entidades$lstSeleccion">
<option value="A82473018">RENTA 4 BANCO, S.A.</option>
<option value="A78292661">RENTA 4 GESTORA, S.G.I.I.C., S.A.</option>
</select>
</body></html>
"""

_POST_SIN_RESULTADOS = """
<html><body>
<p class="validacion">No se han encontrado resultados</p>
</body></html>
"""

_POST_ESTRUCTURA_INESPERADA = "<html><body>algo completamente distinto, sin select ni mensaje</body></html>"


def _mock_session(post_text):
    session = MagicMock()
    get_resp = MagicMock(text=_GET_PAGE)
    get_resp.raise_for_status.return_value = None
    post_resp = MagicMock(text=post_text)
    post_resp.raise_for_status.return_value = None
    session.get.return_value = get_resp
    session.post.return_value = post_resp
    return session


def test_busqueda_con_resultados():
    with patch("app.services.cnmv_registry_service.requests.Session", return_value=_mock_session(_POST_WITH_RESULTS)):
        matches = cnmv_registry_service.search_registered_entities("Renta 4")

    assert len(matches) == 2
    assert matches[0].code == "A82473018"
    assert matches[0].name == "RENTA 4 BANCO, S.A."


def test_busqueda_sin_resultados():
    with patch("app.services.cnmv_registry_service.requests.Session", return_value=_mock_session(_POST_SIN_RESULTADOS)):
        matches = cnmv_registry_service.search_registered_entities("AICHAINTRADER")

    assert matches == []


def test_estructura_inesperada_lanza_runtimeerror():
    with patch("app.services.cnmv_registry_service.requests.Session", return_value=_mock_session(_POST_ESTRUCTURA_INESPERADA)):
        with pytest.raises(RuntimeError, match="No se encontró el formulario"):
            cnmv_registry_service.search_registered_entities("cualquier cosa")


def test_envia_los_tokens_de_viewstate_en_el_post():
    session = _mock_session(_POST_SIN_RESULTADOS)
    with patch("app.services.cnmv_registry_service.requests.Session", return_value=session):
        cnmv_registry_service.search_registered_entities("algo")

    posted_data = session.post.call_args.kwargs["data"]
    assert posted_data["__VIEWSTATE"] == "fake-viewstate"
    assert posted_data["__EVENTVALIDATION"] == "fake-validation"
    assert posted_data["ctl00$ContentPrincipal$txtBusqueda"] == "algo"
