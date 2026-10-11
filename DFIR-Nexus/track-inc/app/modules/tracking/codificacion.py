"""
Decodificación de los ficheros de log subidos.

Antes solo se aceptaba UTF-8 estricto, y en Windows eso deja fuera justo los
logs más habituales:

  - UTF-8 con BOM (Bloc de notas, `Out-File -Encoding utf8` en PowerShell 5.1):
    se aceptaba, pero el BOM quedaba pegado a la primera línea y su hora no
    se reconocía.
  - UTF-16 LE, lo que genera por defecto `Out-File` / `>` en PowerShell 5.1:
    rechazado con 400.
  - cp1252 (ANSI de Windows en español): una ruta con "José" daba 400.

Orden de detección: BOM explícito, UTF-16 sin BOM (bytes nulos alternos),
UTF-8 y, como último recurso, cp1252. Lo que tras decodificar sigue teniendo
caracteres de control no es texto y se rechaza: es preferible un error claro
a analizar basura binaria como si fueran comandos.
"""

from __future__ import annotations

import codecs


class FicheroNoTextoError(ValueError):
    """El contenido no es un log de texto legible."""


def _parece_utf16_sin_bom(datos: bytes) -> str | None:
    muestra = datos[:4000]
    if len(muestra) < 4:
        return None
    pares, impares = muestra[0::2], muestra[1::2]
    # Texto ASCII en UTF-16: uno de cada dos bytes es nulo.
    if impares.count(0) > len(impares) * 0.4 and pares.count(0) < len(pares) * 0.1:
        return "utf-16-le"
    if pares.count(0) > len(pares) * 0.4 and impares.count(0) < len(impares) * 0.1:
        return "utf-16-be"
    return None


def _es_texto(texto: str) -> bool:
    control = sum(1 for c in texto[:20000] if ord(c) < 32 and c not in "\t\n\r\f\v")
    return control == 0


def decodificar_log(datos: bytes) -> tuple[str, str]:
    """Devuelve (texto, codificación detectada). Lanza FicheroNoTextoError."""
    candidatas: list[str] = []
    if datos.startswith(codecs.BOM_UTF8):
        candidatas = ["utf-8-sig"]
    elif datos.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)):
        candidatas = ["utf-16"]
    else:
        sin_bom = _parece_utf16_sin_bom(datos)
        candidatas = [sin_bom] if sin_bom else ["utf-8", "cp1252"]

    for codificacion in candidatas:
        try:
            texto = datos.decode(codificacion)
        except UnicodeDecodeError:
            continue
        if _es_texto(texto):
            return texto, codificacion

    raise FicheroNoTextoError(
        "El fichero no parece un log de texto: se admite UTF-8 (con o sin BOM), UTF-16 o Windows-1252."
    )
