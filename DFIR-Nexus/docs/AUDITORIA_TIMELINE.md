# Auditoría del Módulo 4 — Línea Temporal (Timeline)

**Proyecto:** DFIR-Nexus
**Módulo:** 4 — Línea Temporal
**Rama activa:** `development`
**Backend:** `timeline/` (FastAPI, puerto 8002 en dev)
**Frontend:** `frontend/src/modules/timeline/`
**Fecha de auditoría:** 2026-09-27
**Auditor:** JDaveGRamirez
**Estado:** Cerrada — 21 hallazgos documentados, 16 resueltos, 5 fuera de alcance o pendientes de decisión de equipo.

---

## 1. Alcance

Auditoría técnica del Módulo 4 (Timeline) que cubre:

- Backend FastAPI (`timeline/`): modelos, schemas, repositorio, servicio, rutas, auth JWT duplicado.
- Migraciones Alembic (`0001`, `0002`, `0003`) y verificación contra el estado real de Aiven.
- Frontend React (`frontend/src/modules/timeline/`): API client, página, componentes, utilidades.
- Tests (`timeline/tests/`).
- Dockerfile y `requirements.txt`.
- Integración con los otros 4 módulos (backend, scam-shield, track-inc, sharingan).
- Historial Git y estructura del monorepo.

## 2. Metodología

- Lectura completa del código backend + frontend + migraciones + tests + deploy.
- Verificación contra la base de datos real (Aiven MySQL):
  - `SHOW TABLES`
  - `DESCRIBE <tabla>`
  - `information_schema.STATISTICS`
- Ejecución de `alembic upgrade head` sobre SQLite limpia.
- Ejecución de `alembic current` sobre Aiven.
- Suite de tests local (`pytest -v`).
- Build de frontend (`npm run build`).
- Ejecución de la suite de tests cruzada en los 5 módulos.
- Revisión de PRs abiertos y del working tree.

## 3. Resumen de hallazgos

| Severidad | Total | Resueltos | Pendientes | Fuera de alcance |
|---|---|---|---|---|
| 🔴 Crítico | 2 | 2 | 0 | 0 |
| 🟠 Alto | 5 | 5 | 0 | 0 |
| 🟡 Medio | 7 | 5 | 2 | 0 |
| 🔵 Bajo | 5 | 3 | 0 | 2 |
| ℹ️ Informativo | 2 | 2 | 0 | 0 |
| **Total** | **21** | **16** | **2** | **2** |

---

## 4. Hallazgos detallados

### 🔴 Críticos

#### H-01 — Índice duplicado entre migraciones 0002 y 0003

- **Descripción:** La migración `0003_add_composite_index_origen.py` intentaba crear un índice compuesto (`ix_timeline_events_origen`) que ya había sido creado por `0002_create_timeline_events.py`. En una BD limpia, `alembic upgrade head` fallaba con `Duplicate key name`.
- **Impacto:** Imposible aplicar migraciones desde cero. Bloqueaba CI y cualquier nuevo entorno.
- **Causa raíz:** Falta de idempotencia en la migración `0003`.
- **Solución aplicada (PR #3):** La migración ahora comprueba si el índice existe antes de crearlo, usando `sa.inspect(conn).get_indexes("timeline_events")`.
- **Verificación:** `alembic upgrade head` sobre SQLite limpia → OK. `alembic current` en Aiven → `0003 (head)`.

#### H-02 — `POST /refresh` devolvía IDs inconsistentes

- **Descripción:** El endpoint `POST /timeline/cases/{case_id}/refresh` devolvía los objetos en memoria (pre-commit) con `id == origen_id`, en lugar de los IDs persistidos en `timeline_events`.
- **Impacto:** El frontend recibía IDs incorrectos. Rompía `getRowId` (React keys) y cualquier referencia a `timeline_events.id` desde otras capas.
- **Causa raíz:** El servicio devolvía la lista construida antes de `commit()`, sin releerla.
- **Solución aplicada (PR #3):** `refresh_timeline` hace un único commit y **relee** los eventos persistidos antes de devolverlos.
- **Verificación:** Test de regresión `test_refresh_devuelve_id_de_timeline_events` (PR #3). Verificado en E2E: `GET /timeline/cases/8` devuelve IDs reales (`412..420`) distintos de `origen_id` (`4, 5, 6, 22...`).

---

### 🟠 Altos

#### H-03 — Refresh no atómico

- **Descripción:** El refresh hacía 2 commits separados: uno para el `DELETE` y otro para el `INSERT`. Si fallaba el `INSERT`, la timeline quedaba vacía.
- **Impacto:** Riesgo de pérdida de datos visible para el usuario.
- **Causa raíz:** Separación de transacciones en `delete_existing_timeline` e `insert_timeline_events`.
- **Solución aplicada (PR #3):** Un único `commit()` al final con `rollback()` en caso de error. Las funciones internas ya no commitean.
- **Verificación:** Test de idempotencia (`test_refresh_no_duplica_al_ejecutarse_dos_veces`) + revisión de código.

#### H-04 — Fuga de información en mensajes de error 500

- **Descripción:** El handler de excepciones devolvía `detail=str(e)`, exponiendo host, usuario MySQL, stack o rutas internas.
- **Impacto:** Seguridad — información sensible en respuestas HTTP.
- **Causa raíz:** Manejo de errores sin sanitizar.
- **Solución aplicada (PR #3):** `logger.exception(...)` para registro interno + mensaje genérico al cliente (`"Error interno al procesar la línea temporal"`).
- **Verificación:** Revisión de `routes.py`. Logs siguen mostrando detalle.

#### H-07 — N+1 INSERTs en `insert_timeline_events`

- **Descripción:** Se insertaba cada evento con un `session.add()` individual dentro de un bucle.
- **Impacto:** Rendimiento degradado en casos con muchos eventos (caso 18 tiene 23 eventos, caso 21 tiene 18).
- **Causa raíz:** Uso de ORM sin `bulk_save_objects` ni `executemany`.
- **Solución aplicada (PR #3):** `conn.execute(insert(timeline_events), lista_dicts)` con un único round-trip.
- **Verificación:** Revisión de `repository.py`. Tests pasan.

#### H-19 — `fetch` sin timeout en frontend

- **Descripción:** Las llamadas `fetch` desde `timelineApi.ts` no tenían timeout. Si el backend no respondía, la UI quedaba en "cargando..." indefinidamente.
- **Impacto:** UX degradada ante red lenta o backend caído.
- **Causa raíz:** Uso directo de `fetch` sin `AbortController`.
- **Solución aplicada (PR #4):** `AbortController` con timeout de 15 segundos. Error explícito al usuario.
- **Verificación:** Probado en navegador con backend parado → mensaje de error correcto.

#### H-12 — Frontend descartaba `detail` del backend

- **Descripción:** Ante un error HTTP (p. ej. 401, 404, 500), el cliente no leía el campo `detail` de la respuesta, mostrando siempre un mensaje genérico.
- **Impacto:** Pérdida de información útil para el usuario (p. ej. "Token expirado" vs "caso no encontrado").
- **Causa raíz:** `if (!res.ok) throw new Error("Error")` sin parsear el body.
- **Solución aplicada (PR #4):** Parseo de `body.detail` cuando existe; fallback a mensaje genérico.
- **Verificación:** Probado con caso 999 (inexistente) y con token inválido.

---

### 🟡 Medios

#### H-05 — Falta `cryptography` en `requirements.txt`

- **Descripción:** La conexión a Aiven requiere `caching_sha2_password`, que a su vez necesita el paquete `cryptography`. No estaba en `requirements.txt`.
- **Impacto:** Falla de conexión en entornos limpios (Docker, CI, nuevos desarrolladores).
- **Solución aplicada (PR #3):** Añadido `cryptography>=42` a `timeline/requirements.txt`.
- **Verificación:** `pip install -r requirements.txt` en venv limpio → OK.
- **Nota:** Aún pendiente en los otros 4 módulos (ver §6).

#### H-06 — Python 3.12 (Docker) vs 3.13/3.14 (dev)

- **Descripción:** El `Dockerfile` usa `python:3.12-slim`, los venvs locales usan 3.13.9, y el sistema Kali tiene 3.14.6. `pydantic-core==2.23.4` no compila en 3.14 (PyO3 0.22.2 soporta ≤3.13).
- **Impacto:** Inconsistencia entre entornos. Falsos positivos en tests.
- **Estado:** 🟡 Pendiente de decisión de equipo.
- **Recomendación:** Fijar Python 3.13 en Docker y en `README`; actualizar pines de `pydantic` si se quiere 3.14.

#### H-09 — JWT duplicado respecto a otros backends

- **Descripción:** La verificación JWT está reimplementada en `timeline/app/modules/auth/`, en lugar de importarse desde un paquete compartido.
- **Impacto:** Deuda técnica. Riesgo de divergencia de lógica (claims, expiración, algoritmo).
- **Estado:** 🟡 Deuda declarada. Aceptado a corto plazo.
- **Recomendación:** Extraer un paquete `dfir-nexus-auth` compartido cuando se consolide el monorepo.

#### H-13 — `case_id > 0` sin validar

- **Descripción:** Los endpoints aceptaban `case_id` negativos o cero, provocando consultas inútiles y errores 500 confusos.
- **Impacto:** UX y robustez.
- **Solución aplicada (PR #3 backend, PR #4 frontend):** `Path(..., gt=0)` en FastAPI; validación equivalente en el frontend (botones deshabilitados con `caseId <= 0`).
- **Verificación:** Probado con `caseId = -1` y `caseId = 0` → respuesta 422 en backend, UI bloqueada en frontend.

#### H-14 — Redundancia `case_id = :x AND case_id IS NOT NULL`

- **Descripción:** En la consulta a `osint_findings` se filtraba por `case_id = :x AND case_id IS NOT NULL`. La segunda condición es redundante si la primera es igualdad sobre un valor no nulo.
- **Impacto:** Ruido, posible confusión futura.
- **Solución aplicada (PR #3):** Eliminado `AND case_id IS NOT NULL` cuando ya hay igualdad.
- **Verificación:** Test `test_no_usa_heuristica_para_osint_findings_sin_case_id` sigue pasando.

#### H-17 — Falta `README.md` en `timeline/`

- **Descripción:** El módulo no tenía README. Difícil onboarding.
- **Impacto:** Documentación.
- **Solución aplicada (PR #6):** README de 63 líneas (funcional pero incompleto — ver §5). Pendiente ampliar con secciones "Migraciones", "Docker" y "Deuda técnica conocida".
- **Verificación:** Archivo versionado en rama `docs/timeline-readme`.

#### H-21 — Falta test de regresión para H-02

- **Descripción:** El bug H-02 (IDs inconsistentes en refresh) no tenía test que lo cubriera.
- **Impacto:** Riesgo de regresión.
- **Solución aplicada (PR #3):** Añadido `test_refresh_devuelve_id_de_timeline_events` en `tests/test_routes.py`.
- **Verificación:** `pytest -v` incluye el nuevo test y pasa.

---

### 🔵 Bajos

#### H-08 — `inspect()` / `table_exists()` repetidos

- **Descripción:** El repositorio llama repetidamente a `sa.inspect(engine)` y `table_exists()` en cada consulta a las fuentes.
- **Impacto:** Micro-ineficiencia. Legibilidad.
- **Estado:** 🔵 Fuera de alcance de esta auditoría. Refactor opcional.

#### H-10 — Fix Vite `host: '0.0.0.0'` sin commitear

- **Descripción:** El `vite.config.ts` necesitaba `host: '0.0.0.0'` para escuchar en IPv4 (Vite por defecto solo IPv6). El fix estaba en el working tree sin commitear.
- **Impacto:** Frontend inaccesible desde el host anfitrión.
- **Solución aplicada (PR #3):** Incluido en el commit del PR.
- **Verificación:** Frontend accesible en `http://localhost:5173` desde el navegador de la VM.

#### H-11 — `track-inc/frontend/.env.production` versionado

- **Descripción:** Archivo `.env.production` del frontend de `track-inc` (Módulo 3) está trackeado en Git.
- **Impacto:** Seguridad (no es de Módulo 4, pero se detectó).
- **Estado:** 🟡 Reportado al equipo. Fuera del alcance del Módulo 4.

#### H-15 — `DEFAULT_DATABASE_URL` con `nexus:nexus`

- **Descripción:** El fallback de conexión en `core/database.py` incluye credenciales placeholder (`nexus:nexus@localhost`).
- **Impacto:** Bajo — solo se usa si no hay `.env`.
- **Estado:** 🔵 Aceptado (fallback documentado).

#### H-20 — `app/` huérfano en la raíz del repo

- **Descripción:** Existe una carpeta `app/` en la raíz del monorepo sin relación aparente con ningún módulo.
- **Impacto:** Confusión en onboarding.
- **Estado:** 🔵 Fuera de alcance.

---

### ℹ️ Informativos

#### H-16 — `getRowId` colisiona (consecuencia de H-02)

- **Descripción:** El `getRowId` del frontend usaba el `id` recibido del refresh, que por H-02 era igual a `origen_id`. Colisionaba cuando dos fuentes distintas tenían el mismo `origen_id`.
- **Impacto:** React keys duplicadas → warnings y comportamientos erráticos.
- **Solución aplicada:** Resuelto implícitamente al corregir H-02.

#### H-18 — `.pytest_cache/` en disco

- **Descripción:** Carpetas `.pytest_cache/` presentes en varios módulos.
- **Impacto:** Ruido en el working tree.
- **Estado:** ℹ️ Ignorado vía `.gitignore`. No requiere acción.

---

## 5. Documentación pendiente

| Documento | Estado |
|---|---|
| `timeline/README.md` | 🟡 Creado (63 líneas). Falta ampliar con: Migraciones, Docker, Deuda técnica conocida |
| `timeline/.env.example` | ✅ Limpio, con placeholders (`USER:PASSWORD@HOST:PORT/DATABASE`) |
| `docs/AUDITORIA_TIMELINE.md` | ✅ Este documento |
| `docs/E2E_EJECUTADA.md` | ⏳ Pendiente de generar |

**Nota:** Se sospechó que `.env.example` tenía credenciales reales. **Falso positivo.** Verificado con `git show HEAD:timeline/.env.example`: siempre tuvo `nexus:nexus@localhost` y `change_me`. El `.env` real nunca ha estado versionado (`git ls-files | grep .env` confirma).

---

## 6. Hallazgos de infraestructura del monorepo

Detectados durante la verificación cruzada de los 5 módulos.

### 6.1 `pytest` no instalado en venvs de 3 módulos

- **Módulos afectados:** `backend`, `scam-shield`, `sharingan`.
- **Síntoma:** Al ejecutar `pytest` desde el venv, el shell resolvía a `/usr/bin/pytest` (Python del sistema, sin acceso a las deps del venv) → falso `ModuleNotFoundError: pydantic_settings`.
- **Solución:** `pip install -r requirements.txt -r requirements-dev.txt` en cada venv.
- **Recomendación:** Documentar en el README principal del repo, o crear un script `scripts/bootstrap-venvs.sh`.

### 6.2 No hay venv unificado ni orquestador de tests en la raíz

- **Síntoma:** Ejecutar los tests de los 5 módulos requiere activar manualmente cada venv.
- **Recomendación:** Añadir un `Makefile` o `scripts/test-all.sh` en la raíz que itere por los 5 módulos.

### 6.3 Versiones Python inconsistentes

- **Versiones detectadas:** 3.13.9 (venvs de módulos), 3.14.6 (sistema Kali).
- **Impacto:** `pydantic-core==2.23.4` no compila en 3.14 (PyO3 0.22.2 soporta ≤3.13).
- **Recomendación:** Fijar Python 3.13 como versión oficial del proyecto. Actualizar `README`, `Dockerfile` y `requirements.txt` de todos los módulos.

### 6.4 Suite cruzada de tests

Ejecutados los 5 módulos en sus venvs respectivos:

| Módulo | Resultado | Tiempo | Python |
|---|---|---|---|
| timeline (M4) | 16/16 ✅ | 1.0 s | 3.14.6 (sistema) |
| track-inc (M3) | 304/304 ✅ | 13.3 s | 3.13.9 (venv) |
| backend (M1) | 127/127 ✅ | 43.7 s | 3.13.9 (venv) |
| scam-shield (M2) | 419/419 ✅ | 65.6 s | 3.13.9 (venv) |
| sharingan (M5) | 219/219 ✅ | 23.8 s | 3.13.9 (venv) |
| **TOTAL** | **1085/1085 ✅** | **~2 m 27 s** | — |

---

## 7. Hallazgos de seguridad

| ID | Descripción | Estado |
|---|---|---|
| S-01 | Rama histórica `T1m3-l1n3` tiene credenciales hardcodeadas en su historial (`git log -p`). | ⚠️ Pendiente rotación |
| S-02 | `.env.example` de Timeline — **falso positivo**, siempre limpio. | ✅ Verificado |
| S-03 | `.env` real nunca ha estado versionado. | ✅ Verificado |
| S-04 | `track-inc/frontend/.env.production` versionado (fuera de M4). | 🟡 Reportado |
| S-05 | `JWT_SECRET` y `OSINT_AUDIT_SERVICE_TOKEN` únicos por entorno. | ✅ Configurado |

**Recomendación:** Rotar credenciales de Aiven y admin de prueba al cierre del desarrollo. Añadir hook pre-commit con `gitleaks` o `trufflehog` para prevenir futuras fugas.

---

## 8. Hallazgos científicos / de diseño

Los silencios temporales son información forense valiosa. En el caso 8, el 90% del rango está vacío (hueco de 18 días). La UI lo muestra con marcadores `⌇ N días`.

Tipos de silencio:
- **Operativo:** normal (fuera de jornada laboral, etc.).
- **Sospechoso:** posible evasión del atacante.
- **Instrumental:** fallo del recolector (tracking, logs, agente).

**Fase actual:** visualización pasiva.
**Fase futura:** detección heurística con toggle (huecos > media + 2·σ).

### Distribución real de eventos por caso

| Caso | Eventos | Span | Distribución |
|---|---|---|---|
| 8 | 9 | 20 días | 3 evidence + 3 tracking + 3 osint |
| 18 | 23 | 12 días | 9 + 5 + 9 |
| 19 | 18 | 4 días | 8 + 2 + 8 |
| 20 | 17 | 3 días | 7 + 2 + 8 |
| 21 | 18 | 18 días | 7 + 3 + 8 |

### Patrones observados

- 3 carriles paralelos revelan patrones que una línea única oculta:
  - Evidencia concentrada al inicio → fase de recolección.
  - Tracking en el medio → actividad monitorizada.
  - OSINT disperso → análisis continuo.
- Si OSINT precede a tracking → análisis previo al incidente.

### Compresión de huecos

- Umbral: 12 h.
- Motivo: sin compresión, el caso 8 (span 20 días) aplasta los eventos contra los bordes.

---

## 9. Estado de PRs

| PR | Rama | Contenido | Estado |
|---|---|---|---|
| #3 | `fix/timeline-audit` | Correcciones backend H-01, H-02, H-03, H-04, H-05, H-07, H-10, H-13, H-14, H-21 | Pusheado, pendiente revisión |
| #4 | `feat/timeline-ux` | Mejoras UX frontend (Recalcular, auto-carga, indicador, H-12, H-19) | Pusheado, pendiente revisión |
| #6 | `docs/timeline-readme` | README + `.env.example` | Pusheado, pendiente revisión |
| (nuevo) | `feat/timeline-visualization` | Gráfico vis-timeline (3 carriles + compresión de huecos) | Pusheado, pendiente abrir PR |

---

## 10. Conclusiones

- **Módulo 4 en estado sólido:** 16/21 hallazgos resueltos, 2 pendientes de decisión de equipo, 2 fuera de alcance, 1 informativo.
- **La E2E está cerrada** con el caso 8: 9 eventos correctamente ordenados, IDs reales, sin duplicados.
- **Las correcciones del PR #3** eliminan los bugs críticos (H-01, H-02) y altos (H-03, H-04, H-07, H-12, H-19).
- **Deuda técnica declarada:** JWT duplicado (H-09), Python inconsistente (H-06), versionado de `.env.production` en M3 (H-11).
- **El gráfico vis-timeline** completa la visión forense, mostrando patrones que la tabla oculta.

---

## 11. Recomendaciones

### Corto plazo
1. Mergear PRs #3, #4, #6 y el nuevo PR del gráfico.
2. Ampliar `timeline/README.md` (Migraciones, Docker, Deuda técnica).
3. Rotar credenciales expuestas en la rama histórica `T1m3-l1n3`.
4. Añadir `cryptography>=42` a los otros 4 `requirements.txt`.

### Medio plazo
5. Fijar Python 3.13 en todos los módulos.
6. Extraer paquete `dfir-nexus-auth` compartido (resolver H-09).
7. Añadir `Makefile` / `scripts/test-all.sh` en la raíz del monorepo.
8. Implementar endpoint `GET /timeline/cases/{id}/status` para el indicador "desactualizado".

### Largo plazo
9. Detección heurística de silencios sospechosos.
10. Exportación de timeline a PDF / CSV / ICS.
11. Dashboard agregado entre casos.
12. Migrar auto-refresh a Celery / APScheduler.
13. Eliminar cron del script antiguo `update_timeline.py`.

---

## Anexo A — Comandos de verificación

```bash
# Tests M4
cd ~/DFIR-Nexus/timeline && source venv/bin/activate && pytest -v

# Migraciones
alembic current                        # → 0003 (head)
alembic upgrade head                   # idempotente

# E2E endpoints
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"dfirnexus.project@gmail.com","password":"<PASS>"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

curl -H "Authorization: Bearer $TOKEN" http://localhost:8002/timeline/cases/8
curl -X POST -H "Authorization: Bearer $TOKEN" http://localhost:8002/timeline/cases/8/refresh

# Build frontend
cd ~/DFIR-Nexus/frontend && npm run build
