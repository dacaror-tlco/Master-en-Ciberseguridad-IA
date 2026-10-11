# Estado del Módulo 5 (Sharingan) — Generador de Informes

Documento de continuidad entre sesiones. Qué está hecho, qué se decidió y por
qué, y qué queda pendiente. La especificación de arquitectura sigue siendo el
`CLAUDE.md` de la raíz del proyecto; esto es el registro de avance.

Última actualización: **2026-09-23**.

> **Novedades recientes:**
>
> 1. **Compatibilidad con las ramas de los compañeros, comprobada contra su
>    código y no contra la especificación** (2026-08-29). Tres cosas dejan
>    de ser un riesgo de integración: los ids de Alembic ya no colisionan,
>    la pantalla es un reemplazo directo del placeholder del Módulo 1 y hay
>    tests que ejecutan el módulo sobre el DDL real del Módulo 1. De paso se
>    corrigen dos afirmaciones falsas sobre el Módulo 2 y aparece un bloqueo
>    nuevo y grave: **dos tablas `cases` incompatibles**. Ver
>    "Compatibilidad con las otras ramas".
> 2. El Módulo 2 ya existe como código real en la rama `scam-shield`, reescrito
>    para adaptarse al esquema de módulos de Nexus. Ver "Contraste con el
>    Módulo 2 real": **no crea la tabla `osint_results`**, así que el Anexo B de
>    todos los informes saldría vacío al integrar. Nada que corregir dentro del
>    Módulo 5; es una decisión de contrato del equipo.
> 3. El informe se emite ya en **cuatro formatos** (PDF, DOCX, HTML y JSON).
>    Ver "Exportación en varios formatos".
> 4. Tres arreglos de robustez del registro de informes: ruta relativa en
>    `archivo_pdf`, restricción única sobre `(case_id, version)` con reintento,
>    y desempate en el orden de la cronología. Ver "Decisiones tomadas".
> 5. Revisado el despliegue en Raspberry Pi con dominio y endurecida la
>    protección contra inyección. Ver sus dos secciones.
> 6. El espejo se ha vuelto **permisivo al leer**, para digerir el formato que
>    propone el Módulo 3 sin pedirle que lo cambie. Ver "Contrato con los
>    módulos que escriben".
> 7. El informe emitido lleva **huella SHA-256** y se verifica al descargarlo.
>    Ver "Huella del informe emitido".
> 8. Se archiva el **prompt literal** enviado a la IA, y las tablas del PDF
>    parten los valores largos por donde se leen. Ver "Registro de la
>    generación" y "Cortes de línea en las tablas del PDF".
> 9. El perito puede **acotar el alcance de la emisión** —qué anexos, qué
>    franja temporal, qué severidad, en qué formatos— y el informe declara
>    por sí mismo lo que ha dejado fuera. Ver "Alcance de la emisión".
> 10. **Ya existen las ramas de los Módulos 3 y 4**, y contrastarlas ha
>    cazado algo grave: el espejo declaraba una columna `tracking_events.
>    detalles` que su tabla real no tiene, y con ella no se habría generado
>    ningún informe al integrar. Ver "Contraste con los Módulos 3 y 4 reales".
> 11. **El módulo se ha ejecutado por fin contra la base compartida del
>    equipo** (Aiven, `defaultdb`). Salieron dos fallos, los dos corregidos:
>    faltaba aplicar `m5_0005`, y `osint_results` no existe allí — lo que no
>    dejaba el Anexo B vacío, sino que tumbaba *toda* generación con un 500.
>    Ver "Contra la base compartida del equipo".
> 12. **Verificadas las tablas del Módulo 1 en esa base**, a petición suya: no
>    hay nada a lo que adaptarse, y de paso queda reproducido el 500 al borrar
>    un caso con informes, que hasta ahora era una predicción.

---

## Estado actual: funcional y testeado

Backend completo del Módulo 5. **166/166 tests en verde** (SQLite en memoria,
llamadas a Anthropic mockeadas, sin red).

### Endpoints

| Método | Ruta | Notas |
|---|---|---|
| `POST` | `/reports/generate` | `{case_id, generado_por, notas?, opciones?}` → compone el informe, lo guarda en los formatos pedidos y crea una versión nueva. Sin `opciones`, el caso entero en los cuatro formatos |
| `GET` | `/reports/{id}` | Metadatos del informe |
| `GET` | `/reports/{id}/download` | `?formato=pdf\|docx\|html\|json`; sin parámetro, PDF. Verifica la huella antes de servir y la publica en `X-Informe-SHA256` |
| `GET` | `/reports/{id}/prompt` | Transcripción literal de lo enviado a la IA; `410` si el informe es anterior a que se archivase |
| `GET` | `/cases/{case_id}/reports` | Todas las versiones generadas para el caso |
| `GET` | `/health` | Comprobación de vida |

Códigos de error: `404` caso/informe inexistente · `409` colisión de versión
entre generaciones simultáneas (reintentar) · `422` caso sin cronología,
alcance imposible o que deja la cronología vacía, o formato no soportado ·
`503` sin `ANTHROPIC_API_KEY` o IA no disponible (red,
rate limit, 5xx) · `502` la IA respondió algo no firmable (truncado, rechazado,
o citando eventos inexistentes) · `410` el fichero registrado ya no existe.

### Estructura del informe generado

El informe sigue el esqueleto de un informe pericial (UNE 197010), no un volcado:

portada identificada (código `INF-XXXX-vN`, versión, fecha de emisión, caso,
responsable, emisor) → 1. Objeto y alcance → 2. Antecedentes (incluye las notas
del perito) → 3. Material analizado → 4. Metodología → 5. Cronología →
6. Hallazgos → 7. Conclusiones → 8. Declaración sobre el uso de IA →
9. Firma → Anexo A (evidencias) · Anexo B (OSINT) · Anexo C (tracking).

Pie con `Página X de Y` y el código del informe en todas las páginas.

---

## Decisiones tomadas (y por qué)

* **Hallazgos y conclusiones separados.** Antes eran un único bloque de texto
  del LLM que mezclaba hechos y juicio pericial. Se piden a la IA como salida
  estructurada (`output_config.format` con JSON Schema) y se imprimen en
  secciones distintas.

* **Trazabilidad evento → registro de origen.** La tabla de cronología incluye
  una columna `Ref.` con `origen_modulo#origen_id`, y en el prompt los eventos
  van numerados `[E1]`, `[E2]`… El sistema **valida por código** que la
  narrativa no cita ningún evento inexistente y rechaza el informe si lo hace.
  Es la comprobación de alucinación más barata que hay y no necesita red.

* **Nada de `temperature`.** Claude Opus 5 rechaza `temperature`/`top_p`/`top_k`
  con HTTP 400. La reproducibilidad exacta no es alcanzable con un LLM: se
  gestiona **declarándola** en el apartado 8 (modelo, nivel de esfuerzo, versión
  de prompt) en lugar de fingirla. Tampoco existe un ID de modelo con fecha para
  `claude-opus-5` que pudiera fijarse.

* **`max_tokens` a 8000 y comprobación de `stop_reason`.** El pensamiento del
  modelo consume del mismo presupuesto que la respuesta; con el límite anterior
  (1024) un caso con muchos eventos producía conclusiones cortadas a mitad de
  frase que se guardaban y se firmaban igual. Ahora si `stop_reason` es
  `max_tokens` o `refusal` el informe **no se genera**.

* **Un único sello de tiempo.** El PDF y su fila en `reports` comparten
  `fecha_generacion`; antes cada uno estampaba su propio `now()`.

* **Anexos con los datos de los Módulos 1, 2 y 3.** Un informe cuya única prueba
  es la narrativa no es defendible. `app/modules/shared/models.py` amplía el
  espejo de solo lectura a `evidences`, `osint_results` y `tracking_events`.

* **La ruta del informe se guarda relativa al almacén** (`case_1/report_v2.pdf`),
  no absoluta. Guardarla absoluta ataba cada fila a la máquina que generó el
  informe: al desplegar en Docker o mover el almacenamiento, todas las filas
  anteriores apuntarían a ficheros inexistentes, y de paso la API exponía la
  estructura de directorios del servidor. Las filas antiguas con ruta absoluta
  se siguen sirviendo: reescribir la ruta de un informe ya emitido es tocar el
  registro de algo que ya se firmó.

* **Restricción única sobre `(case_id, version)`** (migración `0003`, sin
  columnas nuevas). El número de versión se calculaba leyendo el máximo actual,
  así que dos generaciones simultáneas del mismo caso podían emitir dos «v2»
  distintos: dos documentos periciales bajo el mismo código `INF-XXXX-vN`, que
  es justo lo que ese código existe para impedir. El servicio reserva la
  versión con un `flush` **antes** de escribir los ficheros y reintenta si
  choca; si escribiera primero, el perdedor de la carrera habría sobrescrito
  los documentos del ganador con los suyos. Agotados los reintentos responde
  `409`, no `500`: reintentar la petición funciona.

* **La cronología desempata por `fecha_hora` e `id`.** El apartado de
  metodología afirma que el orden es determinista, pero `orden` lo fija el
  Módulo 4 y no es único; sin desempate, dos versiones del mismo informe
  podrían contradecirse en el orden de los eventos empatados.

* **Columna `notas` en `reports`** (migración `m5_0002`). Es la primera de las
  desviaciones del modelo de datos oficial —hoy son cuatro: las columnas
  `notas`, `huellas` y `opciones` en `reports`, más los identificadores de
  texto (ver "Contrato con los módulos que escriben")— y
  está justificada: las notas del perito entran en el prompt y condicionan las
  conclusiones, así que dejarlas sin registrar rompía la reproducibilidad del
  informe.

* **Todo el texto va envuelto en `Paragraph` y escapado.** Una cadena suelta en
  una celda de `Table` de reportlab **no** hace salto de línea (se desborda de la
  columna), y reportlab interpreta mini-HTML, así que un `<` o un `&` en una
  descripción rompía la generación. Hay tests para ambos casos.

---

## Protección contra inyección (XSS)

El informe reproduce texto de los Módulos 1 a 4: nombres de dominio de OSINT,
líneas de log, descripciones de evidencia. Parte de eso lo elige el investigado
—quien registra un dominio decide cómo se llama—, así que se trata como
contenido hostil. Es además contenido que acaba en un documento que se archiva
y se reenvía, no solo en una pantalla.

### Capas

1. **Escapado.** Todo el texto pasa por `html.escape` (con comillas, que es lo
   que impide salirse de un atributo). El PDF usa el escapado de reportlab y el
   DOCX y el JSON los de sus propias bibliotecas.
2. **Política de contenido del documento** (`CSP_INFORME`): `default-src
   'none'`, solo el CSS incrustado. Aunque un día se escapase mal, el navegador
   no ejecutaría nada. Va **incrustada en el `<meta>`** además de en la
   cabecera, porque el informe se abre desde disco o desde el correo, donde no
   hay respuesta HTTP.
3. **`X-Content-Type-Options: nosniff`** en toda la API: sin ella un navegador
   puede decidir que una respuesta JSON «parece» HTML y renderizarla.

### Detalles

* El HTML no carga **nada** de fuera: ni scripts, ni fuentes, ni imágenes. Hay
  un test que lo comprueba, y sirve a la vez para el archivado a largo plazo.
* La única interpolación en contexto de atributo (`Espacio`) fuerza formato
  numérico, así que no se puede inyectar por ahí ni haciéndola configurable.
* El frontend no usa `dangerouslySetInnerHTML` en ninguna parte; React escapa
  por defecto.

### Tests (`tests/test_xss.py`)

Siete cargas —etiqueta, ruptura de atributo, manejador de evento,
`javascript:`, cierre de `<style>`— metidas por **todos** los campos de texto
ajeno a la vez. No se comprueba por subcadenas, que confunde el texto escapado
con el marcado real: se **parsea el HTML** y se exige que no aparezca ninguna
etiqueta ni ningún atributo fuera de la lista permitida, y que ningún atributo
empiece por `on`.

Comprobado que los tests fallan de verdad: desactivando el escapado, tres se
ponen en rojo.

### Pendiente

`CSP_INFORME` permite `style-src 'unsafe-inline'` por el `<style>` del propio
documento. Se puede cerrar con un hash del bloque de estilos si algún día se
quiere apurar; no aporta gran cosa mientras `default-src` siga en `'none'`,
porque el CSS por sí solo no ejecuta.

---

## Registro de la generación

Hecho el 2026-08-28. Era la mitad del punto 11 de "Pendiente".

Al emitir se archiva `report_vN.prompt.txt` junto a las cuatro copias, con la
transcripción literal de lo enviado al modelo: parámetros de la llamada,
prompt de sistema y prompt de usuario con la cronología concreta. Se recupera
con `GET /reports/{id}/prompt` y se verifica con su huella igual que las
copias.

### Por qué

El apartado 8 ya declaraba modelo, esfuerzo y versión de instrucciones. Pero
esa declaración hay que creérsela: `2026-08-15.1` es una etiqueta y el texto
al que apunta vive en el código, que cambia; un informe de hace tres meses
declara una versión cuyo contenido nadie puede ya exhibir. La transcripción
no hay que creérsela. Además es **la única entrada del informe que no se
puede reconstruir leyendo el propio documento**: los hechos están en los
anexos, pero lo que se le pidió al modelo, no.

### Decisiones

* **Un fichero con las copias, no una columna.** Es un documento de la
  emisión, como ellas, y se le exige la misma integridad: su huella va en
  `reports.huellas` bajo la clave `prompt`. De paso evita una columna más
  sobre el modelo de datos oficial, que ya lleva varias sin refrendar.
* **Van también los parámetros de la llamada**, no solo los dos prompts: el
  mismo texto con otro `effort` o con otro esquema de salida no produce lo
  mismo, así que el prompt a secas no explicaría la salida.
* **Endpoint propio, no un `formato` más.** No es una copia del informe en
  otro soporte; meterlo en `FormatoInforme` lo habría hecho aparecer como si
  lo fuera, y `document.py` no lo compone.
* **El apartado 8 solo promete el archivo si existe.** Una previsualización no
  llama a la IA y no archiva nada; si el párrafo saliera igual, el documento
  declararía un registro que no tiene. Hay test.
* **Los informes anteriores devuelven `410` y no se reconstruye nada.** El
  prompt que produciría el código de hoy no tiene por qué ser el que se usó,
  y presentarlo como tal sería falsear el registro, que es peor que no
  tenerlo.

---

## Cortes de línea en las tablas del PDF

Hecho el 2026-08-28. Era la otra mitad del punto 11.

Los valores del Anexo B —dominios, correos, URLs— no caben en su columna y
reportlab los partía por donde le tocaba: `direccion@beltran-logistica` /
`.com` se leía como `…logistica` / `.com`, pero `victima@dominio-c` /
`orporativo.example.com` ya no se lee. Ahora el corte se elige antes, en los
separadores del propio valor (`.`, `-`, `/`, `@`, `_`, `:`).

No es una cuestión de exactitud: reportlab no inserta guion al partir, así que
concatenar las líneas devuelve el valor íntegro en los dos casos, y hay un
test que fija esa propiedad. Es que el Anexo B existe para que alguien
compruebe un indicador por su cuenta, casi siempre tecleándolo desde el papel.

Dos cosas que costaron y conviene no volver a intentar:

* **El espacio de ancho cero (U+200B) no sirve.** reportlab no lo trata como
  oportunidad de corte, y encima Helvetica le da 6 pt de ancho: se vería.
* **Solo se tocan las palabras que por sí solas no caben.** La primera versión
  partía por separadores todo el contenido de la celda y rompió lo que ya
  funcionaba: la columna «Consulta (UTC)» pasó a mostrar `2026-08-03 13:` /
  `00`, con la hora cortada por la mitad, habiendo un espacio en medio que era
  un sitio perfectamente bueno para el salto. Hay test de regresión.

Lo que no tiene separadores —un SHA-256— se deja entero y decide reportlab;
contra eso no hay nada mejor.

---

## Huella del informe emitido

Hecho el 2026-08-28. Era el punto 9 de "Pendiente".

Al emitir se guarda el SHA-256 de las cuatro copias en la columna nueva
`reports.huellas` (JSON, migración `0004`), y al descargar se recalcula sobre
el fichero del almacén. Si no coincide, `409` y no se sirve.

### Por qué

La única comprobación que había al descargar era que el fichero *existiera*.
Sustituir el PDF en disco por otro documento no lo detectaba nadie y la API lo
entregaba igual, presentándolo como el informe pericial emitido en su día. Un
informe alterado hace más daño entregado que no entregado: quien lo recibe no
tiene forma de distinguirlo.

### Decisiones

* **La huella se calcula sobre los bytes recién compuestos, no releyendo el
  fichero.** Releerlo daría por buena cualquier alteración ocurrida entre
  escribir y verificar, que es exactamente el hueco que esto viene a cerrar.
* **Una columna JSON con los cuatro formatos**, no cuatro columnas de texto,
  por el mismo motivo por el que `archivo_pdf` guarda una sola ruta: las
  cuatro copias se emiten juntas y se nombran igual. Añadir un quinto formato
  no vuelve a tocar el esquema. Es la **segunda columna** que este módulo
  añade a `reports` (la primera fue `notas`) y la cuarta desviación del modelo
  de datos oficial: hay que refrendarla con el equipo.
* **`409`, no `410`.** El `410` ya significa «esta copia no se emitió nunca»,
  que es lo normal en los informes anteriores a los cuatro formatos. Quien
  descarga tiene que poder distinguir eso de un fichero que ya no es el que el
  informe declara.
* **Cada copia responde de sí misma.** Que alguien toque el DOCX no es motivo
  para dejar de servir el PDF, que es el documento firmado.
* **Los informes anteriores a la migración `0004` no tienen huella y se sirven
  sin verificar.** No se les calcula a posteriori: el hash del fichero que hoy
  está en disco no demuestra que sea el que se emitió, así que rellenarlo
  ahora sería fabricar una prueba, no recuperarla.
* **La huella se publica** en la cabecera `X-Informe-SHA256` y en `ReportOut`,
  y el panel de detalle del frontend la muestra. Una huella que solo comprueba
  el servidor no le demuestra nada a quien recibe el documento; publicada,
  cualquiera la contrasta con `sha256sum`.
* **No va impresa dentro del PDF**, por lo evidente: un documento no puede
  contener su propio hash.

### Tests (`tests/test_huella_informe.py`)

Trece. Los que importan: que la huella registrada sea la del fichero realmente
escrito (si se guardase la de otra cosa, *todas* las descargas fallarían), que
alterar **un solo byte** se detecte —el caso realista es cambiar una cifra de
una fecha, no reemplazar el fichero entero—, que tocar una copia no bloquee
las demás, y que un informe sin huella se siga sirviendo.

### Lo que esto no es

No es la cadena de custodia que el `CLAUDE.md` deja fuera de alcance. Allí se
descartan los hashes **de la evidencia**, que competen al Módulo 1. Esto es la
huella del documento que emite este módulo, y no depende de ningún otro.

### Lo que sigue sin cubrir

Que el fichero coincida con su huella demuestra que nadie lo tocó **en disco**.
No demuestra nada frente a quien pueda escribir en la base de datos: quien
cambie la fila puede cambiar el hash. Cerrar eso es firma criptográfica y
tercero de confianza, no un hash, y está muy por encima del alcance de la
práctica.

---

## Contrato con los módulos que escriben

Este módulo lee cinco tablas que no son suyas y las imprime. Ya van **tres**
veces que un desajuste minúsculo en ellas habría impedido generar *cualquier*
informe:

| Módulo | Desajuste | Consecuencia |
|---|---|---|
| 1 (`modulo-casos`) | `estado` guardado por valor y leído por nombre | LookupError en cada informe |
| 2 (`scam-shield`) | `osint_results` no existe | Anexo B vacío siempre |
| 3 (propuesta 2026-08) | `severidad` con tilde, ids de texto | LookupError y error de tipo |

De ahí el criterio nuevo del espejo: **ser permisivo al leer**. Un módulo que
solo lee y solo imprime no gana nada siendo estricto con el formato ajeno; gana
no caerse. Ser estricto tendría sentido si validase datos, y no es el caso.

### Lo que ahora se tolera

* **Severidad y estado con tilde, en mayúsculas o con espacios.** `crítica`,
  `CRÍTICA` y `  Critica  ` se leen todas como `critica`, que es lo que se
  imprime. Implementado con `_missing_` en los Enum y un `TypeDecorator`
  (`EnumTolerante`), porque la fila la escribe otro y puede llegar de
  cualquiera de esas formas. Un valor **inventado** (`gravísima`) sigue
  fallando: tolerar variantes no es tragar cualquier cosa.
* **Identificadores de texto** (`evt-7f3a9c2e`, `tl-1`, `obs-9f2a8b1c`) en
  `tracking_events.id`, `timeline_events.id` y `timeline_events.origen_id`,
  vía el tipo `IdAjeno`. Un entero cabe en un texto; al revés, no. Si el equipo
  acuerda INTEGER, esto sigue funcionando sin tocar nada. **Es una desviación
  consciente del modelo de datos oficial**, pendiente de que se fije el tipo.
* ~~**`tracking_events.detalles`**~~ **Retirado el 2026-09-02.** Se toleró
  como segunda desviación del esquema —el detalle crudo del evento, mismo
  criterio que `osint_results.raw_response`— hasta comprobar que la tabla real
  del Módulo 3 no tiene esa columna. Aquí está el límite de la permisividad, y
  conviene tenerlo claro: se puede ser tolerante con **lo que trae** una
  columna, nunca con **si existe**. Un `SELECT` pide las columnas declaradas y
  MySQL responde «Unknown column» a la que falta, así que esto no era una
  concesión sino un fallo garantizado. Ver "Contraste con los Módulos 3 y 4
  reales".

### Lo que no se tolera, y por qué

`origen_modulo` tiene que identificar **en qué tabla** buscar el `origen_id`
(`evidences`, `osint`, `tracking`), que es como lo define el `CLAUDE.md`. En la
propuesta del Módulo 3 venía como `"mentor"`, que probablemente sea el nombre
en clave de su módulo —el equipo los usa para las ramas: `sharingan`,
`scam-shield`—. No es un valor inventado, pero tampoco resuelve: el informe
promete en su metodología que *cualquier afirmación puede contrastarse contra
el registro del que procede*, y ese texto lo lee un juez, no el equipo.
`tracking#evt-7f3a9c2e` se sigue hasta el Anexo C; `mentor#evt-7f3a9c2e`
necesita una tabla de equivalencias que nadie de fuera tiene.

Pendiente de acordar con el equipo: si se decide que la columna lleve nombres
en clave, este módulo puede traducirlos al imprimir (una tabla de equivalencias
y el `match` de la columna «Ref.»), pero esa equivalencia tiene que estar
escrita y acordada, no adivinada.

Hay un test que lo comprueba de verdad (`test_cada_referencia_de_la_cronologia_
resuelve_en_los_anexos`): cada `modulo#id` de la columna «Ref.» debe aparecer
como fila del anexo correspondiente. No es teórico — al pasar a identificadores
de texto, el previsualizador renumeraba las filas y el Anexo C decía «2» donde
la cronología decía `tracking#evt-7f3a9c2e`. Dos tablas del mismo informe
nombrando distinto el mismo registro.

### Otra cosa a decirle al Módulo 3

En su ejemplo, el evento ocurre a las `16:20:15` y la entrada de cronología que
lo describe marca `16:20:10`. Si no coinciden, la Cronología y el Anexo C del
informe dan **horas distintas para el mismo hecho**, y eso en un peritaje se lo
regala a la parte contraria. `timeline_events.fecha_hora` debería ser
exactamente la `hora` del evento de origen.

### Fixture de referencia

`fixtures/caso_005_bindshell_modulo3.json` está escrita con el formato que
propuso el Módulo 3 —ids de texto y severidad con tilde— e incluye eventos de
nmap y de tráfico web. Sirve de contrato ejecutable: si alguien endurece el
espejo, ese test se cae antes que la integración. Llevaba también un objeto
`detalles` por evento, retirado el 02/09 con la columna.

---

## Despliegue previsto en Raspberry Pi con dominio

Revisado el 2026-08-17, al saberse que el destino es un Pi enganchado a un
dominio. Detalle operativo en el README; aquí lo que condiciona decisiones.

### Comprobado

* **Hace falta Raspberry Pi OS de 64 bits.** Contrastado contra PyPI: en
  `armv7l` no hay rueda de `lxml`, `pillow`, `uvloop` ni `httptools`, así que
  pip las compilaría en el propio Pi. En `arm64` están todas. `mysql:8.4`
  publica `arm64/v8` (verificado en el manifiesto), pero no `armv7`.
* **No hay dependencias de fuentes ni de locale**: reportlab usa Helvetica,
  que es interna, y HTML y JSON se escriben en UTF-8 explícito. Un Pi sin
  entorno gráfico no necesita nada más.
* Los endpoints son síncronos, así que FastAPI los atiende en su pool de
  hilos y una generación larga no bloquea al resto.

### Ajustado

* La aplicación se publica solo en `127.0.0.1`; delante tiene que ir un proxy
  inverso con el TLS.
* MySQL deja de publicar el 3306 en el host: le basta la red interna de
  Compose. Publicado, un Pi con dominio expone MySQL a Internet.
* El contenedor deja de correr como root.
* CORS pasa a configurarse por entorno (`CORS_ORIGINS`) en vez de estar fijado
  a `*` en el código.

### Pendiente de decisión del equipo, y es bloqueante para salir a Internet

**El módulo no tiene autenticación** — está fuera de alcance por decisión del
proyecto, pero esa decisión se tomó cuando era una aplicación local. Con un
dominio delante, cualquiera que sepa la URL puede descargar cualquier informe
pericial (datos personales de una investigación) y generar informes, que son
llamadas de pago a Anthropic sin límite de frecuencia.

Hasta que el proyecto defina su autenticación: red privada (VPN o Tailscale) o
credenciales en el proxy inverso antes de que la petición llegue a la
aplicación. Conviene además limitar la frecuencia de `POST /reports/generate`,
que es el único endpoint que cuesta dinero.

**Nota para cuando llegue la autenticación**: el HTML se sirve `inline` desde
el origen de la API. Hoy es seguro porque no hay sesiones que robar; el día que
las haya, servir HTML en el mismo origen que la API pasa a ser una vía de XSS
contra ellas, aunque el contenido vaya escapado. Revisarlo entonces.

### Y el reloj

El Pi no tiene reloj de tiempo real. Sin sincronizar, `fecha_generacion` —que
se estampa en la portada de un documento pericial— sería falsa, y la conexión
TLS con Anthropic fallaría. Exigir `systemd-timesyncd` o `chrony` activos y
arrancar el servicio con `After=time-sync.target`.

---

## Compatibilidad con las otras ramas

Hecho el 2026-08-29, después de descargar las ramas de los compañeros y leer
su código. Todo lo de esta sección son cambios **dentro del Módulo 5**: no se
ha tocado ni pedido nada a nadie.

El criterio fue separar dos cosas que se venían mezclando: lo que este módulo
puede arreglar por su cuenta y lo que exige una decisión del equipo. Casi todo
lo que había apuntado como "bloqueo" era de lo segundo, pero no todo.

### Resuelto: la colisión de ids de Alembic

Las revisiones de este módulo se llamaban `0001`…`0004`, y el Módulo 1 tiene
también un `0001`. Al fusionar, todos los módulos comparten un único
directorio `versions/`, y dos revisiones con el mismo id hacen que Alembic
aborte con «Duplicate revision identifier»: no se aplica ninguna migración, ni
la suya ni la mía.

Ahora son `m5_0001`…`m5_0004`. Al fusionar queda **una sola línea**: poner
`down_revision = "0001"` en `m5_0001`, para que la creación de `reports` vaya
después de la de `cases` (`reports.case_id` es FK real y MySQL exige que la
tabla referenciada exista). Las instrucciones están en la cabecera del propio
fichero de migración, que es donde las va a leer quien haga la fusión.

No se encadena ya porque mientras el módulo funcione por separado no tiene
delante el fichero del Módulo 1 y Alembic no sabría resolver el id.

> Efecto secundario: una base de datos de desarrollo anterior al 29/08 tiene
> registrado un id que ya no existe. `alembic stamp m5_0004` y listo; no toca
> datos.

### Resuelto: el frontend ya no pide cambiar el `router.tsx` ajeno

El README del módulo decía que la integración necesitaba «dos cambios de una
línea» en ficheros compartidos, el primero repuntar el import del router al
barril del módulo. Es falso: el Módulo 1 ya importa

```ts
import { ReportsPage } from '@/modules/reports/pages/ReportsPage'
```

y esta carpeta exporta `ReportsPage` con ese mismo nombre desde ese mismo
fichero. Copiar `frontend/src/modules/reports/` **sustituye el placeholder sin
que nadie edite nada**. Verificado ejecutando `tsc --noEmit` sobre el árbol
combinado con el `router.tsx` de `modulo-casos` sin modificar: cero errores.

Queda un único cambio compartido, la variable `VITE_REPORTS_API_BASE_URL`, y
desaparece en cuanto los dos backends se sirvan desde el mismo origen.

Consecuencia para el futuro: `pages/ReportsPage.tsx` y el nombre de su export
son ahora un punto de enganche con otra rama. No se renombran.

### Resuelto a medias: el esquema del Módulo 1, ahora comprobado al ejecutar

`tests/test_esquema_modulo1.py` (11 tests) monta `cases` y `evidences` con el
DDL transcrito literalmente de la migración `0001` del Módulo 1, y ejecuta el
módulo encima: lectura de las cuatro variantes de `estado`, generación del
informe completo, y el Anexo B vacío sin reventar.

La diferencia con `test_contrato_modulos.py` importa: aquel fija hasta dónde
llega la tolerancia del espejo; este comprueba que el módulo funciona contra
el esquema del **dueño** de la tabla. Es la parte del trabajo de integración
que sí se puede hacer antes de integrar.

Incluye dos alarmas de deriva:

* el espejo no puede declarar columnas que la tabla real no tenga (comprobado
  que salta: inyectando una columna falsa caen 8 tests, que es exactamente lo
  que pasaría en producción con un «no such column»);
* el `EstadoCaso` del espejo tiene que cubrir todos los valores del ENUM real.
  Si el Módulo 1 añade un quinto estado, salta aquí en vez de al leer un caso
  con ese estado, que es cuando dejaría de generarse cualquier informe.

Un detalle que costó una iteración: el candidato natural para demostrar que
los tests corren sobre el DDL ajeno y no sobre el espejo era meter un `estado`
inventado y esperar el rechazo. No funciona: `sa.Enum` en SQLAlchemy 2.x trae
`create_constraint=False`, así que sobre SQLite no emite el CHECK. El
discriminante que sí se aplica es `responsable`, NOT NULL en el Módulo 1 y
nullable en el espejo a propósito.

### Documentado, no resuelto: lo que exige decisión del equipo

* **La ruta `POST /reports/generate` duplicada** tiene salida sin tocar código:
  quien monte la app puede remontar cualquiera de los dos routers con
  `include_router(router, prefix=...)`. Este módulo no cede la ruta por su
  cuenta: `reports` es la tabla que le asigna el `CLAUDE.md`.
* **Las dos tablas `cases`** y **la base de datos separada** no tienen arreglo
  desde aquí. Ver "Contraste con el Módulo 2 real".
* **El 500 al borrar un caso con informes** ocurre en el proceso del Módulo 1,
  y desde el 02/09 está reproducido contra la base compartida, no supuesto.
  Lo que sí se ha hecho es dejar escrita la asimetría en el espejo: `evidences`
  cascadea (copiado de su DDL real) y `reports` no, con el motivo al lado. Un
  informe pericial emitido no se borra en silencio porque se borre el caso.

---

## Contra la base compartida del equipo

Hecho el 2026-09-02. Hasta aquí todo se había probado sobre SQLite en memoria y
sobre DDL ajeno transcrito. La compañera del Módulo 4 montó una MySQL en Aiven
(`defaultdb`, 1 GB gratuito) para que todos los módulos apunten al mismo sitio,
y esta es la primera vez que el módulo se ejecuta contra ella.

### Lo que había allí

MySQL 8.4.8, 22 tablas, esquema montado y sin estrenar (0 casos, 0 eventos).
Tres cosas que confirman decisiones tomadas a ciegas:

* **`cases` es la del Módulo 1**, no la incompatible del Módulo 2. El que era
  el bloqueo más grave de la lista no se ha materializado.
* **`tracking_events` coincide** con el DDL transcrito de la rama `track-inc`,
  y **no tiene `detalles`**. La retirada de esa columna, hecha esa misma mañana
  contra su código, queda confirmada contra la base real.
* `evidences`, `timeline_events` y `reports` correctas, con sus FK e índices.

### Fallo 1, propio: faltaba aplicar `m5_0005`

`reports` estaba en la forma de `m5_0004` (con `notas` y `huellas`, sin
`opciones`), así que leer la tabla daba «Unknown column `reports.opciones`».

Detrás había algo peor: la **única** tabla de versiones de Alembic era
`alembic_version_scamshield`. Las tablas se habían creado a mano o con
`create_all`, sin registrar ninguna migración, de modo que un `alembic upgrade
head` habría intentado crear `reports` desde cero y habría fallado.

Resuelto sellando el historial (`stamp m5_0004`) y aplicando la migración que
faltaba. A partir de ahora las migraciones de este módulo se aplican solas.
Además, `alembic/env.py` adopta dos defensas que el Módulo 2 ya tenía y que en
una base compartida no son opcionales:

* **Tabla de versiones propia** (`alembic_version_sharingan`), para no pisarse
  con el Alembic de otro módulo apuntando a la misma base.
* **`include_name` limitado a las tablas que este módulo posee.** Hoy `env.py`
  importa solo el modelo de `reports`, así que `Base.metadata` no contiene las
  demás — pero eso depende de que nadie añada un import transitivo del espejo.
  Si alguien lo hiciera, un `--autogenerate` contra la base compartida
  propondría **modificar las tablas de otros módulos** para que se parecieran
  al espejo: convertir `tracking_events.id` en VARCHAR, crear `osint_results`,
  quitar claves ajenas. Migraciones destructivas sobre datos ajenos. Ahora la
  lista de lo que Alembic puede tocar desde aquí es explícita.

### Fallo 2, y era peor de lo documentado: `osint_results` no existe

Estaba anotado como «el Anexo B saldría vacío». Es falso: `repository`
consultaba esa tabla **sin condiciones** al componer cualquier informe, así que
en cuanto el Módulo 1 cree un caso y el Módulo 4 le ponga cronología, *toda*
generación devolvería un 500. Ni siquiera excluir el Anexo B con las opciones de
alcance servía de escape, porque la consulta ocurre antes de aplicar el filtro.

Y el arreglo fácil —tolerar la tabla ausente y seguir imprimiendo «No constan
consultas OSINT registradas para este caso»— habría sido **falso**: sí constan,
hay análisis reales en `osint_findings`. Es el mismo criterio por el que un
anexo excluido a petición del perito no imprime «no constan».

Así que el Anexo B distingue ahora tres situaciones (`app/modules/reports/osint.py`):

| Situación | Qué hace el informe |
|---|---|
| `osint_results` existe | La fuente oficial. Igual que siempre |
| No existe, pero sí `osint_findings` | Lee la capa de lectura del Módulo 2 y **declara** que lo hace |
| Ninguna de las dos | Dice que el registro OSINT no está disponible, no que no hubo consultas |

Detalles que importan:

* **Se comprueba que la tabla exista antes de consultarla**, en vez de
  intentarlo y recoger el error. El mensaje varía según el motor, y sobre todo
  un `SELECT` fallido deja la transacción inutilizable: recogerlo obligaría a
  un `rollback` a mitad de componer el informe.
* **Nunca se leen las dos a la vez.** Mezclar dos registros con vocabularios
  distintos daría un anexo que no se puede leer sin saber de dónde viene cada
  fila.
* **Las equivalencias no son exactas y el anexo lo dice.** «Reputación» pasa a
  ser `risk_level` con su puntuación —la clasificación del Módulo 2, no el
  veredicto de VirusTotal—, «Det.» pasa a ser `flag_count`, y el país no consta
  porque `osint_findings` no lo publica. Quien lea el informe no puede acabar
  creyendo que «high (72)» es lo que dijo una fuente externa.
* **`osint_findings.case_id` va hoy a NULL**, así que este respaldo no
  devolverá nada hasta que el Módulo 2 lo rellene. Que esté escrito es lo que
  permite que funcione ese día sin volver a tocar este módulo.

### Comprobado ejecutando, no razonando

* Las cinco lecturas que hace el módulo al componer un informe, contra la base
  real: todas en verde.
* **Informe completo de extremo a extremo contra la MySQL compartida**: caso,
  evidencia y dos eventos de tracking escritos con SQL crudo (como lo haría
  cada módulo), cronología proyectada como la escribe el Módulo 4, y los cuatro
  formatos compuestos. La evidencia llega al Anexo A, el evento crítico al
  Anexo C, la severidad se lee del ENUM nativo de MySQL y la columna «Ref.»
  apunta al `tracking_events.id` real. Todo dentro de una transacción deshecha
  al final: **no queda ni una fila** en la base del equipo, comprobado después.
* 8 tests nuevos (`tests/test_anexo_b_fuentes.py`), incluido el que fija que el
  informe no afirme que no hubo consultas cuando lo que pasa es que no puede
  saberlo. Suite en 166/166.

### Verificación de las tablas del Módulo 1, a petición suya

El compañero del Módulo 1 pidió que le probáramos su esquema en la base
compartida. Comprobado escribiendo con SQL crudo —como lo haría su módulo— y
leyendo con este, todo en una transacción deshecha al final:

* **Tiene exactamente dos tablas**, `cases` y `evidences`. Ninguna otra, ninguna
  renombrada, ningún sitio alternativo del que salgan los resultados. Coinciden
  columna a columna con su `backend/app/modules/cases/models.py`. **Nada a lo
  que este módulo tenga que adaptarse.**
* **Los cuatro valores del ENUM `estado`** se escriben y se leen bien. Era el
  punto crítico: es exactamente donde el espejo y su tabla divergieron en
  agosto, y aquel desajuste habría impedido generar cualquier informe.
* **Los valores por defecto los pone la base**: sin `estado` sale `abierto`, y
  `fecha_creacion` se rellena sola. El espejo los lee sin problema aunque no
  los declare.
* Una evidencia suya **llega al Anexo A**.
* El **borrado en cascada de `evidences` funciona**: borrar un caso no deja
  evidencias huérfanas.

Y salió el fallo que este documento venía anticipando desde el 29/08, ahora ya
reproducido: **borrar un caso que tenga informes devuelve un 500**. Ver
"Confirmado en la base compartida: borrar un caso con informes falla".

### Lo que queda pendiente y no es de este módulo

* Que el equipo decida si `osint_results` se implanta o si `osint_findings` es
  el contrato definitivo. Este módulo funciona con las dos y no fuerza la mano.
* Que el Módulo 2 rellene `osint_findings.case_id`. Sin eso, ningún hallazgo
  puede atribuirse a un caso y el Anexo B sale vacío igualmente.
* Que los demás módulos registren sus migraciones. Hoy solo el Módulo 2 y este
  tienen historial de Alembic en la base compartida; el esquema de los Módulos
  1, 3 y 4 está allí sin que Alembic sepa cómo llegó.
* Que el Módulo 1 devuelva `409` al borrar un caso con informes, en vez del
  `500` que da hoy. Comunicado el 02/09.
* La conexión va por TLS, pero **sin verificar el certificado del servidor**
  (nadie configura `ssl_ca`). Para lo que hay hoy es asumible; antes de meter
  datos reales de un peritaje, no.

---

## Contraste con los Módulos 3 y 4 reales (ramas `track-inc` y `T1m3-l1n3`)

Hecho el 2026-09-02, en cuanto aparecieron sus ramas. Hasta aquí el contrato
con estos dos módulos era la mejor estimación contra el `CLAUDE.md` más una
propuesta por escrito del Módulo 3. Ya hay código con el que contrastarlo, y
como pasó con el Módulo 1, coincidir en los nombres de columna no bastaba.

### Corregido: el espejo declaraba una columna que no existe

`tracking_events.detalles` (JSON) la propuso el Módulo 3 en agosto para no
perder el detalle crudo del evento —uid, gid, puertos, salidas de herramienta—,
y este módulo la aceptó siguiendo el criterio de ser permisivo al leer. **Su
tabla real no la tiene.**

Y esto no era una tolerancia de más, era un fallo garantizado. Ser permisivo
sirve para el *contenido* de una columna: una tilde en `severidad`, un id de
texto donde se esperaba un entero. No sirve para su *existencia*: un `SELECT`
pide todas las columnas declaradas, y MySQL responde «Unknown column» a la que
no está. Al integrar, ningún informe de ningún caso con eventos de tracking se
habría generado. Que la columna fuese nullable no cambiaba nada: nullable dice
qué puede ir dentro de una columna que existe, no si existe.

Retirada del espejo, del Anexo C (que citaba el detalle crudo como almacenado),
de `load_fixtures.py` y de la fixture `caso_005`. La propuesta queda anotada
aquí por si el Módulo 3 decide crearla: su agente sí captura ese detalle
—`RawEvent.payload`, en `track-inc/agent/evidence/models.py`— y lo descarta al
proyectar a `tracking_events`. Si la añade, esto se revierte y el anexo vuelve
a citarla.

### Lo que sí encaja, comprobado ejecutando

`tests/test_esquema_modulo3.py` (12 tests) monta `tracking_events` con el DDL
transcrito de su migración `6b5d49c8a514` y ejecuta el módulo encima. Mismo
papel que `test_esquema_modulo1.py`: lo que se prueba es el esquema del
**dueño** de la tabla, no el espejo.

* **`severidad` se lee bien.** El Módulo 3 usa `values_callable`, así que
  guarda `alta` y no `ALTA`. Es exactamente lo que falló con el `estado` del
  Módulo 1, y aquí no pasa.
* **`id` es INTEGER**, no los `evt-7f3a9c2e` que se propusieron. `IdAjeno`
  admite las dos cosas y normaliza a texto, así que no hay nada que cambiar:
  un entero cabe en un texto.
* **El resto de columnas coincide** con la especificación al pie de la letra.
* **`origen_modulo = 'tracking'`**: el script del Módulo 4 escribe el nombre de
  la tabla, no el nombre en clave del módulo. La decisión de `52c50d8` se
  sostiene contra su código real, y con ella la promesa de que la columna
  «Ref.» resuelve.
* **`origen_id`** lleva el entero de `tracking_events.id`, y **`orden`** va de
  1 a N por caso.

La alarma de deriva se comprobó *provocándola*: reintroduciendo `detalles` en
el espejo caen 10 de los 12 tests, y no solo el que la vigila — caen todas las
lecturas, que es el fallo que habría dado en producción.

### Novedad buena: los ids de Alembic ya no chocan con nadie

La migración del Módulo 3 es `6b5d49c8a514` con `down_revision = "0001"`, es
decir, **ya cuelga de la del Módulo 1**. No hay colisión con las `m5_000N` de
este módulo. Al fusionar, `m5_0001` colgará también de `0001`, lo que deja dos
ramas hermanas bajo la misma raíz; Alembic lo admite, pero necesitará una
revisión de merge para tener una sola cabeza. Es un paso mecánico y conocido,
no un bloqueo.

### Pendiente de hablar con el equipo: el Módulo 4 solo proyecta tracking

Su script recorre `tracking_events` y escribe una entrada de cronología por
cada uno. **Nada más.** Ni `evidences` ni `osint_results` llegan nunca a
`timeline_events`, pese a que el mensaje de su commit dice «3 fuentes».

Consecuencia para el informe: los Anexos A y B no tendrían ninguna entrada de
cronología que los respalde. No es que salgan vacíos —el Anexo A sí listaría
las evidencias del caso—, es que ningún hecho narrado apuntaría a ellos. El
informe queda reducido a lo que el Módulo 3 detectó.

No se arregla desde aquí, y el módulo no se cae por ello:
`test_los_anexos_a_y_b_quedan_vacios_con_la_proyeccion_actual_del_modulo_4` lo
deja fijado. Si el Módulo 4 amplía su script, ese test se caerá — y será una
buena noticia que habrá que venir a recoger.

### Y un aviso que darle al Módulo 4

El código de su rama está **en el commit anterior al último**. El último
(`7c63a51`, «feat: modulo 4 script timeline unificado con .env y 3 fuentes»)
borró 100 líneas y dejó `update_timeline.py` con un solo comentario:
`# (pega el contenido del script mejorado que te di antes...)`.
Parece un descuido al pegar, no una decisión. Conviene avisar antes de que
alguien clone esa rama y crea que el módulo no existe.

---

## Contraste con el Módulo 1 real (rama `modulo-casos`)

Hasta ahora `app/modules/shared/models.py` era una estimación contra el
`CLAUDE.md`. Ya existe código real con el que contrastarlo: la rama
`modulo-casos` trae `backend/app/modules/cases/` (modelos `Case` y `Evidence`,
migración `0001_initial_cases_evidences`, CRUD completo) y además un frontend
React propio del módulo.

### Corregido: `estado` y `severidad` se leían mal

El Módulo 1 declara `cases.estado` con `values_callable`, así que en base de
datos guarda el **valor** del Enum (`abierto`), igual que la especificación.
El espejo de Módulo 5 usaba `Enum(EstadoCaso)` a secas, y por defecto SQLAlchemy
guarda y busca por **nombre de miembro** (`ABIERTO`). Leer un caso creado por el
Módulo 1 lanzaba:

```
LookupError: 'abierto' is not among the defined enum values.
Possible values: ABIERTO, EN_PROGRESO, CERRADO, ARCHIVADO
```

Es decir, en cuanto se integrasen los módulos **ningún informe se habría podido
generar**. Corregido en `shared/models.py` (`values_callable=_por_valor`, en
`EstadoCaso` y también en `Severidad`, que tenía el mismo defecto de cara al
Módulo 3). `tests/test_shared_models.py` cubre la regresión insertando filas con
SQL crudo — crearlas con el propio ORM usaría la misma convención al escribir y
al leer, y no detectaría el desajuste.

### Pendiente de hablar con el equipo: colisión de migraciones

Las dos ramas tienen una migración con **el mismo identificador `0001` y
`down_revision = None`**:

| Rama | Fichero | revision |
|---|---|---|
| `modulo-casos` | `0001_initial_cases_evidences.py` | `0001` |
| `sharingan` | `0001_create_reports_table.py` | `0001` |

Alembic no puede resolver dos raíces con el mismo id en un único historial, así
que al fusionar en `main` hay que renumerar una de las dos cadenas (o usar
`branch_labels` y un merge revision). Lo lógico es que la del Módulo 1 quede
primero y la de Módulo 5 cuelgue de ella, porque `reports.case_id` es FK real a
`cases.id` y MySQL exige que `cases` exista antes.

### Confirmado en la base compartida: borrar un caso con informes falla

**Ya no es una predicción.** Comprobado el 2026-09-02 contra la MySQL del
equipo: con un caso que tiene una evidencia y un informe, el `DELETE` sobre
`cases` lo rechaza el motor.

```
(1451, 'Cannot delete or update a parent row: a foreign key constraint fails
       ("defaultdb"."reports", CONSTRAINT "fk_reports_case_id" ...)')
```

El Módulo 1 expone `DELETE /cases/{case_id}` y sus `evidences` tienen
`ondelete="CASCADE"`, así que esas se van solas. `reports.case_id` **no** lo
tiene —y es deliberado—, de modo que la excepción sube sin capturar y el
Módulo 1 devuelve un **500**.

Conviene separar dos cosas que se confunden. Que la base se plante **es el
comportamiento correcto**: es lo único que hoy impide que borrar un caso desde
el frontend haga desaparecer un informe pericial ya entregado, con su código,
su huella y su PDF. Lo que está mal es la *forma* de contarlo: un 500 dice «me
he roto» cuando lo que ha pasado es «no puedo, y por un buen motivo».

Hay tres salidas y es decisión de equipo, no de este módulo:

1. Cascada también en `reports` — simple, pero destruye informes ya emitidos.
2. Impedir borrar un caso que tenga informes (409 desde el Módulo 1).
3. Borrado lógico — pero "cadena de custodia avanzada / soft-delete" está
   explícitamente fuera de alcance en el `CLAUDE.md`.

Preferible la 2: un informe pericial emitido no debería desaparecer porque
alguien borre el caso. Basta con que el Módulo 1 consulte `reports` antes de
borrar y, si hay filas, responda `409` con el número de informes emitidos en
lugar de intentar el `DELETE`. Nada que cambiar en el esquema ni en este
módulo.

---

## Alcance de la emisión

Hecho el 2026-08-31. Hasta ahora un informe documentaba el caso entero, sin
excepción. El perito no siempre quiere eso: un encargo puede cubrir solo un
día concreto, o solo los eventos graves, o no cubrir el rastreo OSINT. Antes,
eso obligaba a emitir el informe completo y recortarlo a mano fuera del
sistema — que es exactamente donde una copia deja de poder contrastarse contra
su original.

`POST /reports/generate` acepta ahora un objeto `opciones` (anexos, formatos,
`desde`/`hasta`, `severidad_minima`, `solo_osint_con_detecciones`). Omitirlo
reproduce **exactamente** lo de antes: los tres anexos, la cronología entera,
los cuatro formatos y ningún párrafo añadido. Eso era el requisito de partida —
la personalización no debía cambiar lo que ya se emitía — y es lo que dejan
comprobado los tests de los formatos, que siguen pasando sin tocar un assert.

### Las dos reglas de las que sale todo lo demás

1. **Nada se omite en silencio.** Si la emisión deja algo fuera, el propio
   documento lo declara en su apartado 1, nombrando uno a uno los anexos
   excluidos. El párrafo lo redacta el código (`descripcion_alcance`), no la
   IA: es un hecho sobre la emisión, no narrativa, y no puede quedar a
   criterio del modelo. Un informe recortado que no declara su recorte engaña
   sobre su propio alcance, y eso lo lee un juez.

2. **La columna «Ref.» siempre resuelve.** La metodología del informe promete
   que cualquier afirmación se puede contrastar contra el registro del que
   procede. Por eso un filtro nunca puede dejar en la cronología una entrada
   que apunte a una fila que el informe no imprime: al descartar una fila se
   descartan también las entradas que la referencian, y después cada anexo se
   reduce a lo que la cronología resultante cita. El invariante se cumple por
   construcción, no por vigilancia, y lo verifica el test que ya existía
   (`test_cada_referencia_de_la_cronologia_resuelve_en_los_anexos`).

### Decisiones

* **El recorte se aplica antes de llamar a la IA**, no al imprimir. El prompt
  numera los eventos `[E1]`, `[E2]`… y el sistema valida que la narrativa no
  cite ninguno inexistente. Si el modelo redactase sobre la cronología entera
  y el documento imprimiese una recortada, el informe hablaría de hechos que
  sus propias tablas no recogen — y esa validación, que es la defensa contra
  la alucinación, daría por buenas las referencias a lo que no se imprimió.

* **Un anexo excluido no deja rastro en su sitio**: ni título ni «no constan
  registros». Decir «no constan» de algo que sí consta y no se ha impreso
  sería falso. Que falta se dice una sola vez y donde corresponde: la
  declaración de alcance. Los títulos salen del mismo diccionario
  (`NOMBRE_ANEXO`) que esa declaración, para que el lector no tenga que
  adivinar a qué anexo se refiere lo que se le dice que falta.

* **Dos límites no negociables, rechazados con `422` al validar el cuerpo** y
  no a mitad de generar: sin ningún anexo no queda nada que respalde la
  cronología (mismo motivo por el que un caso sin `timeline_events` da 422), y
  sin PDF se emitirían copias sin original, porque el PDF es el documento que
  se firma y al que las demás se refieren. Una franja invertida tampoco pasa.

* **`EmptySelectionError` es distinto de `EmptyTimelineError`.** Los dos son
  `422`, pero no son el mismo problema: en el segundo falta el Módulo 4 y el
  perito no puede hacer nada; en el primero el arreglo está en su propia
  petición, y el mensaje dice qué aflojar.

* **Columna `opciones` en `reports`** (migración `m5_0005`, JSON, nullable).
  Cuarta columna que este módulo añade sobre el modelo de datos oficial,
  después de `notas` y `huellas`, y como ellas pendiente de refrendo del
  equipo. El motivo es el mismo que el de `notas`: sin ella el informe no es
  reproducible. Dos informes del mismo caso pueden diferir sin que nada haya
  cambiado en los datos, y lo único que lo explica es esta columna. El
  documento declara su alcance en prosa y solo cuando hay recorte; aquí queda
  en un formato comparable entre versiones. Es además lo que distingue «este
  formato no se pidió» de «este informe es anterior a los cuatro formatos»,
  que la API responde distinto. Nullable: los informes anteriores se emitieron
  sin opciones, que equivale a las de por defecto.

* **`FormatoInforme` se ha mudado de `formats.py` a `opciones.py`**, porque
  desde que se puede elegir es vocabulario de una opción. `formats.py` lo
  reexporta, así que quien lo importaba de allí lo sigue encontrando.

* **Una referencia colgante se conserva.** Si una entrada de cronología apunta
  a un `origen_id` que no existe en el caso —dato inconsistente de otro
  módulo—, el filtro la deja pasar, que es lo que ya hacía antes. Recortar es
  cosa de las opciones, no la ocasión de empezar a descartar datos ajenos por
  nuestra cuenta.

* **Las fechas se comparan como UTC ingenuo.** Las del almacén llegan sin zona
  (MySQL `DATETIME`) y las de la API pueden traerla; compararlas entre sí
  reventaría. Es lo que el resto del módulo ya asume al imprimir «(UTC)».

### En el frontend

`ReportScopeFields.tsx` y `reportScope.ts`, dentro del formulario de
generación, más el alcance mostrado en el panel de detalle. `tsc -b` limpio
sobre el árbol combinado.

### Tests (`tests/test_opciones_informe.py`)

30 tests. Cubren los filtros uno a uno, la propagación del recorte a los
anexos, el invariante de «Ref.», el texto de la declaración de alcance, los
tres alcances imposibles, la distinción entre los dos `422`, lo que se guarda
en `reports.opciones` y —el que más importa— que sin opciones el informe sale
idéntico al de antes.

---

## Exportación en varios formatos

Cada generación emite el mismo informe en cuatro soportes: **PDF** (el que se
firma y el que registra `reports.archivo_pdf`), **DOCX** (para que el
destinatario lo cite o lo incorpore a un escrito), **HTML** (revisión en
pantalla e impresión desde el navegador) y **JSON** (archivo consultable, diff
entre versiones de un caso, consumo por otras herramientas).

### Decisiones

* **Un solo sitio donde vive el contenido.** Añadir tres formatos copiando la
  estructura del PDF habría dejado la norma UNE escrita cuatro veces, y con
  ella la garantía de que antes o después el PDF y el DOCX dijeran cosas
  distintas bajo el mismo código de informe. `document.py` modela el informe
  como bloques (`Titulo`, `Parrafo`, `Tabla`, `Espacio`, `SaltoPagina`) y cada
  `*_builder.py` solo traduce bloques a su formato. Añadir un formato es
  escribir un renderizador y registrarlo en `formats.py`.

* **Los cuatro se emiten a la vez, no bajo demanda.** Componer el DOCX al
  descargarlo leería la base de datos tal y como esté *ese* día: un caso al que
  se le han añadido eventos entretanto produciría un documento distinto bajo el
  mismo código. Emitiéndolos juntos comparten contenido, código y sello de
  tiempo, y pueden contrastarse entre sí. Hay un test dedicado a eso.

* **Un informe antiguo no se rerenderiza.** Los emitidos antes de esta función
  solo tienen PDF; pedirles otro formato devuelve `410` con la explicación, y
  la salida es generar una versión nueva. Fabricar hoy un documento y
  presentarlo como si se hubiera emitido entonces es justo lo que un informe
  pericial no puede permitirse.

* **Sin columnas nuevas.** El modelo de datos oficial solo contempla
  `archivo_pdf`. Las demás copias son ese mismo fichero con otra extensión y la
  ruta se deriva, así que no hay migración ni segunda desviación del esquema.

* **Paginación del DOCX con campos de Word** (`PAGE`/`NUMPAGES`) en vez de
  números fijos: Word los recalcula al repaginar, que es lo que ocurre en
  cuanto alguien edita el documento. Un número escrito a mano mentiría.

* **HTML autónomo**: estilos incrustados, sin recursos externos, para que siga
  leyéndose igual dentro de años en una máquina sin red. Las tablas anchas (el
  Anexo B tiene ocho columnas) hacen scroll propio en pantalla y se sueltan al
  imprimir.

### En el frontend

El panel de detalle mantiene «Descargar PDF» como acción principal y añade
debajo tres botones secundarios (DOCX, HTML, JSON) bajo el rótulo «mismo
informe en otro soporte». No se presentan en igualdad a propósito: el PDF es
el documento firmado, y sugerir que da lo mismo cuál se aporta sería falso.

### Verificado contra un backend en marcha

Se levantó el módulo con la fixture `caso_003_fraude_bec` y se comprobó de
punta a punta desde la interfaz. Los cuatro formatos se descargan con su
`media_type` y su nombre de fichero, un formato inexistente da `422`, y los
ficheros que recibe el navegador coinciden byte a byte con los de disco. El
HTML se revisó renderizado: portada, cronología y los tres anexos correctos,
incluida la tabla de ocho columnas del Anexo B, que era la duda.

Dos cosas se corrigieron ahí, que ningún test habría detectado:

* **El HTML se servía como `attachment`.** El navegador lo descargaba en vez de
  mostrarlo, que es justo lo que ese formato venía a evitar. Ahora se sirve
  `inline` (seguro: todo el texto pasa por `html.escape`, con test propio, y el
  documento no incrusta scripts). Los otros tres siguen como `attachment`.
* **Al pulsar HTML se perdía la aplicación.** Servido en línea,
  `window.location.assign` reemplazaba la pantalla por el informe. Ahora ese
  botón abre otra pestaña; los demás no cambian de página.

También se arregló que `scripts/load_fixtures.py` y `seed_dev_db.py` no
arrancaban tal y como los documenta el README: Python pone en `sys.path` el
directorio del script, no el actual, así que `import app` fallaba.

### El DOCX, abierto en Word

**Comprobado el 2026-08-30, sin incidencias.** Hasta entonces el DOCX solo se
había verificado releyéndolo con `python-docx` —secciones, cronología, campos
del pie—, que confirma que el fichero dice lo que debe pero no que Word lo
interprete bien.

Importaba sobre todo por el pie: no lleva números escritos, lleva los campos
`PAGE` y `NUMPAGES` sin valor cacheado, para que la paginación se recalcule si
el destinatario edita el documento. Que eso rinda un «Página 3 de 5» de verdad
solo lo dice Word.

Se revisó sobre `fixtures/caso_004_exfiltracion_interna.json`, que es la que
más estresa el formato: 8 eventos, 4 evidencias, las cuatro severidades y
`<`, `>` y `&` metidos a propósito en el texto para que un doble escapado o un
XML roto salten a la vista.

Reproducible con:

```bash
python scripts/previsualizar_informe.py fixtures/caso_004_exfiltracion_interna.json
# -> storage/previsualizacion/caso_004_exfiltracion_interna.docx
```

### Sin verificar

Queda el responsive del frontend por debajo de `md`.

---

## Contraste con el Módulo 2 real (rama `scam-shield`)

La rama `scam-shield` se reescribió el 2026-08-15 ("Adapta scam-shield al
frontend y al esquema de módulos de Nexus"): pasó a `app/modules/osint/…`,
adoptó MySQL y añadió Alembic. Contrastado su código con lo que este módulo
espera del Módulo 2, salen cuatro cosas.

### La tabla `osint_results` no existe

El Módulo 2 **no** implementa la tabla `osint_results` del `CLAUDE.md`. Su
migración `6af9a574a7a5_esquema_inicial_osint` crea una tabla por tipo de
análisis: `ip_cases`, `email_cases`, `wallet_cases`, `phone_cases`,
`image_cases`, `facial_search_cases`, `reverse_image_search_cases`,
`osint_domain_cases`, `typosquatting_cases`, `cnmv_check_cases`,
`cnmv_warnings`, `monitored_subjects`, `risk_alerts`, `integrity_ledger`,
`ofac_sanctioned_addresses`.

Consecuencia directa: el **Anexo B saldría vacío en todos los informes**
("No constan consultas OSINT registradas para este caso"), porque nadie
escribe nunca en `osint_results`. No es un fallo del Módulo 5 y no rompe nada
— los anexos ya degradan de forma limpia cuando no hay filas — pero un informe
pericial sin los indicadores objetivos consultados pierde buena parte de su
respaldo probatorio.

Salidas posibles, y es decisión de equipo:

1. Que el Módulo 2 escriba además una fila en `osint_results` por cada
   consulta (proyección al modelo común). Es lo que dice la especificación y
   lo que menos toca al resto de módulos.
2. Que el Módulo 4 haga esa proyección al correlacionar.
3. Que el Módulo 5 lea las 15 tablas del Módulo 2 — descartable: acopla los
   dos módulos y rompe el "bajo acoplamiento" del `CLAUDE.md`.

Preferible la 1.

### `case_id` ni siquiera está en sus tablas de análisis

**Corregido el 2026-08-29** tras leer el código descargado (commit `4514a17`).
Lo que decía antes esta sección —`case_id` como `Integer` nullable y sin
`ForeignKey`— ya no es cierto: en las tablas de análisis del Módulo 2 **no hay
ninguna columna `case_id`**. El único `case_id` de su esquema es el de
`integrity_ledger`, y apunta a sus propios casos de análisis, no a `cases.id`
del Módulo 1.

O sea que hoy no existe ningún camino, ni siquiera por convención, entre un
análisis OSINT y el caso pericial al que pertenece.

### Dos tablas `cases` incompatibles

**Detectado el 2026-08-29.** Es el bloqueo más grave de la lista, y no estaba
registrado. El Módulo 2 declara en `app/models/case.py`:

```python
class Case(Base):
    __tablename__ = "cases"
    domain, risk_score, whois, ssl, virustotal, resolved_ip,
    abuseipdb, dns, ip_reputations, crtsh, wayback, risk_flags, errors
```

Eso no es un caso pericial: es el resultado de un análisis de dominio. Y ocupa
el nombre de la tabla central del proyecto, la que el `CLAUDE.md` define con
`nombre`, `estado`, `fecha_creacion`, `descripcion` y `responsable`, y de la
que cuelgan por `case_id` los otros cuatro módulos.

Contra una sola base de datos las dos definiciones no pueden coexistir. Y
afecta directamente a este módulo: `reports.case_id` es FK a `cases.id`, así
que si la `cases` que gana es la del Módulo 2, ningún informe puede
registrarse. No se arregla desde aquí: o el Módulo 2 renombra su tabla (a
`domain_analyses`, por ejemplo), o el proyecto se queda sin su entidad
principal.

### No comparte ni el motor de base de datos

**Corregido el 2026-08-29.** Antes esta sección decía que los tres módulos
apuntaban a tres esquemas MySQL distintos (`nexus`, `scamshield`,
`nexus_informes`). Falso en el caso del Módulo 2:

| Módulo | Motor | Cómo crea las tablas |
|---|---|---|
| 1 (`modulo-casos`) | MySQL, esquema `nexus` | Alembic (`0001`) |
| 2 (`scam-shield`) | **SQLite** (`sqlite:///./scamshield.db`), con **PostgreSQL** previsto en el docstring de su `database.py` | `Base.metadata.create_all()` |
| 5 (`sharingan`) | MySQL, esquema `nexus_informes` | Alembic (`m5_0001`…`m5_0004`) |

No es una diferencia de configuración: sus columnas son `String` sin longitud,
que en MySQL no es DDL válido para un `VARCHAR`. Migrarlos a MySQL no es
cambiar la URL, hay que revisar sus 15 modelos.

### Colisión de ruta: `POST /reports/generate`

El Módulo 2 declara en `app/api/routes/report.py` un
`APIRouter(prefix="/reports")` con `POST /generate`: exactamente la misma ruta
que este módulo. Montadas las dos en una sola app FastAPI, se queda con la
primera registrada **sin avisar**, y las peticiones acabarían en el generador
que no toca.

Esto sí tiene salida sin tocar código de nadie: quien monte la aplicación
puede remontar cualquiera de los dos con
`app.include_router(router, prefix="/loquesea")`. Pero hay que decidirlo, no
descubrirlo en marcha.

### Y ninguna raíz de Alembic

**Corregido el 2026-08-29.** Antes se decía aquí que el Módulo 2 aportaba una
tercera raíz, `6af9a574a7a5`. Ya no: **ha dejado de usar Alembic**. Crea las
tablas con `Base.metadata.create_all(bind=engine)` en `app/main.py`.

Así que las raíces son dos, no tres, y el problema cambia de forma: no es
encadenar tres cadenas, es que el Módulo 2 no tiene historial de esquema que
encadenar. La colisión que quedaba —`0001` del Módulo 1 contra `0001` de este
módulo— **está resuelta desde el lado de este módulo**: ver "Compatibilidad
con las otras ramas".

---

## Fuera de alcance por decisión explícita

Del `CLAUDE.md` del proyecto: sistema de usuarios y autenticación, permisos y
roles, cadena de custodia avanzada, hashes de integridad de evidencia. **No
implementar sin instrucción explícita.**

Añadido en esta sesión: identificación ampliada del perito (titulación,
colegiación, organización, destinatario). Se descartó por ahora porque cada
campo sería una columna nueva en `reports` y el modelo de datos oficial no los
contempla; el bloque de firma actual usa `generado_por`. Retomar si el equipo
decide ampliar el esquema.

---

## Frontend del Módulo 5 — hecho

Ya existe un frontend común de NEXUS (React 19 + Tailwind v4, rama
`modulo-casos`), con su sistema de diseño documentado en `DESIGN_SYSTEM.md` y
`FRONTEND_MODULE_GUIDE.md`. Sobre él se ha construido la pantalla de informes.

* **Qué se ha subido**: solo `frontend/src/modules/reports/` — la aportación de
  este módulo. El resto del frontend es de `modulo-casos` y no se duplica ni se
  toca desde esta rama.
* **Los dos cambios de integración** (una línea en `app/router.tsx` y la
  variable `VITE_REPORTS_API_BASE_URL` en `.env.example`) están **documentados,
  no commiteados**, en `frontend/src/modules/reports/README.md`, para no pisar
  ficheros de otra rama.
* **Comprobado**: `tsc -b`, `npm run build` y `oxlint` limpios, y la pantalla
  ejecutada contra el backend real con una base de datos sembrada (listado,
  detalle, descarga y modal) sin errores de consola. Sin verificar: el
  responsive real por debajo de `md`, y la generación contra Anthropic (gasta
  crédito real).
* **Dos URLs base**: mientras Módulo 1 y Módulo 5 sean dos apps FastAPI
  distintas no pueden compartir puerto. Al fusionarlos se borra
  `VITE_REPORTS_API_BASE_URL` y todo cae en `VITE_API_BASE_URL`.

---

## Pendiente

### A hablar con el equipo (nada de esto se arregla desde este módulo)

1. **`osint_results` no la crea nadie** — confirmado el 02/09 contra la base
   compartida, donde tampoco está. Ya **no tumba el informe**: el Anexo B lee
   `osint_findings` como respaldo y declara de dónde viene (ver "Contra la base
   compartida del equipo"). Lo que sigue siendo decisión de equipo es cuál de
   las dos es el contrato definitivo, y que el Módulo 2 rellene
   `osint_findings.case_id`, hoy siempre NULL.
2. ~~**Una sola base de datos.**~~ **Resuelto por el equipo**: hay una MySQL
   compartida en Aiven (`defaultdb`), con el esquema de los Módulos 1, 3, 4 y 5
   ya montado y la `cases` correcta —la del Módulo 1—. Este módulo se ha
   ejecutado contra ella de extremo a extremo. Queda que los demás registren
   sus migraciones: hoy el esquema está allí sin que Alembic sepa cómo llegó.
3. **Dos `POST /reports/generate`** (este módulo y el Módulo 2). Retirar uno o
   separar prefijos antes de fusionar.
4. **Borrar un caso con informes**: `evidences` cascadea, `reports` no.
   **Reproducido el 02/09 contra la base compartida** (MySQL 1451 → 500 en el
   Módulo 1). Que la base lo impida es lo correcto y no se toca; lo que falta
   es que el Módulo 1 lo detecte antes y devuelva un `409` con el número de
   informes emitidos. Comunicado. Detalle en "Contraste con el Módulo 1 real".
5. ~~**Historial de Alembic**: tres raíces independientes.~~ **Revisado el
   2026-08-29.** Son dos, no tres: el Módulo 2 ha dejado de usar Alembic. Y la
   colisión de id (`0001` contra `0001`) **ya está resuelta desde este
   módulo**: sus revisiones son ahora `m5_0001`…`m5_0004`. Queda solo el paso
   de fusión, una línea: encadenar `m5_0001` a la `0001` del Módulo 1, porque
   `reports.case_id` es FK real a `cases.id` y MySQL exige que `cases` exista
   antes. Instrucciones en la cabecera del propio fichero de migración.
6. **Dos tablas `cases` incompatibles** (Módulo 1 y Módulo 2). El bloqueo más
   grave y el más reciente. Sin una `cases` única no hay proyecto: es la
   entidad de la que cuelgan los cinco módulos. Detalle en "Contraste con el
   Módulo 2 real".

### Trabajo propio del módulo

7. ~~**Módulos 3 y 4** — siguen sin rama.~~ **Contrastados el 2026-09-02**,
   en cuanto aparecieron `track-inc` y `T1m3-l1n3` — ver "Contraste con los
   Módulos 3 y 4 reales". Volvió a demostrarse que coincidir de nombre en el
   `CLAUDE.md` no garantiza nada: el espejo declaraba una columna que la tabla
   real no tiene. Queda una cosa que **no** se arregla desde aquí: el script
   del Módulo 4 solo proyecta `tracking_events` a la cronología, así que los
   Anexos A y B no tendrían ninguna entrada que los respalde.
8. **Al integrar en `main`**: sustituir `app/modules/shared/models.py` por los
   modelos canónicos de los Módulos 1–4 (mismos nombres de tabla y columnas,
   sin migración de datos).
9. **Queda por mirar a ojo**: solo el responsive del frontend por debajo de
   `md`. El DOCX se abrió en Word el 2026-08-30 sin incidencias (ver "El DOCX,
   abierto en Word"); el resto de la comprobación visual ya estaba hecha (ver
   "Verificado contra un backend en marcha").
10. ~~**Huella de integridad del informe emitido (SHA-256).**~~ **Hecho el
   2026-08-28** — ver "Huella del informe emitido". Queda pendiente de
   refrendo del equipo la columna nueva (`reports.huellas`), como el resto de
   desviaciones del modelo de datos oficial.
11. **Guardar hallazgos y conclusiones por separado.** La IA los devuelve
    estructurados, se aplanan en `resumen_ia` y el frontend los vuelve a
    separar con una expresión regular sobre `HALLAZGOS…CONCLUSIONES`. Dos
    columnas eliminarían el regex y su camino de respaldo. También requiere
    tocar el esquema.
12. ~~**Menores**~~ **Hechos el 2026-08-28**: el prompt exacto se archiva (ver
    "Registro de la generación") y las tablas del PDF parten los valores
    largos por sus separadores (ver "Cortes de línea en las tablas del PDF").
    `scope` en las cabeceras HTML ya estaba hecho desde `ab9d540`; este punto
    lo daba por pendiente por error. Queda una menor de verdad: el HTML usa
    `word-break: break-word`, que parte igual de mal que reportlab; el PDF es
    el documento firmado y es donde importaba.
13. **Mejoras identificadas y no hechas**: bloque de firma con datos colegiales
    del perito (ver "fuera de alcance").
14. ~~**Acotar el alcance de la emisión.**~~ **Hecho el 2026-08-31** — ver
    "Alcance de la emisión". La columna nueva (`reports.opciones`) queda,
    como `notas` y `huellas`, pendiente de refrendo del equipo. Sin hacer,
    y a propósito: el HTML y el DOCX no llevan indicador visual de recorte
    más allá del párrafo del apartado 1, que es donde tiene que estar.

---

## Asistente conversacional (`app/modules/chat/`) — 2026-09-05/10

Módulo nuevo dentro de este backend. **No escribe nada ni añade tablas**: el
historial lo mantiene el navegador. Cinco ficheros:

| Fichero | Qué resuelve |
|---|---|
| `context.py` | Arma el expediente del caso desde las seis tablas, numerado `EV1`/`OS1`/`TR1`/`TL1`/`IN1`. Recorta por colección con topes declarados |
| `conocimiento.py` | Recuperación sobre `docs/` + una ficha fija de NEXUS |
| `llm.py` | Proveedor: Anthropic (por defecto desde el 23/09) u Ollama (local). Streaming y salida con esquema JSON |
| `service.py` | Compone el prompt, valida las citas y arma la respuesta |
| `routes.py` | `POST /chat` y `POST /chat/stream` (SSE) |

### Por qué vive aquí y no como sexto backend

Es exactamente la lectura que ya hace el informe —las seis tablas del
contrato en solo lectura— con el cliente de IA ya configurado. Un proceso
aparte habría duplicado venv, `.env`, puerto y espejo de modelos sin ganar
aislamiento real. Reutiliza `reports/repository.py` para leer.

### Por qué NO es un bucle de agente con herramientas

Se paga dos veces. En seguridad: si el modelo elige el `case_id` o compone la
consulta, el aislamiento entre casos depende de que el modelo se porte bien, y
una instrucción en un prompt no es un control de acceso. En rendimiento: sin
GPU cada turno son decenas de segundos y un modelo de 3B encadena llamadas de
forma poco fiable. El reparto es el del informe: **el servidor recopila, el
modelo redacta**.

Alcance garantizado: no existe consulta que alcance otro caso. **No**
garantizado: *quién* pide qué caso — el proyecto no tiene autenticación. El
día que la haya, el filtro va en `routes.py` y el resto no cambia.

### Fuga entre casos por el historial (encontrada y cerrada)

El historial se reenvía al modelo en cada turno. Preguntando por el caso 8 y
cambiando el desplegable al 1 sin limpiar, el prompt del caso 1 contenía
`203.0.113.45`, `srv-preprod-01` y `auth.log`. Cerrado en los dos lados: la
interfaz mantiene un hilo por caso, y `ChatRequest.historial_case_id` permite
al servidor descartar el historial ajeno y avisarlo. Siete tests en
`tests/test_aislamiento_entre_casos.py`.

### Lecciones del modelo local, medidas

* **Documentación de más empeora la respuesta.** Con cuatro apartados vagamente
  relacionados delante, `qwen2.5:3b` se inventó los cinco módulos de NEXUS
  copiando los títulos de esos apartados; sin ellos los enumeró bien. La
  recuperación se calibró por **cobertura relativa** (lo útil cae en 0,60-0,73;
  el ruido en 0,51-0,58) y con caso seleccionado no se pasa documentación.
* **Los hechos que no se pueden equivocar no dependen de una búsqueda**: la
  ficha de NEXUS va fija en el prompt de sistema.
* **Un modelo pequeño atiende a lo último que lee**: las reglas de brevedad y
  de citación van al final.
* **Un modelo más pequeño no es más rápido de extremo a extremo.**
  `qwen2.5:1.5b` da 2,1× en tokens/s aislados pero tardó 149,6 s frente a 95 s
  (más verboso, agota el tope) y devolvió cero citas.

### Rendimiento

De 185,8 s a 65-95 s en local, y 6-12 s con `claude-opus-5`. Lo que más bajó
fue el prompt de entrada (64,9 s → 0,3 s): menos tokens y, sobre todo, prompt
de sistema estable para que Ollama reutilice su caché de prefijo. Ver el
detalle en `CLAUDE.md`.

## Narrativa del informe con modelo local — 2026-09-05

`NARRATIVA_PROVIDER=ollama` redacta hallazgos y conclusiones sin API de pago.
Se decide **aparte del chat** a propósito: una respuesta de chat floja se
descarta releyéndola, el informe se firma y se entrega.

**Esquema de salida distinto para la ruta local.** Con el mismo esquema que
usa Claude —dos cadenas— el modelo local escribía hallazgos razonables y
**sin una sola referencia**, pese a exigírselo el prompt. La ruta local usa un
esquema donde cada hallazgo es un objeto con su afirmación y la lista de
eventos que la sostienen: así el esquema **obliga** a que las referencias
existan y los corchetes los escribe el código, no el modelo.

**Agujero destapado, y no era del modelo local**: `_validar_citas` comprobaba
que las citas presentes fuesen válidas pero **nunca que hubiera alguna**. Con
Claude no se notaba porque siempre citaba. Una narrativa sin citas se rechaza
ahora **por las dos rutas**.

Aislamiento de los tests: el `conftest` fija `narrativa_provider` y
`chat_provider` a `anthropic`. Sin eso, un `.env` de desarrollo con `ollama`
desviaba tests que mockean Anthropic y **la suite llamaba de verdad al
modelo** — 8 fallos y 20 minutos en vez de 50 segundos.

## Marca de agua del PDF — 2026-09-05

«Expediente XSS» y el lema del grupo, en diagonal y en todas las páginas (una
hoja suelta tiene que poder atribuirse). A 26 pt y 7 % de opacidad: al primer
intento, 46 pt se comían los párrafos del apartado 1 pese al mismo alfa — a
ese tamaño manda la superficie de tinta. Un test impide subir la opacidad:
una marca legible de un vistazo se confunde con un sello «BORRADOR» y
cambiaría lo que el documento dice de sí mismo.

## Integración con la Fase 4 y con el despliegue — 2026-09-23

El trabajo del 05-06/09 (asistente, dashboard, narrativa local, arreglos de
interfaz) se había quedado sin subir mientras `development` avanzaba por otro
lado: Yolanda cerró la **Fase 4, identidad centralizada con JWT** —login, guard
de rutas, perfil, y los cinco backends exigiendo token— y dacaror montó el
**stack de producción** (compose + gateway nginx), ya publicado en
nexus.gondorhub.com. Fusionado en la rama `integracion/asistente-ia`.

Lo que hubo que unir de verdad, más allá de resolver cuatro conflictos:

- **`/chat` y `/chat/stream` pasan a exigir JWT**, con la misma dependencia a
  nivel de router que los cinco endpoints de informes. Es la ruta donde más
  importa: el expediente completo del caso viaja en el prompt, así que un
  `/chat` abierto era una lectura íntegra de cualquier investigación sin
  credenciales. Siete tests en `test_auth_chat.py`, uno de ellos comprobando
  que el 401 de `/chat/stream` llega como código HTTP y no como evento del
  flujo — importa porque es lo que permite al frontend distinguir «sesión
  caducada» de «el modelo falló a mitad».
- **El frontend del chat y del dashboard adjuntan el token.** El dashboard
  trataba cualquier fallo de una fuente como «este bloque no está disponible»
  y seguía pintando el resto; el 401 es la excepción, porque no es una fuente
  caída sino una sesión que ya no vale.
- **El proveedor por defecto pasa a ser Anthropic.** La vía local sigue entera
  y probada (`llm.py::_ollama`, `test_narrativa_local.py`), pero a ~3,5
  tokens/s sin GPU son cinco minutos por pregunta y el equipo no la usa. La
  consecuencia queda dicha en el README de la raíz, en Seguridad: con este
  proveedor el expediente sale hacia un tercero, y `CHAT_PROVIDER=ollama` es
  la salida para un caso que no pueda salir de la máquina.
- **El gateway necesitaba dos cosas para el chat**: `location` propia para
  `/api/reports/chat/stream` sin buffer, y timeouts de 600 s en todo
  `/api/reports/` — el minuto por defecto de nginx corta tanto el streaming
  como la generación de un informe.
- **`JWT_SECRET` no llegaba a los contenedores**, así que el stack publicado
  firma con el `change_me` del código. Se pasa ya desde `deploy/.env` con
  fallback al mismo valor, para arreglarlo sin invalidar las sesiones de nadie
  mientras la variable siga vacía.

Cinco tests nuevos más en `test_citas_del_chat.py`: la retirada de citas
inventadas era la propiedad más vistosa del módulo y no tenía test propio.

### Streaming también con la API, y un rechazo que ya no parece un fallo

Al pasar el motor a Anthropic salieron dos cosas que solo se notan en esa vía:

- **`/chat/stream` no streameaba.** El flujo estaba hecho para Ollama; con
  Anthropic se devolvía la respuesta de una pieza al final, así que la pantalla
  se quedaba en blanco los segundos que tarda la API. Peor: ese camino llamaba
  a `responder()`, que **rearmaba el expediente entero por segunda vez** —las
  consultas de las seis tablas, dos veces por pregunta—. Ahora
  `llm.generar_en_trozos` cubre los dos proveedores con la misma forma
  (`("trozo", str)` … `("salida", Salida)`) y `service.py` no tiene rama por
  proveedor ni prepara el contexto dos veces. De paso, la truncadura del modelo
  local se lee del `done_reason` que manda Ollama en vez de deducirla contando
  trozos contra `num_predict`, que fallaba en cuanto un trozo traía más de un
  token.
- **Un rechazo por políticas se veía como «el modelo no ha devuelto ninguna
  respuesta».** Llega con HTTP 200 y `stop_reason: "refusal"`, así que hay que
  comprobarlo antes de leer el contenido. En esta aplicación no es un caso
  exótico: se pregunta por intrusiones, malware y direcciones de atacantes, que
  es material que un clasificador puede leer como una petición ofensiva. Ahora
  se distingue, con la categoría, y se dice que reformular suele bastar.

Siete tests en `test_chat_en_trozos.py`, y el que importa es el que fija que el
texto final está verificado aunque los trozos no: si el elemento final del flujo
se perdiera, en pantalla quedaría el borrador del modelo con sus citas
inventadas intactas y nada fallaría de forma visible.

### El `case_id` de OSINT: era el frontend

`osint_findings.case_id` estaba a NULL en casi todo, y con él vacío el Anexo B
de los informes sale sin nada aunque haya trabajo de OSINT hecho. La causa no
estaba en este módulo ni en el modelo de datos: los nueve endpoints de análisis
de scam-shield aceptaban `case_id` desde el principio y lo guardaban en su tabla
y en la proyección. **El frontend nunca lo mandaba**, porque no había dónde
elegir el caso.

Arreglado con un selector de expediente en la cabecera del módulo OSINT, común a
las nueve pantallas y persistido en el navegador. Con caso elegido, cada análisis
nace atribuido; sin él, la cabecera avisa de lo que eso implica en vez de dejar
que se descubra semanas después. El PATCH de vinculación que ya existía sigue
siendo la red de seguridad para lo anterior — y para lo ya analizado es la única
vía, porque nada en la fila dice a qué caso pertenecía.

## Cómo retomar

```bash
cd sharingan
python -m venv venv
venv/Scripts/python -m pip install -r requirements.txt -r requirements-dev.txt
venv/Scripts/python -m pytest tests -q   # 218 tests, sin red

# Pruebas manuales completas: ver la sección "Guía de pruebas manuales"
# del README.md, que incluye el orden de arranque (fixture → alembic).
```

Copia de trabajo local:
`C:\Users\pc\Documents\Ciber\Proyectos\nexus-worktrees\dev-local\sharingan`
(worktree de `Proyectos\nexus`, ver `Proyectos/CLAUDE.md`).
Repo: `https://github.com/dacaror-tlco/DFIR-Nexus`, carpeta `sharingan/`. El
trabajo vivo del módulo está en `integracion/asistente-ia`; la rama
`sharingan` quedó en el estado del 02/09.
