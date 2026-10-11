"""
Compone un informe a partir de una fixture y escribe los cuatro formatos en
disco, **sin base de datos**. Sirve para ver la maqueta del informe sin
levantar MySQL ni aplicar migraciones.

    python scripts/previsualizar_informe.py fixtures/caso_003_fraude_bec.json
    python scripts/previsualizar_informe.py fixtures/caso_003_fraude_bec.json --con-ia

Acepta además el mismo alcance que `POST /reports/generate`, para poder ver un
informe recortado sin montar nada:

    python scripts/previsualizar_informe.py fixtures/caso_003_fraude_bec.json         --anexos evidences,tracking --desde 2026-08-03 --severidad-minima alta

Por defecto la narrativa (hallazgos y conclusiones) es un **texto de relleno**,
no la redacta la IA: así la previsualización no gasta crédito ni necesita
`ANTHROPIC_API_KEY`. El propio documento lo dice en su portada para que nadie
confunda una previsualización con un informe emitido. Con `--con-ia` se llama
a Anthropic de verdad y la narrativa es la real.

Lo que se previsualiza es exactamente lo que produciría el módulo contra la
base de datos: el mapeo JSON → objeto lo comparte con `load_fixtures.py` y los
renderizadores son los mismos que usa `POST /reports/generate`. Lo único que
no ocurre es guardar la fila en `reports`.
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.modules.reports import (  # noqa: E402
    ai_narrative,
    docx_builder,
    document,
    html_builder,
    json_builder,
    pdf_builder,
)
from app.modules.reports.osint import FuenteOsint, desde_osint_result  # noqa: E402
from app.modules.reports.opciones import (  # noqa: E402
    TODOS_LOS_ANEXOS,
    TODOS_LOS_FORMATOS,
    Anexo,
    FormatoInforme,
    OpcionesInforme,
)
from app.modules.shared.models import Severidad  # noqa: E402
from scripts.load_fixtures import construir_objetos  # noqa: E402

NARRATIVA_RELLENO = ai_narrative.Narrativa(
    hallazgos=(
        "TEXTO DE RELLENO — esta previsualización no ha pasado por la IA.\n\n"
        "En un informe real, este apartado contiene la exposición de los hechos "
        "acreditados a partir de la cronología, con la referencia [E1], [E2]… del "
        "evento del que procede cada afirmación. Se genera con --con-ia."
    ),
    conclusiones=(
        "TEXTO DE RELLENO — esta previsualización no ha pasado por la IA.\n\n"
        "En un informe real, este apartado contiene el juicio pericial que se "
        "desprende de los hallazgos anteriores, separado de ellos precisamente "
        "para que se distinga el hecho de su interpretación."
    ),
)


def previsualizar(
    fixture: Path,
    destino: Path,
    con_ia: bool,
    opciones: OpcionesInforme | None = None,
) -> Path:
    opciones = opciones or OpcionesInforme()
    data = json.loads(fixture.read_text(encoding="utf-8"))
    caso, hijos = construir_objetos(data)

    # Sin base de datos no hay claves autoincrementales: se numeran a mano
    # para que la columna «Ref.» de la cronología y los anexos cuadren.
    caso.id = data["case"].get("id", 1)
    for filas in hijos.values():
        for indice, fila in enumerate(filas, start=1):
            # Solo se numera lo que venga sin identificador. Pisar el que trae
            # la fixture hacia que el Anexo C dijese «2» donde la columna
            # «Ref.» de la cronologia decia «tracking#evt-7f3a9c2e»: dos tablas
            # del mismo informe nombrando distinto el mismo registro, que es
            # exactamente la trazabilidad que el informe promete tener.
            if fila.id is None:
                fila.id = indice
            fila.case_id = caso.id

    timeline = sorted(hijos["timeline_events"], key=lambda e: e.orden)
    if not timeline:
        raise SystemExit(
            f"{fixture.name} no tiene timeline_events: el módulo devolvería un 422 "
            f"(un informe sin cronología no es defendible)."
        )

    # Mismo recorte y en el mismo orden que el servicio: primero se selecciona
    # y después se redacta, para que la narrativa no hable de eventos que el
    # documento no imprime.
    # Las fixtures traen los indicadores en el formato de `osint_results`, que
    # es el del modelo de datos oficial. Se normalizan igual que hace el
    # repositorio para que la previsualización recorra el mismo camino que una
    # generación de verdad (ver app/modules/reports/osint.py).
    indicadores = [desde_osint_result(o) for o in hijos["osint_results"]]
    seleccion = opciones.aplicar(
        timeline, hijos["evidences"], indicadores, hijos["tracking_events"]
    )
    if not seleccion.timeline_events:
        raise SystemExit(
            f"El alcance elegido no deja ningún evento de los {len(timeline)} que tiene "
            f"{fixture.name}: el módulo devolvería un 422."
        )
    timeline = seleccion.timeline_events

    if con_ia:
        narrativa = ai_narrative.generar_narrativa(caso, timeline, None)
    else:
        narrativa = NARRATIVA_RELLENO
        caso.nombre = f"{caso.nombre} [PREVISUALIZACIÓN]"

    doc = document.construir_documento(
        case=caso,
        timeline_events=timeline,
        narrativa=narrativa,
        generado_por="Previsualización local",
        version=1,
        generado_el=datetime.now(timezone.utc),
        evidences=seleccion.evidences,
        osint_results=seleccion.osint_results,
        fuente_osint=FuenteOsint.RESULTS,
        tracking_events=seleccion.tracking_events,
        notas=None,
        opciones=opciones,
    )

    destino.mkdir(parents=True, exist_ok=True)
    salidas = {
        "pdf": pdf_builder.construir_pdf,
        "docx": docx_builder.construir_docx,
        "html": html_builder.construir_html,
        "json": json_builder.construir_json,
    }
    for extension, render in salidas.items():
        if extension not in {f.value for f in opciones.formatos}:
            continue
        ruta = destino / f"{fixture.stem}.{extension}"
        ruta.write_bytes(render(doc))
        print(f"  {ruta}  ({ruta.stat().st_size:,} bytes)")

    return destino


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fixture", type=Path, help="Ruta al fichero JSON de fixture")
    parser.add_argument(
        "--destino",
        type=Path,
        default=Path("storage/previsualizacion"),
        help="Carpeta de salida (por defecto storage/previsualizacion)",
    )
    parser.add_argument(
        "--con-ia",
        action="store_true",
        help="Redacta la narrativa con Anthropic (necesita ANTHROPIC_API_KEY y gasta crédito)",
    )
    parser.add_argument(
        "--anexos",
        help="Anexos incluidos, separados por comas: evidences,osint,tracking",
    )
    parser.add_argument(
        "--formatos",
        help="Formatos que se componen, separados por comas. El PDF siempre entra",
    )
    parser.add_argument("--desde", help="Documenta solo los hechos posteriores (ISO 8601)")
    parser.add_argument("--hasta", help="Documenta solo los hechos anteriores (ISO 8601)")
    parser.add_argument(
        "--severidad-minima",
        choices=[s.value for s in Severidad],
        help="Descarta los eventos de tracking por debajo de esta severidad",
    )
    parser.add_argument(
        "--solo-osint-con-detecciones",
        action="store_true",
        help="Descarta los indicadores OSINT que ninguna fuente marcó",
    )
    args = parser.parse_args()

    def _conjunto(valor, tipo, por_defecto):
        if not valor:
            return por_defecto
        return frozenset(tipo(v.strip()) for v in valor.split(",") if v.strip())

    try:
        opciones = OpcionesInforme(
            anexos=_conjunto(args.anexos, Anexo, TODOS_LOS_ANEXOS),
            formatos=_conjunto(args.formatos, FormatoInforme, TODOS_LOS_FORMATOS),
            desde=datetime.fromisoformat(args.desde) if args.desde else None,
            hasta=datetime.fromisoformat(args.hasta) if args.hasta else None,
            severidad_minima=(
                Severidad(args.severidad_minima) if args.severidad_minima else None
            ),
            solo_osint_con_detecciones=args.solo_osint_con_detecciones,
        )
    except ValueError as exc:
        # El mismo mensaje con el que la API respondería 422: el alcance se
        # valida en un solo sitio (opciones.py) y aquí solo se muestra.
        raise SystemExit(f"Alcance no válido: {exc}") from exc

    if not args.con_ia:
        print("Narrativa de relleno (sin IA). Usa --con-ia para la redacción real.\n")
    if opciones.hay_recorte:
        print(f"Alcance recortado: {opciones.descripcion_alcance()}\n")
    previsualizar(args.fixture, args.destino, args.con_ia, opciones)
