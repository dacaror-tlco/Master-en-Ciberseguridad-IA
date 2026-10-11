# DFIR Nexus — Integración y despliegue

Documento autosuficiente sobre el estado actual de la integración de los cinco
módulos de Nexus en la rama `development`, cómo está estructurado el proyecto,
cómo se comunican los módulos entre sí, y cómo levantar y desplegar todo el
sistema. No hace falta leer ningún otro documento para entender el proyecto
a partir de aquí, aunque `docs/CONTRATOS.md` (más breve, formato de referencia
rápida) y `sharingan/ESTADO.md` (bitácora detallada del Módulo 5) complementan
algunos puntos con más profundidad histórica.

---

## 1. Resumen del proyecto

**DFIR Nexus** es una plataforma de asistencia a peritos informáticos y
analistas forenses, desarrollada como práctica de un Máster de Ciberseguridad
e Inteligencia Artificial. Automatiza el flujo de una investigación:
recopilar evidencias, consultar fuentes OSINT, analizar logs post-incidente,
construir una cronología y generar un informe pericial asistido por IA.

El proyecto está compuesto por **cinco módulos**, cada uno desarrollado de
forma independiente por un integrante distinto del equipo, en su propia rama
Git original:

| Módulo | Responsabilidad | Rama original |
|---|---|---|
| **Casos** | Alta/edición/borrado de casos periciales y sus evidencias | `modulo-casos` |
| **OSINT** | Análisis de dominios, emails, IPs, teléfonos, wallets, imágenes, etc. en fuentes abiertas | `scam-shield` |
| **Tracking** | Análisis de logs post-incidente y clasificación de eventos sospechosos | `track-inc` |
| **Timeline** | Construcción de la cronología consolidada del caso | `feature/timeline-integration` (sustituye al script antiguo de `T1m3-l1n3`) |
| **Informes** | Generación de informes periciales asistida por IA (PDF/DOCX/HTML/JSON) | `sharingan` |

**Punto clave de la arquitectura**: los cinco módulos son hoy **cinco backends
FastAPI independientes**, cada uno con su propio proceso, su propio puerto,
sus propias dependencias Python y su propia cadena de migraciones Alembic.
No se ha fusionado ningún backend con otro. La integración se realiza
**exclusivamente a través de una base de datos MySQL compartida** (alojada en
Aiven): un módulo escribe su tabla, y otro módulo la lee directamente — nunca
se pasan resultados completos entre backends por HTTP ni se importa código
Python de un backend desde otro.

---

## 2. Arquitectura final

```mermaid
graph TD
    FE["Frontend único (React)\nfrontend/src"]

    FE -->|VITE_API_BASE_URL| Casos["Casos :8000\nbackend/"]
    FE -->|VITE_OSINT_API_URL| OSINT["OSINT :8124\nscam-shield/"]
    FE -->|VITE_TRACKING_API_URL| Tracking["Tracking :8001\ntrack-inc/"]
    FE -->|VITE_TIMELINE_API_URL| Timeline["Timeline :8002\ntimeline/"]
    FE -->|VITE_REPORTS_API_URL| Informes["Informes :8003\nsharingan/"]

    Casos --> DB[(MySQL / Aiven\nbase compartida)]
    OSINT --> DB
    Tracking --> DB
    Timeline --> DB
    Informes --> DB
```

Los puertos anteriores son los que asume por defecto el frontend (ver
`frontend/.env.example` y los `.env.example` de cada backend) — no son un
invento de este documento.

El patrón de comunicación es siempre el mismo:

```text
Módulo productor
      ↓
guarda su resultado en su tabla propia de MySQL
      ↓
otro módulo consulta esa tabla directamente (SQL propio, nunca importando
el modelo Python del dueño)
```

Ningún backend llama por HTTP a otro backend para obtener datos de negocio.
La única excepción es el propio frontend de Casos, que sí hace una llamada
HTTP a Tracking/Timeline/Informes (son "sus" backends, cada módulo expone su
propia API para que la UI la consuma) — pero eso es frontend→backend, no
backend→backend.

---

## 3. Tablas de integración (contrato compartido)

| Tabla | Propietario | Escritura | Lectura |
|---|---|---|---|
| `cases` | Casos | Casos | OSINT (referencia lógica opcional), Tracking, Timeline, Informes |
| `evidences` | Casos | Casos | Timeline, Informes |
| `osint_findings` | OSINT | OSINT | Timeline, Informes |
| `tracking_events` | Tracking | Tracking | Timeline, Informes |
| `timeline_events` | Timeline | Timeline | Informes |
| `reports` | Informes | Informes | Ninguno actualmente (es la hoja final del grafo; queda disponible para un futuro consumidor, p. ej. un dashboard) |

Detalle por tabla, verificado contra el código y el esquema real de Aiven:

### `cases` (propiedad de Casos)
Entidad central del sistema. Campos: `id`, `nombre`, `estado` (ENUM
`abierto`/`en_progreso`/`cerrado`/`archivado`), `fecha_creacion`,
`fecha_actualizacion`, `descripcion`, `responsable`, `eliminado`,
`fecha_eliminacion`. Es el identificador (`cases.id`) que enlaza todo lo
demás. Ningún otro módulo escribe en ella. `DELETE /cases/{id}` es un
borrado lógico (`eliminado=true`), nunca físico — ver CLAUDE.md, sección
`cases`, y `backend/app/modules/cases/service.py`.

### `evidences` (propiedad de Casos)
Material analizado del caso. FK `case_id → cases.id`, **`ON DELETE
CASCADE`** (vestigial desde el endurecimiento de Cases/Evidence: `cases`
ya no se borra físicamente, así que esa cascada no se ejercita, pero se
mantiene como red de seguridad). Campos añadidos: `fecha_adquisicion`
(timestamp forense, distinto de `fecha_subida`), `fecha_actualizacion`,
`hash_valor` (SHA-256 de `valor`, integridad), `eliminado`,
`fecha_eliminacion`. Timeline la lee para el origen `"evidence"` de la
cronología (excluye `eliminado=true` y prefiere `fecha_adquisicion` sobre
`fecha_subida` cuando existe); Informes la lee para el Anexo A del
informe.

### `osint_findings` (propiedad de OSINT)
Fila normalizada por cada análisis OSINT terminado (dominio, email, IP,
teléfono, wallet, imagen...). Campos clave: `case_type`, `source_table`,
`source_id`, `case_id` (nullable, **sin FK física** — referencia lógica
deliberada, ver §14), `subject_type`, `subject_value`, `risk_score`,
`risk_level`, `headline`, `flag_count`, `top_flags`, `details`,
`analyzed_at`, `created_at`. `UNIQUE(case_type, source_id)`. Timeline la lee
para el origen `"osint"`; Informes la lee para el Anexo B.

### `tracking_events` (propiedad de Tracking)
Eventos clasificados de un log post-incidente. FK `case_id → cases.id`,
**sin `ON DELETE CASCADE`**. Campos: `hora`, `evento`, `severidad` (ENUM
`baja`/`media`/`alta`/`critica`), `fuente_log`, `usuario_detectado`.
Timeline la lee para el origen `"tracking"`; Informes la lee para el
Anexo C.

### `timeline_events` (propiedad de Timeline)
Cronología consolidada del caso. FK `case_id → cases.id`, **`ON DELETE
CASCADE`**. Campos: `fecha_hora`, `descripcion`, `origen_modulo`,
`origen_id` (referencia lógica, **no FK física**, a la fila de origen en
`evidences`/`osint_findings`/`tracking_events` según `origen_modulo`),
`orden`. Índice compuesto `ix_timeline_events_origen (origen_modulo,
origen_id)`. Informes la lee para construir la columna vertebral del
documento (sin `timeline_events`, Informes no genera el informe — ver §11).

### `reports` (propiedad de Informes)
Informes periciales emitidos. FK `case_id → cases.id`, **sin `ON DELETE
CASCADE`** (deliberado: un informe pericial ya emitido no debe borrarse en
silencio al borrar el caso). `UNIQUE(case_id, version)`. Campos: además de
los oficiales (`fecha_generacion`, `resumen_ia`, `archivo_pdf`,
`generado_por`, `version`), tres columnas añadidas por Informes sobre el
modelo de datos oficial (`notas`, `huellas`, `opciones`) — documentadas y
justificadas en el propio código, pendientes de refrendo formal del equipo.

---

## 4. Integración por fases

### Fase 0 — Infraestructura común
Commit `86c85ddf75ec2113b8bcdb6188130d78520317e6`.

- Se creó la rama `development` a partir de `origin/modulo-casos`.
- Se configuró en `backend/alembic/env.py` una tabla de versión propia,
  `alembic_version_casos`, con `include_name` limitado a `{"cases",
  "evidences"}` — para que el Alembic de Casos nunca proponga tocar tablas
  de otro módulo, y para que su historial no comparta fila con el de nadie
  más.
- Se creó `backend/.env.example` (sin credenciales reales) y se corrigió
  `.gitignore` (el patrón `.env.*` estaba ocultando también los propios
  `.env.example`, sin querer).
- Se creó `docs/CONTRATOS.md`, documento vivo de referencia rápida sobre
  ownership de tablas, que se ha ido ampliando en cada fase posterior.

### Fase 1 — OSINT
Commit `c0eb0f245d61a2b2aefc9e5abee4a285518ffa92`.

- Se trajo `scam-shield/` completo a `development` como backend
  independiente, sin modificar la rama original.
- Se confirmó que `cases` sigue siendo la tabla canónica de Casos: el
  modelo interno de análisis de dominio de OSINT ya se llama
  `osint_domain_cases` en su propia tabla (no colisiona con `cases`).
- Se resolvió la única colisión real de rutas: el `cases_router` de OSINT
  (`GET /cases`, `GET /cases/{id}`) pasó de `prefix="/cases"` a
  `prefix="/domain-analysis-cases"`.
- Se añadió un campo `case_id` explícito (opcional, nunca inferido por
  heurística) a las 8 rutas de análisis que todavía no lo aceptaban, para
  que `osint_findings.case_id` se pueda rellenar de verdad.
- Se renombró la ruta antigua de generación de informes de OSINT,
  `POST /reports/generate`, a `POST /analysis/reports/generate` (colisionaba
  en namespace con el `/reports/generate` real, propiedad de Informes —
  aunque el conflicto real se resolvió formalmente en la Fase 4, el cambio
  de ruta ya quedó hecho aquí).
- Alembic de OSINT ya traía su propio aislamiento (`alembic_version_scamshield`,
  `include_name` limitado a sus tablas) desde `origin/scam-shield`.

### Fase 2 — Tracking
Commit `e5b0340bd85fa9153e6b8ebf50bc77a5cc425b8c`.

- Se trajo `track-inc/` completo como backend independiente.
- Se retiró el placeholder `app/modules/cases/` (un `Case`/`cases` mínimo
  que Tracking usaba para poder probarse en aislamiento mientras Casos no
  existía) — ya no hace falta, `cases` existe de verdad.
- `repository.py::case_exists` dejó de importar el modelo de Casos y pasó
  a una lectura SQL directa y mínima (`SELECT 1 FROM cases WHERE id = :id`):
  acceso directo a la tabla compartida, nunca al código de otro backend.
- Se añadió el endpoint `GET /cases-lookup` (proyección propia de Tracking
  sobre `cases`, solo `id`/`nombre`/`estado`) para el selector de caso del
  frontend, ya que antes ese selector llamaba por error al mismo backend
  que Casos, asumiendo un único proceso.
- Se configuró `alembic_version_tracking` con `include_name` limitado a
  `{"tracking_events"}`.
- El frontend de Tracking se integró en `frontend/src/modules/tracking/`,
  con una variable de entorno propia, `VITE_TRACKING_API_URL`, para no
  depender del backend de Casos. Puerto de desarrollo: `8001`.

### Fase 3 — Timeline
Commit `41167abb92578af0492a94388484b14000030d73`.

- Se extrajo el código de `origin/feature/timeline-integration` (donde
  vivía dentro del proceso de Casos) a un backend propio e independiente,
  `timeline/`, puerto de desarrollo `8002`.
- Lee `tracking_events`, `evidences` y `osint_findings` con SQL directo y
  mínimo, filtrando siempre por `case_id` explícito — en particular,
  `osint_findings` se filtra por `case_id` real, **nunca** por
  `subject_value`, dominio ni ninguna otra heurística.
- Genera y persiste `timeline_events` mediante un **snapshot/refresco
  completo**, no incremental:
  ```text
  DELETE FROM timeline_events WHERE case_id = X
          ↓
  lee tracking_events + evidences + osint_findings del caso X
          ↓
  ordena por (fecha_hora, origen_modulo, origen_id)
          ↓
  INSERT de todas las filas resultantes, con `orden` recalculado desde 1
  ```
  Cada llamada a `POST /timeline/cases/{id}/refresh` reconstruye la
  cronología entera del caso desde cero a partir de las tablas fuente.
- Se añadió `ON DELETE CASCADE` en la FK `timeline_events.case_id →
  cases.id` en el modelo del nuevo backend, reflejando la estructura que
  ya existía realmente en Aiven (no se introdujo, se documentó).
- Alembic propio (`alembic_version_timeline`), `include_name` limitado a
  `{"timeline_events"}`.
- El frontend se reescribió usando `shared/ui` (antes tenía estilos
  inline) y se eliminó un `case_id` de prueba (`8`) que quedaba
  hardcodeado por defecto en el formulario.

### Fase 4 — Informes
Commit `842ff62c12ce96befa1ba49e311a5b96c058cfa9`.

- Se trajo `sharingan/` completo como backend independiente, puerto de
  desarrollo `8003`.
- Endpoints: `POST /reports/generate`, `GET /reports/{id}`,
  `GET /reports/{id}/download`, `GET /reports/{id}/prompt`,
  `GET /cases/{case_id}/reports` (lectura anidada, no reivindica `/cases`).
- Lee `cases`, `evidences`, `osint_findings` (con fallback documentado a
  `osint_results`, la tabla del modelo de datos oficial que nunca llegó a
  implementarse), `tracking_events` y `timeline_events` mediante modelos
  Python **locales de solo lectura** (`app/modules/shared/models.py`) —
  nunca importa el código de otro backend. Escribe únicamente `reports`.
- Genera el informe en 4 formatos (PDF, DOCX, HTML, JSON), calcula una
  huella SHA-256 de cada fichero emitido (incluida la transcripción del
  prompt enviado a la IA) y la guarda en `reports.huellas`; al descargar,
  verifica que el fichero en disco coincide con esa huella antes de
  servirlo.
- El versionado de informes (`reports.version`) usa `MAX(version)+1` con
  reintento ante colisión de la restricción `UNIQUE(case_id, version)` —
  no depende solo del cálculo en memoria, la propia base de datos actúa
  como red de seguridad ante condiciones de carrera.
- Se resolvió formalmente el conflicto de rutas `/reports/generate` entre
  OSINT e Informes: Informes es su único propietario real.
- Alembic propio (`alembic_version_sharingan`, cadena `m5_0001..m5_0005`),
  ya traía desde `origin/sharingan` el mismo aislamiento por
  `include_name` que el resto de módulos.

### Fase 5.3B — Convergencia del índice de Timeline
Commit `1ef8c64`.

Migración `timeline/alembic/versions/0003_add_composite_index_origen.py`:
añade únicamente el índice `ix_timeline_events_origen` sobre
`(origen_modulo, origen_id)` en `timeline_events`. No crea tablas, no
modifica columnas, no toca ninguna FK ni ninguna otra tabla — es
puramente aditiva, y existe porque `CLAUDE.md` exige ese índice para
Timeline y la versión original de la tabla no lo tenía. La cadena de
Timeline quedó en `0001 → 0002 → 0003`.

### Fase 5.4 — Estado de integración (no es una auditoría, es el estado vigente)

- Las cinco ramas originales (`modulo-casos`, `scam-shield`, `track-inc`,
  `feature/timeline-integration`, `sharingan`) siguen existiendo en el
  remoto, intactas.
- Cada uno de los cinco backends tiene su propia tabla de versión de
  Alembic en la base compartida: `alembic_version_casos`,
  `alembic_version_scamshield`, `alembic_version_tracking`,
  `alembic_version_timeline`, `alembic_version_sharingan`.
- Existe además una tabla `alembic_version` (sin sufijo), histórica de un
  momento anterior a esta integración en el que Casos y Timeline
  compartían la tabla de versión por defecto — ya no la usa ningún
  backend, se conserva sin tocar como vestigio documentado.
- Las seis tablas contractuales (`cases`, `evidences`, `osint_findings`,
  `tracking_events`, `timeline_events`, `reports`) existen en la base
  compartida, con datos reales, y su esquema coincide con lo que cada
  backend espera.
- `timeline_events` tiene su índice compuesto `ix_timeline_events_origen`
  desde la Fase 5.3B.
- Las cinco migraciones/versiones de Alembic conviven en la misma base sin
  pisarse entre sí, cada una con su propio alcance y su propia tabla de
  versión.

---

## 5. Alembic

Cada backend gestiona **únicamente sus propias tablas** con Alembic, y
sella su propio historial en una tabla de versión con nombre propio — nunca
la tabla `alembic_version` por defecto, para no compartir fila con el
historial de otro backend que apunte a la misma base.

| Backend | Directorio | Tabla de versión | Tablas que puede gestionar |
|---|---|---|---|
| Casos | `backend/` | `alembic_version_casos` | `cases`, `evidences`, `case_audit_log` |
| OSINT | `scam-shield/` | `alembic_version_scamshield` | `osint_findings` + tablas internas de OSINT |
| Tracking | `track-inc/` | `alembic_version_tracking` | `tracking_events` |
| Timeline | `timeline/` | `alembic_version_timeline` | `timeline_events` |
| Informes | `sharingan/` | `alembic_version_sharingan` | `reports` |

Este aislamiento se implementa en cada `alembic/env.py` con dos mecanismos:
`version_table=<nombre propio>` (dónde se guarda el historial) e
`include_name` (una función que solo deja pasar, para autogenerate, las
tablas que ese backend realmente posee) — así un `alembic revision
--autogenerate` en un backend nunca puede proponer tocar la tabla de otro,
aunque por error se importara su modelo.

Cada backend se gestiona **desde su propio directorio**, con su propio
entorno virtual activado:

```bash
cd backend      && alembic current && alembic history && alembic heads
cd scam-shield  && alembic current && alembic history && alembic heads
cd track-inc    && alembic current && alembic history && alembic heads
cd timeline     && alembic current && alembic history && alembic heads
cd sharingan    && alembic current && alembic history && alembic heads
```

`alembic upgrade head` aplicaría, desde cada uno de esos directorios, solo
las migraciones pendientes de ese backend concreto — nunca las de otro.
**No es necesario ejecutar ningún `upgrade` para poner al día un checkout
nuevo de la base ya existente**: las tablas contractuales y las tablas de
versión ya existen en Aiven con el contenido correcto (ver §4, Fase 5.3B);
un `upgrade head` normal en cada backend, contra esa misma base, no
encontraría nada pendiente que aplicar.

**Excepción vigente — Casos (rama `feature/cases-evidence-hardening`)**:
las migraciones `0002` (soft-delete + `fecha_actualizacion`), `0003`
(`hash_valor` con backfill + `fecha_adquisicion`) y `0004`
(`case_audit_log`) existen en el repositorio pero **no se han aplicado
contra Aiven en esta tarea**, a propósito: `alembic/env.py` ya documentaba
desde Fase 0 que la tabla `alembic_version` por defecto de Aiven está en
un estado que requiere un `stamp` explícito y autorizado antes del primer
`upgrade` real contra esa base (ver comentario en `alembic/env.py`), y esa
autorización sigue sin darse. Las migraciones se han validado localmente
(cadena de revisiones sin bifurcaciones, `Base.metadata.create_all` contra
SQLite en toda la suite de tests) pero no contra MySQL real — no se ha
podido levantar un MySQL local en este entorno para probarlas con el motor
de producción antes de tocar Aiven. **Antes de ejecutar `alembic upgrade
head` en `backend/` contra Aiven**, revisar ese comentario y confirmar el
`stamp` pendiente.

---

## 6. Base de datos Aiven

Todos los backends apuntan a **la misma instancia MySQL gestionada por
Aiven**, a la misma base de datos dentro de ella (el nombre exacto vive
solo en cada `.env` local, nunca en este documento). No hay una base por
módulo: la integración se basa precisamente en que todos comparten el
mismo esquema físico.

Variables de entorno necesarias para la conexión (ver §7 para el detalle
completo, sin valores reales):

- Casos, OSINT: `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DB`.
- Tracking, Timeline, Informes: una única `DATABASE_URL` con el DSN completo
  (`mysql+pymysql://usuario:contraseña@host:puerto/basededatos`).

La conexión requiere TLS (Aiven lo exige); el cliente `mysql` de línea de
comandos necesita `--ssl-mode=REQUIRED` explícito. Los drivers Python
(`pymysql`) han negociado TLS correctamente sin configuración adicional en
las pruebas realizadas durante esta integración.

Tablas por módulo: ver la tabla completa de §3. En resumen, `cases` y
`evidences` son de Casos; `osint_findings` (más ~15 tablas internas no
contractuales) es de OSINT; `tracking_events` es de Tracking;
`timeline_events` es de Timeline; `reports` es de Informes.

---

## 7. Variables de entorno

| Variable | Módulo | Obligatoria | Función | Ejemplo |
|---|---|---|---|---|
| `MYSQL_HOST` | Casos, OSINT | Sí (para arrancar contra MySQL real) | Host de Aiven | `localhost` (ver `.env.example`; en producción, el host real de Aiven) |
| `MYSQL_PORT` | Casos, OSINT | Sí | Puerto de Aiven | `3306` |
| `MYSQL_USER` | Casos, OSINT | Sí | Usuario de la BD | `nexus_user` |
| `MYSQL_PASSWORD` | Casos, OSINT | Sí | Contraseña de la BD | — (nunca en `.env.example`) |
| `MYSQL_DB` | Casos, OSINT | Sí | Nombre de la base | `nexus` |
| `DATABASE_URL` | Tracking, Timeline, Informes | Sí | DSN completo de conexión | `mysql+pymysql://usuario:contraseña@host:3306/nexus` |
| `DB_URL` | OSINT | No | Alternativa a `MYSQL_*`: fuerza SQLite local para desarrollo 100% offline | `sqlite:///./scamshield_local.db` |
| `ANTHROPIC_API_KEY` | OSINT, Informes | **Solo Informes**: sí, para completar `POST /reports/generate` (ver §14). En OSINT es opcional (narrativa de email con IA) | Clave de la API de Anthropic | — |
| `REPORTS_STORAGE_DIR` | Informes | No (tiene valor por defecto) | Carpeta donde se guardan los PDF/DOCX/HTML/JSON generados | `./storage/reports` |
| `VIRUSTOTAL_API_KEY` | OSINT | No, opcional | Señal adicional en el análisis de dominio/IP | — |
| `ABUSEIPDB_API_KEY` | OSINT | No, opcional | Reputación de IP | — |
| `ETHERSCAN_API_KEY`, `TRON_API_KEY` | OSINT | No, opcional | Consulta de wallets | — |
| `OPENSPAM_API_KEY`, `IPQUALITYSCORE_API_KEY`, `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN` | OSINT | No, opcional | Señales de análisis de teléfono | — |
| `SERPAPI_API_KEY`, `PIMEYES_API_KEY` | OSINT | No, opcional | Búsqueda inversa/facial de imágenes | — |
| `FCA_API_EMAIL`, `FCA_API_KEY` | OSINT | No, opcional (las dos juntas o ninguna) | Registro de entidades financieras (Reino Unido) | — |
| `PUBLIC_BASE_URL` | OSINT | No, opcional | URL pública de la instancia, para que SerpApi pueda descargar la imagen a analizar | — |
| `VITE_API_BASE_URL` | Frontend | Sí | Backend de Casos | `http://localhost:8000` |
| `VITE_OSINT_API_URL` | Frontend | Sí | Backend de OSINT y Fraude | `http://localhost:8124` |
| `VITE_TRACKING_API_URL` | Frontend | Sí | Backend de Tracking | `http://localhost:8001` |
| `VITE_TIMELINE_API_URL` | Frontend | Sí | Backend de Timeline | `http://localhost:8002` |
| `VITE_REPORTS_API_URL` | Frontend | Sí | Backend de Informes | `http://localhost:8003` |

Ninguna de estas variables tiene un valor real en este documento ni en los
`.env.example` del repositorio — todos son valores de ejemplo o vacíos.

**Convención `localhost` vs `127.0.0.1`**: todo lo anterior usa siempre
`localhost`, nunca `127.0.0.1`, y esto no es solo estético. Para CORS,
`http://localhost:5173` y `http://127.0.0.1:5173` son **orígenes distintos**
aunque resuelvan a la misma máquina — Casos (`backend/app/main.py`) solo
permite explícitamente el primero en su `allow_origins`. Por eso:
- El frontend **se abre siempre en `http://localhost:5173`**, nunca en
  `http://127.0.0.1:5173` (si no, Casos rechazará sus peticiones por CORS).
- Las variables `VITE_*_URL` de arriba (destinos, no el origen del propio
  frontend) se mantienen también en `localhost` por coherencia, aunque para
  CORS solo importe el origen desde el que se sirve la página, no el host al
  que apunta el `fetch`.

---

## 8. Backends: cómo arrancar cada uno

Todos son aplicaciones FastAPI servidas con `uvicorn app.main:app`. Cada uno
necesita su propio entorno virtual de Python (dependencias distintas, a
veces versiones distintas de la misma librería).

| Módulo | Directorio | Instalación | Arranque | Puerto por defecto | `/health` | `/openapi.json` |
|---|---|---|---|---|---|---|
| Casos | `backend/` | `pip install -r requirements.txt` | `uvicorn app.main:app --reload --port 8000` | 8000 | `GET /health` | sí |
| OSINT | `scam-shield/` | `pip install -r requirements.txt` | `uvicorn app.main:app --reload --port 8124` | (sin fijar; se recomienda 8124 para convivir con Casos) | `GET /health` | sí |
| Tracking | `track-inc/` | `pip install -r requirements.txt` | `uvicorn app.main:app --reload --port 8001` | 8001 | *(no tiene `/health`; usar `GET /` como comprobación de vida)* | sí |
| Timeline | `timeline/` | `pip install -r requirements.txt` | `uvicorn app.main:app --reload --port 8002` | 8002 | `GET /health` | sí |
| Informes | `sharingan/` | `pip install -r requirements.txt` | `uvicorn app.main:app --reload --port 8003` | 8003 | `GET /health` | sí |

Variables necesarias para arrancar cada uno: ver §7. Casos/OSINT necesitan
las 5 variables `MYSQL_*` (o `DB_URL`/SQLite en OSINT); Tracking/Timeline/
Informes necesitan `DATABASE_URL`. Importante: **Tracking comprueba el
esquema de la base en el arranque** (`_verificar_esquema()` en su
`lifespan`) y **no arranca** si no puede conectar o si falta alguna tabla
que su modelo declara — es un comportamiento deliberado para no divergir en
silencio del esquema real.

`scam-shield/requirements-dev.txt`, `timeline/requirements-dev.txt` y
`sharingan/requirements-dev.txt` añaden `pytest`/`httpx` (y en el caso de
Informes, `pypdf`) para poder ejecutar la suite de tests de cada backend.

### 8.1. Estado de la configuración local frente a Aiven

Los 5 backends tienen ya su `.env` local (no versionado, ver §7 y
`.gitignore`) con las mismas credenciales de la instancia MySQL de Aiven —
mismo host, puerto, usuario, contraseña y base de datos en los 5. Se ha
verificado, con una conexión real de solo lectura (`SELECT 1`, sin tocar
esquema ni datos), que los 5 autentican y conectan correctamente contra esa
base compartida.

**Pendiente conocido**: `track-inc` y `timeline` **no cargan su `.env`
automáticamente** — a diferencia de Casos, OSINT e Informes (que usan
`pydantic-settings` con `env_file=".env"`), sus `app/core/database.py` leen
`DATABASE_URL` directamente de `os.environ`, sin `python-dotenv` de por
medio. Esto significa que, aunque su `.env` ya tiene la `DATABASE_URL` de
Aiven correcta, **arrancarlos con `uvicorn`/`npm run dev:all` seguirá
usando el valor por defecto hardcodeado** (`mysql+pymysql://nexus:nexus@localhost:3306/nexus`)
hasta que se resuelva de una de estas formas:
- exportar `DATABASE_URL` como variable de entorno real del shell antes de
  arrancar esos dos procesos, o
- añadir `python-dotenv` + `load_dotenv()` a sus `database.py` (cambio de
  código, no tocado todavía a propósito, pendiente de decisión explícita).

---

## 9. Frontend

Estructura real (`frontend/src/`):

```text
frontend/src/
├── app/
│   └── router.tsx          # único punto que conecta rutas con páginas
├── shared/
│   ├── ui/                 # Button, Input, Select, Card, DataTable, StatusBadge, Modal, Alert, Icon
│   └── layout/              # AppShell, SideNav, TopBar, TableWithDrawerLayout
└── modules/
    ├── cases/               # Módulo 1, backend propio (VITE_API_BASE_URL)
    ├── osint/               # Módulo 2, backend propio (VITE_OSINT_API_URL), rutas propias (ver abajo)
    ├── tracking/             # UI integrada aquí, backend propio (VITE_TRACKING_API_URL)
    ├── timeline/             # UI integrada aquí, backend propio (VITE_TIMELINE_API_URL)
    └── reports/               # UI integrada aquí, backend propio (VITE_REPORTS_API_URL)
```

Regla de dependencia (ya existente antes de esta integración, respetada en
las cinco fases): `modules/*` puede importar `shared/*`; `shared/*` nunca
importa `modules/*`; un módulo nunca importa otro módulo.

**OSINT ya no tiene un frontend propio y separado.** Hasta esta fase existía
`scam-shield/frontend/`, una segunda aplicación Vite completa que había que
arrancar e instalar por separado (puerto 5174), y `modules/osint/` en el
frontend común era solo un enlace ("Abrir OSINT y Fraude") que abría esa
segunda pestaña. Eso dejó de cumplir el objetivo de un único punto de
entrada, así que su UI se integró directamente en `frontend/`:

- `modules/osint/` en `frontend/src` es hoy una copia de
  `scam-shield/frontend/src/modules/osint/` (rutas, páginas, componentes,
  clientes API, tipos y estado — `SelectionContext`), montada bajo
  `/osint/*` en `app/router.tsx` con sus propias sub-rutas (`domain`,
  `email`, `wallet`, `typosquatting`, `phone`, `cnmv`, `image`, `ip`,
  `monitoring`, `cases`, `report`), en vez de una sola página.
- Solo se copió `modules/osint/**`. Los `shared/ui` y `shared/layout`
  propios que tenía `scam-shield/frontend` (una bifurcación casi idéntica a
  los del frontend común, con dos diferencias reales: un tono `error` en
  `StatusBadge` y un `SideNav` con las mismas entradas pero apuntando a
  `/osint`) se descartaron — el único cambio real que hizo falta traer fue
  añadir ese tono `error` a `shared/ui/StatusBadge` (aditivo: no cambia los
  tonos existentes), porque varios componentes de OSINT lo usan para
  severidad/riesgo.
- Los ficheros que referenciaban `VITE_API_BASE_URL` (`api/httpClient.ts`,
  `api/reportApi.ts`) se cambiaron a `VITE_OSINT_API_URL`: esa variable ya
  la usa `modules/cases` para *su* backend (puerto 8000), y OSINT es un
  backend distinto (puerto 8124) — mismo motivo por el que Tracking,
  Timeline e Informes ya tenían cada uno la suya.
- El backend de OSINT (`scam-shield/app/`) **no se ha tocado**: sigue siendo
  el mismo proceso independiente en el puerto 8124, con su misma API. Su
  frontend integrado le habla por HTTP exactamente igual que antes lo hacía
  `scam-shield/frontend` — sigue siendo frontend→backend, nunca
  backend→backend.
- **`scam-shield/frontend/` no se ha borrado** (queda como referencia/copia
  de seguridad hasta confirmar que la integración cubre todo su alcance) y
  sigue siendo instalable/arrancable por separado si hiciera falta, pero
  `npm run dev:all` ya no lo arranca — ya no hace falta abrir `:5174` para
  nada.

Instalación y arranque:
```bash
cd frontend
npm install
npm run dev              # desarrollo, http://localhost:5173 por defecto
npm run build             # build de producción -> frontend/dist/
```

**En Windows, si `npm run build` falla con `Cannot find module ... .node`:** el
`package-lock.json` se generó en otra plataforma y `npm install` puede dejarse
los binarios nativos de Windows. Se instalan a mano, los tres en el mismo
comando:

```bash
cd frontend
npm install --no-save @rolldown/binding-win32-x64-msvc@1.2.3 \
  lightningcss-win32-x64-msvc@1.32.0 @tailwindcss/oxide-win32-x64-msvc@4.3.3
```

Las versiones tienen que coincidir con las de `rolldown`, `lightningcss` y
`@tailwindcss/oxide` que resuelva el lock; si el lock cambia, hay que ajustarlas.

---

## 10. Endpoints por backend

```text
Casos (backend/, puerto 8000)
  POST   /cases
  GET    /cases
  GET    /cases/{case_id}
  PUT    /cases/{case_id}
  DELETE /cases/{case_id}
  POST   /cases/{case_id}/evidences
  GET    /cases/{case_id}/evidences
  GET    /cases/{case_id}/evidences/{evidence_id}
  PUT    /cases/{case_id}/evidences/{evidence_id}
  DELETE /cases/{case_id}/evidences/{evidence_id}
  GET    /health

OSINT (scam-shield/, puerto 8124 recomendado)
  POST   /analysis/domain            (y equivalentes: /analysis/email, /analysis/ip,
                                       /analysis/phone, /analysis/wallet, /analysis/cnmv-check,
                                       /analysis/typosquatting, /analysis/image)
  GET    /domain-analysis-cases
  GET    /domain-analysis-cases/{case_id}
  GET    /osint-findings
  GET    /osint-findings/{finding_id}
  POST   /analysis/reports/generate  (PDF de riesgo propio de OSINT, no toca `reports`)
  POST   /analysis/consolidated
  GET    /health

Tracking (track-inc/, puerto 8001)
  GET    /cases-lookup
  POST   /cases/{case_id}/tracking/analyze
  POST   /cases/{case_id}/tracking/events
  GET    /cases/{case_id}/tracking/events
  GET    /cases/{case_id}/tracking/verify
  GET    /                            (comprobación de vida; no hay /health)

Timeline (timeline/, puerto 8002)
  GET    /timeline/cases/{case_id}
  POST   /timeline/cases/{case_id}/refresh
  GET    /health

Informes (sharingan/, puerto 8003)
  POST   /reports/generate
  GET    /reports/{report_id}
  GET    /reports/{report_id}/download
  GET    /reports/{report_id}/prompt
  GET    /cases/{case_id}/reports
  GET    /health
```

Ninguno de los cinco reivindica un `/cases` propio con CRUD completo salvo
Casos; ninguno reivindica `/reports` propio salvo Informes.

---

## 11. Flujo funcional completo

```text
 1. POST /cases (Casos)                     → INSERT en cases
 2. POST /cases/{id}/evidences (Casos)       → INSERT en evidences
 3. POST /analysis/domain (OSINT, con case_id) → INSERT en osint_domain_cases
                                                  + INSERT en osint_findings (case_id relleno)
 4. GET /osint-findings?case_id=X (OSINT)    → lectura, para localizar el finding generado
 5. POST /cases/{id}/tracking/analyze (Tracking) → sube un log, devuelve preview clasificado
                                                     (no persiste nada todavía)
 6. POST /cases/{id}/tracking/events (Tracking)  → INSERT en tracking_events
 7. POST /timeline/cases/{id}/refresh (Timeline) → DELETE + INSERT en timeline_events,
                                                     leyendo evidences + tracking_events +
                                                     osint_findings del caso
 8. POST /reports/generate (Informes)         → lee cases + evidences + osint_findings +
                                                  tracking_events + timeline_events,
                                                  genera narrativa con IA,
                                                  INSERT en reports,
                                                  escribe los 4 ficheros en disco
 9. GET /reports/{id} (Informes)              → confirma persistencia
10. GET /reports/{id}/download?formato=pdf     → descarga el PDF real
11. Verificación de integridad                 → cabecera X-Informe-SHA256 comparada contra
                                                   el hash del fichero descargado
```

En cada paso, la única información que viaja entre módulos es el
`case_id` — nunca el contenido completo de lo que hizo el módulo anterior.

---

## 12. Despliegue local

### 1. Requisitos
- Python 3.12 (o compatible con FastAPI/SQLAlchemy 2.x)
- Node.js reciente (para Vite/React 19)
- Acceso de red a la instancia MySQL de Aiven (o un MySQL local para
  desarrollo 100% offline)
- Cinco entornos virtuales de Python independientes (uno por backend)

### 2. Clonado
```bash
git clone https://github.com/dacaror-tlco/DFIR-Nexus.git
cd DFIR-Nexus
git checkout development
```

### 3. Configuración de `.env`
Copiar el `.env.example` de cada backend y de `frontend/` a `.env`, y
rellenar con las credenciales reales (nunca subir estos ficheros a Git):
```bash
cp backend/.env.example backend/.env
cp scam-shield/.env.example scam-shield/.env
cp track-inc/.env.example track-inc/.env
cp timeline/.env.example timeline/.env
cp sharingan/.env.example sharingan/.env
cp frontend/.env.example frontend/.env
```

### 4. Instalación de dependencias

Cada backend sigue siendo un proceso Python independiente, con su propio
entorno virtual (esto **no ha cambiado**: el launcher de la sección 6 no
fusiona nada, solo automatiza arrancar los procesos que ya existían):
```bash
cd backend      && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt && deactivate && cd ..
cd scam-shield  && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt && deactivate && cd ..
cd track-inc    && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt && deactivate && cd ..
cd timeline     && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt && deactivate && cd ..
cd sharingan    && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt && deactivate && cd ..
```
En Windows, sustituir `source venv/bin/activate` por `venv\Scripts\activate`
(o simplemente omitir la activación: `pip install` funciona igual invocando
`venv\Scripts\pip.exe install -r requirements.txt`).

El **frontend usa `npm workspaces`** desde la raíz del repositorio, así que
una única instalación cubre el frontend principal y el de OSINT a la vez:
```bash
npm install
```

### 5. Migraciones
Con la base compartida ya existente (como la de Aiven usada durante esta
integración), no hace falta ejecutar ningún `upgrade` para un checkout
nuevo — las tablas y las tablas de versión ya están al día (ver §4/§5).
Si se levanta una base completamente vacía, cada backend debe ejecutar,
desde su propio directorio, `alembic upgrade head`.

### 6. Arranque de todo el sistema — un único comando

Desde la raíz del repositorio, con los cinco `.env` ya configurados (paso 3)
y los cinco entornos virtuales ya creados (paso 4):
```bash
npm run dev:all
```

Este comando **no fusiona los backends ni cambia su arquitectura**: es un
orquestador de desarrollo (`concurrently`, ejecutando
`scripts/run-backend.mjs`) que arranca, cada uno como su **propio proceso
independiente**, con su **propio intérprete Python** (el del `venv` de ese
backend):

```text
npm run dev:all
        │
        ├── Casos      (backend/venv)      → :8000
        ├── OSINT      (scam-shield/venv)  → :8124
        ├── Tracking   (track-inc/venv)    → :8001
        ├── Timeline   (timeline/venv)     → :8002
        ├── Informes   (sharingan/venv)    → :8003
        └── Frontend                       → :5173
```

Un único frontend: la UI de OSINT vive integrada en `frontend/` (§9), así
que su backend (:8124) sigue arrancando como proceso propio, pero ya no hay
un segundo `npm run dev` ni un segundo puerto de frontend que abrir.

La salida de cada proceso aparece en la misma terminal, con un prefijo de
color (`[CASOS]`, `[OSINT]`, `[TRACKING]`, `[TIMELINE]`, `[INFORMES]`,
`[FRONTEND]`) para poder distinguirlos. Si el `venv` de algún backend
todavía no existe, `run-backend.mjs` lo detecta y muestra el comando exacto
para crearlo, en vez de fallar con un error críptico.

Funciona igual en **Windows, Linux y macOS**: el propio script Node
(`scripts/run-backend.mjs`) resuelve la ruta del intérprete Python de cada
`venv` según el sistema operativo (`venv/bin/python` en Linux/macOS,
`venv\Scripts\python.exe` en Windows) — no depende de activar manualmente
ningún entorno virtual ni de sintaxis de shell específica de una plataforma.

**Alternativa manual** (útil para depurar un solo backend de forma
aislada, o si se prefiere no usar el launcher): seguir arrancando cada
proceso a mano, en su propia terminal, exactamente como antes:
```bash
# Terminal 1
cd backend && source venv/bin/activate && uvicorn app.main:app --reload --port 8000

# Terminal 2
cd scam-shield && source venv/bin/activate && uvicorn app.main:app --reload --port 8124

# Terminal 3
cd track-inc && source venv/bin/activate && uvicorn app.main:app --reload --port 8001

# Terminal 4
cd timeline && source venv/bin/activate && uvicorn app.main:app --reload --port 8002

# Terminal 5
cd sharingan && source venv/bin/activate && uvicorn app.main:app --reload --port 8003

# Terminal 6
cd frontend && npm run dev
```

(`scam-shield/frontend` sigue existiendo y se puede arrancar igual, a mano,
si hiciera falta depurarlo de forma aislada — pero no forma parte del flujo
normal: su UI ya vive integrada en `frontend/`, ver §9.)

### 7. Cómo detener todo
Con `npm run dev:all`, basta con **Ctrl+C una vez** en esa misma terminal:
`concurrently` propaga la señal a los seis procesos y los cierra a todos
(incluidos los procesos `uvicorn --reload`, que tienen su propio proceso
"reloader" hijo). Si por lo que sea algún proceso quedara colgado (poco
habitual, pero puede pasar si se mata la terminal en vez de usar Ctrl+C),
se puede liberar el puerto directamente:
```bash
# Linux/macOS
lsof -ti:8000 | xargs kill -9   # repetir con 8124, 8001, 8002, 8003, 5173

# Windows (PowerShell)
Get-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess | Stop-Process -Force
```

### 8. Comprobación mediante `/health`
```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8124/health
curl http://127.0.0.1:8001/            # Tracking no tiene /health
curl http://127.0.0.1:8002/health
curl http://127.0.0.1:8003/health
```

### 9. Acceso al frontend

**`http://localhost:5173` es el único sitio al que hace falta entrar a
mano** (siempre como `localhost`, nunca como `127.0.0.1` — ver §7, CORS).
Desde ahí se prueban Casos, Evidencias, OSINT y Fraude, Tracking, Timeline e
Informes: los cinco viven bajo esa misma UI (`/cases`, `/osint`,
`/tracking`, `/timeline`, `/reports`). Ya no hace falta abrir ningún otro
puerto de frontend. Los puertos 8000/8124/8001/8002/8003 son exclusivamente
para la comunicación frontend↔backend: no hace falta visitarlos
directamente salvo para depurar.

---

## 13. Despliegue en producción

### Infraestructura actualmente implementada
- Cinco backends FastAPI ejecutables de forma independiente con `uvicorn`.
- Una base de datos MySQL compartida ya alojada en Aiven, en uso real
  durante toda esta integración.
- Un `Dockerfile`/`docker-compose.yml` propios **solo en OSINT**
  (`scam-shield/deploy/`) y en Tracking (`track-inc/deploy/`) — el resto de
  módulos no tienen contenedorización propia todavía.
- Nada de reverse proxy, dominio público, CI/CD ni orquestador está
  implementado para el conjunto de los cinco backends.

### Infraestructura recomendada para producción — Pendiente / recomendado
```mermaid
graph TD
    Internet --> RP[Reverse Proxy\nnginx / Traefik]
    RP --> FE[Frontend\nbuild estático]
    RP --> Casos
    RP --> OSINT
    RP --> Tracking
    RP --> Timeline
    RP --> Informes
    Casos --> DB[(MySQL / Aiven)]
    OSINT --> DB
    Tracking --> DB
    Timeline --> DB
    Informes --> DB
```

Recomendaciones, ninguna implementada todavía:
- Un `Dockerfile` por backend (extender el patrón ya existente en
  OSINT/Tracking a Casos/Timeline/Informes) y un `docker-compose.yml`
  conjunto para levantar los cinco a la vez.
- Un reverse proxy único (nginx/Traefik) que resuelva el namespace de
  rutas de los cinco backends bajo un solo dominio, en vez de exponer cada
  puerto por separado.
- Un pipeline de CI/CD (tests + build + despliegue) — hoy la suite de
  tests de cada backend se ejecuta manualmente.
- Certificado HTTPS/TLS en el propio dominio de la aplicación (la conexión
  a Aiven ya usa TLS, pero eso es solo la base de datos).

---

## 14. Dependencias externas

| Dependencia | Módulo(s) | Obligatoria | Comportamiento si falta |
|---|---|---|---|
| MySQL/Aiven | Los cinco | **Sí** | Ningún backend puede operar sin conexión a la base compartida; Tracking incluso rechaza arrancar |
| Anthropic (`ANTHROPIC_API_KEY`) | Informes | **Sí**, para completar la generación del informe | `POST /reports/generate` responde `503` controlado (no `500`); no se inserta nada en `reports` |
| Anthropic | OSINT | No | Solo afecta a la narrativa en lenguaje sencillo de un análisis de email; el resto del análisis se completa igual |
| VirusTotal, AbuseIPDB, Etherscan/Tron, OpenSpam, SerpApi, PimEyes, IPQualityScore, Twilio, FCA Register | OSINT | No | Cada llamada externa está aislada en su propio bloque try/except: si falla o no hay clave, el análisis se completa igual con menos señales |
| WHOIS, crt.sh, Wayback Machine | OSINT | No (no requieren clave) | Servicios públicos sin autenticación; degradan igual que el resto si no responden |

**Confirmado en el código actual**: la generación completa de un informe
(`POST /reports/generate`) depende de `ANTHROPIC_API_KEY`. Sin ella, el
endpoint devuelve un error controlado y no persiste nada — no genera un
informe a medias.

---

## 15. Seguridad

> **Actualización (septiembre de 2026): autenticación y CORS, descritos más
> abajo como pendientes, están implementados.** Ver README §Autenticación y
> autorización y §Seguridad para el estado real (JWT HS256, roles
> `analyst`/`admin`, Argon2id, `CORS` restringido a `http://localhost:5173`
> en los 5 backends). Se conserva el resto de esta sección porque sigue
> siendo cierto (el problema de CORS-que-en-realidad-es-un-500 sigue
> siendo un problema real de FastAPI/Starlette, no algo que la autenticación
> resuelva) o porque sigue pendiente (HTTPS propio, firewall de Aiven,
> rotación de la credencial de `T1m3-l1n3`, logs/backups).

### Ya implementado
- Ningún `.env` real está versionado en el repositorio (`.gitignore`
  excluye `.env`/`.env.*`, con excepción explícita de los `.env.example`).
- Cabeceras `X-Content-Type-Options: nosniff` y `Referrer-Policy:
  no-referrer` en las respuestas de Informes.
- Política de seguridad de contenido (`Content-Security-Policy:
  default-src 'none'`) en la respuesta HTML del informe, para que un
  posible fallo de escapado nunca ejecute un script.
- Huella SHA-256 de cada fichero de informe emitido, verificada antes de
  servirlo (protección de integridad, no de acceso).
- Conexión a Aiven por TLS.
- **Autenticación (JWT) y autorización (roles) en los 5 backends** — ver
  nota de actualización arriba y el README.

### Recomendaciones futuras — Pendiente / recomendado
- **HTTPS** en las propias APIs (hoy se sirven en HTTP plano en local); en
  producción, terminar TLS en el reverse proxy.
- ~~**CORS**: Casos ya restringe...~~ Resuelto: los 5 backends restringen
  `allow_origins` a `http://localhost:5173` (ver README §Seguridad para el
  razonamiento sobre por qué eso no hacía falta tocarlo en el despliegue con
  gateway, y sí en desarrollo directo).

  Nota aparte, no confundir con lo anterior — un problema real ya
  encontrado y corregido: en FastAPI/Starlette, una excepción no controlada
  dentro de una ruta (p. ej. no poder conectar con MySQL) produce un 500
  "en bruto" que **no pasa por `CORSMiddleware`**. El navegador nunca ve la
  cabecera `Access-Control-Allow-Origin` y lo reporta como un bloqueo de
  CORS, aunque la configuración de CORS sea correcta — ocultando así el
  error real (p. ej. de conexión a la base de datos) detrás de un síntoma
  que no lo es. Un `@app.exception_handler(Exception)` normal **no basta**
  para arreglarlo (comprobado empíricamente): su respuesta tampoco
  atraviesa `CORSMiddleware`. Los cinco `main.py` llevan por eso un
  middleware HTTP (`@app.middleware("http") def
  convertir_errores_no_controlados`) que envuelve `call_next()` en un
  try/except — su respuesta sí es un `Response` ASGI normal que atraviesa
  `CORSMiddleware` igual que una respuesta correcta. Importante: debe
  registrarse **antes** de `app.add_middleware(CORSMiddleware, ...)` en el
  código fuente — Starlette anida los middlewares en orden inverso al de
  registro, así que lo último añadido queda más "por fuera" y no antes.
- ~~**Autenticación/autorización**: ninguno de los cinco backends tiene
  hoy...~~ Resuelto — ver nota de actualización arriba.
- **Firewall / acceso restringido a MySQL**: limitar qué orígenes pueden
  conectar a la instancia de Aiven a las IPs de los backends desplegados.
- **Rotación de credenciales**: el repositorio tiene, en el historial de
  la rama `T1m3-l1n3` (obsoleta, no integrada en `development`), una
  credencial de Aiven hardcodeada en texto plano — pendiente de rotación
  independientemente de esta integración.
- **Logs y backups**: no hay ninguna estrategia de logging centralizado ni
  de backup de la base compartida implementada todavía.

---

## 16. Estado actual del proyecto

> **Actualización (septiembre de 2026)**: el hueco de carga de `.env` en
> Tracking/Timeline de más abajo está resuelto desde hace tiempo (los dos lo
> cargan correctamente al arrancar); hay además un despliegue en contenedores
> del stack completo (`deploy/`, ver README §Despliegue) que no existía
> cuando se escribió esta sección. La necesidad de una `ANTHROPIC_API_KEY`
> real para generar informes (y, ahora también, para el asistente
> conversacional) sigue siendo cierta.

Los cinco módulos están integrados en `development` como backends
independientes, comunicándose exclusivamente a través de la base de datos
MySQL compartida de Aiven. Las seis tablas contractuales existen con datos
reales y su esquema coincide con lo que cada backend espera. Cada backend
tiene su propia cadena de migraciones Alembic, aislada de las demás.

**La prueba E2E completa (crear caso → evidencia → OSINT → tracking →
timeline → informe → descarga) sigue sin ejecutarse todavía como una única
pasada continua** (ver README §Flujo forense) — sí se ha verificado en vivo,
por separado, el tramo de identidad (login → Cases → OSINT → vinculación →
auditoría, dos procesos reales, sin mocks). Avance reciente: los 5
backends ya tienen `.env` local con las mismas credenciales de Aiven, y se
ha confirmado conexión real (lectura) contra la base compartida en los 5
(ver §8.1). Para completar la prueba E2E hace falta, como mínimo:
- Una `ANTHROPIC_API_KEY` real, sin la cual el paso de generación de
  informe (y el asistente conversacional) se detiene en un `503` controlado
  antes de escribir nada.
- Los cinco backends arrancados simultáneamente contra la base compartida
  (ya lo están habitualmente, vía `npm run dev:all`).

Las API keys externas de OSINT (VirusTotal, AbuseIPDB, Etherscan/Tron,
OpenSpam, SerpApi, PimEyes, IPQualityScore, Twilio, FCA Register) son
opcionales: su ausencia no bloquea ningún flujo, solo reduce las señales
disponibles en el análisis.

Pendiente adicional, ya identificado durante la integración: convergencia
definitiva de la tabla de versión `alembic_version` (histórica, sin dueño
hoy) en una futura fase de limpieza; decisión formal del equipo sobre las
tres columnas que Informes añadió a `reports` (`notas`, `huellas`,
`opciones`); rotación de la credencial expuesta en `T1m3-l1n3`.

---

## 17. Comandos rápidos

```bash
# --- todo el sistema a la vez (recomendado para desarrollo) ---
npm install        # instala el orquestador + los dos frontends (workspaces)
npm run dev:all    # arranca los 5 backends + los 2 frontends
# Ctrl+C una vez, en esa misma terminal, detiene todo.
# (los 5 venvs de Python de los backends hay que crearlos antes, ver abajo)
```

```bash
# instalar (una vez por backend)
cd backend     && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt
cd scam-shield && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt
cd track-inc   && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt
cd timeline    && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt
cd sharingan   && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt

# migrar (cada uno desde su propio directorio, con su venv activo)
cd backend     && alembic upgrade head
cd scam-shield && alembic upgrade head
cd track-inc   && alembic upgrade head
cd timeline    && alembic upgrade head
cd sharingan   && alembic upgrade head

# arrancar Casos
cd backend && uvicorn app.main:app --reload --port 8000

# arrancar OSINT
cd scam-shield && uvicorn app.main:app --reload --port 8124

# arrancar Tracking
cd track-inc && uvicorn app.main:app --reload --port 8001

# arrancar Timeline
cd timeline && uvicorn app.main:app --reload --port 8002

# arrancar Informes
cd sharingan && uvicorn app.main:app --reload --port 8003

# arrancar frontend
cd frontend && npm install && npm run dev

# build frontend
cd frontend && npm run build

# scam-shield/frontend (opcional/legacy — su UI ya vive integrada en
# frontend/src/modules/osint/, ver §9; no hace falta arrancarlo)
cd scam-shield/frontend && npm install && npm run dev
```
