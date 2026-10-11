"""
Cómo se guarda la hora de un evento.

`tracking_events.hora` es un DATETIME sin zona horaria (esquema de
CLAUDE.md). Para que no sea ambiguo, TODO lo que se guarda va en UTC, sin
zona y a segundos:

  - En UTC: si la hora llega con otra zona (+02:00), se convierte. Guardar
    la hora "de pared" tal cual mezclaba zonas en la misma columna.
  - A segundos: los logs no traen más precisión, y MySQL redondea los
    microsegundos de un DATETIME. Descartarlos antes evita que lo guardado
    difiera de lo enviado (y de la huella de la cadena de integridad).
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

_RE_ZONA = re.compile(r"^(?P<signo>[+-])(?P<h>0\d|1[0-4]):(?P<m>[0-5]\d)$")


def parsear_zona(texto: str | None) -> timezone:
    """Zona horaria en la que están escritas las horas de un log.

    Se acepta `UTC` o un desplazamiento `+02:00` / `-05:00`. No se usan
    nombres IANA (`Europe/Madrid`) a propósito: en Windows requieren el
    paquete `tzdata`, y para un log basta con el desplazamiento que tenía
    la máquina cuando lo escribió. Lanza ValueError si no es válida.
    """
    valor = (texto or "UTC").strip().upper()
    if valor in ("UTC", "Z", "+00:00", "-00:00"):
        return timezone.utc
    m = _RE_ZONA.match(valor)
    if not m:
        raise ValueError(
            f"Zona horaria no válida: '{texto}'. Usa 'UTC' o un desplazamiento como '+02:00'."
        )
    delta = timedelta(hours=int(m["h"]), minutes=int(m["m"]))
    return timezone(delta if m["signo"] == "+" else -delta)


def a_utc_sin_zona(hora: datetime) -> datetime:
    """Normaliza una hora a la forma exacta en que queda en la base de datos.

    Una hora sin zona se da por UTC, que es lo que el parser produce y lo
    que la base de datos contiene.
    """
    if hora.tzinfo is not None:
        hora = hora.astimezone(timezone.utc).replace(tzinfo=None)
    return hora.replace(microsecond=0)
