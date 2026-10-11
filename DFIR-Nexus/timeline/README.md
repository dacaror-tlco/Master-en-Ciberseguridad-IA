# Módulo 4 — Línea Temporal (Timeline)

Backend FastAPI independiente que construye **la cronología consolidada de
un caso** a partir de los eventos generados por otros tres módulos de
DFIR-Nexus, y la persiste en la tabla `timeline_events`.

- **Puerto de desarrollo:** 8002
- **Rama de desarrollo:** `development`
- **Rama histórica (previa a la integración):** `T1m3-l1n3`

## Objetivo

Dado un `case_id`, agregar en orden cronológico:

| Origen | Tabla fuente | Módulo | Campo de fecha usado |
|--------|--------------|--------|----------------------|
| Tracking | `tracking_events` | Módulo 3 | `hora` |
| Evidencias | `evidences` | Módulo 1 | `COALESCE(fecha_adquisicion, fecha_subida)` |
| OSINT | `osint_findings` | Módulo 2 | `analyzed_at` |

Y escribir el resultado en `timeline_events` con un campo `orden`
secuencial (1..N) por caso.

> **Nota sobre OSINT:** el nombre `osint_results` que aparece en
> documentación antigua **no existe en la base de datos**. La tabla real
> es `osint_findings`. Se filtran registros con `case_id IS NOT NULL`.

## Endpoints

| Método | Ruta | Descripción | Auth |
|--------|------|-------------|------|
| `GET` | `/timeline/cases/{case_id}` | Devuelve la timeline persistida | JWT |
| `POST` | `/timeline/cases/{case_id}/refresh` | Recalcula (DELETE + INSERT) y devuelve el resultado | JWT |
| `GET` | `/health` | Healthcheck | Público |

`case_id` debe ser entero > 0.

## Estrategia de refresco

`refresh` es un **snapshot completo**: borra los `timeline_events` del
caso y los vuelve a insertar en una **única transacción** (commit al
final, rollback ante error).

Orden global: `(fecha_hora ASC, origen_modulo ASC, origen_id ASC)`.

## Requisitos

- Python 3.12 (Docker) o 3.13/3.14 (dev; ver H-06 de la auditoría).
- MySQL 8+ (Aiven en producción).
- Dependencias: ver `requirements.txt` y `requirements-dev.txt`.

## Puesta en marcha (desarrollo local)

```bash
cd ~/DFIR-Nexus/timeline
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt

## Migraciones (Alembic)

| Revisión | Contenido |
|---|---|
| `0001_initial_cases_evidences.py` | Bootstrap aislado. Nunca aplicado a Aiven. |
| `0002_create_timeline_events.py` | Crea la tabla `timeline_events` + índice compuesto. |
| `0003_add_composite_index_origen.py` | Idempotente (resuelve H-01 de la auditoría). |

Aplicar:

    cd timeline
    alembic upgrade head
    alembic current      # -> 0003 (head)

## Docker

    cd timeline
    docker build -t dfir-nexus-timeline -f deploy/Dockerfile .
    docker run --env-file .env -p 8002:8002 dfir-nexus-timeline

Imagen base: `python:3.12-slim`. Ver deuda técnica H-06 (inconsistencia
de versión Python entre Docker y desarrollo).

## Testing

    cd timeline
    source venv/bin/activate
    pip install -r requirements.txt -r requirements-dev.txt
    pytest -v

Resultado esperado en `development`: 15 tests passing.
Con el PR #3 mergeado: 16 tests (incluye test de regresión H-02).

## Deuda técnica conocida

| ID | Descripción | Estado |
|---|---|---|
| H-06 | Python 3.12 (Docker) vs 3.13/3.14 (dev). pydantic-core==2.23.4 no compila en 3.14. | Decisión de equipo |
| H-09 | JWT duplicado respecto a otros backends. Debería ser paquete compartido. | Deuda declarada |
| H-11 | track-inc/frontend/.env.production versionado (fuera del alcance de M4). | Reportado al equipo |
| H-15 | DEFAULT_DATABASE_URL con nexus:nexus en fallback de core/database.py. | Aceptado (solo si falta .env) |
| H-20 | Carpeta app/ huérfana en la raíz del repo. | Fuera de alcance |

## Documentación relacionada

- docs/AUDITORIA_TIMELINE.md — Auditoría técnica completa (21 hallazgos).
- docs/E2E_EJECUTADA.md — Testimonio de la E2E con caso 8.
- docs/CONTRATOS.md — Contratos entre módulos.
- docs/INTEGRACION_Y_DESPLIEGUE.md — Guía general del monorepo.
