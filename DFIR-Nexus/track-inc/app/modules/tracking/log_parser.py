r"""
Parser de logs para el Módulo 3 (CU-03: "Analizar logs de tracking").

Formato de entrada esperado: texto plano, una entrada por línea, del
estilo de lo que describe la documentación del equipo:

    2026-08-10 14:32:05  powershell.exe -EncodedCommand SQBFAFgA...
    2026-08-10 14:32:11  net user hacker P@ssw0rd123! /add
    2026-08-10 14:32:20  net localgroup administrators hacker /add

Si un comando produjo salida, esta va en las líneas siguientes, indentadas:

    2026-08-14 03:11:19  whoami
        CORP\svc_backup

La indentación es lo que las distingue de un comando nuevo. No todos los
comandos producen salida; los que no la tienen quedan con `output` a None.

Es deliberadamente tolerante: si una línea no trae timestamp reconocible,
no se descarta — hereda la hora de la línea anterior que sí la tenía
(ver `_inferir_horas`) y se marca como inferida. Preferimos una evidencia
con timestamp aproximado a perder la evidencia por completo.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone, tzinfo

from agent.evidence.models import EventSource, HostInfo, RawEvent

# --- formatos de marca temporal al principio de línea ---------------------
# Todos admiten ir entre corchetes y exigen un espacio (o fin de línea) detrás:
# así "2026-08-14T03:11:19.123Z whoami" ya no deja ".123Z whoami" como comando.

# ISO 8601 y variantes: 2026-08-14 03:11:19, 2026-08-14T03:11:19.123Z,
# 2026-08-14T03:11:19+02:00, 2026/08/14 03:11:19
_RE_ISO = re.compile(
    r"^\[?(?P<y>\d{4})[-/](?P<mo>\d{2})[-/](?P<d>\d{2})[ T](?P<h>\d{1,2}):(?P<mi>\d{2}):(?P<s>\d{2})"
    r"(?:[.,](?P<frac>\d{1,9}))?\s?(?P<zona>Z|[+-]\d{2}:?\d{2})?\]?(?=\s|$)"
)
# Día/mes/año (formato español y del Visor de eventos): 14/08/2026 3:11:22.
# Si el mes no es válido se prueba mes/día (08/14/2026), el orden de EE. UU.
_RE_DMY = re.compile(
    r"^\[?(?P<a>\d{1,2})/(?P<b>\d{1,2})/(?P<y>\d{4})[ T,]\s*(?P<h>\d{1,2}):(?P<mi>\d{2}):(?P<s>\d{2})\]?(?=\s|$)"
)
# syslog: "Aug 14 03:11:21 host sshd[1]: ..." (sin año)
_MESES = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], start=1
)}
_RE_SYSLOG = re.compile(
    r"^(?P<mes>Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(?P<d>\d{1,2})\s+"
    r"(?P<h>\d{2}):(?P<mi>\d{2}):(?P<s>\d{2})(?=\s|$)",
    re.IGNORECASE,
)

# --- usuario asociado a la línea ------------------------------------------
_USER_PATTERNS = [
    # Logs de autenticación (sshd, PAM). Van primero porque "sudo: pepe : ... ;
    # USER=root" trae los dos: quien ejecuta (pepe) y la cuenta a la que salta
    # (root), y el que identifica al responsable de la línea es el primero.
    re.compile(r"\bsudo:\s*([A-Za-z0-9._\-\\]+)\s*:", re.IGNORECASE),
    # "Accepted password for root from 10.0.0.5", "Failed password for invalid
    # user admin from ...": la cuenta contra la que se intenta entrar.
    re.compile(
        r"\b(?:accepted|failed)\s+(?:password|publickey|none|keyboard-interactive)"
        r"\s+for\s+(?:invalid\s+user\s+)?([A-Za-z0-9._\-\\$]+)",
        re.IGNORECASE,
    ),
    re.compile(r"\binvalid\s+user\s+([A-Za-z0-9._\-\\$]+)", re.IGNORECASE),
    # "session opened for user root", "New session 7 of user mlopez." El grupo
    # no se queda el punto final: sería parte del nombre de la cuenta.
    re.compile(r"\b(?:for|of)\s+user\s+([A-Za-z0-9._\-\\$]*[A-Za-z0-9_$])", re.IGNORECASE),
    # "user:jsmith", "/user:CORP\admin" (runas). No detrás de ? o &: en una URL
    # (`?user=pepe`) es un parámetro, no quien ejecuta el comando.
    re.compile(r"(?<![\w?&])user[:=]\s*([^\s,;&]+)", re.IGNORECASE),
    re.compile(r"(?<![\w?&])usuario[:=]\s*([^\s,;&]+)", re.IGNORECASE),
    # "as DOMAIN\user"
    re.compile(r"\bas\s+([A-Za-z0-9_\-\.\\]+)\\([A-Za-z0-9_\-\.]+)\b"),
    # psexec/paexec -u CORP\adm (solo en ellos: en curl, -u lleva usuario:contraseña)
    re.compile(r"\b(?:ps|pa)exec(?:64)?(?:\.exe)?\b.*?\s-u\s+\"?([^\s\"]+)", re.IGNORECASE),
    # schtasks /ru SYSTEM
    re.compile(r"\bschtasks(?:\.exe)?\b.*?\s/ru\s+\"?([^\s\"]+)", re.IGNORECASE),
]
_RE_WHOAMI = re.compile(r"^whoami(?:\.exe)?$", re.IGNORECASE)
_RE_CUENTA = re.compile(r"^[\w.\-]+\\[\w.\-$]+$")
_MAX_USUARIO = 100  # tracking_events.usuario_detectado es VARCHAR(100)


def _zona_explicita(texto: str | None) -> tzinfo | None:
    if not texto:
        return None
    if texto == "Z":
        return timezone.utc
    signo = 1 if texto[0] == "+" else -1
    digitos = texto[1:].replace(":", "")
    return timezone(signo * timedelta(hours=int(digitos[:2]), minutes=int(digitos[2:])))


def _anio_syslog(mes: int, dia: int, ahora: datetime) -> int:
    """syslog no trae año: el actual, salvo que la fecha quede en el futuro
    (un log de diciembre analizado en enero), en cuyo caso el anterior."""
    anio = ahora.year
    try:
        if datetime(anio, mes, dia, tzinfo=timezone.utc) > ahora + timedelta(days=1):
            anio -= 1
    except ValueError:
        pass
    return anio


def _extract_timestamp(line: str, zona: tzinfo = timezone.utc) -> tuple[datetime | None, str]:
    """Devuelve (timestamp_o_None, resto_de_la_línea_sin_el_timestamp).

    La hora se interpreta en `zona` (la del equipo que escribió el log) salvo
    que la propia marca traiga zona (`Z`, `+02:00`), y se devuelve en UTC.
    """
    ts: datetime | None = None
    fin = 0

    if m := _RE_ISO.match(line):
        frac = (m["frac"] or "0")[:6].ljust(6, "0")
        try:
            ts = datetime(int(m["y"]), int(m["mo"]), int(m["d"]), int(m["h"]), int(m["mi"]), int(m["s"]), int(frac))
            ts = ts.replace(tzinfo=_zona_explicita(m["zona"]) or zona)
            fin = m.end()
        except ValueError:
            ts = None
    elif m := _RE_DMY.match(line):
        a, b = int(m["a"]), int(m["b"])
        for dia, mes in ((a, b), (b, a)):
            try:
                ts = datetime(int(m["y"]), mes, dia, int(m["h"]), int(m["mi"]), int(m["s"]), tzinfo=zona)
                fin = m.end()
                break
            except ValueError:
                continue
    elif m := _RE_SYSLOG.match(line):
        mes, dia = _MESES[m["mes"].lower()], int(m["d"])
        try:
            anio = _anio_syslog(mes, dia, datetime.now(timezone.utc))
            ts = datetime(anio, mes, dia, int(m["h"]), int(m["mi"]), int(m["s"]), tzinfo=zona)
            fin = m.end()
        except ValueError:
            ts = None

    if ts is None:
        return None, line.strip()
    return ts.astimezone(timezone.utc), line[fin:].strip()


def _extract_user(line: str) -> str | None:
    for pattern in _USER_PATTERNS:
        match = pattern.search(line)
        if match:
            return match.group(match.lastindex)[:_MAX_USUARIO]
    return None


def _usuario_de_whoami(comando: str, salida: list[str]) -> str | None:
    """La salida de `whoami` ES el usuario con el que se ejecutaba: el dato más
    fiable del log, y antes se ignoraba."""
    if _RE_WHOAMI.match(comando) and salida and _RE_CUENTA.match(salida[0]):
        return salida[0][:_MAX_USUARIO]
    return None


def _inferir_horas(entradas: list[dict], fallback_base: datetime) -> None:
    """Da hora a las líneas que no la traen, sin inventar fechas.

    Una línea sin marca temporal hereda la hora de la anterior que sí la
    tenía: es la mejor cota real (ocurrió después de esa). Las del principio
    del fichero, antes de la primera marca, toman la de esa primera marca.

    Antes recibían la hora del análisis ("ahora"), y así se guardaban en
    `tracking_events`: un comando del incidente del 14 de agosto aparecía en
    Timeline como ocurrido el día en que se subió el log. Solo si el fichero
    no trae NINGUNA marca temporal se usa "ahora" (con un milisegundo por
    línea para conservar el orden), porque no hay nada mejor.
    """
    conocidas = [e["timestamp"] for e in entradas if e["timestamp"] is not None]
    if not conocidas:
        for e in entradas:
            e["timestamp"] = fallback_base + timedelta(milliseconds=e["line_number"])
        return

    anterior = conocidas[0]
    for e in entradas:
        if e["timestamp"] is None:
            e["timestamp"] = anterior
        else:
            anterior = e["timestamp"]


def parse_log_text(
    text: str,
    fuente_log: str,
    agent_id: str = "tracking-module",
    zona: tzinfo = timezone.utc,
) -> list[RawEvent]:
    """
    Convierte el contenido de un fichero de log en una lista de
    RawEvent (source=LOG), listos para pasar por el clasificador.
    Líneas vacías se ignoran. `zona` es la zona horaria en que están
    escritas las horas del log; los timestamps resultantes van en UTC.
    """
    host_info = HostInfo(agent_id=agent_id, hostname="n/a", os="n/a")
    events: list[RawEvent] = []
    fallback_base = datetime.now(timezone.utc)

    # Se recogen primero las entradas para poder adjuntar a cada comando las
    # líneas de salida que vengan debajo, antes de construir el RawEvent.
    entradas: list[dict] = []

    # Un BOM que llegue hasta aquí (texto ya decodificado por otro camino)
    # impediría reconocer la hora de la primera línea.
    text = text.removeprefix("\ufeff")

    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue

        indentada = raw_line[:1] in (" ", "\t")
        timestamp, command = _extract_timestamp(line, zona)
        # Una línea con solo la marca temporal no tiene comando: se conserva
        # la línea entera para no producir un evento vacío.
        command = command or line

        # Línea indentada y sin marca temporal propia: es la salida del
        # comando anterior, no un comando nuevo. Requerir la indentación
        # evita romper el comportamiento tolerante: una línea sin sangrar
        # y sin timestamp sigue siendo su propio evento.
        if indentada and timestamp is None and entradas:
            entradas[-1]["salida"].append(line)
            continue

        had_timestamp = timestamp is not None

        entradas.append({
            "command": command,
            "raw_line": line,
            "line_number": line_number,
            "user": _extract_user(command),
            "timestamp": timestamp,
            "timestamp_inferred": not had_timestamp,
            "salida": [],
        })

    _inferir_horas(entradas, fallback_base)

    for entrada in entradas:
        entrada["user"] = entrada["user"] or _usuario_de_whoami(entrada["command"], entrada["salida"])
        events.append(RawEvent(
            source=EventSource.LOG,
            event_type="command",
            timestamp=entrada["timestamp"],
            host_info=host_info,
            payload={
                "command": entrada["command"],
                "raw_line": entrada["raw_line"],
                "line_number": entrada["line_number"],
                "user": entrada["user"],
                "timestamp_inferred": entrada["timestamp_inferred"],
                # None si el comando no produjo salida en el log: no todos
                # la tienen, y así el campo se distingue de una salida vacía.
                "output": "\n".join(entrada["salida"]) or None,
            },
        ))

    return events
