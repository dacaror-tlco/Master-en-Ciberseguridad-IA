"""
Renderizado del informe a HTML.

Pensado para revisar el informe en pantalla y para imprimirlo desde el
navegador, no para incrustarlo en la aplicación: el fichero es autónomo
(estilos en línea, sin recursos externos), de modo que sigue leyéndose
igual dentro de diez años en una máquina sin red, que es justo lo que se le
pide a un documento pericial archivado.

Todo el texto pasa por `html.escape`: procede de la base de datos y del LLM,
así que hay que asumir que contiene `<`, `&` o comillas.
"""
from html import escape

from app.modules.reports.document import (
    Documento,
    Espacio,
    Parrafo,
    SaltoPagina,
    Tabla,
    Titulo,
)

_ETIQUETA_TITULO = {0: "h1", 1: "h2", 2: "h3"}

#: Política de seguridad de contenido del propio documento.
#:
#: El escapado es la defensa principal, pero el informe reproduce texto que
#: viene de los Módulos 1 a 4 —nombres de dominio, líneas de log, descripciones
#: de evidencia—, es decir, contenido que un atacante puede haber influido: si
#: alguien registra un dominio con una etiqueta en el nombre, ese nombre acaba
#: impreso en el Anexo B. Con esta política, aunque un día se escapase mal, el
#: navegador no ejecutaría nada: `default-src 'none'` bloquea scripts, imágenes
#: y peticiones de red, y solo se permite el CSS incrustado, que no ejecuta.
#:
#: Va como `<meta>` y no solo como cabecera a propósito: el informe se archiva
#: y se abre desde disco o desde el correo, donde no hay respuesta HTTP que
#: lleve cabeceras. La cabecera se añade además al servirlo (ver routes.py).
CSP_INFORME = (
    "default-src 'none'; "
    "style-src 'unsafe-inline'; "  # el <style> del propio documento
    "base-uri 'none'; "
    "form-action 'none'"
)

_ESTILOS = """
:root { color-scheme: light; }
body {
  font-family: -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  max-width: 46rem; margin: 0 auto; padding: 3rem 1.5rem 6rem;
  color: #16181d; background: #fff; line-height: 1.65;
}
h1 { font-size: 1.9rem; text-align: center; margin: 0 0 2rem; }
h2 { font-size: 1.4rem; margin: 3rem 0 1rem; }
h3 {
  font-size: 1.05rem; margin: 2.25rem 0 .75rem;
  padding-bottom: .35rem; border-bottom: 1px solid #d8dbe2;
}
p { margin: 0 0 .8rem; text-align: justify; }
/* El anexo B tiene ocho columnas: en un móvil no cabe, y encogerlas más lo
   haría ilegible. Que la tabla haga scroll propio en vez de desbordar la
   página, que es lo que rompe la lectura del resto del informe. */
.tabla { overflow-x: auto; margin: .5rem 0 1.25rem; }
table {
  width: 100%; border-collapse: collapse; min-width: 32rem;
  font-size: .82rem; line-height: 1.45;
}
th, td { border: 1px solid #b9bec9; padding: .4rem .55rem; vertical-align: top; }
th { background: #20242f; color: #fff; text-align: left; font-weight: 600; }
td { word-break: break-word; }
tbody tr:nth-child(even) { background: #f5f6f8; }
.salto { page-break-before: always; }
footer {
  margin-top: 4rem; padding-top: 1rem; border-top: 1px solid #d8dbe2;
  font-size: .75rem; color: #6b7280; display: flex; justify-content: space-between;
}
@media print {
  body { max-width: none; padding: 0; }
  h2, h3 { page-break-after: avoid; }
  tr { page-break-inside: avoid; }
  /* En papel no hay scroll: la tabla tiene que caber entera o partirse. */
  .tabla { overflow: visible; }
  table { min-width: 0; }
}
"""


def construir_html(documento: Documento) -> bytes:
    partes: list[str] = []
    for bloque in documento.bloques:
        match bloque:
            case Titulo(texto=texto, nivel=nivel):
                etiqueta = _ETIQUETA_TITULO[nivel]
                partes.append(f"<{etiqueta}>{escape(texto)}</{etiqueta}>")
            case Parrafo(texto=texto):
                partes.append(f"<p>{escape(str(texto))}</p>")
            case Tabla():
                partes.append(_tabla(bloque))
            case Espacio(alto_cm=alto):
                # Única interpolación del fichero en contexto de atributo. Hoy
                # el valor lo pone `document.py` y siempre es un float, pero
                # forzar el formato numérico hace que siga siendo imposible
                # inyectar aquí aunque alguien haga configurable el espaciado.
                partes.append(f'<div style="height:{float(alto):.2f}cm"></div>')
            case SaltoPagina():
                partes.append('<div class="salto"></div>')

    cuerpo = "\n".join(partes)
    pie = (
        f"<footer><span>{escape(documento.codigo)}</span>"
        f"<span>DFIR Nexus — Módulo 5</span></footer>"
    )
    return (
        "<!DOCTYPE html>\n"
        '<html lang="es">\n<head>\n'
        '<meta charset="utf-8">\n'
        f'<meta http-equiv="Content-Security-Policy" content="{CSP_INFORME}">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{escape(documento.titulo)}</title>\n"
        f"<style>{_ESTILOS}</style>\n"
        f"</head>\n<body>\n{cuerpo}\n{pie}\n</body>\n</html>\n"
    ).encode("utf-8")


def _tabla(bloque: Tabla) -> str:
    # `scope` para que un lector de pantalla asocie cada celda con su columna;
    # en una tabla de ocho columnas como el Anexo B, sin eso los datos se leen
    # como una lista de valores sueltos.
    cabecera = "".join(f'<th scope="col">{escape(c)}</th>' for c in bloque.cabeceras)
    filas = "".join(
        "<tr>" + "".join(f"<td>{escape(str(celda))}</td>" for celda in fila) + "</tr>"
        for fila in bloque.filas
    )
    return (
        f'<div class="tabla"><table><thead><tr>{cabecera}</tr></thead>'
        f"<tbody>{filas}</tbody></table></div>"
    )
