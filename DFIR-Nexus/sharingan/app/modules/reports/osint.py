"""
De dónde salen los indicadores del Anexo B, y cómo se dice en el informe.

El modelo de datos oficial define `osint_results` (Módulo 2). Esa tabla **no la
crea nadie**: ni la rama `scam-shield`, ni la base compartida del equipo, donde
el 2026-09-02 se comprobó que sencillamente no existe. El Módulo 2 mantiene
~10 tablas internas, una por tipo de análisis, y desde el 02/09 publica
`osint_findings` como capa de lectura estable, cuyo commit nombra a informes
como consumidor.

Eso deja al Anexo B con tres situaciones posibles, y **las tres tienen que
poder distinguirse en el documento**. No es un capricho de trazabilidad: un
anexo vacío que dice «no constan consultas OSINT» cuando lo que pasa es que
nadie ha creado la tabla está afirmando algo falso sobre la investigación, y
eso lo lee un juez. Es el mismo criterio con el que un anexo excluido a
petición del perito no imprime «no constan» (ver `opciones.py`).

Las tres, y lo que el informe dice en cada una:

1. `osint_results` existe → es la fuente oficial. El anexo se comporta como
   siempre, y si no hay filas para el caso dice que no constan consultas.
2. `osint_results` no existe pero sí `osint_findings` → se lee el respaldo, y
   el anexo declara que lo que muestra procede de la capa de lectura del
   Módulo 2 y no del registro de la especificación.
3. No hay ninguna de las dos → el anexo declara que el registro OSINT no está
   disponible en este sistema. No dice que no haya consultas, porque no lo
   sabe.

Antes de esto, el caso 3 no era un anexo vacío sino un error 500: el `SELECT`
sobre una tabla inexistente aborta la generación entera, y se ejecuta sin
condiciones, así que ni siquiera excluir el Anexo B lo evitaba.
"""
import enum
from dataclasses import dataclass
from datetime import datetime


class FuenteOsint(str, enum.Enum):
    """De qué tabla salen los indicadores de esta emisión."""

    #: `osint_results`, la del modelo de datos oficial.
    RESULTS = "osint_results"
    #: `osint_findings`, la capa de lectura que publica el Módulo 2.
    FINDINGS = "osint_findings"
    #: Ninguna de las dos existe en esta base de datos.
    NO_DISPONIBLE = "no_disponible"


@dataclass(frozen=True)
class IndicadorOsint:
    """
    Un indicador consultado, ya normalizado, venga de donde venga.

    Los nombres de los campos son los de `osint_results` a propósito: es el
    vocabulario del modelo de datos oficial, y así el resto del módulo —el
    filtro de `opciones.py`, la tabla del Anexo B— no tiene que saber cuál de
    las dos tablas se leyó. Lo que sí depende de la fuente es lo que el informe
    *declara*, y eso viaja aparte, en `RegistroOsint.fuente`.
    """

    id: str
    tipo_indicador: str
    valor: str
    reputacion: str | None
    pais: str | None
    detecciones: int | None
    fuente: str
    fecha_consulta: datetime


@dataclass(frozen=True)
class RegistroOsint:
    """Los indicadores del caso y de qué tabla se han leído."""

    indicadores: list[IndicadorOsint]
    fuente: FuenteOsint


def desde_osint_result(fila) -> IndicadorOsint:
    """Copia directa: la fila ya está en el vocabulario oficial."""
    return IndicadorOsint(
        id=str(fila.id),
        tipo_indicador=fila.tipo_indicador,
        valor=fila.valor,
        reputacion=fila.reputacion,
        pais=fila.pais,
        detecciones=fila.detecciones,
        fuente=fila.fuente,
        fecha_consulta=fila.fecha_consulta,
    )


def desde_osint_finding(fila) -> IndicadorOsint:
    """
    Traduce una fila de `osint_findings` al vocabulario del Anexo B.

    Dos equivalencias que no son exactas y que por eso el anexo explica en su
    nota al pie cuando lee esta fuente:

    * **Reputación ← `risk_level`.** El Módulo 2 no publica la reputación que
      dio cada fuente externa, sino su propia clasificación de riesgo
      (`low`/`medium`/`high`, con cortes en 30 y 60). Se imprime con la
      puntuación al lado para que se vea que es un juicio del Módulo 2 y no el
      veredicto de VirusTotal.
    * **Detecciones ← `flag_count`.** En `osint_results` son las detecciones
      que reportó la fuente; aquí es el número de señales que marcó el análisis
      del Módulo 2. Se parecen, no son lo mismo.

    `pais` no tiene equivalente: `osint_findings` no lo publica. Va a `None`,
    que el anexo imprime como «—», en vez de inventarlo a partir de `details`.
    """
    return IndicadorOsint(
        id=str(fila.id),
        tipo_indicador=fila.subject_type,
        valor=fila.subject_value,
        reputacion=f"{fila.risk_level} ({fila.risk_score})",
        pais=None,
        detecciones=fila.flag_count,
        fuente=f"scam-shield/{fila.case_type}",
        fecha_consulta=fila.analyzed_at,
    )


#: Nota al pie del Anexo B, según de dónde se hayan leído los indicadores. La
#: del caso 1 es la de siempre. Las otras dos existen para que el documento no
#: afirme nada que no le conste.
NOTA_POR_FUENTE: dict[FuenteOsint, str] = {
    FuenteOsint.RESULTS: (
        "La fecha de consulta es relevante: la reputación de un indicador cambia con "
        "el tiempo, por lo que una comprobación posterior puede arrojar un resultado "
        "distinto sin que ello contradiga lo aquí recogido. La respuesta íntegra de "
        "cada fuente queda almacenada en la base de datos del caso "
        "(osint_results.raw_response) y no se reproduce en este anexo por extensión."
    ),
    FuenteOsint.FINDINGS: (
        "La fecha de consulta es relevante: la reputación de un indicador cambia con "
        "el tiempo, por lo que una comprobación posterior puede arrojar un resultado "
        "distinto sin que ello contradiga lo aquí recogido. Los indicadores de este "
        "anexo proceden del registro consolidado de análisis del módulo OSINT "
        "(osint_findings) y no del registro de indicadores previsto en el modelo de "
        "datos del sistema (osint_results), que no está implantado. En consecuencia, "
        "la columna «Reputación» recoge la clasificación de riesgo asignada por ese "
        "módulo —no el veredicto literal de cada fuente externa—, la columna «Det.» "
        "el número de señales que su análisis marcó, y no consta el país asociado al "
        "indicador. El detalle íntegro de cada análisis queda almacenado en la base "
        "de datos del caso y no se reproduce aquí por extensión."
    ),
}

#: Texto del anexo cuando no hay ninguna fila que mostrar. Distinguir estos
#: tres casos es la razón de ser de este módulo.
VACIO_POR_FUENTE: dict[FuenteOsint, str] = {
    FuenteOsint.RESULTS: "No constan consultas OSINT registradas para este caso.",
    FuenteOsint.FINDINGS: (
        "No constan consultas OSINT asociadas a este caso. Se ha consultado el "
        "registro consolidado de análisis del módulo OSINT (osint_findings), en el "
        "que ningún análisis aparece vinculado al presente caso. Esta ausencia no "
        "acredita que no se hayan realizado consultas: acredita que ninguna consta "
        "vinculada a este expediente."
    ),
    FuenteOsint.NO_DISPONIBLE: (
        "No ha sido posible documentar este anexo: el registro de indicadores OSINT "
        "no está disponible en el sistema del que procede este informe. No debe "
        "interpretarse como que no se realizaron consultas en fuentes abiertas, sino "
        "como que este informe no ha podido acceder a su registro."
    ),
}
