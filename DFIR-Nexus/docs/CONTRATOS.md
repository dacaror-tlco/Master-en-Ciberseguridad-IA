# Contratos entre módulos — rama `development`

Documento vivo de la Fase 0 (04/09/2026). Sigue siendo la referencia para
**las reglas de acoplamiento entre backends** (quién posee cada tabla, cómo
se lee lo que no se posee, nunca importar el modelo ORM ajeno) — esa parte
no ha cambiado. Complementa a `CLAUDE.md` (raíz) sin sustituirlo; en caso de
conflicto sobre el modelo de datos oficial, `CLAUDE.md` tiene prioridad.

> **Actualización (septiembre de 2026): los "estados reales en Aiven" fechados
> más abajo (04/09/2026) son ya históricos, no el estado actual.** Para el
> estado real hoy, ver el README de la raíz. Correcciones puntuales a las
> afirmaciones más propensas a inducir a error:
> - **Puertos de desarrollo**: Casos corre en `:8000`, no en `:8123` (la tabla
>   de la sección "Backends independientes integrados hasta ahora" más abajo
>   tenía el puerto de una verificación puntual, no el real).
> - **Tablas de versión de Alembic**: las cinco existen ya (`alembic_version_casos`,
>   `_scamshield`, `_tracking`, `_timeline`, `_sharingan`), con migraciones
>   aplicadas de verdad contra Aiven — nada de lo que sigue sobre "no existe
>   todavía" o "pendiente de autorización" en esta sección refleja el estado
>   actual. Casos añadió además `users` y `auth_audit_log` a lo que posee
>   (identidad de la plataforma), fuera del modelo de datos original de este
>   documento.
> - **OSINT ya no tiene frontend propio y separado**: se integró en el
>   frontend único (`frontend/src/modules/osint/`), igual que Tracking,
>   Timeline e Informes.
> - **`osint_findings.case_id` dejó de ser un pendiente**: OSINT atribuye el
>   `case_id` en el momento del análisis (selector de expediente en la
>   cabecera del módulo) y, además, permite vincular/cambiar/desvincular a
>   posteriori desde `/osint/cases` — ver README, sección OSINT.

## Regla general de acoplamiento

* Cada backend mantiene sus **propios modelos Python** para las tablas que
  posee. **Ningún backend importa el paquete Python de otro backend.**
* Un backend puede necesitar **leer** una tabla que no posee (p. ej. Timeline
  leyendo `tracking_events`). Esa lectura se hace contra el esquema real de la
  tabla (SQL directo, o un modelo de solo lectura/contrato definido y mantenido
  localmente por quien lee) — nunca importando el modelo ORM del dueño.
* Ningún módulo escribe una tabla que no posee.
* No se pasan JSON/resultados completos entre backends por HTTP salvo que el
  consumidor sea un cliente externo al ecosistema de bases de datos.

## Tabla de propiedad

| Tabla | Owner | Escribe | Lee | FK a `cases.id` |
|---|---|---|---|---|
| `cases` | Casos | Casos | OSINT (referencia lógica opcional), Tracking, Timeline, Informes | — (es la entidad) |
| `evidences` | Casos | Casos | Timeline, Informes | Sí, `ON DELETE CASCADE` |
| `osint_findings` | OSINT | OSINT | Timeline, Informes | Sí, lógica (nullable, sin FK física) |
| `tracking_events` | Tracking | Tracking | Timeline, Informes | Sí, **sin** `ON DELETE CASCADE` |
| `timeline_events` | Timeline | Timeline | Informes | Sí, `ON DELETE CASCADE` |
| `reports` | Informes | Informes | Ninguno (hoja del grafo) — Informes también lee `cases`, `evidences`, `osint_findings` y `tracking_events` (nunca escribe ninguna) | Sí, **sin** `ON DELETE CASCADE` |
| tablas internas de OSINT (`osint_domain_cases`, `email_cases`, `ip_cases`, `phone_cases`, `wallet_cases`, etc.) | OSINT | OSINT | Nadie fuera de OSINT | Ninguna (algunas tienen `case_id` lógico opcional, ver `scam-shield/docs/CONTRATO-DATOS.md`) |

## Pendiente explícito: `osint_findings.case_id`

`case_id` existe, está indexado, y permite NULL. **No debe rellenarse por
heurística** (no inferir el caso por coincidencia de sujeto/fecha/etc.). El
flujo correcto es que el análisis reciba y asocie explícitamente el `case_id`
del caso de Nexus sobre el que se está trabajando, en el momento del análisis
— tarea de la Fase 1 (OSINT), no resuelta todavía.

## Índices/constraints ya confirmados en Aiven (04/09/2026)

* `evidences.case_id → cases.id`, `ON DELETE CASCADE`.
* `tracking_events.case_id → cases.id`, sin cascade.
* `timeline_events.case_id → cases.id`, `ON DELETE CASCADE`.
* `reports.case_id → cases.id`, sin cascade.
* `osint_findings`: índice sobre `case_id` (nullable); `UNIQUE(case_type, source_id)`.

## Alembic: tablas de versión independientes

La base es compartida pero el historial de migraciones no: cada backend sella
su propio historial en su propia tabla de versión, para no pisarse con el de
otro backend apuntando a la misma base.

| Backend | Tabla de versión | Estado real en Aiven (04/09/2026) |
|---|---|---|
| Casos | `alembic_version_casos` (Fase 0) | No existe todavía — `cases`/`evidences` existen pero sin este tracking |
| OSINT | `alembic_version_scamshield` | `3ea435e2a953` |
| Tracking | `alembic_version_tracking` (Fase 2) | No existe todavía |
| Timeline | `alembic_version_timeline` (Fase 3) | No existe todavía — cabeza real de la cadena de este backend: `0002` |
| Informes | `alembic_version_sharingan` (ya la usaba en origin/sharingan) | `m5_0005` — coincide exactamente, sin cambios |
| — (tabla por defecto, heredada de pruebas previas) | `alembic_version` | `0002` — refleja que en algún momento se aplicó contra Aiven la cadena Casos(`0001`)+Timeline(`0002`) con el nombre de tabla por defecto, fuera de esta integración. No se toca en Fase 0. |

### Convergencia segura de `sharingan m5_0001` (pendiente, NO ejecutada)

`m5_0001_create_reports_table.py` tiene `down_revision = None` en el
archivo, pero ya está aplicada/sellada en Aiven bajo
`alembic_version_sharingan` (cabeza real: `m5_0005`). Por eso:

* **No se reescribe el historial ya aplicado.** No se toca `revision` de
  ninguna migración de `m5_000N` (son las claves ya guardadas en
  `alembic_version_sharingan`).
* Editar `down_revision` de `m5_0001` (de `None` a `"0001"`) es seguro en
  principio porque ese campo no se guarda en la tabla de versión — solo
  ordena el grafo para entornos nuevos — pero **no se hace en Fase 0**: es
  trabajo de Fase 4 (Informes), y antes de tocar ese archivo hay que
  confirmar contra Aiven que ningún proceso automático (CI, otro
  desarrollador) vaya a generar una migración `--autogenerate` a partir de
  ese cambio de grafo sin revisión humana.
* Si al llegar a la fase de convergencia final se prefiere no tocar el
  archivo histórico en absoluto, la alternativa igual de segura es una
  **migración de convergencia nueva y vacía** (`depends_on`/`down_revision`
  apuntando a `"0001"` y `"m5_0005"` a la vez, sin `upgrade()`/`downgrade()`
  reales).
* **Decisión explícita de la Fase 4**: no se ha tocado. La integración de
  Informes en `development` se limitó a código y contrato, tal y como se
  pidió; la convergencia de las cinco cadenas Alembic en una sola queda
  para una fase específica de validación/convergencia final, todavía no
  iniciada.

## Estado de Fase 0 respecto a Aiven

Ninguna migración ni `stamp` se ha ejecutado contra Aiven en Fase 0. El único
cambio de Alembic es de código (`backend/alembic/env.py`, tabla de versión
propia para Casos). Aplicar esa configuración contra Aiven de verdad requiere
`alembic stamp 0001` (no `upgrade`, porque `cases`/`evidences` ya existen) y
queda pendiente de autorización explícita antes de ejecutarse.

## Backends independientes integrados hasta ahora

| Backend | Directorio | Puerto de desarrollo | Fase |
|---|---|---|---|
| Casos | `backend/` | 8123 (usado en verificación) | 0 |
| OSINT | `scam-shield/` (+ frontend propio en `scam-shield/frontend/`) | 8124 | 1 |
| Tracking | `track-inc/` | 8001 | 2 |
| Timeline | `timeline/` | 8002 | 3 |
| Informes | `sharingan/` | 8003 | 4 |

OSINT es el único con frontend propio y separado (`VITE_OSINT_APP_URL`,
enlazado desde `/osint`); Tracking, Timeline e Informes integran su UI
directamente en `frontend/src/modules/{tracking,timeline,reports}/`, cada
uno apuntando a su propio backend (`VITE_TRACKING_API_URL`,
`VITE_TIMELINE_API_URL`, `VITE_REPORTS_API_URL`) — nunca al de Casos, salvo
para leer `GET /cases` con el fin de poblar un selector (Informes ya traía
esto resuelto así desde `origin/sharingan`: `CASES_API_BASE_URL` separada
de `REPORTS_API_BASE_URL`).

## Fase 3 — Timeline

* `timeline_events` ya existía en Aiven con `ON DELETE CASCADE` antes de
  extraer este backend (confirmado el 04/09/2026); el modelo y la migración
  `0002` de este backend reflejan esa estructura real, no la introducen.
* Se añadió el índice compuesto `(origen_modulo, origen_id)` que `CLAUDE.md`
  exige para este módulo y que la versión de origen
  (`feature/timeline-integration`) no tenía — aditivo sobre una tabla que
  este backend posee, no toca ninguna tabla ajena.
* `osint_findings` se lee filtrando por `case_id` explícito (columna
  nullable) — nunca por `subject_value`, dominio ni ningún otro campo. Un
  hallazgo con `case_id = NULL` no aparece en ninguna timeline hasta que
  OSINT lo asocie explícitamente (Fase 1, pendiente de UI que lo haga).
* Igual que Casos y Tracking, el `alembic stamp 0002` de Timeline contra
  Aiven (con su nueva tabla de versión) queda pendiente de autorización
  explícita — no se ha ejecutado.

## Fase 4 — Informes

* `origin/sharingan` ya traía, sin necesidad de adaptación, casi todo lo
  que exige el contrato de `development`: modelos de solo lectura locales
  (`app/modules/shared/models.py`) para `cases`/`evidences`/
  `osint_findings`/`tracking_events`/`timeline_events` (nunca importa el
  código de otro backend), tabla de versión propia
  (`alembic_version_sharingan`) con `include_name` ya limitado a
  `reports`, versionado de informes protegido por
  `UNIQUE(case_id, version)` + reintento ante `IntegrityError` (no solo
  `SELECT MAX(version)`), y lectura de `osint_findings` filtrada por
  `case_id` explícito, sin heurísticas.
- **Único conflicto real resuelto en esta fase**: `POST /reports/generate`
  de OSINT (`scam-shield/app/modules/osint/report/routes.py`) colisionaba
  en namespace con el mismo endpoint de Informes, el propietario real.
  Renombrado a `/analysis/reports/generate` (mismo prefijo que el resto de
  OSINT); actualizados su frontend (`reportApi.ts`) y sus tests. No se ha
  tocado ninguna otra ruta de OSINT.
- `cases_router` de Informes (`GET /cases/{case_id}/reports`) se conserva
  tal cual: es una lectura anidada en su propio backend/puerto, no una
  reivindicación de `/cases` — mismo patrón que Tracking.
- **Nota de diseño verificada, no asumida**: `generate_report` exige que el
  caso tenga al menos un `timeline_event` (`EmptyTimelineError` → 422 si
  no), comportamiento intencional y ya probado en `origin/sharingan`
  (`test_generate_report_sin_eventos`, fixture
  `caso_002_sin_eventos.json`). Evidencias/OSINT/Tracking sí pueden estar
  vacíos sin error — verificado con una suite nueva
  (`tests/test_fase4_contrato_informes.py`) que usa `osint_findings` (no
  `osint_results`, que sigue sin existir en ningún sitio real) para
  reflejar el estado real de Aiven.
- `alembic_version_sharingan` no se ha tocado: su cabeza real (`m5_0005`)
  coincide exactamente con la de `origin/sharingan`, y no se ha ejecutado
  ningún `stamp`/`upgrade` contra Aiven en esta fase.
