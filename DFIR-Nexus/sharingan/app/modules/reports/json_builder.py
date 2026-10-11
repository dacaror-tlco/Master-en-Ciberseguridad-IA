"""
Renderizado del informe a JSON.

No es un volcado de la base de datos, es el mismo documento que se firma
pero legible por máquina: las secciones en orden, con sus párrafos y sus
tablas. Sirve para archivarlo de forma consultable, para diffear dos
versiones de un informe (`v1` frente a `v2` de un caso) y para que otra
herramienta lo procese sin tener que extraer texto de un PDF.

Se ignoran los bloques que solo existen para maquetar (espacios y saltos de
página): en un formato de datos no significan nada.

`formato_version` está para que un consumidor pueda detectar cambios en esta
estructura sin adivinar; súbelo si cambia la forma del documento.
"""
import json
from dataclasses import dataclass, field

from app.modules.reports.document import Documento, Parrafo, Tabla, Titulo

FORMATO_VERSION = "1"


@dataclass
class _Seccion:
    titulo: str
    nivel: int
    parrafos: list[str] = field(default_factory=list)
    tablas: list[dict] = field(default_factory=list)


def construir_json(documento: Documento) -> bytes:
    secciones: list[_Seccion] = []

    for bloque in documento.bloques:
        match bloque:
            case Titulo(texto=texto, nivel=nivel):
                secciones.append(_Seccion(titulo=texto, nivel=nivel))
            case Parrafo(texto=texto):
                if secciones:
                    secciones[-1].parrafos.append(str(texto))
            case Tabla():
                if secciones:
                    secciones[-1].tablas.append(
                        {
                            "cabeceras": bloque.cabeceras,
                            "filas": [[str(c) for c in fila] for fila in bloque.filas],
                        }
                    )

    contenido = {
        "formato_version": FORMATO_VERSION,
        "informe": {
            "codigo": documento.codigo,
            "case_id": documento.case_id,
            "case_nombre": documento.case_nombre,
            "version": documento.version,
            "generado_por": documento.generado_por,
            "generado_el": documento.generado_el.isoformat(),
            "modelo_ia": documento.modelo_ia,
            "generador": "DFIR Nexus — Módulo 5 (Sharingan)",
        },
        "secciones": [
            {
                "titulo": seccion.titulo,
                "nivel": seccion.nivel,
                "parrafos": seccion.parrafos,
                "tablas": seccion.tablas,
            }
            for seccion in secciones
        ],
    }
    return json.dumps(contenido, ensure_ascii=False, indent=2).encode("utf-8")
