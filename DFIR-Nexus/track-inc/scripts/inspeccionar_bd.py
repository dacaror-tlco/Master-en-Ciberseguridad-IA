"""
Inspector de SOLO LECTURA de la base de datos configurada en .env.

Pensado para mirar la base compartida del equipo sin instalar ningun cliente:
usa el venv del propio modulo. No modifica nada — solo ejecuta SHOW y SELECT.

Uso, desde la raiz del modulo:

    venv\\Scripts\\python.exe scripts\\inspeccionar_bd.py              # resumen
    venv\\Scripts\\python.exe scripts\\inspeccionar_bd.py tracking_events
    venv\\Scripts\\python.exe scripts\\inspeccionar_bd.py cases --filas 20

La contrasena nunca se imprime: la URL sale enmascarada.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text  # noqa: E402

from app.core.database import DATABASE_URL, engine  # noqa: E402

# Tablas de las que este modulo es responsable; el resto son de companeros.
TABLAS_PROPIAS = {"tracking_events"}


def url_enmascarada() -> str:
    return re.sub(r"//[^:]+:[^@]+@", "//***:***@", DATABASE_URL)


def resumen(con) -> None:
    print(f"Conectado a: {url_enmascarada()}")
    print(f"Servidor   : {con.execute(text('select version()')).scalar()}")
    print(f"Base       : {con.execute(text('select database()')).scalar()}")
    print()

    tablas = [r[0] for r in con.execute(text("show tables"))]
    print(f"{'TABLA':<34} {'FILAS':>8}   DE QUIEN")
    print("-" * 62)
    for t in tablas:
        n = con.execute(text(f"select count(*) from `{t}`")).scalar()
        if t in TABLAS_PROPIAS:
            duenio = "<- tuya (Modulo 3)"
        elif t.startswith("alembic_version"):
            duenio = "historial de migraciones"
        else:
            duenio = "otro modulo"
        print(f"{t:<34} {n:>8}   {duenio}")

    print()
    print("Historial de migraciones por modulo:")
    for t in tablas:
        if t.startswith("alembic_version"):
            v = [r[0] for r in con.execute(text(f"select version_num from `{t}`"))]
            print(f"  {t:<32} {v}")


def detalle(con, tabla: str, filas: int) -> None:
    existentes = {r[0] for r in con.execute(text("show tables"))}
    if tabla not in existentes:
        print(f"La tabla '{tabla}' no existe. Disponibles: {', '.join(sorted(existentes))}")
        return

    print(f"=== {tabla} — estructura ===")
    for r in con.execute(text(f"describe `{tabla}`")):
        nulo = "NULL" if r[2] == "YES" else "NOT NULL"
        print(f"  {r[0]:<20} {str(r[1]):<44} {nulo}")

    total = con.execute(text(f"select count(*) from `{tabla}`")).scalar()
    print(f"\n=== {tabla} — {min(filas, total)} de {total} filas ===")
    resultado = con.execute(text(f"select * from `{tabla}` limit :n"), {"n": filas})
    columnas = list(resultado.keys())
    print("  " + " | ".join(c[:18].ljust(18) for c in columnas))
    print("  " + "-" * (21 * len(columnas)))
    for fila in resultado:
        print("  " + " | ".join(str(v)[:18].ljust(18) for v in fila))


def main() -> None:
    p = argparse.ArgumentParser(description="Inspector de solo lectura de la BD del proyecto.")
    p.add_argument("tabla", nargs="?", help="tabla a detallar; sin argumento, muestra el resumen")
    p.add_argument("--filas", type=int, default=10, help="filas a mostrar (por defecto 10)")
    args = p.parse_args()

    with engine.connect() as con:
        if args.tabla:
            detalle(con, args.tabla, args.filas)
        else:
            resumen(con)


if __name__ == "__main__":
    main()
