"""
Extracción de indicadores (IOC) de los eventos de tracking.

Un comando de un log post-incidente suele arrastrar los datos que de verdad
importan para la investigación: la IP a la que se conectó el atacante, el
dominio del que descargó el binario, la ruta donde lo dejó, la cuenta que
creó. Hoy eso vive dentro del texto de `evento` y hay que leerlo a ojo.

Este módulo lo saca a datos estructurados, con dos reglas:

  1. Se extrae del COMANDO, de su SALIDA y, si el comando es un PowerShell
     con `-EncodedCommand`, del COMANDO DECODIFICADO. Muchos indicadores
     solo aparecen en la salida (`ping` devuelve la IP resuelta, `netstat`
     las conexiones) o dentro del base64, y son justo los más valiosos.

  2. Cada indicador conserva DE DÓNDE sale: comando, salida o decodificado,
     y en qué línea del fichero. Es el requisito de procedencia de la
     arquitectura v2 (sección 17): poder responder "¿de dónde sale este
     dato?" hasta la línea original del log.

No se persiste nada: `tracking_events` mantiene exactamente el esquema de
CLAUDE.md. Los indicadores se calculan al analizar y viajan en la respuesta
de la API, para que Timeline, Correlation Engine o IOC Intelligence los
consuman sin tener que reparsear el texto del evento (lo que romperia la
frontera de integración del módulo).
"""

from __future__ import annotations

import ipaddress
import re
from dataclasses import dataclass

# --- patrones ---------------------------------------------------------------
# Deliberadamente conservadores: es preferible no extraer un indicador dudoso
# a llenar la investigación de ruido que el perito tenga que descartar.

# Los lookarounds impiden que un numero de version como "1.2.3.4.5" produzca
# la falsa IP "1.2.3.4": \b se satisface con el punto siguiente y no basta.
_RE_IPV4 = re.compile(r"(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])")
# Candidatos a IPv6; se validan después con `ipaddress`, que descarta horas
# (03:11:19) y direcciones MAC (00:1a:2b:3c:4d:5e).
_RE_IPV6 = re.compile(r"(?<![\w:.])(?:[0-9a-f]{0,4}:){2,7}[0-9a-f]{0,4}(?![\w:.])", re.IGNORECASE)
_RE_URL = re.compile(r"\b(?:https?|ftp)://[^\s\"'<>|]+", re.IGNORECASE)
# dominio con TLD alfabetico de 2+ letras; excluye asi las IPv4
_RE_DOMINIO = re.compile(
    r"\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,24}\b", re.IGNORECASE
)
# Rutas entre comillas primero: pueden llevar espacios ("C:\Program Files\...").
_RE_RUTA_WIN_ENTRE_COMILLAS = re.compile(r"[\"']([A-Za-z]:\\[^\"'\r\n]+)[\"']")
_RE_RUTA_WIN = re.compile(r"\b[A-Za-z]:\\[^\s\"'|<>,;]+")
_RE_RUTA_UNC = re.compile(r"\\\\[A-Za-z0-9._-]+\\[^\s\"'|<>,;]+")
# %TEMP%\a.exe, $env:APPDATA\b.exe
_RE_RUTA_VARIABLE = re.compile(r"(?:%[A-Za-z_][A-Za-z0-9_]*%|\$env:[A-Za-z_][A-Za-z0-9_]*)\\[^\s\"'|<>,;)]+", re.IGNORECASE)
# Rutas absolutas de Linux, solo bajo directorios de sistema conocidos: así
# no se confunden con parámetros de Windows (/add, /all) ni con fracciones.
_RE_RUTA_LINUX = re.compile(
    r"(?<![\w:/.\\-])/(?:etc|tmp|var|home|root|usr|opt|dev|bin|sbin|proc|boot|mnt|srv|lib|lib64|run)(?:/[^\s\"'|<>;&)]*)?"
)
_RE_HASH = re.compile(r"\b[a-fA-F0-9]{32}\b|\b[a-fA-F0-9]{40}\b|\b[a-fA-F0-9]{64}\b")
_RE_EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_RE_HXXP = re.compile(r"\bhxxp(s?)://", re.IGNORECASE)
_RE_FXP = re.compile(r"\bfxp://", re.IGNORECASE)
_RE_PUNTO_DESACTIVADO = re.compile(r"[\[({]\.[\])}]")
_RE_FIN_DE_HOST = re.compile(r"[/\\?#]")
_RE_HEX = re.compile(r"[0-9a-f]", re.IGNORECASE)

# Extensiones de fichero que NO son dominios, para que "svc.exe", "auth.log"
# o "exploit.py" no acaben clasificados como tales. Algunas coinciden con
# dominios de país (.py, .pl, .sh, .md): se prefiere no extraer un dominio
# dudoso a llenar la lista de nombres de fichero.
_EXTENSIONES = {
    "exe", "dll", "bat", "cmd", "ps1", "psm1", "psd1", "vbs", "vbe", "js", "jse", "wsf", "hta", "jar",
    "msi", "scr", "sys", "cpl", "lnk", "iso", "img", "vhd", "vhdx",
    "log", "txt", "csv", "xml", "json", "yaml", "yml", "ini", "cfg", "conf", "md", "rtf",
    "zip", "rar", "7z", "gz", "tar", "cab", "dat", "tmp", "bak", "old", "db", "sqlite",
    "sam", "hiv", "reg", "evtx", "etl", "pcap", "pcapng", "dmp",
    "doc", "docx", "xls", "xlsx", "xlsm", "ppt", "pptx", "pdf", "odt", "eml", "msg", "pst", "ost",
    "png", "jpg", "jpeg", "gif", "bmp",
    "py", "pyc", "sh", "pl", "rb", "php", "asp", "aspx", "jsp", "c", "h", "cpp", "cs", "go",
    "key", "pem", "crt", "cer", "pfx", "p12", "kdbx", "ovpn",
}

# Dominios de nivel superior aceptados para un dominio suelto en el texto.
# Sin esta lista, los nombres de tipos de .NET (`System.Net.WebClient`,
# `System.IO.File`) salían como dominios. Los códigos de país (2 letras) se
# aceptan todos. Un host dentro de una URL o ruta UNC no pasa por aquí: ahí
# no hay duda de que es un host.
_TLD_GENERICOS = {
    "com", "net", "org", "info", "biz", "io", "co", "app", "dev", "xyz", "top", "online", "site",
    "club", "shop", "store", "tech", "cloud", "live", "link", "click", "space", "website", "win",
    "pro", "name", "mobi", "gov", "edu", "mil", "int", "arpa", "onion", "local", "lan", "corp",
    "internal", "home", "icu", "vip", "work", "life", "world", "email", "support", "services",
    "digital", "network", "systems", "zone", "fun", "run", "host", "server", "cc", "tk", "ml",
}

_PREFIJOS_DOTNET = ("system.", "microsoft.", "windows.")


@dataclass(frozen=True)
class Indicador:
    """Un indicador encontrado, con su procedencia."""

    tipo: str       # ip_publica | ip_privada | dominio | url | ruta | hash | email
    valor: str
    origen: str     # "comando", "salida" o "decodificado"


def refang(texto: str) -> str:
    """Deshace el "defang" habitual de los indicadores compartidos en tickets
    e informes (`hxxp://evil[.]com`, `185[.]220[.]101[.]7`)."""
    if "xp" not in texto and "." not in texto:
        return texto  # nada que reactivar: evita tres pasadas en la mayoría de líneas
    texto = _RE_HXXP.sub(r"http\1://", texto)
    texto = _RE_FXP.sub("ftp://", texto)
    return _RE_PUNTO_DESACTIVADO.sub(".", texto).replace("[:]", ":")


def _clasificar_ip(texto: str) -> str | None:
    """Distingue IP publica de no pública, y descarta lo que no es una IP.

    La distincion importa: la IP del atacante es casi siempre publica, y una
    privada (10.x, 192.168.x) apunta a maquina interna. Mezclarlas obligaria
    al perito a separarlas a mano.

    Pública es lo enrutable en Internet (`is_global`). Todo lo demás cuenta
    como privada: redes internas, loopback, enlace local, CGNAT (100.64/10)
    y los rangos reservados para documentación (192.0.2/24, 203.0.113/24…).
    """
    try:
        ip = ipaddress.ip_address(texto)
    except ValueError:
        return None  # "1.2.3.4.5" o "999.1.1.1" caen aqui
    return "ip_publica" if ip.is_global else "ip_privada"


def _es_nombre_de_fichero(texto: str) -> bool:
    sufijo = texto.rsplit(".", 1)[-1].lower()
    return sufijo in _EXTENSIONES


def _es_dominio_suelto(texto: str) -> bool:
    bajo = texto.lower()
    if _es_nombre_de_fichero(bajo) or bajo.startswith(_PREFIJOS_DOTNET):
        return False
    tld = bajo.rsplit(".", 1)[-1]
    return len(tld) == 2 or tld in _TLD_GENERICOS


def _host_de(referencia: str) -> str | None:
    """Saca el host de una URL (`http://host/...`) o de una ruta UNC
    (`\\\\host\\recurso`). Devuelve None si no hay host reconocible."""
    texto = referencia.strip()
    if "://" in texto[:8]:
        resto = texto.split("://", 1)[1]
    elif texto.startswith("\\\\"):
        resto = texto[2:]
    else:
        return None
    autoridad = _RE_FIN_DE_HOST.split(resto, maxsplit=1)[0].split("@")[-1]  # fuera credenciales
    if autoridad.startswith("["):  # IPv6 en URL: http://[2001:db8::1]:8080/
        return autoridad[1:].split("]", 1)[0] or None
    return autoridad.split(":")[0] or None  # fuera el puerto


def _anadir_host(referencia: str, anadir) -> None:
    """Registra el host de una URL o ruta UNC como IP o dominio propio."""
    host = _host_de(referencia)
    if not host:
        return
    tipo_ip = _clasificar_ip(host)
    if tipo_ip:
        anadir(tipo_ip, host)
    elif not _es_nombre_de_fichero(host) and _RE_DOMINIO.fullmatch(host):
        anadir("dominio", host.lower())


def _extraer_de(texto: str, origen: str) -> list[Indicador]:
    if not texto:
        return []

    encontrados: list[Indicador] = []

    def anadir(tipo: str, valor: str) -> None:
        encontrados.append(Indicador(tipo=tipo, valor=valor, origen=origen))

    texto = refang(texto)

    # URLs primero, porque contienen dominios e IPs dentro. El host SI se
    # extrae ademas por separado: si el atacante descarga de
    # http://185.220.101.7/x.exe y luego exfiltra a \\185.220.101.7\share,
    # lo que hay que ver de un vistazo es que es LA MISMA IP. Dejarla solo
    # dentro de la URL la haria invisible como indicador correlacionable,
    # que es justo lo que pide el Correlation Engine de la arquitectura v2.
    for url in _RE_URL.findall(texto):
        limpia = url.rstrip(".,;)]}'\"")
        anadir("url", limpia)
        _anadir_host(limpia, anadir)
    resto = _RE_URL.sub(" ", texto)

    for ruta in _RE_RUTA_UNC.findall(resto):
        anadir("ruta", ruta)
        _anadir_host(ruta, anadir)
    resto = _RE_RUTA_UNC.sub(" ", resto)

    for ruta in _RE_RUTA_WIN_ENTRE_COMILLAS.findall(resto):
        anadir("ruta", ruta.rstrip())
    resto = _RE_RUTA_WIN_ENTRE_COMILLAS.sub(" ", resto)

    for patron in (_RE_RUTA_WIN, _RE_RUTA_VARIABLE, _RE_RUTA_LINUX):
        for ruta in patron.findall(resto):
            anadir("ruta", ruta.rstrip(".)"))
        resto = patron.sub(" ", resto)

    for h in _RE_HASH.findall(resto):
        anadir("hash", h.lower())

    for correo in _RE_EMAIL.findall(resto):
        anadir("email", correo.lower())
    resto = _RE_EMAIL.sub(" ", resto)

    for ip in _RE_IPV4.findall(resto):
        tipo = _clasificar_ip(ip)
        if tipo:
            anadir(tipo, ip)
    resto = _RE_IPV4.sub(" ", resto)

    for candidato in _RE_IPV6.findall(resto):
        if "::" not in candidato and candidato.count(":") < 7:
            continue  # sin "::" una IPv6 necesita 8 grupos: evita horas y MAC
        if len(candidato) < 3 or not _RE_HEX.search(candidato):
            continue  # "::" suelto: el operador estático de PowerShell, [IO.File]::Open
        tipo = _clasificar_ip(candidato)
        if tipo:
            anadir(tipo, candidato.lower())
            resto = resto.replace(candidato, " ")

    for dominio in _RE_DOMINIO.findall(resto):
        if _es_dominio_suelto(dominio):
            anadir("dominio", dominio.lower())

    return encontrados


def extraer_indicadores(
    comando: str, salida: str | None = None, decodificado: str | None = None
) -> list[Indicador]:
    """Indicadores de un evento, del comando, su salida y el comando
    decodificado, sin duplicados.

    Si el mismo valor aparece en varios sitios se conserva el primero en este
    orden: comando, decodificado, salida. Lo que ejecutó el atacante manda
    sobre el resultado observado.
    """
    encontrados = (
        _extraer_de(comando, "comando")
        + _extraer_de(decodificado or "", "decodificado")
        + _extraer_de(salida or "", "salida")
    )

    unicos: dict[tuple[str, str], Indicador] = {}
    for ind in encontrados:
        clave = (ind.tipo, ind.valor)
        if clave not in unicos:
            unicos[clave] = ind
    return list(unicos.values())
