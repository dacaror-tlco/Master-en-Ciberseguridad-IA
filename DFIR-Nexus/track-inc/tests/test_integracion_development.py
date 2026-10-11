"""
Lo que el equipo añadió al integrar Tracking en `development` y que tiene que
seguir cumpliéndose en esta versión.
"""


from app import main
from app.main import app
from app.modules.tracking import service
from .conftest import cliente, crear_caso


def test_un_error_no_controlado_sale_como_json_con_cabeceras_cors(monkeypatch):
    """Contrato común de los backends: un 500 no controlado es JSON y lleva
    CORS; si no, el navegador lo reporta como bloqueo de CORS y se pierde."""
    def roto(*_args, **_kwargs):
        raise RuntimeError("fallo inesperado")

    monkeypatch.setattr(service, "get_events_for_case", roto)
    case_id = crear_caso()
    with cliente(raise_server_exceptions=False) as c:
        r = c.get(f"/cases/{case_id}/tracking/events", headers={"Origin": "http://localhost:5173"})

    assert r.status_code == 500
    assert r.json() == {"detail": "Error interno del servidor"}
    assert r.headers.get("access-control-allow-origin") == "http://localhost:5173"


def test_las_rutas_de_casos_de_prueba_solo_existen_con_sqlite():
    """Contra MySQL (la base compartida o la del despliegue) Tracking no
    expone ninguna forma de crear casos: son del Módulo 1."""
    assert main.usar_casos_locales("sqlite:///./nexus_dev.db") is True
    assert main.usar_casos_locales("mysql+pymysql://u:p@nexus.aivencloud.com:15486/defaultdb") is False
    assert main.usar_casos_locales("mysql+pymysql://u:p@mysql:3306/nexus") is False


def test_tracking_no_importa_nada_del_modulo_de_casos():
    """Un backend no importa modelos Python de otro (docs/CONTRATOS.md)."""
    import pathlib

    raiz = pathlib.Path(__file__).resolve().parents[1] / "app"
    for fichero in raiz.rglob("*.py"):
        texto = fichero.read_text(encoding="utf-8")
        assert "app.modules.cases" not in texto, fichero
