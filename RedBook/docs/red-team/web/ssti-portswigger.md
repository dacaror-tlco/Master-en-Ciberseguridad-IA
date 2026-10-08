---
tags:
- Auditoría web
---

# SSTI PortSwigger

**EVOLVE ACADEMY · MÁSTER EN CIBERSEGURIDAD OFENSIVA**

**SSTI — Server-Side Template Injection**

Laboratorios PortSwigger (ERB/Ruby y Tornado/Python)

Instructor: Carlos Castillo · 28/07/2026

| **ℹ Metadatos a confirmar**  Número de sesión provisional: esta clase encaja en el bloque web posterior a SSRF y Path Traversal. Confirma el número de sesión antes de archivarla en la colección. |
| --- |

# **1. Objetivos de la sesión**

- Entender qué es una vulnerabilidad **SSTI** (Server-Side Template Injection) y por qué puede escalar hasta ejecución de comandos (RCE).
- Aprender a **detectar** un SSTI: reflejo del input, prueba del 7\*7, cadena *polyglot* y forzado de errores.
- Saber **identificar el motor de plantillas** que corre por detrás (ERB, Tornado, Jinja2, FreeMarker, Twig...).
- **Explotar** dos laboratorios de PortSwigger: uno en ERB/Ruby (contexto de valor) y otro en Tornado/Python (contexto de código).
- Repasar la **metodología de auditoría web**: entender la aplicación antes de lanzarse a buscar la vulnerabilidad.

# **2. Conceptos clave**

## **Plantilla y motor de plantillas**

Ninguna web seria tiene el contenido *hardcodeado*: los textos que ves ("Bienvenido de vuelta, Cibersia Security SL") se generan de forma **dinámica** por usuario o por empresa. Para eso se usan **plantillas** (templates): un formato fijo con **variables** que se rellenan en tiempo de ejecución.

Ejemplo de plantilla: Hola {{ nombre }}. Con el dato nombre = Carlos, el **motor de plantillas** (template engine) evalúa la variable y produce Hola Carlos.

Cada lenguaje tiene su propio motor con su **sintaxis**: Ruby usa ERB, Python usa Tornado o Jinja2, Java usa FreeMarker, PHP usa Twig, etc. Igual que una *webshell* .php solo se ejecuta si el back-end es PHP, la sintaxis del payload SSTI depende del motor.

## **La vulnerabilidad**

El SSTI aparece cuando un **dato controlado por el usuario** entra dentro del código de la plantilla y el motor lo **evalúa** en lugar de tratarlo como texto plano. Es decir: hay una **mala sanitización** del campo de entrada.

La señal de partida es sencilla: si un valor que **yo controlo** (mi nombre, el nombre de mi empresa, un comentario...) **se refleja** en algún punto de la web, ahí hay potencial de SSTI. No hace falta conocer el motor de antemano; hay que probarlo.

| **⚠ Reflejo ≠ vulnerabilidad confirmada**  Que un valor se refleje NO garantiza que sea vulnerable: es un **potencial** SSTI. Hay que confirmarlo (con 7\*7 → 49 o forzando error). No confundas con manipular el HTML en el F12: eso es solo el frontend. En SSTI la petición llega al servidor, se procesa y vuelve reflejada. |
| --- |

## **Lado seguro vs. lado vulnerable**

La prueba universal es el 7\*7. Metemos 7\*7 en el campo reflejado:

- **Lado seguro**: la web devuelve literalmente 7\*7. El motor trata el input como texto, no lo evalúa.
- **Lado vulnerable**: la web devuelve 49. El motor ha **evaluado** la expresión. En ese momento "se abre todo el mundo": si evalúa 7\*7, puede evaluar código.

## **Analogía con SQL Injection**

SSTI se razona igual que un **SQL Injection**, pero cambiando el "código" abusado: en SQLi abusamos de la **consulta**; en SSTI abusamos de la **plantilla**. En SQLi cerramos la consulta con una comilla antes de inyectar; en SSTI cerraremos la expresión de la plantilla antes de inyectar lo nuestro (se ve en el Lab 2).

| **ℹ Ampliación**  En SSTI solemos tener **más poder** que en un SQLi típico: el SQLi suele estar más filtrado/sanitizado, mientras que si un valor se refleja tal cual, ya tenemos capacidad directa de modificarlo. El objetivo final habitual es el **RCE**. |
| --- |

# **3. Desarrollo técnico**

## **3.1 Flujo de una plantilla (seguro vs. vulnerable)**

| **1. Plantilla: Hola {{ nombre }}** |
| --- |

**↓**

| **2. Dato del usuario: nombre = Carlos** |
| --- |

**↓**

| **3. El motor evalúa la variable** |
| --- |

**↓**

| **4. Resultado esperado: Hola Carlos (flujo seguro)** |
| --- |

El problema empieza cuando el atacante mete 7\*7 (o una expresión del motor) y el motor lo evalúa: Hola 49. A partir de ahí se puede pivotar a lectura de ficheros, extracción de objetos internos y, en el peor caso, **RCE**.

## **3.2 Motores de plantillas por lenguaje**

No hay que aprenderse todos de memoria (para eso están HackTricks, Google o la IA). Sí conviene reconocer los principales y su prueba de vida (7\*7):

| **Motor** | **Lenguaje** | **Sintaxis (prueba 7\*7)** | **Resultado** |
| --- | --- | --- | --- |
| ERB | Ruby | <%= 7\*7 %> | 49 |
| Tornado | Python | {{7\*7}} | 49 |
| Jinja2 | Python | {{7\*7}} | 49 |
| Mako | Python | ${7\*7} | 49 |
| FreeMarker | Java | ${7\*7} | 49 |
| Twig | PHP | {{7\*7}} | 49 |
| Nunjucks | Node.js | {{7\*7}} | 49 |
| Razor | .NET | @(7\*7) | 49 |
| Django | Python | {{7\*7}} (restringido) | no evalúa 7\*7 |
| **⚠ Motores restringidos (Django)**  **Django** está más restringido por diseño: valida bien y limita la lectura de objetos y atributos internos, por lo que normalmente no se salta con el 7\*7. Aun así, no te fíes: en algunos motores restringidos todavía se pueden extraer objetos e información interna. Si se consigue la **clave secreta** del framework (SECRET\_KEY), se puede llegar a comprometer todo. |
| **ℹ Corrección de artefactos de transcripción**  Los verdaderos nombres de motor pueden aparecer mal transcritos en audio. Correcciones aplicadas: "Ginja/Jingja/Ninja 2" → **Jinja2**; "ERB/RB/ERP/CRV" → **ERB**; "TWing/TheWinds/Twink" → **Twig**; "Freimarker/FreeMarket" → **FreeMarker**; "Nunchunque/Nunjungs" → **Nunjucks**; "Radzor" → **Razor**. |

## **3.3 Las 3 fases de explotación**

| **1. Detectar: encontrar un indicio (input reflejado, 7\*7, polyglot)** |
| --- |

**↓**

| **2. Identificar el motor (forzando errores, probando sintaxis por motor)** |
| --- |

**↓**

| **3. Explotar: dar con la sintaxis final para leer, listar o ejecutar** |
| --- |
| **ℹ Ampliación**  Detectar e identificar el motor no basta: si no consigues **explotarlo**, todo el trabajo se queda en "prueba realizada". La explotación real (con sus filtros y límites) es lo que cierra la vulnerabilidad. |

## **3.4 Detección: la cadena polyglot y el forzado de errores**

Truco genérico (navaja suiza): una cadena *polyglot* que mezcla los caracteres especiales de todos los motores. Al inyectarla, si el motor "entiende" alguno de sus caracteres, se rompe la sintaxis y **fuerza un error** que nos delata el motor:

| ${{<%[%'"}}%\ |
| --- |

La idea es la misma que soltar la misma palabra en 7 idiomas: cuando el motor "oye" el suyo, se activa. En el Lab 1, al inyectar la polyglot, el motor **se comió** el <% y el %> → señal clara de **ERB (Ruby)**.

Los **códigos de error** son oro. Muchas apps en **preproducción** dejan trazas de error para los desarrolladores. Si están públicas, ese *stack trace* nos revela lenguaje, motor y hasta **versión**. En el Lab 2 el error mostró Ruby 2.7.0 y detalles internos que no deberían exponerse.

| **ℹ Buena práctica**  Un error verboso ya es en sí una vulnerabilidad (fuga de información interna: versiones, rutas, funciones). Fuérzalo, cópialo y, si no reconoces el motor, pásaselo a la IA (Claude/ChatGPT) o búscalo en Google/HackTricks para identificar tecnología y payloads. |
| --- |

## **3.5 Escalada: RCE, clave secreta y sandbox**

- **RCE**: el objetivo típico. De un 7\*7 se pasa a ejecutar comandos (p. ej. system(...) en Ruby, os.system(...) en Python).
- **Clave secreta del framework** (SECRET\_KEY): si se extrae, se compromete todo (firmas de sesión, tokens...).
- **Sandbox / Docker**: el motor puede correr en un contenedor "ultraprotegido". Es una barrera, pero no es infalible: se puede intentar escapar (movimiento lateral / pivoting) — tema avanzado, no cubierto hoy.

| **⚠ Explotación en laboratorio autorizado**  En una auditoría real no necesitas una shell perfecta: en cuanto obtienes ejecución (un simple whoami que responde), **ya estás ejecutando comandos** y ya es una vulnerabilidad. La calidad de la shell es secundaria. |
| --- |

## **3.6 Lab 1 — SSTI básico en ERB (Ruby) · contexto de valor**

Entorno: tienda de PortSwigger. **Objetivo**: eliminar morale.txt del directorio personal de Carlos. La descripción del lab ya indica que el motor es **ERB (Ruby)** (simula un cliente que entrega documentación → caja gris).

**Metodología primero** (Carlos insistió mucho): no ir directo al SSTI, sino **entender la aplicación**. Solo hay dos estados: producto con stock y producto sin stock.

1. Analizar la tienda: home, listado de productos, product ID.
2. Con **Burp Intruder**, enumerar IDs (1–20) y comparar longitudes de respuesta → distinguir *en stock* (200) de *sin stock* (302 + mensaje).
3. El producto sin stock devuelve un mensaje de error que se **refleja** en el parámetro message de la URL → punto de inyección.
4. Inyectar la cadena polyglot → el motor consume <%/%> → es **ERB (Ruby)**.
5. Confirmar con la prueba de vida <%= 7\*7 %> → devuelve 49.
6. Explotar con RCE para borrar el fichero objetivo.

Payload de confirmación (7\*7) y payload de RCE en ERB:

| <%= 7\*7 %>  <%= system("rm /home/carlos/morale.txt") %> |
| --- |
| **✓ Resultado**  system(...) en Ruby devuelve true si el comando se ejecuta correctamente. Al lanzar el payload de borrado, la web mostró true → fichero eliminado → **laboratorio resuelto**. Un compañero (Adrián) lo resolvió con otra sintaxis ERB usando objetos/funciones; también válida, porque el motor la interpreta igual. |
| **ℹ Verificar dato**  El nombre del fichero se pronunció como "Morales.txt" en el audio; el fichero real del laboratorio PortSwigger es morale.txt. Verifícalo en el enunciado antes de lanzar el comando. |

## **3.7 Lab 2 — SSTI en Tornado (Python) · contexto de código**

Entorno: blog de PortSwigger, con **login** (credenciales wiener / peter entregadas por el "cliente" → caja gris). **Objetivo**: de nuevo, eliminar morale.txt del directorio de Carlos.

Análisis de la app: *My account* permite cambiar el **preferred name** (parámetro blog-post-author-display), que se refleja como **nombre de autor** en los comentarios/posts. Ese es el punto de inyección.

Diferencia clave con el Lab 1: aquí NO inyectamos en un **valor** libre, sino dentro de una **variable/expresión** de la plantilla (algo tipo user.name, que el back-end envuelve en {{ ... }}). Es el **contexto de código**.

Detección del motor: forzando la aplicación con sintaxis inválida, la app **petó** y el error reveló **Python + Tornado**. La prueba {{7\*7}} no salía limpia (aparecía con llaves) precisamente porque el input ya vive dentro de una expresión.

Idea de explotación (analogía SQLi): **primero cerrar** la expresión que pone el back-end y **luego** inyectar lo nuestro. Meter {{ }} dentro de otro {{ }} no tiene sentido sintáctico y **rompe** (igual que un OR 1=1 sin cerrar la consulta).

| **1. Back-end: {{ user.name }} (nosotros solo vemos user.name)** |
| --- |

**↓**

| **2. Cerrar la expresión existente: ...}}** |
| --- |

**↓**

| **3. Abrir un bloque de statement: {% import os %}** |
| --- |

**↓**

| **4. Inyectar la ejecución: {{ os.system('rm /home/carlos/morale.txt')** |
| --- |
| **⚠ Pendiente — no cubierto en la transcripción**  La sesión terminó aquí por tiempo: se detectó el motor (Tornado/Python), se razonó el escape de contexto y quedó pendiente cerrar la explotación (RCE) con import os. Carlos avisó de que probablemente haga falta **URL-encodear** el payload (sobre todo el % de {% %} y los espacios como +). Continúa mañana. |
| **ℹ Fidelidad**  El razonamiento de escape de contexto y los payloads exactos de Tornado no llegaron a completarse en clase; lo anterior refleja la dirección planteada por el instructor, no una cadena final verificada en el laboratorio. Verifícala en HackTricks / documentación de Tornado. |

# **4. Payloads y comandos importantes**

Detección genérica (polyglot) para forzar error e identificar motor:

| ${{<%[%'"}}%\ |
| --- |

Prueba de vida 7\*7 por motor (los principales):

| ERB (Ruby): <%= 7\*7 %>  Tornado (Python): {{7\*7}}  Jinja2 (Python): {{7\*7}}  FreeMarker (Java): ${7\*7}  Twig (PHP): {{7\*7}} |
| --- |

Lab 1 — RCE en ERB (Ruby):

| <%= system("rm /home/carlos/morale.txt") %> |
| --- |

Lab 2 — dirección de explotación en Tornado (Python), pendiente de cerrar y URL-encodear:

| }}{% import os %}{{ os.system('rm /home/carlos/morale.txt') |
| --- |
| **⚠ Errores comunes en Burp**  En Burp: recuerda **URL-encode** (Ctrl+U sobre la selección, desde el = del parámetro) y el **espacio** del comando como +. Y completa el flujo con **Follow redirect** en el Repeater, o el lab no marca como resuelto (fue el fallo típico de varios compañeros). |

# **5. Herramientas utilizadas en la sesión**

| **Herramienta** | **Objetivo** | **Fase** | **Uso visto** | **Nivel** | **Notas** |
| --- | --- | --- | --- | --- | --- |
| Burp Suite (Proxy/Repeater) | Interceptar y reenviar peticiones | Explotación web | Enviar payload SSTI, Follow redirect | Recurrente | Núcleo de la sesión |
| Burp Intruder | Enumerar valores | Enumeración web | IDs de producto 1–20, comparar longitudes | Practicada | Detectar stock/sin stock |
| Burp Decoder (URL-encode) | Codificar payloads | Explotación web | Ctrl+U, espacio → + | Practicada | Clave para que el lab acepte el payload |
| HackTricks | Consultar payloads/metodología | Investigación | Ctrl+F por 'Python', sintaxis por motor | Recurrente | Referencia de cabecera para SSTI |
| Wappalyzer | Fingerprint de tecnologías | Reconocimiento | Revisado (poca info) | Mencionada | Aportó poco en estos labs |
| IA (Claude / ChatGPT) | Identificar motor desde el error | Investigación | Pegar stack trace y pedir tecnología/payload | Mencionada | Alternativa a Google/HackTricks |
| **ℹ Herramientas mencionadas (no desarrolladas)**  **Burp AI / "Burp AT"**: PortSwigger anunció el mismo día una IA que automatiza tareas dentro del proxy (autonomía, alcance y ruido configurables). Carlos planeaba probarla. Equivalente conceptual a montar tu propio Burp + MCP/IA. También se citó "el bicho", herramienta interna de Cibersia que audita web de forma pasiva y activa. Ninguna se desarrolló en clase. |

# **6. Riesgos, errores comunes y buenas prácticas**

| **⚠ Filtros y límites de longitud**  Aunque 7\*7→49 funcione, la explotación puede bloquearse: filtros que vetan import, system, os o rutas concretas; o **límites de longitud** del campo (p. ej. un nombre de empresa de 30 caracteres, o una fecha de nacimiento). Habrá que bypassear con Burp. |
| --- |
| **✓ Metodología primero**  No vayas directo a "buscar el SSTI": primero **entiende la aplicación** y saca todas las funcionalidades. La vulnerabilidad aparece después, sobre lo que ya has mapeado. Ir con calma, paso a paso, es la metodología. |
| **ℹ Enfoque de estudio**  No te aprendas de memoria todos los frameworks: es imposible y cambian. Interioriza los **grupos grandes** de vulnerabilidad y su lógica; el detalle se busca en HackTricks, Google o la IA. Lo importante es saber **dónde** ocurre y **cómo** detectarla. |
| **ℹ El valor de los errores**  Forzar la app hasta que "pete" no es perder el tiempo: un error puede abrir una ventana a varias vulnerabilidades y delata tecnología y versión. |

# **7. Conexión con sesiones anteriores**

**SSRF y Path Traversal**: misma metodología de "entender la app y ver cómo trata mi input" (whitelist/blacklist, URL-encode, ../). El SSTI es otra pieza del mismo mapa mental de auditoría web.

**SQL Injection**: patrón idéntico de *cerrar la estructura y luego inyectar* (comilla + OR 1=1 ↔ cerrar }} + payload). Ayuda a razonar el contexto de código del Lab 2.

**IDOR / enumeración de usuarios**: en el Lab 2, cambiar wiener por admin no funcionó porque la cookie de sesión valida el usuario; si funcionara, sería IDOR.

**Burp Intruder** y el "check stock" del bloque SSRF reaparecen aquí para distinguir estados de la app por longitud de respuesta.

# **8. Resumen final**

SSTI = abusar de un **motor de plantillas** cuando un input reflejado se **evalúa** en vez de tratarse como texto. Se detecta viendo si tu valor se refleja, con la prueba 7\*7→49, con la cadena *polyglot* o forzando errores (que además revelan motor y versión). Flujo: **detectar → identificar el motor → explotar**. El potencial llega hasta **RCE**. Hoy: Lab 1 en **ERB/Ruby** (contexto de valor) resuelto con <%= system(...) %>; Lab 2 en **Tornado/Python** (contexto de código) detectado y planteado el escape de contexto, con la explotación **pendiente** para la próxima clase. Lección transversal: la **metodología** (entender la app) pesa más que memorizar sintaxis.

# **9. Checklist de repaso**

1. Sé explicar qué es una plantilla y un motor de plantillas.
2. Reconozco la señal de partida: un valor que controlo se refleja en la web.
3. Aplico la prueba 7\*7→49 para confirmar evaluación.
4. Uso la cadena polyglot y sé forzar errores para identificar el motor y su versión.
5. Distingo contexto de valor (Lab 1) de contexto de código (Lab 2).
6. Sé cerrar la expresión del motor antes de inyectar (analogía SQLi).
7. Conozco los payloads 7\*7 de ERB, Tornado, Jinja2, FreeMarker y Twig.
8. Recuerdo URL-encodear en Burp y hacer Follow redirect.
9. Entiendo que un whoami que responde ya es RCE.

# **10. Preguntas de repaso**

- ¿Por qué 7\*7→49 confirma un SSTI y qué significaría que devolviera 7\*7?
- ¿Para qué sirve la cadena polyglot y por qué delata el motor?
- Explica la diferencia entre contexto de valor (Lab 1) y contexto de código (Lab 2).
- ¿Qué relación tiene el escape de contexto en Tornado con el bypass de un login por SQLi?
- ¿Por qué un error verboso en preproducción es ya una vulnerabilidad?
- Cita el payload 7\*7 de ERB, Tornado, FreeMarker y Twig.

# **11. Actualización del registro de herramientas**

Cambios de nivel y nuevas entradas respecto al registro acumulado (copiable a la base de conocimiento):

| **Herramienta** | **Nivel** |
| --- | --- |
| Burp Suite (Proxy, Repeater, Intruder, Decoder) | Recurrente |
| HackTricks (referencia) | Recurrente |
| Burp AI / "Burp AT" | Mencionada (nuevo) |
| "El bicho" (herramienta interna Cibersia) | Mencionada (nuevo) |
| Wappalyzer | Mencionada |
| **✓ Registro de vulnerabilidades**  Nueva **vulnerabilidad** en el registro: **SSTI (Server-Side Template Injection)** — nivel Introducida/Practicada (Lab 1 completo en ERB; Lab 2 a medias en Tornado). Motores vistos: ERB, Tornado, Jinja2, Mako, FreeMarker, Twig, Nunjucks, Razor, Django. |

# **12. Actualización de memoria del proyecto**

| **Campo** | **Contenido** |
| --- | --- |
| Sesión / tema | SSTI (Server-Side Template Injection) — labs PortSwigger |
| Instructor | Carlos Castillo |
| Fecha | 28/07/2026 |
| Entorno / labs | PortSwigger: Lab 1 ERB/Ruby (resuelto), Lab 2 Tornado/Python (a medias) |
| Vulnerabilidad nueva | SSTI — detección, identificación de motor y explotación a RCE |
| Motores de plantillas | ERB, Tornado, Jinja2, Mako, FreeMarker, Twig, Nunjucks, Razor, Django |
| Técnicas web | Prueba 7\*7, cadena polyglot, forzado de errores, escape de contexto |
| Pendiente | Cerrar RCE del Lab 2 (Tornado + import os, URL-encode); HTB GoodGames (SQLi + SSTI); repaso de metodología |
| Conexiones | SSRF, Path Traversal, SQLi, IDOR, Burp Intruder / check stock |
| Certeza | Alta en teoría y Lab 1; Media en payload final de Lab 2 (no cerrado en clase) |
| **ℹ Copiar a memoria del proyecto**  Bloque para memoria acumulativa: Sesión SSTI (Carlos Castillo, 28/07/2026). Cubierto: concepto de SSTI, plantillas y motores, prueba 7\*7→49, polyglot ${{<%[%'"}}%\, forzado de errores, 3 fases (detectar/identificar/explotar), analogía con SQLi, escape de contexto de código. Lab 1 ERB/Ruby resuelto con <%= system("rm /home/carlos/morale.txt") %> → true. Lab 2 Tornado/Python: motor detectado por error, escape de contexto planteado, RCE pendiente. Herramientas: Burp (Proxy/Repeater/Intruder/Decoder), HackTricks, Wappalyzer, IA. Mencionadas nuevas: Burp AI y 'el bicho' (Cibersia). Pendientes: cerrar Lab 2, HTB GoodGames, repaso de metodología web. |
