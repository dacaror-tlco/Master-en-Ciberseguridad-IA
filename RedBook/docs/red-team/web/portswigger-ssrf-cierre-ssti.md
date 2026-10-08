---
tags:
- Auditoría web
---

# PortSwigger SSRF cierre SSTI

**EVOLVE ACADEMY · MÁSTER EN CIBERSEGURIDAD**

**PortSwigger — Cierre de SSRF + Intro a SSTI**

Instructor: Carlos Castillo · 21/07/2026

Entorno: PortSwigger Web Security Academy (laboratorios SSRF)

# **1. Objetivos de la sesión**

- Cerrar el bloque de **SSRF** (Server-Side Request Forgery) resolviendo tres laboratorios de PortSwigger que aumentan en dificultad.
- Aprender a **bypassear una blacklist** que filtra localhost y 127.0.0.1.
- Encadenar un **Open Redirect** interno para saltar un filtro que solo admite URLs de la propia aplicación.
- Bypassear una **whitelist** abusando del formato completo de una URL (**user-info** @ + **fragmento** #).
- Introducir el bloque siguiente: **SSTI** (Server-Side Template Injection). *Nota: en el material aportado la parte práctica de SSTI queda anunciada pero no llega a desarrollarse (ver sección 8).*

# **2. Conceptos clave**

## **¿Qué es SSRF?**

**SSRF** (Server-Side Request Forgery) es una vulnerabilidad en la que **forzamos al servidor a hacer una petición a una URL que nosotros controlamos**. El servidor actúa como intermediario o "mensajero": nosotros no tenemos alcance a la red interna, pero el servidor sí, así que lo usamos de cebo para que acceda por nosotros a recursos internos.

| **ℹ Cómo se detecta**  Señal de detección: en cuanto veas que una petición (POST o GET), un parámetro o una cabecera contiene o dispara una **llamada a una URL**, deben saltar todas las alertas de SSRF. En los labs el parámetro clave era stockApi, que hacía una llamada a la URL de comprobación de stock. |
| --- |

La URL objetivo no siempre lleva http:// visible: a veces solo aparece un valor tipo stock.weliketoshop.net o una ruta parcial, y el servidor añade el esquema por detrás. No la descartes por eso — sigue siendo una URL.

## **¿A qué se tiene visibilidad con SSRF?**

No a todo. El servidor tendrá visibilidad, sobre todo, a servicios levantados sobre **HTTP** (páginas, paneles, APIs internas). El objetivo típico es acceder a **paneles internos** (por ejemplo http://localhost/admin) que desde fuera están fuera de alcance.

## **Superficies donde puede vivir un SSRF**

- **Cuerpo de la petición (data)**: el caso más habitual (el parámetro stockApi).
- **Cabeceras**: Referer, X-Forwarded-For (X-Forwarded) u otras cabeceras propias que añada la empresa. Si una cabecera contiene una URL, pruébala.

| **⚠ AVISO**  Cuidado: no confundas el **host** (URL base) con los **directorios/rutas** de esa URL. No pruebes el payload sobre el host; va en la parte de la ruta o del parámetro correspondiente. |
| --- |

## **Blacklist vs. Whitelist**

**Blacklist (lista negra)**: el servidor **bloquea ciertas palabras** (p. ej. localhost, 127.0.0.1, admin). Se bypassea buscando representaciones alternativas que la lista no contempla.

**Whitelist (lista blanca)**: el servidor **exige que aparezca algo concreto** (p. ej. que la URL contenga stock.weliketoshop.net). Es más robusta, pero también puede saltarse.

| **ℹ Ampliación — leer los errores**  Distinguir cuál es cuál se hace **leyendo el código de error**. Si dice "debe contener X", es whitelist. Si simplemente bloquea por seguridad sin decir qué exige, empieza asumiendo blacklist y, si no cede, pasa a la lógica de whitelist. |
| --- |

# **3. Desarrollo técnico**

## **Repaso — El SSRF básico (sesión anterior)**

Flujo de partida: la tienda comprueba el stock por ciudad mediante una petición **POST** cuyo parámetro stockApi apunta a una URL. Como esa llamada la ejecuta el **servidor**, cambiamos la URL para que apunte a un recurso interno.

| **1. Atacante (navegador o Burp) envía la petición POST** |
| --- |

**↓**

| **2. El servidor web recibe stockApi y hace la llamada por nosotros** |
| --- |

**↓**

| **3. Reapuntamos stockApi a http://localhost/admin (o a la red interna)** |
| --- |

**↓**

| **4. El servidor, que sí está en la red interna, nos devuelve el recurso** |
| --- |

Para descubrir servicios internos sin conocer la IP, se usa **Burp Intruder** iterando el último octeto de la red interna (http://192.168.0.X:8080/, X de 1 a 254) y, si hace falta, sobre puertos/protocolos.

| **⚠ AVISO**  El barrido con Intruder es tiempo y **ruido**. Reduce el rango al máximo y ten presente el riesgo de detección en un entorno real. |
| --- |

## **Lab 1 — Bypass de blacklist (localhost / 127.0.0.1 / admin filtrados)**

Objetivo: acceder a http://localhost/admin y borrar al usuario **carlos**. El filtro bloquea la palabra localhost y la IP 127.0.0.1; además, en este lab, filtra también la palabra admin.

**Técnica 1 — Representaciones alternativas de la loopback.** El sistema entiende formas abreviadas de 127.0.0.1 como si fueran la misma dirección (funcionan como "alias"):

| 127.0.0.1 -> forma completa  127.0.1 -> se quita un 0, sigue resolviendo a la loopback  127.1 -> forma mínima, equivale a 127.0.0.1 |
| --- |
| **ℹ Ampliación — por qué funciona la abreviatura**  Compruébalo tú mismo con ping: ping 127.1 resuelve a 127.0.0.1. Es el mismo comportamiento de alias/DNS que hace ping google.es frente a su IP. |

**Técnica 2 — Encoding de la palabra filtrada (`admin`).** Si el filtro busca literalmente la cadena admin, se rompe encodeando en **URL-encode**. No hace falta encodear toda la palabra: basta con un carácter para que la validación previa deje de reconocer admin, mientras el servidor sigue interpretándola bien al procesarla.

| admin -> bloqueado (la blacklist lo detecta)  %61dmin -> 'a' encodeada una vez  doble URL-encode sobre la palabra si un solo encode aún es detectado |
| --- |
| **⚠ Error común — sobre-encodear**  A veces un solo URL-encode es cazado por la validación y necesitas 2 (o más) pasadas. Pero NO abuses: si a la 4.ª pasada no cede, no sigas hasta 200. Y ojo con encodear la URL entera: puede disparar un bloqueo por "demasiados caracteres especiales". |

Idea de fondo: *la validación no tiene inteligencia*. Comprueba lo que le programaron (p. ej. "que contenga la cadena admin"). Si ya no es esa cadena exacta, el filtro no salta, pero el servidor sí resuelve el destino.

## **Lab 2 — Open Redirect encadenado (filtro que solo admite URLs propias)**

Aquí el filtro está mejor hecho: **solo permite URLs de la propia aplicación** y rechaza cualquier destino externo. Probar localhost, 127.1, etc. devuelve Invalid external stock check URL. El SSRF "directo" parece muerto... pero no lo está.

Descubrimiento clave: en la tienda existe la función **"Next product"**, una petición GET que hace un **redirect** al siguiente producto (del 5 va al 6). Es una URL **propia de la aplicación** que, además, **redirige a otro sitio**.

| **⚠ Vulnerabilidad — doble salto**  El filtro valida el destino inmediato ("¿es una URL de la aplicación?"), pero NO controla que ese endpoint propio a su vez haga un **Open Redirect**. Ese es el fallo que encadenamos. |
| --- |

La idea: metemos dentro de stockApi la URL propia de "next product", pero manipulando su parámetro de redirección (path) para que, en lugar de ir al producto siguiente, redirija a la red interna. El servidor valida la URL propia, la sigue, y acaba haciendo la petición interna por nosotros.

| **1. El filtro obliga a que stockApi sea una URL de la propia aplicación** |
| --- |

**↓**

| **2. Buscamos un endpoint propio que redirija: /product/nextProduct (Open Redirect)** |
| --- |

**↓**

| **3. Colocamos esa URL propia en stockApi, con su path apuntando a lo interno** |
| --- |

**↓**

| **4. El servidor valida la URL propia y sigue el redirect hasta el recurso interno** |
| --- |
| **ℹ NOTA**  El path hay que enviarlo **URL-encodeado**; si no, Burp devuelve "Missing parameter" (es un problema de formato de la petición, no del SSRF). |
| **⚠ Por qué debe hacerlo el servidor**  Contraprueba importante: si intentas el redirect **directamente desde el navegador/Burp** (el botón next product), lo haces **tú**, no el servidor, y NO hay SSRF. Solo funciona cuando el redirect lo ejecuta el servidor desde dentro de stockApi. Ahí está la diferencia. |

## **Lab 3 — Bypass de whitelist (user-info + fragmento)**

El más difícil. El error es explícito: *"external stock check host must contain `stock.weliketoshop.net`"*. Es una **whitelist**: la URL está obligada a contener ese host. Poner simplemente stock.weliketoshop.net/admin no vale, y localhost menos aún.

La solución abusa del **formato completo de una URL**, que casi nadie usa pero el protocolo admite:

| esquema://[ user-info @ ] host [ :puerto ][ /ruta ][ ?query ][ #fragmento ] |
| --- |

## **Las dos piezas nuevas**

**user-info** (lo que va antes de la @): campo usuario[:contraseña] de la URL. Todo lo escrito **a la izquierda de la `@`** es user-info; el **host real** es lo que va **después de la `@`**.

**Fragmento** (#): todo lo que va **a la derecha del `#`** se omite como destino de red (es el ancla / "comentario" de la URL; sirve para saltar a secciones de la misma página, no para cambiar de recurso).

| **ℹ Ampliación — de dónde sale user-info**  Símil práctico del user-info: es lo mismo que usuario@IP en SSH, o el login básico HTTP que salta en un pop-up del navegador. http://cesar:test123@panel.ejemplo.es intenta autenticar con usuario cesar y contraseña test123 directamente en la URL. |
| --- |

Combinando ambos, construimos una URL que **pasa la validación** (contiene el host de la whitelist como user-info, antes de la @) pero cuyo **host real** es el que nosotros queremos, y el fragmento anula lo que sobra tras la validación:

| https://stock.weliketoshop.net@localhost/admin#stock.weliketoshop.net |
| --- |

Lectura del payload: stock.weliketoshop.net queda como **user-info** (satisface "debe contener el host"), localhost es el **host real** al que se accede, /admin es la ruta, y el #... es el fragmento que se descarta. El # (%23) puede necesitar **doble URL-encode** para pasar el filtro; el primer encode no cuela y el segundo sí.

| **⚠ Error común — dónde va /admin**  La ruta (/admin) va SIEMPRE al final, después del host real. Si la pones antes del @, el servidor la interpreta como parte del dominio (y un dominio no puede llevar barras), así que fallará. El truco solo funciona con la barra al final. |
| --- |
| **ℹ NOTA**  Este lab combina whitelist + un pequeño toque de blacklist (por eso hace falta encodear el #). Concepto de nivel alto: Carlos avisa de que NO cae en un eJPT, pero sí es realista en auditorías de empresa con whitelists en parámetros. |

# **4. Payloads y atajos importantes**

Representaciones de la loopback (bypass de blacklist):

| http://127.0.0.1/admin  http://127.1/admin  http://localhost/admin |
| --- |

Encoding de palabra filtrada (admin):

| http://localhost/%61dmin  (doble URL-encode si un solo encode es detectado) |
| --- |

Bypass de whitelist con user-info + fragmento:

| https://stock.weliketoshop.net@localhost/admin#stock.weliketoshop.net |
| --- |

Acción final del objetivo en los labs (borrar usuario carlos):

| /admin/delete?username=carlos |
| --- |

## **Atajos de Burp (Decoder / Inspector)**

| Ctrl + U -> URL-encode de la selección  Ctrl + Shift + U -> URL-decode de la selección |
| --- |
| **⚠ AVISO**  Anécdota de la sesión (error humano real): un payload dejó de funcionar por copiar stockApi= repetido 7 veces sin querer. Lección: revisa siempre la petición completa antes de dudar de la técnica. |

# **5. Herramientas utilizadas en la sesión**

| **Herramienta** | **Objetivo** | **Fase** | **Uso visto** | **Nivel** | **Notas** |
| --- | --- | --- | --- | --- | --- |
| Burp Repeater | Reenviar y ajustar peticiones | Explotación web | Editar stockApi y reenviar | Practicada | Herramienta central de todos los labs |
| Burp Intruder | Fuzzing de red interna | Enumeración interna | Iterar octeto 1-254 y puertos | Practicada | Descubrir servicios internos vía SSRF |
| Burp Decoder/Inspector | URL-encode / decode | Explotación web | Ctrl+U / Ctrl+Shift+U | Practicada | Clave para bypass de filtros |
| ping | Verificar resolución de IP | Verificación | ping 127.1 | Recurrente | Comprobar equivalencia de la loopback |
| **ℹ NOTA**  Nota: se mencionó Gemini y Claude como apoyo de estudio/depuración (fuera del alcance técnico del lab). No se desarrollan aquí. |

# **6. Riesgos, errores comunes y buenas prácticas**

| **⚠ RIESGO**  El barrido con Intruder genera ruido y puede delatarte en un entorno real. Acota el rango y minimiza intentos. |
| --- |
| **⚠ AVISO**  No busques "una solución para todo": encodear la URL entera puede activar bloqueos por número de caracteres especiales. A veces basta con encodear un solo carácter. |
| **✓ CORRECTO**  Lee siempre los códigos de error: distinguen blacklist ("bloqueado por seguridad") de whitelist ("debe contener X") y orientan el bypass. |
| **✓ CORRECTO**  Metodología y anotaciones: apunta cada payload probado. En auditorías largas (días/semanas) es imprescindible saber qué has probado ya y qué te falta. |
| **⚠ AVISO**  No todo es explotable: si el filtro está bien hecho, puede no haber bypass. Aprende a saber parar (evitar el Rabbit Hole). |

# **7. Conexión con sesiones anteriores**

Esta sesión **cierra el bloque de SSRF** iniciado el día anterior, donde se vio la detección básica (stockApi) y el primer bypass con localhost/127.0.0.1 y el barrido con Intruder.

Se apoya en **Burp Suite** (Proxy, Repeater, Intruder, Decoder), ya trabajado en la sesión dedicada a la herramienta, que aquí vuelve a ser el eje de todo el trabajo web.

El **Open Redirect** y el manejo fino de **URL-encode** enlazan con la metodología web general (fuzzing, lectura de parámetros y rutas) vista en enumeración web y OWASP. El razonamiento "¿lo hace el servidor o lo hago yo?" es el mismo patrón mental que separa un SSRF real de una petición propia.

De cara al examen: Carlos remarca que el bypass de whitelist con user-info es **contenido de nivel alto**, más útil para el trabajo real que para un eJPT.

# **8. Introducción a SSTI (anunciada) y pendiente de la sesión**

Tras cerrar SSRF, Carlos anuncia el siguiente bloque: **SSTI** (Server-Side Template Injection). El plan es verlo primero con laboratorios de PortSwigger y, si da tiempo, con un entorno más realista tipo Hack The Box (aunque no tengáis licencia, para verlo en contexto). Se describe como una vulnerabilidad "que se ve muy rápido" y que depende de un par de factores.

| **ℹ Pendiente de confirmar**  En el material aportado, la parte práctica de SSTI **no llega a desarrollarse**: la grabación cierra tras el tercer lab de SSRF y el descanso. Cuando dispongas de la transcripción de la parte de SSTI, se generará su apunte propio. |
| --- |

También queda anunciada una **clase de repaso el viernes** para resolver dudas y, posiblemente, un laboratorio guiado por fases sobre el formato de URL y el bypass de whitelist.

# **9. Resumen final**

SSRF consiste en **forzar al servidor a pedir una URL que controlamos**, usándolo de intermediario hacia la red interna. La detección es siempre la misma: una llamada a URL en un parámetro o cabecera. Lo que cambia entre labs es la **calidad del filtro** y, por tanto, el bypass necesario.

Los tres labs de hoy escalan en dificultad: **(1)** blacklist, que se rompe con representaciones alternativas de la loopback (127.1) y encoding de palabras filtradas (%61dmin); **(2)** filtro de solo-URLs-propias, que se encadena con un **Open Redirect** interno para lograr el doble salto; **(3)** whitelist, que se salta abusando del **formato completo de URL** (user-info@host#fragmento) con doble URL-encode del #. La clave transversal: entender el protocolo mejor que el desarrollador y leer bien los errores.

# **10. Checklist de repaso**

1. Sé explicar SSRF con el símil del servidor como "mensajero" hacia la red interna.
2. Detecto un posible SSRF al ver una URL en un parámetro (data) o en una cabecera (Referer, X-Forwarded).
3. Distingo blacklist de whitelist leyendo el código de error.
4. Sé abreviar la loopback: 127.0.0.1 -> 127.1, y verificarlo con ping.
5. Sé encodear una palabra filtrada (admin -> %61dmin) y cuándo aplicar doble encode.
6. Entiendo el encadenado con Open Redirect y por qué debe ejecutarlo el servidor, no yo.
7. Sé construir el bypass de whitelist con user-info (@) + fragmento (#) y colocar /admin al final.
8. Recuerdo revisar la petición completa antes de dudar de la técnica (evitar el error del parámetro duplicado).

# **11. Actualización del registro de herramientas**

Cambios de nivel y conceptos nuevos consolidados en esta sesión (copiable a la base de conocimiento del proyecto):

| **Herramienta / Concepto** | **Nivel** |
| --- | --- |
| Burp Repeater | Practicada |
| Burp Intruder | Practicada |
| Burp Decoder/Inspector (URL-encode/decode) | Practicada |
| SSRF (Server-Side Request Forgery) | Practicada |
| Bypass de blacklist (loopback alterna + encoding) | Introducida |
| Open Redirect encadenado en SSRF | Introducida |
| Bypass de whitelist (user-info @ + fragmento #) | Introducida |
| SSTI (Server-Side Template Injection) | Mencionada |
