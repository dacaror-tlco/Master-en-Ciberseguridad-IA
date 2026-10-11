"""
Migra los datos de un scamshield.db (SQLite, esquema pre-Nexus) a la base de
datos MySQL nueva (ver app/core/database.py, alembic/).

Uso:

    python scripts/migrate_sqlite_to_mysql.py --sqlite-path /ruta/a/scamshield.db

Requisitos antes de ejecutarlo:
  - Backup del scamshield.db de origen (este script NUNCA escribe en él).
  - `alembic upgrade head` ya aplicado contra la base de datos MySQL destino
    (las tablas deben existir, vacías o no).
  - Las variables MYSQL_HOST/PORT/USER/PASSWORD/DB (o .env) apuntando a la
    base de datos MySQL destino real.

No es idempotente: insertar dos veces duplicaría filas (los `id` originales
se conservan tal cual, así que una segunda pasada chocaría por clave
primaria salvo que la tabla destino esté vacía). Pensado para una única
ejecución por entorno, con confirmación explícita del operador.
"""
import argparse
import json
import sqlite3
import sys
from datetime import datetime

from sqlalchemy import JSON, DateTime, Table, insert

from app.core.database import Base, engine as mysql_engine
from app.modules.osint.cnmv import models as _cnmv_models  # noqa: F401
from app.modules.osint.domain import models as _domain_models  # noqa: F401
from app.modules.osint.email import models as _email_models  # noqa: F401
from app.modules.osint.image import models as _image_models  # noqa: F401
from app.modules.osint.integrity import models as _integrity_models  # noqa: F401
from app.modules.osint.ip import models as _ip_models  # noqa: F401
from app.modules.osint.monitoring import models as _monitoring_models  # noqa: F401
from app.modules.osint.phone import models as _phone_models  # noqa: F401
from app.modules.osint.typosquatting import models as _typosquatting_models  # noqa: F401
from app.modules.osint.wallet import models as _wallet_models  # noqa: F401

# Nombre de tabla en el SQLite de origen -> nombre de tabla en MySQL.
# Solo "cases" cambió de nombre (ver app/modules/osint/domain/models.py);
# el resto de tablas se llaman igual en ambos esquemas.
TABLE_NAME_MAP = {"cases": "osint_domain_cases"}


def _coerce_value(raw_value, column):
    """
    SQLite guarda JSON/DateTime como texto plano; hay que convertirlo al
    tipo Python real antes de insertar en la columna MySQL equivalente
    (si no, un JSON ya serializado se re-serializaría como string dentro
    de la columna JSON, y una fecha como texto en vez de DATETIME).
    """
    if raw_value is None:
        return None
    if isinstance(column.type, JSON) and isinstance(raw_value, str):
        return json.loads(raw_value)
    if isinstance(column.type, DateTime) and isinstance(raw_value, str):
        text = raw_value.replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(text)
        except ValueError:
            return raw_value  # ya viene en un formato que MySQL puede parsear tal cual
    return raw_value


def migrate_table(sqlite_conn: sqlite3.Connection, mysql_conn, sqlite_table_name: str, mysql_table: Table) -> int:
    cur = sqlite_conn.cursor()
    cur.execute(f"SELECT * FROM {sqlite_table_name}")
    column_names = [d[0] for d in cur.description]
    mysql_columns = {c.name: c for c in mysql_table.columns}

    rows = []
    for raw_row in cur.fetchall():
        row_dict = dict(zip(column_names, raw_row))
        payload = {
            name: _coerce_value(value, mysql_columns[name])
            for name, value in row_dict.items()
            if name in mysql_columns  # ignora columnas que ya no existan; deja NULL las nuevas (p.ej. case_id)
        }
        rows.append(payload)

    if not rows:
        return 0

    mysql_conn.execute(insert(mysql_table), rows)
    return len(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sqlite-path", required=True, help="Ruta al scamshield.db de origen")
    parser.add_argument("--yes", action="store_true", help="No pedir confirmación interactiva")
    args = parser.parse_args()

    sqlite_conn = sqlite3.connect(args.sqlite_path)

    sqlite_tables = [
        row[0]
        for row in sqlite_conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    ]

    print(f"Origen:  {args.sqlite_path}  ({len(sqlite_tables)} tablas)")
    print(f"Destino: {mysql_engine.url}")
    if not args.yes:
        confirm = input("Esto escribe datos reales en MySQL. ¿Continuar? [escribe 'si' para continuar] ")
        if confirm.strip().lower() != "si":
            print("Cancelado.")
            sys.exit(1)

    mysql_meta = Base.metadata

    with mysql_engine.begin() as mysql_conn:
        for sqlite_table_name in sqlite_tables:
            mysql_table_name = TABLE_NAME_MAP.get(sqlite_table_name, sqlite_table_name)
            if mysql_table_name not in mysql_meta.tables:
                print(f"  [omitida] {sqlite_table_name}: no existe tabla equivalente en el esquema nuevo")
                continue
            mysql_table = mysql_meta.tables[mysql_table_name]
            count = migrate_table(sqlite_conn, mysql_conn, sqlite_table_name, mysql_table)
            arrow = f"{sqlite_table_name} -> {mysql_table_name}" if sqlite_table_name != mysql_table_name else sqlite_table_name
            print(f"  {arrow}: {count} filas migradas")

    sqlite_conn.close()
    print("Migración completada.")


if __name__ == "__main__":
    main()
