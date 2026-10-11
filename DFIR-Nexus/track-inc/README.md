# track-inc — Tracking Post-Incidente

Módulo 3 de DFIR-Nexus. Análisis de logs post-incidente: clasificación
de eventos por criticidad y persistencia en `tracking_events`.

Implementación alineada con `CLAUDE.md` (la especificación oficial del
equipo): FastAPI + SQLAlchemy + Alembic + MySQL, patrón
`models.py / schemas.py / repository.py / service.py / routes.py` por
módulo, todo relacionado por `case_id`.

## Documentación

| Documento | Qué es |
|---|---|
| [`CLAUDE.md`](CLAUDE.md) | Especificación oficial del proyecto: modelo de datos, módulos, reglas |
| [`docs/DESIGN.md`](docs/DESIGN.md) | Decisiones de diseño |
| [`docs/DESIGN_SYSTEM.md`](docs/DESIGN_SYSTEM.md) | Sistema de diseño del frontend |
| [`docs/FRONTEND_MODULE_GUIDE.md`](docs/FRONTEND_MODULE_GUIDE.md) | Guía de módulos de frontend |
| [`docs/Documentacion.pdf`](docs/Documentacion.pdf) | Documentación del proyecto |
| [`docs/code.html`](docs/code.html), [`docs/screen.png`](docs/screen.png) | Mockup de referencia de la interfaz |
| [`docs/integracion/INTEGRACION.md`](docs/integracion/INTEGRACION.md) | Qué está ya fusionado con `development` y qué hay que llevar a mano (tabla compartida, volumen de la cadena) |

## Qué hace (CU-03: "Analizar logs de tracking")

1. El analista sube un fichero de log de texto asociado a un caso.
2. Se parsean sus líneas (`log_parser.py`), extrayendo timestamp, comando
   y usuario cuando están presentes.
3. Se clasifican por criticidad con un motor de reglas (`net user`,
   `net localgroup`, `powershell -EncodedCommand`, `vssadmin delete
   shadows`, etc. — ver `agent/classifier/rules.yaml`).
4. El analista revisa la vista previa (nada se ha guardado todavía).
5. Al confirmar, se persiste en `tracking_events` — **exactamente** el
   esquema de `CLAUDE.md`, ni una columna de más.

## Formato de log de entrada

Texto plano, **una entrada por línea**. Se detecta la codificación
(`codificacion.py`) y se devuelve en la respuesta:

| Codificación | Quién la genera |
|---|---|
| UTF-8, con o sin BOM | editores, Bloc de notas, Linux |
| UTF-16 (con o sin BOM) | `Out-File` / `>` en PowerShell 5.1 |
| Windows-1252 | ficheros ANSI en Windows en español |

Lo que no es texto (binarios) responde `400` (ver "Qué NO hace" más abajo).

Timestamps reconocidos al principio de línea, también entre corchetes:

| Formato | Ejemplo |
|---|---|
| ISO 8601, con `T` o espacio, fracción y zona opcionales | `2026-08-10 14:32:05`, `2026-08-10T14:32:05.123Z`, `2026-08-10T14:32:05+02:00` |
| Año/mes/día | `2026/08/10 14:32:05` |
| Día/mes/año, hora de 1 o 2 dígitos (si el mes no cuadra, mes/día) | `10/08/2026 14:35:00`, `14/08/2026 3:11:22`, `08/14/2026 03:11:23` |
| syslog (sin año: el actual, o el anterior si quedaría en el futuro) | `Aug 14 03:11:21 srv sshd[812]: ...` |

Si la marca trae zona (`Z`, `+02:00`), esa manda sobre la elegida al subir el log.

El usuario se extrae, si aparece, de `user:` / `user=` (no de un parámetro de
URL como `?user=`), `usuario:` / `usuario=`, `as DOMINIO\usuario`,
`psexec -u`, `schtasks /ru` y, sobre todo, de **la salida de `whoami`**, que
es el usuario real con el que se ejecutaba.

En los logs de autenticación la cuenta no viene como `user:`, sino dentro de la
frase, así que también se reconocen `Accepted|Failed password for <cuenta>`
(con o sin `invalid user`), `session opened for user <cuenta>`, `of user
<cuenta>` y `sudo: <cuenta> :` — en la línea de `sudo` se toma quien ejecuta,
no la cuenta a la que salta.

### Salida de los comandos

Si un comando produjo salida, va en las líneas siguientes **indentadas**.
Puede ocupar varias líneas:

```
2026-08-22 21:04:38  whoami
    contoso\mlopez
2026-08-22 21:06:03  net user
    Cuentas de usuario de \\WS-CONTA07
    Administrador   mlopez   svc_backup
2026-08-22 21:15:01  wevtutil cl Security
```

La **sangría** es lo que las distingue de un comando nuevo. No todos los
comandos producen salida (`wevtutil cl` arriba no tiene): esos quedan con
el campo vacío, y en el panel se muestran con `—`.

**Las líneas sin timestamp reconocible no se descartan.** Heredan la hora
de la línea anterior que sí la tenía (las del principio del fichero, la de
la primera marca) y quedan marcadas como **hora inferida**. Nunca reciben la
hora del análisis: si no, un comando del incidente aparecería en Timeline
como ocurrido el día en que se subió el log. Solo un fichero sin ninguna
marca temporal usa la hora actual, porque no hay nada mejor. El criterio es
preferir una evidencia con hora aproximada a perder la evidencia entera.

**Zona horaria.** Los logs rara vez dicen en qué zona están escritos; lo
sabe el perito (la del equipo afectado). Al subir el fichero se elige
(`UTC` por defecto, o un desplazamiento como `+02:00`) y las horas se
convierten a UTC. `tracking_events.hora` se guarda **siempre en UTC, sin zona
y a segundos**, y la API la devuelve marcada con `Z`; la interfaz la muestra
en la hora local del navegador indicando la zona (`5:11:19 CEST`), para que
vista previa y eventos guardados no puedan discrepar.

La marca de hora inferida y la regla que disparó no caben en
`tracking_events`, pero no se pierden al guardar: se conservan en la cadena
de integridad local y vuelven en `GET /cases/{id}/tracking/events`.

### Ejemplo real

Entrada:

```
2026-08-10 14:32:05  powershell.exe -EncodedCommand SQBFAFgA
2026-08-10 14:32:11  net user hacker P@ssw0rd123! /add
2026-08-10 14:33:02  vssadmin delete shadows /all /quiet
10/08/2026 14:35:00  whoami
sesion iniciada as CORP\jdoe
```

Vista previa devuelta por `POST /cases/{id}/tracking/analyze`:

| hora | severidad | regla | usuario |
|---|---|---|---|
| 2026-08-10 14:32:05 | `critica` | `powershell_ofuscado_o_descarga_remota` | — |
| 2026-08-10 14:32:11 | `alta` | `cuenta_o_grupo_modificado` | — |
| 2026-08-10 14:33:02 | `critica` | `borrado_evidencias_o_shadow_copies` | — |
| 2026-08-10 14:35:00 | `baja` | — | — |
| 2026-08-10 14:35:00 *(inferida)* | `baja` | — | `jdoe` |

Cada evento devuelve `hora`, `evento`, `severidad`, `regla` y
`usuario_detectado`. Las dos últimas líneas ilustran los dos
comportamientos tolerantes: el formato `dd/mm/aaaa` también se reconoce,
y la línea sin timestamp se conserva con hora inferida.

Las reglas viven en `agent/classifier/rules.yaml` y son editables sin
tocar código ni reiniciar (el motor se recarga cuando cambia el fichero).
Lo que no encaja con ninguna regla se clasifica `baja` con `regla` a nulo —
nada se descarta en silencio.

### Cómo se clasifica

- **Se evalúan todas las reglas y gana la más grave** (a igualdad, la primera
  del fichero). Antes ganaba la primera que casaba, y
  `net user x /add & certutil -urlcache …` salía `alta` en vez de `critica`.
  Además de `regla` (la que decide), cada evento trae `reglas` (todas las que
  casaron) y `mitre` (sus técnicas ATT&CK).
- **El comando se normaliza antes de comparar**: minúsculas, sin `^`,
  comillas ni acento grave, y espacios reducidos a uno. `n^et user`,
  `"net" user`, `net  user` o `i`e`x` ya no esquivan las reglas.
- **Candidatos por subcadena o por expresión regular** (`re:`), para exigir
  límites de palabra (`misc create` ya no es `sc create`) o variantes
  (`-e`, `-ec`, `-enc`… de `-EncodedCommand`).

| Regla | Severidad | MITRE ATT&CK |
|---|---|---|
| `borrado_evidencias_o_shadow_copies` | crítica | T1490, T1070.001 |
| `powershell_ofuscado_o_descarga_remota` | crítica | T1059.001, T1027 |
| `herramienta_post_explotacion` | crítica | T1003, T1570 |
| `volcado_de_credenciales` | crítica | T1003.001–.003 |
| `descarga_con_binario_legitimo` | crítica | T1105, T1197 |
| `exfiltracion_de_datos` | crítica | T1048, T1567 |
| `shell_inverso` | crítica | T1059.004, T1071.001, T1219 |
| `desactivacion_de_defensas` | alta | T1562.001, .002, .004 |
| `cuenta_o_grupo_modificado` | alta | T1136.001, T1098 |
| `persistencia_registro_o_tarea` | alta | T1547.001, T1053.005, T1543.003 |
| `preparacion_de_exfiltracion` | alta | T1560.001 |
| `tunel_o_redireccion_de_puertos` | alta | T1572, T1090, T1105 |
| `movimiento_lateral` | alta | T1021.001, .004, .006, T1047 |
| `escaneo_de_red_o_servicios` | alta | T1046, T1595.002 |
| `herramienta_de_fuerza_bruta` | alta | T1110, T1110.001, .003 |
| `regla_de_cortafuegos_modificada` | alta | T1562.004 |
| `acceso_persistente_ssh_o_sudo` | alta | T1098.004, T1548.003 |
| `reconocimiento_de_red` | media | T1049, T1016, T1018, T1135 |
| `acceso_a_recurso_compartido` | media | T1021.002, T1135 |
| `autenticacion_fallida` | media | T1110 |
| `inicio_de_sesion_remoto` | media | T1078, T1021.004 |
| `enumeracion_de_privilegios` | media | T1033, T1087.001, T1082, T1482 |

Las reglas cubren Windows y Linux, y no solo comandos: una línea de `sshd`
(`Failed password for root from …`, `Accepted publickey for …`), un suceso
4624/4625 del Visor de eventos o el agente de usuario que deja un escáner en el
log del servidor web también se clasifican. Lo que el módulo **no** lee es
tráfico de red capturado (`.pcap`) ni el `.evtx` binario: para eso hay que
exportarlos antes a texto.

## Indicadores (IOC)

Cada evento se analiza en busca de los datos que permiten seguir el rastro del
atacante. Se extraen tanto del **comando** como de su **salida**, y cada
indicador recuerda de cuál de los dos salió.

| Tipo | Ejemplo |
|---|---|
| IP pública (IPv4 o IPv6) | `185.220.101.7`, `2001:4860:4860::8888` |
| IP privada | `192.168.10.240` |
| Dominio | `panel.ejemplo-malo.net` |
| URL | `http://185.220.101.7/upd.exe` |
| Ruta | `C:\Windows\Temp\upd.exe`, `"C:\Program Files\App\x.ini"`, `\\185.220.101.7\exfil`, `%TEMP%\a.exe`, `/etc/shadow` |
| Hash | MD5, SHA-1 o SHA-256 |
| Correo | `soporte@empresa.com` |

**Comando decodificado.** Si el comando es un `powershell -EncodedCommand`
(o cualquiera de sus abreviaturas: `-e`, `-ec`, `-enc`…), se decodifica el
base64 y se muestra en el detalle como *comando decodificado*. Sus
indicadores se extraen con origen `decodificado`, y también se clasifica: la
descarga o la cuenta creada dentro del base64 cuentan para la severidad. Solo
se decodifica; nunca se ejecuta.

Criterios que conviene conocer:

- **Pública y privada van por separado.** La IP del atacante suele ser
  pública; una privada apunta a una máquina interna. Pública es lo enrutable
  en Internet: CGNAT (`100.64.0.0/10`) o los rangos de documentación
  (`203.0.113.0/24`) cuentan como privadas.
- **Indicadores desactivados** (`hxxp://evil[.]com`, `185[.]220[.]101[.]7`)
  se reactivan antes de extraer.
- **Un dominio suelto necesita un dominio de nivel superior real** (`.com`,
  `.local`, un país…): así `System.Net.WebClient` no sale como dominio.
- **El host de una URL o ruta de red se extrae además como indicador propio.**
  Si el binario se descarga de `http://185.220.101.7/...` y los datos se
  exfiltran a `\\185.220.101.7\exfil`, lo que importa es ver que es la misma
  IP, y eso solo es posible si aparece como IP y no únicamente dentro de la URL.
- **Se evitan falsos positivos conocidos**: un nombre de fichero (`svc.exe`,
  `auth.log`, `exploit.py`) no se toma por dominio, ni un número de versión
  (`1.2.3.4.5`), una hora o una dirección MAC por IP.

La respuesta de `POST /cases/{id}/tracking/analyze` trae los indicadores de
cada evento y, en la raíz, **el resumen de todo el log**: cada indicador
agrupado con cuántas veces aparece, en qué líneas y la severidad más alta de
los eventos donde sale, ordenado por esa relevancia. En la interfaz ese
resumen aparece bajo las estadísticas, y cada número de línea abre ese evento
en el panel de detalle.

Los indicadores **no se persisten**: `tracking_events` mantiene el esquema de
`CLAUDE.md`. Se calculan al analizar y viajan en la API —con `tipo` y `origen`
publicados como enumerados en OpenAPI— para que Timeline, el Correlation
Engine o IOC Intelligence los consuman sin reparsear el texto del evento.

## Detalle de un evento

Al pulsar sobre cualquier fila de la tabla se abre un **panel lateral** con
el detalle de ese evento:

| Campo | De dónde sale |
|---|---|
| Comando | la línea parseada |
| Comando decodificado | `powershell.py`, si es un `-EncodedCommand` |
| Severidad y regla que disparó | el clasificador |
| **Por qué es sospechoso** | campo `descripcion` de la regla en `rules.yaml` |
| También casan / MITRE ATT&CK | el clasificador (todas las reglas y sus técnicas, enlazadas) |
| Nº de línea en el fichero | el parser |
| Hora, con su zona y marcada si fue inferida | el parser |
| Línea original del log | el parser, si difiere del comando |
| Indicadores del comando, su salida y el decodificado | `indicators.py` |

Desde 1280 px de ancho el detalle es un panel lateral, igual que el de Casos
(`TableWithDrawerLayout`, ver `DESIGN_SYSTEM.md §6`). En pantallas más
estrechas se abre en una ventana superpuesta: antes no se mostraba y pulsar
una fila no hacía nada visible. En "Eventos guardados" el detalle incluye la
regla y la hora inferida que conserva la cadena local.

**Filtros y exportación.** Sobre las tablas se filtra por severidad (varias a
la vez) y por texto libre (comando, usuario, regla, IP o cualquier
indicador). Se pintan de 500 en 500 filas para que un log de miles de líneas
no bloquee la página. El análisis se exporta a CSV (eventos o indicadores) o
JSON, y los eventos guardados a CSV. Los CSV llevan BOM para Excel,
escriben la hora UTC como `2026-09-12 00:14:07` (el ISO con `T` y `Z` la hoja
de cálculo lo deja como texto y no deja ordenar ni filtrar por día; el JSON sí
conserva el ISO completo) y neutralizan las celdas que empiezan por `= + - @`:
el log lo escribió el atacante, y una celda así se ejecutaría como fórmula al
abrir el fichero.

**Guardar.** Solo se envían los campos que se guardan (no los indicadores ni
la salida). Si ese mismo fichero ya se guardó en el caso, se avisa al
analizar y se pide confirmación antes de duplicar. Cambiar de caso vacía la
vista previa y los eventos mostrados, para no guardar en el caso equivocado.

La tabla incluye una columna **Línea** con el número de línea dentro del
fichero de log — no la posición en la tabla, así que se mantiene al
reordenar.

**Ordenar:** se pulsa sobre la cabecera. Solo `HORA` y `SEVERIDAD` son
pulsables; el resto de columnas no aportan un criterio útil. Cada pulsación
alterna ascendente / descendente, y una flecha marca la columna activa.
`SEVERIDAD` ordena por criticidad real (baja → media → alta → crítica), no
alfabéticamente.

La tabla **no tiene scroll propio**: crece con el número de líneas y es la
página la que se desplaza.

Cada evento ocupa **una sola línea**: si el comando no cabe se corta con
puntos suspensivos (el completo aparece al pasar el ratón y, entero, en el
panel). Así la tabla se lee como un log, sin filas de altura variable.

El panel de detalle **solo aparece al seleccionar una fila** — si estuviera
siempre, restaría ~320 px a la columna del comando incluso vacío — y queda
fijo (`sticky`) para no perderlo de vista al recorrer un log largo.

**Sobre «Salida del comando».** Se rellena con las líneas indentadas que
el log traiga bajo ese comando (ver "Salida de los comandos" más arriba).
No todos producen salida: cuando no la hay, el campo muestra `—`, igual
que cualquier otro campo vacío de la tabla.

Esa salida **nunca se obtiene ejecutando el comando**. Son comandos
extraídos de un incidente real (`vssadmin delete shadows`, `wevtutil cl
Security`, `net user … /add`): ejecutarlos destruiría la máquina de
análisis y contaminaría la evidencia.

Un evento **ya guardado** muestra menos campos que su vista previa: la
regla, la línea original y el número de línea no se persisten, porque
`tracking_events` tiene exactamente las columnas que fija `CLAUDE.md` y
no se le añade ninguna. El panel lo indica en vez de dejarlo en blanco.

## Qué NO hace

Fuera de alcance por definición del módulo (`CLAUDE.md`: analizar logs,
comandos ejecutados y actividad sospechosa):

- **No analiza imágenes** de ningún tipo: ni ficheros gráficos
  (sin Pillow/OpenCV/OCR/EXIF) ni imágenes forenses de disco o volcados
  de memoria (sin `.E01`/`.dd`, pytsk, Sleuthkit ni Volatility).
- **No captura eventos en vivo.** La entrada es siempre un log ya
  existente que el analista sube (CU-03). El motor de captura continua
  que hay en `agent/` pertenece a una fase anterior y no forma parte de
  este flujo.

## Decisión de diseño: la cadena de hashes

`CLAUDE.md` marca la cadena de custodia / hashes de integridad como
*"fuera de alcance por ahora"* y pide no anticiparla en el modelo de
datos oficial. Se mantiene igualmente como capa **interna y opcional**
porque tiene valor real (detecta si alguien manipula un evento ya
registrado), pero:

- **No añade ninguna columna a `tracking_events`.**
- **No usa la base de datos compartida.** Vive en ficheros SQLite
  locales, uno por caso, bajo `.tracking_chain/case_<id>.db` en la raíz
  del módulo, sea cual sea la carpeta desde la que se arranque
  (configurable con `TRACKING_CHAIN_DIR`; ver
  `app/modules/tracking/chain_integrity.py`).
- **No aparece en ningún schema Pydantic ni respuesta de la API.** Hay
  un test dedicado (`test_response_schema_never_leaks_hash_fields`) que
  falla si esto cambia sin querer.
- El único punto de contacto con la API es `GET /cases/{id}/tracking/verify`,
  que devuelve `{ok, mensaje, problemas}` — un veredicto y qué eventos no
  cuadran, nunca los hashes en sí.

**Qué verifica.** Cada eslabón guarda la huella de una fila de
`tracking_events` (su id y sus columnas tal y como quedaron guardadas).
Verificar comprueba dos cosas: que la cadena local no se ha tocado, y que
`tracking_events` sigue coincidiendo con ella. Detecta así eventos
**modificados**, **borrados** o **insertados por fuera de la aplicación**
directamente en la base de datos, y los enumera en `problemas`.

Si en el futuro el equipo decide adoptarla oficialmente, migrarla no
requiere tocar `tracking_events` en absoluto.

## `cases`: el Módulo 1 es el dueño de la tabla

`cases` **pertenece al Módulo 1** (rama `modulo-casos`). Este módulo no la
crea ni la define: solo apunta a ella con la FK de `tracking_events`.

Eso se refleja en dos sitios:

- **Migraciones.** `alembic/versions/0001_initial_cases_evidences.py` es
  una copia literal de la migración del Módulo 1 (mismo `revision`,
  mismo contenido, byte a byte). Está aquí para que el módulo se pueda
  levantar de forma aislada; al fusionar es el mismo fichero, así que no
  genera conflicto. La migración propia, `6b5d49c8a514`, declara
  `down_revision = "0001"` y **solo crea `tracking_events`**.

  ```
  <base> -> 0001 (cases, evidences)  -> 6b5d49c8a514 (tracking_events)
  ```

- **Modelo.** Tracking **no tiene modelo de `cases`** ni importa el de
  Casos (se retiró al integrar en `development`, igual que allí). Lee la
  tabla con SQL mínimo (`repository.py`) y registra solo una referencia a
  `cases.id` (`models.py`) para que SQLAlchemy resuelva la FK. Sin esa
  referencia, guardar eventos fallaba con `NoReferencedTableError`, y es lo
  que le pasa hoy a `development` (ver `docs/integracion/INTEGRACION.md`).
  Alembic no la gestiona.
- **Qué permite según el estado del caso**, con el mismo criterio que Casos:
  - consultar (listar eventos, verificar integridad): cualquier caso
    existente, también uno eliminado;
  - escribir (analizar para guardar, guardar): solo si no está eliminado ni
    archivado; si lo está, `409` con el mismo mensaje que Casos.
  - El selector (`GET /cases-lookup`) no ofrece los eliminados.
- **Casos de prueba en local.** Trabajando con SQLite, `app/dev/casos_locales.py`
  añade `POST /cases/` y `GET /cases/` para crear casos sin el backend de
  Casos. Contra MySQL (la base compartida o la del despliegue) no se montan.

Si el Módulo 1 cambia su migración, hay que traer la versión nueva aquí.
El `revision` compartido hace que el conflicto sea visible en el merge en
vez de pasar desapercibido.

## Autenticación (JWT)

Desde la Fase 4 de `development`, **los cinco endpoints de la API exigen un
JWT**. La identidad es de Casos: es el único módulo con tabla `users` y el
único que emite tokens (`POST /auth/login`). Este backend solo los
**verifica**, con el mismo `JWT_SECRET` compartido por `.env` (igual que ya
se comparte la base de datos), el mismo algoritmo `HS256` y el mismo
contrato de payload (`sub`, `role`, `iat`, `exp`).

`app/modules/auth/` es una **copia deliberada** de la pieza equivalente de
Casos, no un import: ningún backend importa código de otro (CLAUDE.md). Sin
tabla `users` propia, aquí no se puede saber si el usuario sigue activo: se
confía en el token hasta que caduque.

La dependencia se aplica **a nivel de router**, en `app/main.py`, así que
`routes.py` no sabe nada de autenticación. Los dos roles del sistema
(`admin` y `analyst`) entran igual: en Tracking no hay ningún endpoint
reservado a administradores.

| Situación | Respuesta |
|---|---|
| Sin cabecera `Authorization` | `401 Token no proporcionado` |
| Token con firma o formato inválidos | `401 Token inválido` |
| Token caducado | `401 Token expirado` |
| Token válido (`analyst` o `admin`) | la respuesta normal del endpoint |

Siguen **sin** pedir token `/docs`, la página del frontend y el `OPTIONS`
previo de CORS: si el preflight exigiera token, el navegador no podría ni
empezar la llamada. `Authorization` está en los `allow_headers` del CORS.

**Módulo suelto.** Arrancado por su cuenta (`start-dev.ps1`, el Docker de
`deploy/`) no hay ni backend de Casos ni pantalla de login, así que no hay
forma de conseguir un token y la aplicación entera sería un 401. Para eso
está `TRACKING_AUTH_DESACTIVADA=1`, que el lanzador y el compose del módulo
ponen por su cuenta. **Por defecto la autenticación es obligatoria**: hay
que pedir explícitamente lo contrario, y el backend lo escribe en su primera
línea de log, junto con un aviso si `JWT_SECRET` sigue siendo el de ejemplo.

```powershell
.\start-dev.ps1            # sin autenticación (módulo suelto)
.\start-dev.ps1 -ConAuth   # exige el JWT, como en development
```

En el frontend, el token se añade en un único sitio
(`api/httpClient.ts`, leyéndolo de `shared/auth`). Un `401` en una petición
que sí llevaba token se trata como sesión caducada: se borra y se vuelve al
login.

## Arrancar en local

```powershell
.\start-dev.ps1
```

Levanta **la API** en `http://127.0.0.1:8000`, con su documentación en
`/docs`. Un proceso, SQLite local y sin autenticación (ver más arriba).

> **La interfaz ya no la sirve este backend.** Desde la integración en
> `development`, la pantalla de Tracking vive en el frontend único del
> repositorio común (`frontend/src/modules/tracking`), que es la que usa el
> perito. La copia de este módulo (`frontend/`) se conserva como referencia y
> para poder enseñarlo suelto, pero está **en desuso**: mantener dos
> interfaces vivas fue justo lo que hizo que las versiones se separaran.
>
> Para servirla de todos modos:
>
> ```powershell
> .\start-dev.ps1 -ConFrontend
> ```
>
> Eso la compila, activa `TRACKING_FRONTEND_LOCAL=1` y la aplicación vuelve a
> abrirse entera en `http://127.0.0.1:8000`.

**Para probarlo en un minuto** hay un caso de ejemplo listo en
`examples/`: el log `SRV-FILE01_powershell_operational.log` y `CASO.md`, que
explica el incidente y lo que el módulo debe detectar (19 eventos, de baja a
crítica). Súbelo con la zona horaria **UTC+02:00**.

**Con `-ConFrontend`, aplicacion completa en `http://127.0.0.1:8000`.** Mismo
origen, sin CORS, igual que en Docker (`http://localhost:8089`): el build llama
a la API en el mismo host y puerto desde el que se abre la página
(`frontend/.env.production`).

**CORS cerrado.** Solo se aceptan peticiones de otro origen desde el modo
desarrollo (`http://localhost:5173` y `http://127.0.0.1:5173`); `CORS_ORIGINS`
(separados por comas) añade más si hace falta. Antes se aceptaba cualquiera,
y cualquier web abierta en el navegador podía escribir en `tracking_events`
a través del backend local.

**Comprueba a qué base se conecta.** Al arrancar, el log muestra
`Base de datos: …` (sin contraseña). `start-dev.ps1` usa SQLite si no hay
`DATABASE_URL`; con `.\start-dev.ps1 -UsarEnv` usa la del `.env` (la base
**compartida**, como `npm run dev:all` en development) y no ejecuta
migraciones contra ella. Un `uvicorn` lanzado a mano sin `DATABASE_URL`
también usa el `.env`.

Equivalente a mano:

```bash
python -m venv venv
source venv/bin/activate          # en Windows: venv\Scripts\Activate.ps1
pip install -r requirements.txt
cd frontend && npm install && npm run build && cd ..

# El motor oficial es MySQL. Para desarrollo local sin servidor, SQLite vale:
export DATABASE_URL="sqlite:///./nexus_dev.db"

# OBLIGATORIO: la app ya no crea las tablas. Si faltan, se niega a arrancar
# y te recuerda este comando.
alembic upgrade head

uvicorn app.main:app --port 8000
```

Si solo has tocado backend y ya hay un build hecho, `.\start-dev.ps1 -SinBuild`
se salta la compilacion.

### Modo desarrollo, con recarga en caliente

Solo si vas a tocar el frontend **propio** (el que está en desuso) y quieres
que los cambios se vean al guardar. Levanta dos procesos (uvicorn con
`--reload` y Vite), y entonces **la aplicacion se abre en
`http://localhost:5173`**:

```powershell
.\start-dev.ps1 -Dev -ConFrontend
```

Para tocar la interfaz **oficial**, la de verdad, se trabaja en el frontend
único del repositorio común, no aquí.

### Que responde cada ruta

| Ruta | Responde | ¿Pide token? |
|---|---|---|
| `/`, `/tracking`, `/cases`, `/timeline`... | la aplicacion React | no |
| `/cases/{id}/tracking/...`, `/cases-lookup` | la API | **sí** |
| `/cases/` | casos de prueba, solo con SQLite | no |
| `/docs` | documentacion interactiva de la API | no |
| `/legacy` | UI antigua, solo referencia historica | no |

Fijate en la **barra final**: es lo que separa la pantalla de casos (`/cases`)
de la API de casos (`/cases/`). Las rutas de la API y `/docs` se registran
antes que el frontend, y este ultimo hace de respaldo con `index.html` para
que recargar en `/tracking` no devuelva un 404.

## Migraciones (Alembic)

```bash
# tras modificar un modelo:
python -m alembic revision --autogenerate -m "descripción del cambio"
python -m alembic upgrade head

# deshacer la última migración:
python -m alembic downgrade -1
```

`env.py` resuelve la base de datos **igual que la aplicación**
(`DATABASE_URL`, o las variables `MYSQL_*` del `.env`, con TLS para MySQL
gestionado) — no hace falta editar `alembic.ini` — y al arrancar anuncia la
base destino, sin contraseña. **Ojo:** si tu `.env` apunta a la base
compartida, Alembic también; para trabajar en local, fija antes
`DATABASE_URL=sqlite:///./nexus_dev.db` (es lo que hace `start-dev.ps1`).

Dos salvaguardas:

- **Tabla de versiones `alembic_version_tracking`**, la misma que usa Tracking
  en `development` y en la base compartida. Cada módulo lleva su historial
  en su propia tabla.
- **Autogenerate solo mira `tracking_events`** (`TABLAS_PROPIAS` en
  `env.py`). Antes comparaba contra toda la base y, al no haber modelo de
  `evidences`, proponía borrarla. `tests/test_alembic.py` comprueba que
  modelos y migraciones coinciden sin tocar tablas ajenas.

## Tests

```bash
python -m pytest tests/ -v
```

234 tests en total: 187 del módulo (parser, codificaciones y formatos de
hora, clasificación con el `rules.yaml` real, indicadores y
`-EncodedCommand`, integridad contra `tracking_events`, guardado atómico y
concurrente, zona horaria, validaciones de la API, CORS, Alembic y
rendimiento) y 47 del motor interno de `agent/`.

Los tests usan una SQLite y una carpeta de cadena temporales
(`tests/conftest.py`): nunca tocan `nexus_dev.db`, `.tracking_chain/` ni la
base de datos del `.env`.

## Rendimiento

Medido con un log de 20.000 comandos (y 6.667 líneas de salida):

| | Antes | Ahora |
|---|---|---|
| Analizar | 6,35 s | 2,85 s, con más reglas, indicadores y decodificación |
| Respuesta del análisis | 9,5 MB | 10,1 MB sin comprimir → **0,32 MB** con gzip |
| Petición de guardado | 12,3 MB | 3,7 MB (solo los campos que se guardan) |
| Mientras se analiza | toda la app bloqueada | el resto de peticiones responden |

Cómo: el clasificador serializa el evento una vez (no una por condición),
funde los candidatos de cada condición en una sola expresión regular y
comprueba antes las condiciones exactas; `rules.yaml` se cachea y solo se
recarga si cambia; el análisis corre fuera del bucle de eventos; las
respuestas van comprimidas y sin campos nulos; el guardado inserta todas las
filas en un solo viaje a la base de datos; y la interfaz pinta las tablas de
500 en 500 filas.

`requirements-web.txt` tiene solo lo que necesita la aplicación (es lo que
instala el Dockerfile); `requirements.txt` añade los tests y el motor de
captura en vivo de `agent/` (watchdog, psutil, flask, pywin32). Las versiones
van **fijadas** (`==`), como en Casos y Timeline: con rangos abiertos, dos
personas podían instalar versiones distintas del mismo proyecto.

## Endpoints

| Método | Ruta | Qué hace |
|---|---|---|
| POST | `/cases/{case_id}/tracking/analyze` | Sube un log (`file`, y opcional `zona_horaria`: `UTC` o `+02:00`), devuelve vista previa clasificada (no persiste) |
| POST | `/cases/{case_id}/tracking/events` | Persiste los eventos revisados en `tracking_events` |
| GET | `/cases/{case_id}/tracking/events` | Lista los eventos guardados de un caso, paginados (`skip`, `limit`; 100 por defecto, 1000 como máximo) |
| GET | `/cases/{case_id}/tracking/verify` | Verifica la integridad interna (capa opcional) |
| GET | `/cases-lookup` | Casos para el selector del frontend (`id`, `nombre`, `estado`), sin los eliminados |
| POST | `/cases/` | *(solo con SQLite)* crea un caso de prueba local |
| GET | `/cases/` | *(solo con SQLite)* lista los casos de prueba locales |

Respuestas y límites que conviene conocer:

| Código | Cuándo |
|---|---|
| `401` | Falta el JWT, o es inválido o caducado (ver "Autenticación") |
| `400` | El fichero no es texto, o la zona horaria no es válida |
| `404` | El caso no existe, o la ruta de la API no existe (JSON, no la página) |
| `409` | Se intenta analizar o guardar en un caso **eliminado o archivado** (mismo criterio y mensaje que Casos), o guardar un fichero de log que **ya se guardó en ese caso** (mismo SHA-256; repetir con `"forzar": true` si es intencionado) |
| `413` | El fichero supera `TRACKING_MAX_LOG_MB` (20 MB por defecto, el mismo límite que la pasarela nginx del despliegue) |
| `500` | Error no controlado: siempre como JSON `{"detail": "Error interno del servidor"}` y con cabeceras CORS (contrato común de los backends) |
| `422` | `fuente_log` o `usuario_detectado` de más de 100 caracteres, o un `evento` de más de 65.535 bytes: los límites de las columnas de `tracking_events`, que SQLite no aplica pero MySQL sí |

La paginación sigue el patrón de Casos y OSINT (`skip`/`limit`). La interfaz
pide páginas hasta agotarlas, porque necesita el caso completo para filtrar;
la verificación de integridad también mira todos los eventos, nunca una
página. El cliente HTTP comparte contrato con el resto del frontend:
`new ApiError(status, detail)`, con `detail` tal cual lo devuelve FastAPI
(en los 422 es una lista, y se convierte en un mensaje legible).

El análisis devuelve `sha256_log` (huella del fichero subido) y
`eventos_ya_guardados` (cuántos eventos de ese mismo fichero hay ya en el
caso), para avisar antes de duplicar. El SHA-256 queda también en la cadena
de integridad local como procedencia de cada evento. El análisis se ejecuta
fuera del bucle de eventos: un log grande ya no bloquea el resto de la
aplicación mientras se procesa.

## Estructura

```
track-inc/
├── app/
│   ├── main.py                 # FastAPI: rutas, verificación de esquema, frontend
│   ├── core/
│   │   └── database.py         # engine/sesión compartidos (Base única)
│   ├── dev/
│   │   └── casos_locales.py    # casos de prueba, SOLO con SQLite (nunca contra MySQL)
│   └── modules/
│       └── tracking/
│           ├── models.py           # TrackingEvent — esquema oficial exacto (+ referencia a cases.id)
│           ├── schemas.py          # Pydantic — sin campos de hash
│           ├── repository.py       # acceso a datos puro
│           ├── service.py          # lógica de negocio
│           ├── routes.py           # endpoints FastAPI
│           ├── log_parser.py       # CU-03: parseo de logs de texto
│           ├── indicators.py       # extracción de IOC: IPs, dominios, URLs, rutas...
│           ├── severity_mapping.py # Criticality (interno) <-> Severidad (oficial)
│           └── chain_integrity.py  # cadena de hashes, aislada del esquema oficial
├── agent/                      # motor interno: clasificador + cadena de hashes
├── alembic/                    # migraciones versionadas
├── alembic.ini
├── config/                     # plantilla de configuración del agente
├── deploy/                     # Dockerfile (variantes `api` y `completo`) + docker-compose + .env.example
├── docs/integracion/           # lo que hay que llevar a mano al repositorio común
├── examples/                   # caso de ejemplo (log + CASO.md) y demos del motor interno
├── frontend/                   # interfaz propia, EN DESUSO (la oficial vive en el frontend comun)
├── legacy-frontend/            # UI antigua sin build, servida en /legacy
├── tests/                      # 304 tests (módulo + motor interno)
├── requirements-web.txt        # solo la aplicación web (Docker)
└── requirements.txt            # entorno completo: web + tests + agent/
```

## Sobre `agent/`

Motor de clasificación por reglas y cadena de hashes desarrollado antes
que la API. `app/modules/tracking/` lo reutiliza como dependencia interna
(ver `chain_integrity.py`), pero nunca lo expone en la API ni en el
esquema oficial. Contiene además exploraciones previas (collectors en
vivo, servicio de sistema, panel Flask) de una fase en la que se planteó
un agente de monitorización continua en vez del flujo "subir log ya
existente" que pide CU-03. Siguen pasando sus tests, pero **no forman
parte del flujo actual**.
