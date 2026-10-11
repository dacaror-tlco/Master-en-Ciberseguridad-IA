"""
Decodificación de `powershell -EncodedCommand`.

Es la ofuscación más habitual en un incidente: el comando real va en base64
(UTF-16LE) y el log solo muestra `powershell -enc SQBFAFgAIAAoAE4AZQB3…`. Sin
decodificarlo, el perito no ve la URL de descarga ni la IP del C2, y los
indicadores que esconde no aparecen en ningún sitio.

Nunca se ejecuta nada: solo se decodifica el texto.
"""

from __future__ import annotations

import base64
import binascii
import re

# PowerShell acepta cualquier prefijo no ambiguo de -EncodedCommand (-e, -ec,
# -en, -enc, -enco…) y también con barra (/enc). -ExecutionPolicy no casa:
# tras la "e" viene una "x", no un espacio.
_FLAG = r"[-/]e(?:c|n(?:c(?:o(?:d(?:e(?:d(?:c(?:o(?:m(?:m(?:a(?:n(?:d)?)?)?)?)?)?)?)?)?)?)?)?)?"
_RE_ENCODED = re.compile(
    rf"\b(?:powershell|pwsh)(?:\.exe)?\b.*?\s{_FLAG}\s+[\"']?(?P<b64>[A-Za-z0-9+/]{{8,}}={{0,2}})",
    re.IGNORECASE,
)
_MAX_DECODIFICADO = 20000


def decodificar_encoded_command(comando: str) -> str | None:
    """Devuelve el comando oculto en `-EncodedCommand`, o None si no lo hay o
    no es un base64 UTF-16LE legible."""
    m = _RE_ENCODED.search(comando)
    if not m:
        return None
    b64 = m["b64"]
    try:
        datos = base64.b64decode(b64 + "=" * (-len(b64) % 4), validate=True)
        texto = datos.decode("utf-16-le")
    except (binascii.Error, UnicodeDecodeError, ValueError):
        return None
    texto = texto.strip("\x00").strip()
    if not texto or any(ord(c) < 32 and c not in "\t\r\n" for c in texto):
        return None
    return texto[:_MAX_DECODIFICADO]
