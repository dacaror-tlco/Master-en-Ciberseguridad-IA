"""
Formatos de salida del informe.

Todos se generan en la misma llamada y a partir del mismo `Documento`, no
bajo demanda. La razón es pericial, no técnica: si el DOCX se compusiera al
descargarlo, leería la base de datos tal y como esté *ese* día, y un caso al
que se le han añadido eventos entretanto produciría un documento distinto
bajo el mismo código de informe. Emitiéndolos a la vez, las cuatro copias
comparten contenido, código y sello de tiempo, y cualquiera puede
contrastarlas entre sí.

El PDF es el documento que se firma; los demás son copias en otros soportes.

Desde que el perito puede elegir en cuáles se emite, `FormatoInforme` vive en
`opciones.py` —es vocabulario de una opción— y se reexporta aquí para que
quien lo importaba de este módulo lo siga encontrando. Elegir menos formatos
no rompe lo de arriba: los elegidos se siguen componiendo juntos y del mismo
`Documento`; los no elegidos sencillamente no existen, y pedirlos devuelve
`410` en vez de componerse tarde.
"""
from collections.abc import Callable
from dataclasses import dataclass

from app.modules.reports import docx_builder, html_builder, json_builder, pdf_builder
from app.modules.reports.document import Documento
from app.modules.reports.opciones import FormatoInforme

__all__ = ["FORMATOS", "FORMATO_PRINCIPAL", "Formato", "FormatoInforme"]


@dataclass(frozen=True)
class Formato:
    media_type: str
    render: Callable[[Documento], bytes]


FORMATOS: dict[FormatoInforme, Formato] = {
    FormatoInforme.PDF: Formato("application/pdf", pdf_builder.construir_pdf),
    FormatoInforme.DOCX: Formato(
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        docx_builder.construir_docx,
    ),
    FormatoInforme.HTML: Formato("text/html; charset=utf-8", html_builder.construir_html),
    FormatoInforme.JSON: Formato("application/json", json_builder.construir_json),
}

#: El formato firmado, y el que registra la columna `reports.archivo_pdf`.
FORMATO_PRINCIPAL = FormatoInforme.PDF
