"""
La FK de `tracking_events` a `cases` tiene que resolverse con la aplicación sola.

Este test existe por una avería concreta: al integrar en `development` se retiró
el modelo placeholder de Casos de este backend —correcto, la tabla es del
Módulo 1— y `case_exists` pasó a leerla con SQL directo. Pero
`tracking_events.case_id` seguía declarando `ForeignKey("cases.id")`, y
SQLAlchemy necesita encontrar la tabla apuntada **dentro del mismo `MetaData`**
para ordenar las tablas al hacer `flush`. Sin ella, cualquier INSERT en
`tracking_events` abortaba con `NoReferencedTableError` y
`POST /cases/{id}/tracking/events` devolvía 500 **siempre**, en local y en
producción.

Lo que hizo que el fallo pasara tres semanas sin verse es que el resto de la
suite no lo puede detectar: `conftest.py` declara su propia tabla `cases` de
apoyo, así que dentro de los tests la FK siempre resuelve. De ahí que este test
arranque **un intérprete nuevo**, sin `conftest`: es la única forma de comprobar
lo que ve el proceso real.
"""
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

#: Lo mínimo que hace un flush por dentro: pedirle a la FK su columna destino.
#: `fk.column` es una propiedad perezosa y es justo la que lanzaba la excepción.
COMPROBACION = (
    "from app.modules.tracking.models import TrackingEvent\n"
    "fk = next(iter(TrackingEvent.__table__.c.case_id.foreign_keys))\n"
    "assert fk.column is not None\n"
    "print(fk.column)\n"
)


def test_la_fk_a_cases_resuelve_sin_las_tablas_de_apoyo_de_los_tests():
    resultado = subprocess.run(
        [sys.executable, "-c", COMPROBACION],
        cwd=RAIZ,
        capture_output=True,
        text=True,
    )

    assert resultado.returncode == 0, (
        "la FK de tracking_events no resuelve con la aplicación sola, así que "
        "guardar eventos devolvera 500 con el backend en marcha:\n"
        f"{resultado.stderr}"
    )
    assert "cases.id" in resultado.stdout
