"""
Tests del parseo de la página de la CNMV. El HTML de aquí es una
RECONSTRUCCIÓN basada en la estructura observada (columnas Fecha /
Compañías / Documento / Documento en inglés / Observaciones) — no es una
copia exacta del HTML en crudo real, que no pudimos inspeccionar
directamente al construir esto (ver el aviso en cnmv_service.py). Si algo
falla contra la web real, empieza por comparar el HTML real con lo que
se asume aquí.
"""
import pytest

from app.services.cnmv_service import _parse_page

_FAKE_PAGE_WITH_ENTRIES = """
<html><body>
<table>
<tr><th>Fecha</th><th>Compañías sobre las que se advierte</th><th>Documento</th><th>Documento (en inglés)</th><th>Observaciones</th></tr>
<tr>
  <td>18/05/2026</td>
  <td>HTTPS://AICHAINTRADER.COM/ES/<br>AI CHAIN TRADER</td>
  <td>x</td><td>x</td><td></td>
</tr>
<tr>
  <td>11/05/2026</td>
  <td>HTTPS://EUROCAPITAL-EAF.NET (CLON)<br>EURO CAPITAL EAF (CLON)</td>
  <td>x</td><td>x</td>
  <td>NO GUARDA RELACIÓN CON EUROCAPITAL WEALTH MANAGEMENT, EAF, SLU</td>
</tr>
</table>
</body></html>
"""

_FAKE_EMPTY_PAGE = "<html><body><table><tr><th>Fecha</th><th>Compañías</th></tr></table></body></html>"

_FAKE_PAGE_WITHOUT_TABLE = "<html><body><p>Estructura completamente distinta</p></body></html>"


def test_parsea_entradas_correctamente():
    entries = _parse_page(_FAKE_PAGE_WITH_ENTRIES)
    assert len(entries) == 2
    assert entries[0]["fecha"] == "18/05/2026"
    assert "AICHAINTRADER" in entries[0]["companias"]
    assert "AI CHAIN TRADER" in entries[0]["companias"]


def test_extrae_observaciones_cuando_existen():
    entries = _parse_page(_FAKE_PAGE_WITH_ENTRIES)
    assert entries[1]["observaciones"] is not None
    assert "EUROCAPITAL" in entries[1]["observaciones"]


def test_observaciones_vacias_da_none_no_string_vacio():
    entries = _parse_page(_FAKE_PAGE_WITH_ENTRIES)
    assert entries[0]["observaciones"] is None


def test_pagina_vacia_da_lista_vacia():
    assert _parse_page(_FAKE_EMPTY_PAGE) == []


def test_pagina_sin_tabla_reconocible_lanza_error_claro():
    """
    Importante: si la CNMV cambia el HTML, esto debe fallar de forma
    RUIDOSA (excepción clara), no devolver silenciosamente una lista vacía
    que parecería "no hay advertencias" cuando en realidad es "no hemos
    podido leer la página".
    """
    with pytest.raises(RuntimeError, match="No se encontró la tabla"):
        _parse_page(_FAKE_PAGE_WITHOUT_TABLE)


def test_filas_que_no_empiezan_por_fecha_se_ignoran():
    """La cabecera de la tabla u otras filas decorativas no deben colarse como datos."""
    entries = _parse_page(_FAKE_PAGE_WITH_ENTRIES)
    for e in entries:
        assert e["fecha"] not in ("Fecha", "")
