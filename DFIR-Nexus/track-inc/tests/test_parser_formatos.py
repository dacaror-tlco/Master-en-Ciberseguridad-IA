"""
Codificaciones, formatos de hora y usuario: los logs reales de Windows y
Linux que antes se rechazaban o se leían mal.
"""

from datetime import datetime, timedelta, timezone

import pytest

from app.main import app
from app.modules.tracking.codificacion import FicheroNoTextoError, decodificar_log
from app.modules.tracking.log_parser import parse_log_text
from .conftest import cliente, crear_caso

LINEA = "2026-08-14 03:11:19  type C:\\Users\\José\\notas.txt"


# --- codificaciones ---------------------------------------------------------

@pytest.mark.parametrize(
    ("datos", "codificacion"),
    [
        (LINEA.encode("utf-8"), "utf-8"),
        (LINEA.encode("utf-8-sig"), "utf-8-sig"),        # Bloc de notas
        (LINEA.encode("utf-16"), "utf-16"),              # Out-File en PowerShell 5.1
        (LINEA.encode("utf-16-le"), "utf-16-le"),        # UTF-16 sin BOM
        (LINEA.encode("cp1252"), "cp1252"),              # ANSI de Windows
    ],
)
def test_decodifica_las_codificaciones_habituales(datos, codificacion):
    texto, detectada = decodificar_log(datos)
    assert texto.removeprefix("\ufeff") == LINEA
    assert detectada == codificacion


def test_rechaza_binario():
    with pytest.raises(FicheroNoTextoError):
        decodificar_log(b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff")


def test_bom_no_rompe_la_hora_de_la_primera_linea():
    texto, _ = decodificar_log(("2026-08-14 03:11:19  whoami\n").encode("utf-8-sig"))
    evento = parse_log_text(texto, "a.log")[0]
    assert evento.payload["timestamp_inferred"] is False
    assert evento.payload["command"] == "whoami"


def test_la_api_acepta_utf16_y_dice_la_codificacion():
    with cliente() as c:
        case_id = crear_caso("Cod", "perito")
        r = c.post(
            f"/cases/{case_id}/tracking/analyze",
            files={"file": ("ps.log", "2026-08-14 03:11:19  whoami".encode("utf-16"))},
        )
    assert r.status_code == 200
    assert r.json()["codificacion"] == "utf-16"
    assert r.json()["eventos"][0]["evento"] == "whoami"


# --- formatos de hora -------------------------------------------------------

@pytest.mark.parametrize(
    ("linea", "esperada", "comando"),
    [
        ("2026-08-14T03:11:19.123Z whoami", "2026-08-14T03:11:19.123000+00:00", "whoami"),
        ("2026-08-14T03:11:19+02:00 whoami", "2026-08-14T01:11:19+00:00", "whoami"),
        ("[2026-08-14 03:11:20] hostname", "2026-08-14T03:11:20+00:00", "hostname"),
        ("2026/08/14 03:11:21 ipconfig", "2026-08-14T03:11:21+00:00", "ipconfig"),
        ("14/08/2026 3:11:22 ipconfig /all", "2026-08-14T03:11:22+00:00", "ipconfig /all"),
        ("08/14/2026 03:11:23 net view", "2026-08-14T03:11:23+00:00", "net view"),
    ],
)
def test_formatos_de_hora(linea, esperada, comando):
    evento = parse_log_text(linea, "a.log")[0]
    assert evento.payload["timestamp_inferred"] is False
    assert evento.timestamp.isoformat() == esperada
    assert evento.payload["command"] == comando


def test_la_zona_explicita_de_la_marca_gana_a_la_del_log():
    evento = parse_log_text("2026-08-14T03:11:19Z whoami", "a.log", zona=timezone(timedelta(hours=2)))[0]
    assert evento.timestamp.isoformat() == "2026-08-14T03:11:19+00:00"


def test_syslog_sin_anio():
    evento = parse_log_text("Jan  2 03:11:21 srv sshd[812]: Accepted password for root", "auth.log")[0]
    assert evento.payload["timestamp_inferred"] is False
    assert (evento.timestamp.month, evento.timestamp.day, evento.timestamp.hour) == (1, 2, 3)
    assert evento.timestamp <= datetime.now(timezone.utc) + timedelta(days=1)
    assert evento.payload["command"] == "srv sshd[812]: Accepted password for root"


def test_numero_pegado_a_la_hora_no_es_marca_temporal():
    evento = parse_log_text("2026-08-14 03:11:19abc", "a.log")[0]
    assert evento.payload["timestamp_inferred"] is True


# --- usuario ----------------------------------------------------------------

@pytest.mark.parametrize(
    ("comando", "usuario"),
    [
        ("runas /user:CORP\\admin cmd", "CORP\\admin"),
        ("psexec \\\\10.0.0.5 -u CORP\\adm -p x cmd", "CORP\\adm"),
        ("schtasks /create /tn upd /tr C:\\x.exe /ru SYSTEM", "SYSTEM"),
        ("curl http://x/login?user=pepe", None),
        ("curl -u admin:secreto http://x", None),
    ],
)
def test_usuario_detectado(comando, usuario):
    evento = parse_log_text(f"2026-08-14 03:11:19  {comando}", "a.log")[0]
    assert evento.payload["user"] == usuario


def test_la_salida_de_whoami_da_el_usuario():
    evento = parse_log_text("2026-08-14 03:11:19  whoami\n    corp\\svc_backup\n", "a.log")[0]
    assert evento.payload["user"] == "corp\\svc_backup"


def test_usuario_se_recorta_a_100_caracteres():
    evento = parse_log_text("2026-08-14 03:11:19  login user:" + "u" * 300, "a.log")[0]
    assert len(evento.payload["user"]) == 100
