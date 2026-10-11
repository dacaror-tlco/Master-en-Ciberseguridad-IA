# MCP Server — DFIR-Nexus

Sexto proceso independiente de DFIR-Nexus: un servidor **MCP (Model
Context Protocol)** que expone capacidades del proyecto como *tools*
invocables directamente por Claude, en vez de tener que ejecutar `curl` o
un test a mano en cada ocasión.

- **Transporte:** stdio (Claude Code lo lanza como subproceso; no abre
  ningún puerto de red propio).
- **Estado:** Fase 2A a 2I completadas — **veintidós tools**: trece de
  solo lectura, ocho de escritura (`confirmado: bool` obligatorio) y una
  de análisis sin persistencia, contra los 5 backends de Nexus. Auditoría
  final de cierre (Fase 2A-2I) realizada — ver commit/README de esa
  fecha; dos fallos reales de manejo de excepciones encontrados y
  corregidos (ver `app/core/auth.py` y `_validar_ruta_permitida` en
  `app/main.py`).
- **Lectura (13):** `consultar_caso(case_id)`, `buscar_casos(estado?,
  texto?)`, `consultar_auditoria_caso(case_id)`,
  `listar_evidencias_de_caso(case_id)`,
  `consultar_evidencia(case_id, evidence_id)`,
  `verificar_integridad_evidencia(case_id, evidence_id)`,
  `obtener_cronologia_caso(case_id)`, `listar_informes_de_caso(case_id)`,
  `consultar_informe(report_id)`,
  `listar_eventos_tracking(case_id, skip?, limit?)`,
  `verificar_integridad_tracking(case_id)`,
  `listar_hallazgos_osint(...filtros?)`, `consultar_hallazgo_osint(finding_id)`.
- **Escritura, con `confirmado: bool` obligatorio (8):**
  `recalcular_cronologia`, `crear_caso`, `cambiar_estado_caso`,
  `vincular_hallazgo`, `registrar_evidencia`, `guardar_eventos_tracking`,
  `generar_informe` (coste económico real, IA), `analizar_dominio` (red
  externa real, persiste un hallazgo).
- **Análisis sin persistencia, sin `confirmado` (1):** `analizar_log`
  (sube un fichero LOCAL dentro de un directorio permitido, ver más
  abajo).
- **Deliberadamente fuera de alcance** (ver "Estado actual / Próximas
  fases" más abajo para el detalle completo): `descargar_informe`,
  `consultar_evento_tracking` (Tracking no expone ningún endpoint REST
  de consulta individual de evento), los otros 7 análisis OSINT que
  ejecutan trabajo real, `DELETE /cases/{id}`, desvincular un hallazgo,
  editar/borrar evidencias, gestión de usuarios.

## Por qué es un proceso independiente

Los 5 backends de Nexus (Casos, OSINT, Tracking, Timeline, Informes) son
procesos Python separados, cada uno con su propio `venv`, sin código
compartido — regla explícita del proyecto (`CLAUDE.md`: "un módulo nunca
debe importar otro módulo"). Este servidor MCP respeta la misma regla
frente a los 5: **no importa el código de ningún backend**, habla con
ellos únicamente por HTTP, igual que ya hace el frontend. Por eso vive
como un sexto directorio al mismo nivel (`mcp-server/`), con su propio
`venv`, sus propias dependencias y su propio ciclo de vida — nunca dentro
de `backend/` ni de ningún otro módulo.

## Cómo se comunica con los backends

```
Claude
  │
  ▼
mcp-server (stdio)
  │  Authorization: Bearer <JWT>  (un solo login, contra Casos)
  │
  ├──▶ Casos     (http://localhost:8000)
  ├──▶ Timeline  (http://localhost:8002)
  ├──▶ Informes  (http://localhost:8003)
  ├──▶ Tracking  (http://localhost:8001)
  └──▶ OSINT     (http://localhost:8124)
```

Habla con los **5 backends de Nexus**. Toda la comunicación es HTTP
normal con `httpx`; el servidor MCP no tiene ninguna vía de acceso a la
base de datos ni a los backends que no sea la propia API REST ya
existente. Un único login basta para los cinco: comparten el mismo
`JWT_SECRET` (confirmado en la auditoría de arquitectura MCP), así que el
JWT que emite Casos también lo aceptan Timeline, Informes, Tracking y
OSINT sin autenticarse por separado en cada uno.

## Autenticación

- El servidor se autentica contra `POST /auth/login` **de Casos** (el
  único de los 5 backends que emite JWT) como un **usuario de servicio**
  (`mcp-server@nexus.local`, rol `analyst`), **nunca** como un analista
  humano. La cuenta se creó vía el mecanismo real del proyecto
  (`POST /auth/users`, autenticado como un admin ya existente) — no hay
  ningún script ni endpoint nuevo para esto.
- El JWT se guarda **únicamente en memoria** del proceso (`CasosSession`
  en `app/core/auth.py`) y se reutiliza para hablar con Timeline,
  Informes, Tracking y OSINT. Nunca se escribe en disco, nunca se
  imprime.
- Casos no tiene endpoint de *refresh* (`JWT_EXPIRE_MINUTES=120` en
  `backend/app/core/config.py`, sin mecanismo de renovación). Si una
  petición a cualquiera de los cinco backends recibe un 401, el servidor
  **reautentica una vez contra Casos** y repite esa petición; un segundo
  401 se propaga tal cual — insistir más no serviría, porque el sistema
  no tiene otra forma de renovar el token.
- Las credenciales del usuario de servicio viven **únicamente** en
  `mcp-server/.env` (no versionado — ver `.gitignore`), nunca en código.

## Tools disponibles

Trece son de **solo lectura** (`ToolAnnotations(readOnlyHint=True,
destructiveHint=False)` — sin `confirmado`: no modifican nada). Ocho
**escriben** (`recalcular_cronologia` — Fase 2F; `crear_caso`,
`cambiar_estado_caso`, `vincular_hallazgo` — Fase 2G; `registrar_evidencia`,
`guardar_eventos_tracking`, `generar_informe` — Fase 2H, esta última con
coste económico real; `analizar_dominio` — Fase 2I, con red externa real):
`ToolAnnotations(readOnlyHint=False, destructiveHint=True,
idempotentHint=False)` y `confirmado: bool` **obligatorio**, comprobado en
código antes de cualquier petición HTTP — la pista de protocolo por sí
sola nunca es la protección real (ver docstring de `recalcular_cronologia`
más abajo). Una es **análisis sin persistencia** (`analizar_log` — Fase
2I): ejecuta trabajo real, por lo que `readOnlyHint=False`, pero no
modifica ningún dato, por lo que no lleva `confirmado`.

### Casos (Fase 2A)

### `consultar_caso(case_id: int)`

Consulta el detalle de un caso de Nexus por su id. Llama a
`GET /cases/{case_id}` en Casos.

```
Claude invoca la tool  consultar_caso(case_id=7)
        │
        ▼
mcp-server valida case_id > 0, añade el JWT en memoria,
llama GET http://localhost:8000/cases/7
        │
        ▼
Casos responde 200 con el caso, o 404 si no existe
        │
        ▼
mcp-server devuelve:
  {"encontrado": true,  "caso": {...}}                    (200)
  {"encontrado": false, "case_id": 7, "mensaje": "..."}    (404 — respuesta
                                                             válida, no un error)
```

> **Formato de respuesta**: `consultar_caso` conserva su forma original
> (`encontrado`/`caso`/`mensaje`), tal y como se validó de extremo a
> extremo en el MVP. **No** se ha migrado al formato común de abajo — se
> evaluó y se decidió no tocar un contrato ya probado con Claude Code sin
> necesidad real de hacerlo. Las dos tools nuevas de la Fase 2A sí lo
> usan desde el principio; una unificación de las tres queda como mejora
> opcional para una fase futura, no como parte de esta.

### `buscar_casos(estado: str | None, texto: str | None)`

Llama a `GET /cases` (la API de Casos no tiene filtros por query param) y
filtra **en el propio MCP Server**:

- Sin filtros → todos los casos.
- `estado` → coincidencia exacta contra uno de los 4 valores reales del
  modelo (`abierto`, `en_progreso`, `cerrado`, `archivado`); cualquier
  otro valor se rechaza con `ToolError` antes de llamar a Casos.
- `texto` → coincidencia parcial, sin distinguir mayúsculas/minúsculas,
  sobre `nombre`, `responsable` y `descripcion`.
- Con los dos filtros a la vez → **AND lógico** (un caso debe cumplir
  ambos).

```
{"estado": "ok", "datos": {"total": 2, "casos": [...]}}
```

### `consultar_auditoria_caso(case_id: int)`

Llama a `GET /cases/{case_id}/auditoria` (el endpoint real, sin inventar
ninguno nuevo). Mismo tratamiento de 404 que `consultar_caso`
("no_encontrado" como resultado válido, no como error):

```
{"estado": "ok", "datos": {"entradas": [...]}}
{"estado": "no_encontrado", "detalle": "No existe ningún caso con id=999 en Nexus."}
```

### `crear_caso(nombre: str, responsable: str, confirmado: bool, descripcion: str | None, estado: str | None)` — ⚠️ MODIFICA DATOS (Fase 2G)

Llama a `POST /cases` (puerto 8000). `nombre`/`responsable` son
obligatorios y se validan **no vacíos antes de tocar la red** (el esquema
del backend, `CaseBase`, no lo exige por su cuenta). `estado` es opcional
— si no se indica, el backend decide el valor por defecto (`abierto`), la
tool no lo fuerza; si se indica, se valida contra los cuatro valores
reales de `EstadoCaso` antes de enviarlo.

`confirmado` es **obligatorio**, comprobado **antes de tocar la red** —
mismo mecanismo que `recalcular_cronologia` (Fase 2F): con
`confirmado=false` no se emite ninguna petición HTTP.

```
{"estado": "ok", "datos": {"id": 42, "nombre": "...", "estado": "abierto", ...}}
```

No hay ningún conflicto de dominio posible al crear (no hay nombres
únicos ni restricciones de negocio en el alta): el único error real,
aparte de 401/422/5xx genéricos, es un 422 si algo se cuela sin validar
aquí.

### `cambiar_estado_caso(case_id: int, nuevo_estado: str, confirmado: bool)` — ⚠️ MODIFICA DATOS (Fase 2G)

Llama a `PUT /cases/{case_id}` enviando **únicamente** `{"estado":
nuevo_estado}` — `CaseUpdate` tiene todos los campos opcionales y el
backend aplica `exclude_unset=True` (`service.update_case`), así que
nombre/responsable/descripción quedan intactos. `nuevo_estado` se valida
contra los cuatro valores reales de `EstadoCaso` antes de tocar la red.
Mismo mecanismo de `confirmado` obligatorio, comprobado antes de
cualquier petición HTTP.

```
{"estado": "ok",         "datos": {"id": 8, "estado": "en_progreso", ...}}
{"estado": "no_encontrado", "detalle": "Caso no encontrado"}
{"estado": "conflicto",     "detalle": "Transición de estado no permitida: archivado -> abierto"}
```

> **Limitación real, verificada en el código
> (`backend/app/modules/cases/state_machine.py`)**: no todas las
> transiciones están permitidas (`archivado` es terminal e inmutable;
> `en_progreso` no puede saltar directo a `archivado`, etc.), y un caso
> eliminado lógicamente tampoco admite cambios. Las tres causas —
> transición inválida, caso archivado, caso eliminado — devuelven el
> mismo HTTP 409 con `detail` distinto: esta tool no intenta adivinar
> cuál fue, propaga el mensaje real del backend bajo `estado="conflicto"`
> en vez de inventar una distinción que el backend no da explícitamente
> en el código de estado.

### Evidencias (Fase 2B)

### `listar_evidencias_de_caso(case_id: int)`

Llama a `GET /cases/{case_id}/evidences`. Las evidencias son un
**sub-recurso de Casos** — no tienen backend, puerto ni id propios fuera
de un caso concreto (ver `CLAUDE.md`). Distingue tres situaciones
distintas, no solo dos:

```
{"estado": "ok",            "datos": {"total": 2, "evidencias": [...]}}   # el caso existe y tiene evidencias
{"estado": "sin_resultados", "detalle": "..."}                            # el caso existe, sin evidencias
{"estado": "no_encontrado",  "detalle": "..."}                            # el caso no existe
```

### `consultar_evidencia(case_id: int, evidence_id: int)`

Llama a `GET /cases/{case_id}/evidences/{evidence_id}`. Un 404 de este
endpoint puede significar dos cosas distintas con el mismo código HTTP:
"el caso no existe" o "la evidencia no existe en ese caso". La tool las
distingue usando el `detail` real que devuelve Casos (no un mensaje
genérico inventado aquí) — ver `_detalle_backend` en `app/main.py`.

### `verificar_integridad_evidencia(case_id: int, evidence_id: int)`

Llama a `GET /cases/{case_id}/evidences/{evidence_id}/integridad`. La
integridad ya está completamente resuelta en el backend — no hay ninguna
capacidad que falte ni que inventar: `EvidenceUpdate` no permite tocar
`tipo`/`valor` tras crear la evidencia, así que el backend puede
recalcular `sha256(valor)` en cada consulta y compararlo con el
`hash_valor` guardado al crearla. La tool solo reenvía esa comparación
tal cual, sin calcular nada por su cuenta:

```
{"estado": "ok", "datos": {
  "evidence_id": 3, "algoritmo": "sha256",
  "hash_registrado": "...", "hash_actual": "...", "integro": true
}}
```

`integro=false` no se oculta ni se "arregla": se devuelve tal cual, es la
señal forense de que el contenido cambió por una vía que no fue la API
normal.

### `registrar_evidencia(case_id: int, tipo: str, valor: str, confirmado: bool, observaciones: str | None, fecha_adquisicion: str | None)` — ⚠️ MODIFICA DATOS (Fase 2H)

Llama a `POST /cases/{case_id}/evidences` (puerto 8000). `tipo` y `valor`
son el contenido probatorio y quedan **inmutables** en cuanto se crean
(`EvidenceUpdate` no los admite, ver `verificar_integridad_evidencia` más
arriba). `tipo` se valida contra el límite real de la columna
(`VARCHAR(50)`) **antes de tocar la red** — el esquema Pydantic del
backend no lo exige por su cuenta, así que sin esta validación un `tipo`
más largo habría fallado en MySQL, no de forma limpia en la API.

**Esta tool nunca calcula ni envía `hash_valor`**: el backend lo calcula
él mismo, una única vez, al crear la evidencia
(`backend/app/modules/cases/integrity.py::calcular_hash_valor`) — enviarlo
desde aquí sería redundante en el mejor caso, e inconsistente con la
integridad real en el peor.

```
{"estado": "ok", "datos": {"id": 17, "case_id": 8, "tipo": "imagen_disco", "hash_valor": "...", ...}}
{"estado": "no_encontrado", "detalle": "Caso no encontrado"}
{"estado": "conflicto",      "detalle": "El caso está eliminado: no se pueden añadir evidencias"}
```

> **Verificado en el código**
> (`backend/app/modules/cases/service.py::create_evidence`): un caso
> **archivado** SÍ admite evidencia nueva hoy — `create_evidence` solo
> comprueba que el caso no esté eliminado, nunca su `estado`. No es una
> omisión de esta tool: es el comportamiento real del backend, distinto
> del de `cambiar_estado_caso` (que sí trata `archivado` como terminal).

### Timeline (Fase 2C)

### `obtener_cronologia_caso(case_id: int)`

Llama a `GET /timeline/cases/{case_id}` (puerto 8002).

```
{"estado": "ok",            "datos": {"total": 9, "eventos": [...]}}
{"estado": "sin_resultados", "detalle": "..."}
```

> **Limitación real, verificada en el código de Timeline**
> (`timeline/app/modules/timeline/routes.py`): este endpoint **nunca
> comprueba si el caso existe** — Timeline no es dueño de la tabla
> `cases`, solo lee `timeline_events` para el `case_id` pedido y devuelve
> lo que haya. Por eso `obtener_cronologia_caso` **no puede** devolver
> `"no_encontrado"`: un `case_id` inexistente y un caso real sin
> cronología calculada todavía producen la misma respuesta
> (`sin_resultados`). No es una limitación de la tool, es del contrato
> REST subyacente — documentada en vez de inventar una distinción que el
> backend no ofrece.

### `recalcular_cronologia(case_id: int, confirmado: bool)` — ⚠️ MODIFICA DATOS (Fase 2F)

**Es la primera tool de escritura del MCP Server.** Llama a
`POST /timeline/cases/{case_id}/refresh` (puerto 8002): **borra la
cronología actual del caso y la reconstruye desde cero** a partir de
evidencias, eventos de tracking y hallazgos OSINT. No toca esas tres
fuentes — solo la tabla derivada `timeline_events` de ese caso.

`confirmado` es **obligatorio** (no tiene valor por defecto) y se
comprueba **antes de tocar la red**: con `confirmado=false` la tool
rechaza la llamada con `ToolError` sin emitir ninguna petición HTTP —
verificado con un test que no registra ningún mock de respuesta, de
forma que cualquier intento de red haría fallar el test por sí solo.
`ToolAnnotations(readOnlyHint=False, destructiveHint=True,
idempotentHint=False)` — recordatorio: esta pista es informativa para el
cliente, la protección real es la comprobación de `confirmado` en
código.

```
{"estado": "ok", "datos": {"total": 9, "eventos": [...]}}
```

El backend ya es atómico por su cuenta (`db.rollback()` si algo falla a
mitad, verificado en `timeline/app/modules/timeline/service.py`): esta
tool no añade ninguna garantía transaccional propia, solo reenvía la
petición y su resultado. El único error real documentado de este
endpoint es un 500 genérico (nunca 404: no comprueba si el caso existe).

### Informes (Fase 2C)

### `listar_informes_de_caso(case_id: int)`

Llama a `GET /cases/{case_id}/reports` (puerto 8003). **No genera ningún
informe** — solo lista los ya emitidos. Misma limitación que Timeline,
verificada en `sharingan/app/modules/reports/routes.py`: tampoco
comprueba si el caso existe, así que igualmente solo distingue `"ok"` de
`"sin_resultados"`, nunca `"no_encontrado"`.

```
{"estado": "ok",            "datos": {"total": 2, "informes": [...]}}
{"estado": "sin_resultados", "detalle": "..."}
```

### `consultar_informe(report_id: int)`

Llama a `GET /reports/{report_id}` (puerto 8003). A diferencia de las dos
anteriores, **este endpoint sí comprueba existencia real**
(`if report is None: raise HTTPException(404, ...)` en el backend), así
que sí distingue correctamente `"no_encontrado"`:

```
{"estado": "ok", "datos": {"id": 1, "case_id": 8, "version": 1, "archivo_pdf": "case_8/report_v1.pdf", ...}}
{"estado": "no_encontrado", "detalle": "No existe el informe 999"}
```

**No genera el informe ni descarga ningún fichero.** El campo
`archivo_pdf` que devuelve el backend es una ruta interna del servidor de
Informes — esta tool lo trata como metadata (un texto más en la
respuesta) y en ningún momento intenta leerlo, abrirlo ni copiarlo.
`descargar_informe` queda explícitamente **fuera de esta fase**: es la
siguiente capacidad prevista del roadmap, y necesita un diseño de
staging de ficheros aparte (ver auditoría de diseño de la Fase MCP 2,
§5) antes de poder implementarse con seguridad.

### `generar_informe(case_id: int, generado_por: str, confirmado: bool, notas: str | None)` — ⚠️ MODIFICA DATOS Y TIENE COSTE ECONÓMICO REAL (Fase 2H)

Llama a `POST /reports/generate` (puerto 8003): genera un informe nuevo
mediante una llamada real a un modelo de IA (resumen y conclusiones).
**Nunca la ejecutes sin `confirmado=true` explícito del usuario** — el
motivo no es solo escribir datos, como en el resto de tools de esta
categoría, sino el coste económico y el tiempo reales de la llamada a
IA.

Esta tool **no expone `opciones`** (el alcance parcial que sí admite el
endpoint real: anexos, formatos, rango de fechas) — solo `case_id`,
`generado_por` y `notas` opcionales. Omitir `opciones` es justo lo que
hace el backend por defecto: emite el informe **completo** (los tres
anexos, los cuatro formatos), el mismo comportamiento que tenía este
endpoint antes de que existiera ese campo.

```
{"estado": "ok", "datos": {"id": 5, "case_id": 8, "version": 2, "resumen_ia": "...", "archivo_pdf": "...", ...}}
{"estado": "no_encontrado", "detalle": "No existe el caso 999"}
{"estado": "conflicto",      "detalle": "..."}   # generación simultánea del mismo caso; reintentar basta
```

> **Timeout propio, verificado necesario contra el backend real**: los 5
> clientes HTTP comparten un timeout fijo de 10s
> (`app/core/http_client.py`), pensado para peticiones CRUD normales.
> Esta es la única llamada de todo el MCP Server que dispara de verdad
> una llamada a un modelo de IA (segundos reales) — con el timeout
> compartido, la primera prueba de integración real de esta tool falló
> con un error de conexión que en realidad era un timeout prematuro. Por
> eso `generar_informe`, únicamente ella, pasa `timeout=120.0` en su
> propia petición.
>
> **Errores reales de IA verificados en el código**
> (`sharingan/app/modules/reports/routes.py`): `EmptyTimelineError`/
> `EmptySelectionError` (422, el caso no tiene cronología calculada
> todavía, o el alcance pedido la deja vacía), `AIConfigError`/
> `AIUnavailableError` (503, la IA no está configurada o no responde
> ahora mismo) y `AIResponseError` (502, la IA respondió pero con algo
> no firmable — p. ej. citando un evento que no existe). Los tres
> últimos son >=500 y, desde esta fase, `_peticion_segura` incluye el
> `detail` real del backend también en ese camino (antes solo lo hacía
> para 422) — mejora que beneficia a las diecisiete tools anteriores por
> igual, no solo a esta.

### Tracking (Fase 2D)

Auditado el backend real (`track-inc/app/modules/tracking/routes.py`)
antes de escribir código: **solo existen 2 endpoints GET útiles para
lectura** (además de `/cases-lookup`, ya cubierto por `buscar_casos` de
Casos). **No existe ningún endpoint de consulta individual de un evento
de tracking** — por eso no hay una tool `consultar_evento_tracking`: no
expuesta en esta fase porque el backend Tracking actual no proporciona
un endpoint REST equivalente, y esta fase no crea endpoints nuevos.

### `listar_eventos_tracking(case_id: int, skip: int = 0, limit: int = 100)`

Llama a `GET /cases/{case_id}/tracking/events` (puerto 8001), con la
paginación real del backend (`skip≥0`, `1≤limit≤1000` — los mismos
límites que impone `Query(...)` en el propio endpoint, no inventados
aquí). A diferencia de Timeline/Informes en la Fase 2C, **este endpoint
sí comprueba existencia real del caso** (`service.CaseNotFoundError` →
404 en el backend), así que sí distingue correctamente `"no_encontrado"`:

```
{"estado": "ok",            "datos": {"total": 2, "eventos": [...], "skip": 0, "limit": 100}}
{"estado": "sin_resultados", "detalle": "..."}                                                 # caso real, sin eventos
{"estado": "no_encontrado",  "detalle": "..."}                                                 # el caso no existe
```

### `verificar_integridad_tracking(case_id: int)`

Llama a `GET /cases/{case_id}/tracking/verify` (puerto 8001). El backend
devuelve `{ok, mensaje, problemas[]}` — **deliberadamente sin hashes ni
detalle criptográfico** (así lo documenta el propio schema del backend,
`VerifyIntegrityResponse`, para no filtrar la cadena de integridad
interna al contrato de la API). Esta tool reenvía ese veredicto tal
cual, **sin recalcular ni alterar nada** — verificado con un test
específico de `ok=false` que confirma que no se "arregla" el resultado,
mismo criterio que `verificar_integridad_evidencia` en la Fase 2B:

```
{"estado": "ok", "datos": {"ok": true, "mensaje": "...", "problemas": []}}
{"estado": "no_encontrado", "detalle": "..."}
```

### `guardar_eventos_tracking(case_id: int, fuente_log: str, eventos: list[dict], confirmado: bool, sha256_log: str | None, forzar: bool)` — ⚠️ MODIFICA DATOS (Fase 2H)

Llama a `POST /cases/{case_id}/tracking/events` (puerto 8001). **No
analiza ningún log** — eso es `/analyze` (subir un fichero, clasificarlo,
sin persistir), un endpoint distinto que esta fase no expone a propósito
(ver enunciado: "No implementar análisis de logs/OSINT todavía"). Esta
tool persiste eventos que **ya vienen clasificados** por quien llama.

Cada elemento de `eventos` necesita, como mínimo, `hora` (ISO 8601),
`evento` (texto no vacío) y `severidad` (`baja`/`media`/`alta`/
`critica`); `usuario_detectado` es opcional, máximo 100 caracteres (el
límite real de la columna). Esta tool valida la estructura de **cada**
evento y el volumen del array — máximo 500 por llamada, un límite propio
de la tool (el backend no impone ninguno) para no reenviar por error un
log entero sin pasar por `/analyze` — **antes de tocar la red**.

```
{"estado": "ok", "datos": {"guardados": 2, "tracking_events": [...]}}
{"estado": "no_encontrado", "detalle": "..."}
{"estado": "conflicto",      "detalle": "El caso está archivado: es un registro histórico inmutable"}
{"estado": "conflicto",      "detalle": "Este fichero de log ya se guardó en el caso (3 eventos)."}
```

> **Dos causas distintas del mismo 409, verificadas en el código**
> (`track-inc/app/modules/tracking/service.py`): caso eliminado/archivado
> (`CasoNoModificableError`), o el mismo `sha256_log` ya guardado en ese
> caso sin `forzar=true` (`LogYaGuardadoError`, pensada para evitar
> duplicar eventos si el mismo log se reenvía dos veces). Se propaga el
> `detail` real en vez de inventar una distinción; `sha256_log` es
> opcional — sin él, esta protección de duplicados simplemente no aplica.

### `analizar_log(case_id: int, ruta: str, zona_horaria: str = "UTC")` — análisis, no lectura pura (Fase 2I)

Llama a `POST /cases/{case_id}/tracking/analyze` (puerto 8001), vía
**multipart** (nunca base64: el fichero viaja como bytes tal cual dentro
del `multipart/form-data`, igual que lo sube el frontend). **No
persiste nada** — es la vista previa clasificada, distinta de
`guardar_eventos_tracking` (Fase 2H), que persiste eventos ya revisados.
Por eso no exige `confirmado`, pero tampoco es solo-lectura pura:
`ToolAnnotations(readOnlyHint=False, destructiveHint=False,
idempotentHint=True)` — ejecuta trabajo real (clasificación completa del
fichero) aunque no cambie ningún dato ni tenga efectos de red externa.

**`ruta` es una ruta LOCAL del disco donde corre este MCP Server**, no un
contenido subido por el cliente MCP — el mismo enfoque que ya fijó el
diseño de la Fase MCP 2 (§5): rutas locales, no base64/staging, dado que
Claude Code y este proceso corren en la misma máquina. Controles, en
`_validar_ruta_permitida` (`app/main.py`), **todos antes de leer nada del
fichero**:

1. **Allowlist obligatoria** (`MCP_ALLOWED_FILE_DIRS` en
   `mcp-server/.env`, vacía por defecto): sin al menos un directorio
   configurado, se rechaza cualquier ruta.
2. **`Path.resolve()`** sobre la ruta pedida — normaliza `..` y sigue
   symlinks hasta su destino real — y comprobación de que el resultado
   queda **dentro** de un directorio permitido. Esto cubre a la vez path
   traversal (`../../etc/passwd`) y un symlink que apunte fuera del
   directorio permitido: en ambos casos, lo que se compara es la ruta
   real final, no la que se escribió.
3. Existe, no es un directorio, es un fichero regular.
4. Tamaño ≤ 20 MB — **límite propio de esta tool**, no autoritativo: es
   el mismo valor por defecto que documenta Tracking
   (`TRACKING_MAX_LOG_MB`) para evitar una subida que ya se sabe que
   fallará, pero el 413 real de Tracking (más abajo) sigue siendo la
   última palabra si ese backend cambia su propio límite.

Ningún mensaje de error de esta tool incluye contenido del fichero —
como mucho, la ruta que ya dio quien llama.

```
{"estado": "ok", "datos": {"total_eventos": 4, "por_severidad": {...}, "eventos": [...], "indicadores": [...], "sha256_log": "...", ...}}
{"estado": "no_encontrado", "detalle": "..."}
{"estado": "conflicto",      "detalle": "El caso está eliminado"}
```

> **Formatos y errores reales del backend**
> (`track-inc/app/modules/tracking/routes.py`): 400 si el fichero no se
> puede decodificar como texto (UTF-8/UTF-8 con BOM/UTF-16/CP1252, ver
> `codificacion.py`) o si `zona_horaria` tiene forma correcta pero está
> fuera de rango; 413 si supera el límite real del backend (20 MB por
> defecto, configurable en Tracking vía `TRACKING_MAX_LOG_MB`, no
> visible para este proceso). Ambos se propagan como `ToolError` con el
> `detail` real —nunca contenido del fichero, el backend tampoco lo
> incluye.

### OSINT (Fase 2E)

Auditado el backend real (`scam-shield/app/modules/osint/findings/
routes.py`) antes de escribir código: `osint-findings` es la **vista de
lectura consolidada** de los 8 tipos de análisis OSINT (dominio, email,
wallet, typosquatting, teléfono, CNMV, IP, imagen) — no ejecuta ningún
análisis, solo lee lo que scam-shield ya guardó. Es, con diferencia, el
endpoint más rico en filtros de todo el backend, y son todos reales
(`Query(...)` en el propio router), no inventados aquí.

Los 8 análisis que sí ejecutan trabajo real (`POST /analysis/domain`,
etc. — llamadas a APIs externas, coste, tiempo) y `vincular_hallazgo`
quedan **fuera de esta fase**: no son lectura, y el enunciado los excluye
explícitamente.

### `listar_hallazgos_osint(case_type?, subject_type?, subject_value?, case_id?, risk_level?, min_risk_score?, since?, skip=0, limit=50)`

Llama a `GET /osint-findings` (puerto 8124). Todos los filtros son
opcionales y se combinan con AND — se envían solo los que se indiquen
(un filtro no pedido nunca aparece como `?campo=None` en la petición
real, verificado con un test específico). Paginación real del backend
(`skip≥0`, `1≤limit≤200`). Igual que Timeline/Informes en la Fase 2C,
**no comprueba existencia de `case_id`** —es un filtro más, no una
referencia obligatoria—, así que solo distingue `"ok"` de
`"sin_resultados"`, nunca `"no_encontrado"`.

```
{"estado": "ok",            "datos": {"total": 2, "hallazgos": [...], "skip": 0, "limit": 50}}
{"estado": "sin_resultados", "detalle": "..."}
```

### `consultar_hallazgo_osint(finding_id: int)`

Llama a `GET /osint-findings/{finding_id}` (puerto 8124). A diferencia
del listado, **este endpoint sí comprueba existencia real**
(`if finding is None: raise HTTPException(404, ...)`), así que sí
distingue correctamente `"no_encontrado"`. Devuelve, además de lo que ya
trae el listado, `top_flags` y `details` (el payload completo del
análisis original):

```
{"estado": "ok", "datos": {"id": 4, "case_id": 8, "risk_level": "high", "top_flags": [...], "details": {...}, ...}}
{"estado": "no_encontrado", "detalle": "No existe el finding 999"}
```

### `vincular_hallazgo(finding_id: int, case_id: int, confirmado: bool)` — ⚠️ MODIFICA DATOS (Fase 2G)

Llama a `PATCH /osint-cases/{case_type}/{id}/vinculacion`
(`scam-shield/app/modules/osint/case_link/routes.py`, puerto 8124). Ese
endpoint real identifica la investigación por `case_type` + su id en la
tabla de origen (p. ej. `ip_cases.id`) — **no** por el `finding_id` de
`osint-findings` que usan el resto de tools OSINT. Por eso esta tool hace
**dos peticiones HTTP reales** cuando `confirmado=true`: primero
`GET /osint-findings/{finding_id}` (el mismo endpoint que
`consultar_hallazgo_osint`) para resolver `case_type`/`source_id`, y solo
entonces el `PATCH` real. Ninguna de las dos se emite con
`confirmado=false`.

**Solo vincula, no desvincula**: `case_id` es obligatorio (no admite
`null`), a propósito — el endpoint real sí soporta desvincular
(`case_id: null`), pero esta fase no expone esa capacidad (ver
enunciado: "Solo vincula, no desvincula").

```
{"estado": "ok", "datos": {"case_type": "ip", "id": 4, "case_id": 8, "cambiado": true, "auditoria_registrada": true, "auditoria_error": null}}
{"estado": "no_encontrado", "detalle": "No existe el finding 999"}                       # el hallazgo no existe
{"estado": "no_encontrado", "detalle": "No existe el caso 999, o está eliminado"}        # el caso destino no existe
```

> **Resultados reales verificados en el código
> (`scam-shield/app/modules/osint/case_link/service.py`)**: si el
> hallazgo ya estaba vinculado a ese mismo `case_id`, el backend no
> persiste nada y devuelve HTTP 200 con `cambiado=false` — **no es un
> error**, es un resultado válido que esta tool reenvía tal cual. Los dos
> 404 posibles (hallazgo inexistente, caso destino inexistente o
> eliminado) comparten código HTTP pero traen `detail` distinto: se
> propaga el mensaje real en vez de inventar una distinción. La
> vinculación en OSINT queda persistida siempre que `cambiado=true`,
> independientemente de si el aviso a `case_audit_log` (Casos) tuvo éxito
> (`auditoria_registrada`/`auditoria_error`, informativos, nunca
> bloquean el cambio).

### `analizar_dominio(domain: str, confirmado: bool, case_id: int | None)` — ⚠️ MODIFICA DATOS, RED EXTERNA REAL (Fase 2I)

Llama a `POST /analysis/domain` (puerto 8124): la **única** de las 8
tools de análisis OSINT que expone esta fase, elegida por ser la de
**menor riesgo** — recibe un dominio como texto (sin fichero, sin datos
personales directos), a diferencia p. ej. del análisis de imagen (fichero
+ posible reconocimiento facial) o de email/teléfono (dato personal
directo). Las otras 7 (`analizar_email`, `analizar_wallet`,
`analizar_typosquatting`, `analizar_telefono`, `verificar_cnmv`,
`analizar_imagen`, `analizar_ip`) quedan deliberadamente fuera de esta
fase: mismo patrón de persistencia + red externa real que
`analizar_dominio`, candidatas para una fase futura.

Consulta, en la misma llamada, WHOIS, certificado SSL, VirusTotal, DNS
completo, reputación de cada IP resuelta en AbuseIPDB, subdominios vía
crt.sh e historial en Wayback Machine — **red externa real, con tiempo y
cuotas reales** (por eso su `timeout` propio es de 60s, no el compartido
de 10s). **Verificado en el código**
(`scam-shield/app/modules/osint/domain/service.py::run_domain_analysis`)
que **persiste** un hallazgo OSINT nuevo (fila en `domain_cases` +
`osint_findings`) en cada llamada — por eso, a diferencia de
`analizar_log`, esta tool **sí exige `confirmado=true`** explícito:
comprobado antes de cualquier petición HTTP.

```
{"estado": "ok", "datos": {"id": 55, "domain": "...", "risk_score": 20, "errors": [...], ...}}
```

> **Ninguna fuente externa tumba la petición si falla** (verificado en el
> código: cada llamada externa está en su propio `try/except`) — el
> análisis se completa igual con las fuentes que sí respondieron, y
> `errors` lista cuáles fallaron y por qué, sin ocultarlo. En la
> integración real de esta fase, VirusTotal/AbuseIPDB fallaron por falta
> de API key configurada en el `.env` de OSINT (entorno local de
> desarrollo, no una limitación de esta tool) y crt.sh/Wayback por
> errores transitorios propios — el análisis igualmente devolvió
> `"estado": "ok"` con `risk_score` calculado a partir de lo demás.
>
> No hay ningún 404/409 real que fabricar aquí: `normalize_domain` nunca
> lanza (cualquier cadena "vale", ver `shared/domain_utils.py`) y
> `case_id` no se comprueba contra `cases` al crear (a diferencia de
> `vincular_hallazgo`, que sí lo hace) — verificado en el código, no es
> una omisión de esta tool.

### Errores, en las veintidós tools

Propagados de forma controlada (nunca se inventan datos ni se enmascaran)
como `ToolError` — distinguibles por Claude de una respuesta normal: 401
doble (tras reautenticar una vez contra Casos, sea cual sea el backend de
destino), 422, cualquier 5xx, y errores de conexión/timeout. La lógica
común de estos casos vive en un único sitio (`_peticion_segura` en
`app/main.py`), reutilizado por las veintidós tools para no duplicarla —
con un parámetro `backend` para que el mensaje de error nombre siempre el
backend real (Casos/Timeline/Informes/Tracking/OSINT), no uno
hardcodeado. Desde la Fase 2H, el mensaje de un `>=500` incluye también
el `detail` real del backend cuando lo trae (antes solo lo hacía el de
422) — ver `generar_informe` para el caso que lo motivó.

## Cómo ejecutar el MCP Server

Requisitos: Python 3.12 (mismo que los 5 backends), y Casos corriendo en
`http://localhost:8000` (o la URL que se indique en `.env`).

```bash
cd mcp-server
python3.12 -m venv venv
venv/bin/pip install -r requirements-dev.txt   # incluye requirements.txt
cp .env.example .env   # y rellena MCP_SERVICE_EMAIL/MCP_SERVICE_PASSWORD reales
venv/bin/python -m app.main
```

Arrancado así (manualmente), el proceso queda esperando mensajes por
stdio — es exactamente lo que hace Claude Code por debajo, no un modo de
prueba distinto. No demuestra por sí solo que la integración MCP
funciona (ver más abajo); solo que el proceso arranca sin errores.

## Quién más lo usa: el asistente de Informes

El asistente conversacional (`sharingan/app/modules/chat/fuente_mcp.py`) lee
el expediente del caso a través de este servidor en vez de consultar la base
directamente. Lo lanza como proceso hijo por stdio, uno por pregunta, con dos
particularidades:

- **Con `MCP_ACCESS_TOKEN`**, el JWT del analista que pregunta. El proceso no
  inicia sesión nunca, así que el asistente lee con la identidad de esa
  persona y no con la del usuario de servicio.
- **Solo llama a seis herramientas de lectura** (`consultar_caso`,
  `listar_evidencias_de_caso`, `listar_hallazgos_osint`,
  `listar_eventos_tracking`, `obtener_cronologia_caso`,
  `listar_informes_de_caso`), siempre con el `case_id` fijado por el código.
  El modelo que redacta la respuesta no ve las herramientas ni puede llamarlas.

Cambiar la forma o el nombre de lo que devuelven esas seis herramientas rompe
el asistente: `sharingan/tests/test_chat_fuente_mcp.py` lanza este servidor
real y lo comprueba.

## Cómo se registra localmente en Claude Code

Con `claude mcp add`, en scope **`local`** — la configuración queda
**únicamente en `~/.claude.json` de esta máquina, nunca en ningún
fichero del repositorio**. Es una decisión deliberada: evita hardcodear
en un fichero versionado una ruta absoluta a un `venv` que solo existe en
tu máquina.

```bash
claude mcp add dfir-nexus -s local -- \
  /bin/sh -c "cd $(pwd)/mcp-server && exec venv/bin/python -m app.main"
```

(El wrapper `/bin/sh -c "cd ... && exec ..."` es necesario porque
`claude mcp add` no tiene una opción `--cwd`, y `python -m app.main`
necesita ejecutarse con el directorio de trabajo en `mcp-server/` para
que `app` se resuelva como paquete.)

Comprobar que quedó conectado:

```bash
claude mcp list
claude mcp get dfir-nexus
```

**Cada persona que quiera usar este MCP Server en su propia máquina tiene
que registrarlo así, una vez, con la ruta de su propio `venv`.** No hay
`.mcp.json` en el repositorio ni se espera que lo haya para este MVP.

Una sesión de Claude Code ya abierta **no** detecta automáticamente un
servidor MCP añadido a mitad de sesión: hace falta `/mcp` (reconectar) o
reiniciar la sesión para que la tool aparezca disponible.

## Cómo ejecutar los tests

```bash
cd mcp-server
venv/bin/python -m pytest -v
```

(Usar `python -m pytest`, no el script `pytest` a secas: así el propio
intérprete añade `mcp-server/` a `sys.path` y `import app...` resuelve
sin necesitar un `pytest.ini` ni instalar el paquete.)

**299 tests** en 23 ficheros — uno por tool (22, incluida
`test_auth_login_errores.py` que no es de una tool concreta sino del
núcleo de autenticación compartido, `app/core/auth.py`) + `conftest.py`
con el fixture compartido que resetea el JWT en memoria entre tests:

- **277 mockados** (con `respx`, sin tocar la red): construcción de la
  petición HTTP, cabecera `Authorization`, casos de éxito, 404/409/"no
  encontrado"/"sin_resultados"/"conflicto", 401 + reautenticación,
  segundo 401, 422, 5xx (incluido el `detail` real en 502/503, Fase 2H),
  error de conexión/timeout, validación de entradas en cada tool
  (`case_id`, IDs varios, enums inválidos, filtros combinados,
  paginación fuera de rango, estructura y volumen de arrays, allowlist de
  ficheros — path traversal, symlinks, byte nulo, tamaño), `confirmado`
  obligatorio y comprobado antes de cualquier petición HTTP en las 8
  tools de escritura (probado con tests que no registran ningún mock:
  cualquier llamada de red real haría fallar el test por sí sola), y los
  dos fallos de manejo de excepciones encontrados en la auditoría final
  (`test_auth_login_errores.py`, `test_ruta_con_byte_nulo_...`).
- **22 de integración real** (`test_real_contra_*_local_si_esta_disponible`):
  hablan de verdad con los 5 backends, sin ningún mock. La mayoría son
  solo lectura; las de tools de escritura (Fases 2F-2I) ejecutan la
  escritura real ÚNICAMENTE con `confirmado=True`, documentada en cada
  caso (ver secciones de cada tool arriba) — nunca borran nada. Se saltan
  automáticamente si no hay `MCP_SERVICE_EMAIL`/`MCP_SERVICE_PASSWORD` en
  el entorno, si el backend correspondiente no responde, o si no hay
  datos reales con los que probar sin fabricarlos. Para ejecutarlas:

  ```bash
  MCP_SERVICE_EMAIL=... MCP_SERVICE_PASSWORD=... venv/bin/python -m pytest -k real
  ```

  Estos tests usan `@pytest.mark.asyncio(loop_scope="session")` en vez
  del alcance por test por defecto (solución ya introducida en la
  Fase 2A, reutilizada sin cambios en cada fase posterior): comparten el
  mismo `httpx.AsyncClient` singleton de producción por backend
  (`app.core.http_client`), y cada cliente queda ligado al primer bucle
  de eventos asyncio que lo usa — con el alcance por defecto (uno por
  test), el segundo test real de un mismo backend en la sesión fallaba
  con `RuntimeError: Event loop is closed`. Los tests mockados no lo
  necesitan: `respx` no depende de una conexión real ligada a un bucle de
  eventos.

Ninguna credencial real vive en el código de los tests — los tokens que
aparecen ahí (`"abc123"`, `"token-viejo"`...) son valores inventados para
los mocks, no secretos.

## Requisitos para que funcione localmente

- Python 3.12.
- El backend de Casos arrancado y accesible en `CASOS_BASE_URL`.
- Un usuario de servicio real en la base de datos de Casos, con sus
  credenciales en `mcp-server/.env`.
- Claude Code con este servidor registrado en scope `local` (ver arriba).
- Para las tools de Timeline/Informes/Tracking/OSINT: esos backends
  arrancados y accesibles en `TIMELINE_BASE_URL`/`INFORMES_BASE_URL`/
  `TRACKING_BASE_URL`/`OSINT_BASE_URL` (mismo `.env`).
- Para `analizar_log` (Fase 2I): al menos un directorio en
  `MCP_ALLOWED_FILE_DIRS` (mismo `.env`) — sin él, la tool rechaza
  cualquier ruta.

## Estado actual / Próximas fases

**Fase 2A a 2I completadas** — veintidós tools contra los 5 backends de
Nexus (Casos + su sub-recurso Evidencias, Timeline, Informes, Tracking y
OSINT). Ver "Tools disponibles" arriba para el detalle completo de cada
una; resumen por fase:

- **2A** (Casos): `consultar_caso`, `buscar_casos`, `consultar_auditoria_caso`.
- **2B** (Evidencias): `listar_evidencias_de_caso`, `consultar_evidencia`,
  `verificar_integridad_evidencia`.
- **2C** (Timeline/Informes): `obtener_cronologia_caso`,
  `listar_informes_de_caso`, `consultar_informe`.
- **2D** (Tracking, lectura): `listar_eventos_tracking`,
  `verificar_integridad_tracking`.
- **2E** (OSINT, lectura): `listar_hallazgos_osint`, `consultar_hallazgo_osint`.
- **2F** (primer WRITE): `recalcular_cronologia`.
- **2G** (WRITE riesgo medio): `crear_caso`, `cambiar_estado_caso`,
  `vincular_hallazgo`.
- **2H** (WRITE alto impacto): `registrar_evidencia`,
  `guardar_eventos_tracking`, `generar_informe`.
- **2I** (archivos + análisis): `analizar_log`, `analizar_dominio`.
- **Auditoría final** (Fase 2A-2I, sin nuevas tools): revisión completa de
  las 22 tools, seguridad, contratos REST y tests. Dos fallos reales de
  manejo de excepciones encontrados y corregidos — ver
  `app/core/auth.py::_login` (un fallo de Casos al autenticar que no
  fuera 401, p. ej. un 500, escapaba como `httpx.HTTPStatusError` sin
  envolver en `ToolError`) y `_validar_ruta_permitida` en `app/main.py`
  (un byte nulo embebido en una ruta escapaba como `ValueError`). Ambos
  con test que demuestra el fallo antes de la corrección. Ningún otro
  cambio de comportamiento.

**Todavía NO implementado como tools MCP** (deliberadamente, no es un
olvido — ver la auditoría de diseño de la Fase MCP 2 para el catálogo
completo propuesto):

- **`descargar_informe`** — necesita un diseño de staging de ficheros
  aparte (ver §5 de la auditoría de diseño) antes de implementarse: es
  distinto de `analizar_log` (Fase 2I), que SUBE un fichero en vez de
  descargarlo.
- **`consultar_evento_tracking`** — **no implementable sin crear un
  endpoint nuevo**: auditado el código real de Tracking
  (`track-inc/app/modules/tracking/routes.py`) y confirmado que no existe
  ningún `GET` de consulta individual de un evento.
- **Los otros 7 análisis OSINT** que ejecutan trabajo real
  (`analizar_email`, `analizar_wallet`, `analizar_typosquatting`,
  `analizar_telefono`, `verificar_cnmv`, `analizar_imagen`, `analizar_ip`)
  — mismo patrón de persistencia + red externa real que `analizar_dominio`
  (Fase 2I), que expuso deliberadamente solo la de menor riesgo.
- **Desvincular un hallazgo** (`case_id=null` en
  `PATCH /osint-cases/{tipo}/{id}/vinculacion`) — `vincular_hallazgo`
  (Fase 2G) solo vincula, a propósito.
- **Editar/borrar evidencias**, y **`DELETE /cases/{id}`** — nunca
  expuesto (ver enunciado de la Fase 2G: "No expongas DELETE de casos").
- Los 8 endpoints `GET /{tipo}-cases[/{id}]` por tipo de análisis OSINT
  (p. ej. `GET /domain-analysis-cases`) — `osint-findings` ya cubre
  consulta consolidada de los 8 tipos a la vez.
- Gestión de usuarios vía MCP (decisión ya tomada: no exponerla, o solo
  mucho más adelante y con mucha cautela).

Cada uno de estos puntos sigue siendo candidato de una fase futura, no
parte del alcance actual.
