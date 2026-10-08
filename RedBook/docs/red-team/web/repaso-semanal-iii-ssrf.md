---
tags:
- Auditoría web
---

# Repaso Semanal III SSRF

**EVOLVE ACADEMY · MÁSTER EN CIBERSEGURIDAD OFENSIVA**

**Repaso Semanal III — SSRF**

Instructor: Carlos Castillo · 24/07/2026

*Sesión de repaso (viernes) · Server-Side Request Forgery · Laboratorios PortSwigger*

| **ℹ Contexto del día**  Sesión de repaso semanal centrada en cerrar el bloque de **SSRF** (Server-Side Request Forgery). Se repasó la teoría y los tipos de bypass, y se resolvieron en directo dos laboratorios de PortSwigger: *bypass por open redirect* y *bypass de whitelist*. Al final se anunció **SSTI** (Server-Side Template Injection) como tema de la semana siguiente. |
| --- |

# **Objetivos de la sesión**

- Consolidar el concepto de **SSRF**: usar el servidor web como intermediario para acceder a recursos internos que no están expuestos a Internet.
- Repasar los **tipos de SSRF y sus bypasses**: contra localhost, contra el back-end interno, bypass de blacklist, bypass por open redirect y bypass de whitelist.
- Practicar la **metodología** de detección: identificar un parámetro que reciba una URL y que la resuelva el servidor.
- Resolver el laboratorio *SSRF with filter bypass via open redirection*.
- Resolver el laboratorio *SSRF with whitelist-based input filter bypass*, entendiendo la **anatomía de una URL** y el abuso de userinfo y del **fragmento** (#).
- Interiorizar que el hacking es **prueba y error** y que se avanza poco a poco leyendo los errores del servidor.

# **Conceptos clave**

## **¿Qué es un SSRF?**

El **SSRF** (Server-Side Request Forgery) consiste en abusar de una aplicación web para que sea **el propio servidor** quien realice una petición a un recurso, normalmente **interno**, al que nosotros no podríamos llegar directamente desde fuera. El servidor actúa de *mensajero* o *cabeza de turco*: hace la llamada por nosotros y nos devuelve el resultado.

Desde fuera, un atacante no puede acceder al localhost del servidor ni a su red interna: si pudiera, no habría red interna ni seguridad. Con un SSRF, en cambio, aprovechamos un parámetro que recibe una URL y que el servidor abre por su cuenta, alcanzando así servicios internos.

| **⚠ No confundir con pivoting**  Es muy raro poder acceder a recursos internos a través de una web expuesta a Internet. Cuando ocurre, casi siempre es por un SSRF (u otro contexto concreto de la aplicación). No confundir con *pivoting* u otras vulnerabilidades similares: aquí lo específico es que **la petición la lanza el servidor**, no nuestro navegador. |
| --- |

## **El modelo mental: atacante → servidor → red interna**

| **1. Atacante (nuestro navegador / Burp Repeater)** |
| --- |

**↓**

| **2. Servidor web expuesto a Internet (hace la petición POR nosotros)** |
| --- |

**↓**

| **3. Red interna: localhost, back-end, paneles, servicios sin exposición** |
| --- |
| **ℹ Ampliación (ejemplo del instructor)**  Analogía de clase: si Evolve tuviera un servicio contable accesible solo desde la oficina (por WiFi o cable), estar *dentro de la red* es lo que da acceso. El SSRF te mete *dentro* usando el servidor como puente, igual que un Red Team busca colarse físicamente para engancharse a la red interna. |

## **La señal que dispara la alerta de SSRF**

Cuando en una petición (por ejemplo, en el parámetro stockApi de un POST) vemos que el valor es **una URL** que el servidor va a abrir, se deben encender todas las alarmas de posible SSRF. Truco de lectura: aunque no aparezca http:// de forma explícita (puede estar *hardcodeado* por detrás), si ves **directorios / rutas** dentro del valor, trátalo como una URL. Conviene quitar el *URL-encode* (Decoder) para verlo claro.

# **Tipos de SSRF y bypasses (repaso)**

Carlos repasó los distintos casos, del más sencillo al más complejo. La idea no es memorizarlos todos, sino saber **hasta dónde se puede forzar** y reconocer el patrón.

## **1. SSRF básico contra el servidor local (localhost)**

Sin ninguna validación: allí donde aparezca la URL (en un parámetro GET, en la data de un POST como stockApi, o en una cabecera tipo Referer), se sustituye por localhost o por una IP interna. Es el caso más fácil.

| **⚠ Consejo sobre cabeceras**  En cabeceras (Referer, etc.) no te compliques salvo que lo veas muy claro. No suele merecer la pena. |
| --- |

## **2. SSRF contra el back-end interno (descubrimiento)**

Cuando localhost no da nada, se busca la **red interna** (p. ej. 192.168.0.x). Se usa **Burp Intruder** como si fuera un *Netdiscover / Nmap*: se fuzzea el último octeto de la IP (1–254) para descubrir hosts con servicio web, y después los puertos web probables.

| **⚠ No fuerces la máquina**  Con SSRF solo descubrirás lo que hable **HTTP/HTTPS**: el SSRF te limita a servicios web, no a otros protocolos. Y ojo: no lances los 65.535 puertos como con Nmap; no fuerces la máquina. Móntate un **diccionario de puertos web probables** (1.000–3.000) descartando los típicos no-web (22, 21, 23, 53, 445...). Ese diccionario lo puedes generar con IA. |
| --- |
| **ℹ Corrección de transcripción**  En clase se mencionó apoyarse en **Claude / Claude Code** para generar el diccionario de puertos (transcrito como *"cloud decode"* / *"cloud"*). Para un simple diccionario basta con Claude normal. |

## **3. Bypass de blacklist**

La aplicación bloquea *palabras malas* concretas (admin, localhost, 127.0.0.1...). Como es una lista de lo prohibido, tenemos mucho margen. Técnicas vistas:

- Abusar de representaciones de 127.0.0.1: recortar ceros o dejarlo como 127.1.
- Acortar rangos internos: 192.168.0.x admite formas reducidas (el 0 se da por hecho).
- **URL-encoding** de caracteres que filtran (normalmente 1 o 2). Sin abusar.
- **Doble URL-encoding** si con uno no basta (probar de forma incremental).

| **⚠ Error común**  No abuses del URL-encode 200 veces: no tiene sentido. Como mucho, un mini-diccionario que pruebe de 1 a 100 niveles de codificación como último recurso. |
| --- |

## **4. Bypass por open redirect**

Se usa cuando el filtro obliga a que la URL sea **de la propia aplicación** (no permite una URL externa). La jugada: encontrar dentro de la app un endpoint que haga un **redirect** y aprovecharlo, porque el servidor valida lo primero (que la URL es interna) pero **no comprueba** que esa URL interna redirige a otro sitio.

| **ℹ Ampliación (ejemplo del instructor)**  Los **open redirect** son muy valiosos también fuera del SSRF. En Red Team / phishing, un redirect dentro de un dominio legítimo (p. ej. https://repsol.es/gasolineras/promociones?pais=...) hace que el enlace muestre de primeras el dominio real (favicon, nombre, dominio correcto) y luego redirija al sitio malicioso. Por eso muchos ataques empiezan buscando open redirects en la fase de reconocimiento. *Ejemplo ilustrativo del instructor; Repsol se usó solo como ejemplo, no es un objetivo real.* |
| --- |

## **5. Bypass de whitelist**

El caso más difícil. El filtro obliga a que la URL **contenga sí o sí** un host concreto (p. ej. stock.weliketoshop.net). Aquí no vale un open redirect si no tenemos acceso para encontrarlo, así que hay que **bypassear la whitelist** entendiendo a fondo la **anatomía de una URL** y abusando de userinfo (@) y del **fragmento** (#). Se desarrolla en el Lab 2.

| **✓ Perspectiva de auditoría real**  Carlos insistió: hay ~6 tipos/casos de SSRF, pero lo importante no es que *siempre* aparezcan estos casos exactos. En una auditoría real es habitual encontrar SSRF básicos **sin validación**, porque muchos desarrolladores ni conocen la vulnerabilidad. Quédate con el concepto y la metodología, no con el miedo a los casos difíciles. |
| --- |

# **Lab 1 — SSRF with filter bypass via open redirection**

Laboratorio de PortSwigger resuelto en directo (con Chema). Entorno: tienda web; comprobación de stock mediante el parámetro stockApi en una petición POST.

## **Metodología aplicada**

| **1. Tocar botones: identificar la funcionalidad 'check stock'** |
| --- |

**↓**

| **2. Interceptar en Burp y enviar al Repeater (Ctrl+R)** |
| --- |

**↓**

| **3. Ver que stockApi contiene una URL que resuelve el servidor → posible SSRF** |
| --- |

**↓**

| **4. Probar localhost → BLOQUEADO: 'external stock check' / URL inválida** |
| --- |

**↓**

| **5. Buscar un endpoint interno con redirect (botón 'siguiente producto')** |
| --- |

**↓**

| **6. Reapuntar el redirect al back-end interno: 192.168.0.12:8080/admin** |
| --- |

**↓**

| **7. Accion final: eliminar al usuario 'carlos'** |
| --- |

## **Paso a paso**

1. Detectar la funcionalidad: el botón **Check stock** dispara un POST cuyo parámetro stockApi es una URL que **abre el servidor** (no el navegador). Esa es la señal de SSRF.
2. Comprobar que la URL interna original funciona: el valor por defecto apunta a una ruta de la propia tienda (barra product/stock) y el dominio está *hardcodeado* por detrás. Devuelve el stock (un número).
3. Probar localhost: el servidor responde que solo admite URLs **de la propia aplicación** (no externas). Es una **whitelist** de que la URL debe ser interna a la app.
4. Buscar un **redirect** dentro de la app: el enlace de **'siguiente producto'** contiene una URL válida de la aplicación que, además, hace un redirect mediante un parámetro path.
5. Copiar ese endpoint en stockApi y cambiar el destino del redirect al **back-end interno**. Se descubre el host interno con Intruder (fuzzing de 192.168.0.1-254; responde el .12) y el puerto web (8080).
6. Alcanzar el panel: 192.168.0.12:8080/admin → el servidor abre esa ruta interna. Acción final: eliminar al usuario carlos.

| **ℹ Fidelidad**  Comandos/payloads en una sola línea. Los nombres exactos de los parámetros de redirect (currentProductId, path) provienen del **propio enlace de la aplicación** visible en Burp, no de memoria: verifícalos en la respuesta antes de reusarlos. |
| --- |
| # Valor por defecto (interno, valido): comprobacion de stock de la tienda  stockApi=/product/stock/check?productId=1&storeId=1    # Intento directo (BLOQUEADO por el filtro de whitelist interna):  stockApi=http://localhost/admin    # Endpoint interno con open redirect (enlace 'siguiente producto'):  stockApi=/product/nextProduct?currentProductId=1&path=http://192.168.0.12:8080/admin    # Accion final: eliminar al usuario carlos via el redirect  stockApi=/product/nextProduct?currentProductId=1&path=http://192.168.0.12:8080/admin/delete?username=carlos |
| **ℹ Intruder: descubrimiento de red**  Descubrimiento del back-end con Burp Intruder: marca el octeto variable de la IP como posición, usa el payload numérico **1–254** (step 1) y filtra por código de estado. Un 404 es buena señal (llegaste al puerto pero la ruta no existe); un 200 en /admin es el objetivo. Para IP + puerto a la vez se usa **Cluster bomb** con dos listas. |

# **Anatomía de una URL (base del Lab 2)**

Para bypassear una whitelist hay que conocer todas las partes de una URL. El esquema completo es:

| esquema://[userinfo@]host[:puerto][/ruta][?query][#fragmento]    ejemplo: http://user:pass@panel.academics.es:8080/admin?id=1#seccion |
| --- |
| **Parte** | **Qué es** | **Notas** |
| Esquema / protocolo | http o https | Es un protocolo, como SSH; también se puede 'hackear' a este nivel. |
| userinfo | usuario:contraseña@ | Opcional. Autenticación básica; termina en @. Aquí está el truco del Lab 2. |
| host | Dominio o IP | Lo que la whitelist obliga a que aparezca (stock.weliketoshop.net). |
| puerto | :8080 | Opcional. Servicio web interno probable. |
| ruta | /admin | Se mantiene siempre tras el host/puerto (posición fija). |
| query | ?username=carlos | Parámetros de la petición. |
| fragmento | #seccion | Nunca se envía al servidor: es como un comentario/nota interna. |
| **ℹ El fragmento (#)**  El **fragmento** (#) es la clave: funciona como un *comentario* (similar a un comentario en SQL). Todo lo que va a su derecha se omite. Se usa mucho en *landing pages* para navegar por secciones sin recargar (la página ya está cargada); si intentas capturarlo en Burp, no viaja nada. |

# **Lab 2 — SSRF with whitelist-based input filter bypass**

Mismo entorno (tienda, stockApi en POST). El filtro exige que la URL **contenga** el host stock.weliketoshop.net. Como ese host es interno (ni siquiera es accesible desde el navegador), no podemos encontrar un open redirect dentro de él: la única vía es **bypassear la whitelist** rompiendo el *parser* de la URL.

## **Razonamiento**

1. El filtro obliga a que aparezca stock.weliketoshop.net en la URL (whitelist).
2. Queremos que la petición **real** vaya a localhost/admin, pero que la validación **vea** el host permitido.
3. Colocamos stock.weliketoshop.net de forma que el validador lo detecte como host, y anteponemos localhost con un **fragmento** (#) para que, al resolver, el servidor apunte realmente a localhost e ignore lo que va tras #.
4. El # solo no cuela (rompe demasiado la URL): hay que **URL-encodearlo**. Con un solo encode no funciona; con **doble encode** (%2523) sí.

| **⚠ Payload de whitelist**  Estructura conseguida: localhost + # (doble-encodeado) + @stock.weliketoshop.net + /admin. El validador lee stock.weliketoshop.net como host (whitelist OK); al hacer la petición, el # marca el inicio del fragmento y el destino efectivo es localhost, conservando la ruta /admin. |
| --- |
| # 1) # simple: la URL es valida pero el servidor la rechaza (rompe demasiado)  stockApi=http://localhost#@stock.weliketoshop.net/admin    # 2) # con un solo URL-encode (%23): sigue sin colar  stockApi=http://localhost%23@stock.weliketoshop.net/admin    # 3) # con DOBLE URL-encode (%2523): OK -> acceso a /admin  stockApi=http://localhost%2523@stock.weliketoshop.net/admin    # 4) Accion final: eliminar al usuario carlos  stockApi=http://localhost%2523@stock.weliketoshop.net/admin/delete?username=carlos |
| **ℹ userinfo = autenticación básica**  Sobre userinfo: recuerda que user:pass@host es autenticación básica. Ejemplo mostrado: un login HTML sencillo en panel.academics.es al que se entra con http://test:hola123@panel.academics.es. En el bypass, localhost ocupa el lugar del userinfo respecto al host permitido. |
| **ℹ Atajos de Burp**  Atajos de Burp usados: **Ctrl+R** enviar al Repeater · **Ctrl+U** URL-encode · **Ctrl+Shift+U** URL-decode (Decoder). Con clic derecho aparecen todos los *shortcuts*. |
| **⚠ Error común: saltos de línea**  Al copiar payloads desde el Bloc de notas, borra los **saltos de línea**: Burp los detecta y da error (aparecía como error en las líneas 7-8 de la petición). Codifica solo lo que el servidor no acepta, no la URL entera 'por si acaso'. |

# **Herramientas utilizadas en la sesión**

| **Herramienta** | **Objetivo** | **Fase** | **Uso visto** | **Nivel** | **Notas** |
| --- | --- | --- | --- | --- | --- |
| Burp Repeater | Reenviar y modificar peticiones | Explotación web | Ctrl+R; probar payloads en stockApi | Practicada | Núcleo del trabajo con SSRF |
| Burp Intruder | Descubrir red/puertos internos | Enumeración interna | Payload numérico 1-254; Cluster bomb | Practicada | Actúa como Netdiscover/Nmap vía SSRF |
| Burp Decoder | URL-encode / decode | Explotación web | Ctrl+U / Ctrl+Shift+U; doble encode %2523 | Practicada | Clave para el bypass de whitelist |
| Burp Proxy | Interceptar y reenviar (Forward) | Explotación web | Editar petición interceptada y Forward | Practicada | Comprobaciones 'en directo' en el navegador |
| draw.io | Diagramar el flujo del ataque | Documentación | Diagrama atacante→servidor→red interna | Introducida | Apoyo visual del repaso |
| Claude / Claude Code | Generar diccionario de puertos web | Enumeración (apoyo) | Pedir lista de puertos web probables | Mencionada | Para diccionarios basta Claude normal |
| **ℹ Solo mencionadas**  Dirsearch y Netdiscover/Nmap se mencionan como referencia conceptual (fuzzing de rutas y descubrimiento de red), pero no se ejecutan en esta sesión. |

# **Conexión con sesiones anteriores**

- **Path Traversal**: mismo problema de 'a saber dónde buscar'. En SSRF exploras IPs/puertos internos igual que allí buscabas archivos del sistema; en ambos casos toca investigar y probar.
- **Burp Intruder**: ya visto para fuzzing; aquí se reutiliza como escáner de red interna (IPs y puertos) a través del SSRF.
- **Open redirect**: el mismo concepto que en phishing/Red Team se aplica ahora como pieza de un SSRF (Lab 1).
- **Codificación (URL-encode)**: técnica ya usada en el bypass de blacklist; en whitelist se lleva al **doble encode**.
- **Metodología web**: la rutina de 'tocar botones → interceptar → Repeater → razonar' es la misma que en el resto del bloque web.

# **Resumen final**

Un **SSRF** convierte al servidor en nuestro intermediario para alcanzar recursos internos. La detección es siempre igual: un parámetro que recibe una **URL** que **resuelve el servidor**. A partir de ahí, la metodología va de lo simple a lo complejo: localhost → back-end interno (Intruder) → bypass de blacklist → bypass por **open redirect** (Lab 1, reapuntando un redirect interno a 192.168.0.12:8080/admin) → bypass de **whitelist** (Lab 2, abusando de la anatomía de la URL con userinfo y **fragmento** # **doble-encodeado**, %2523). Lo esencial no es memorizar casos, sino entender el concepto y avanzar con **prueba y error**, leyendo los errores del servidor. En auditorías reales, los SSRF sin validación son más frecuentes de lo que parece.

# **Checklist de repaso**

1. ¿Sé explicar el SSRF como 'el servidor hace la petición por mí' (atacante → servidor → red interna)?
2. ¿Detecto la señal? Un parámetro (p. ej. stockApi) cuyo valor es una URL que abre el servidor.
3. ¿Pruebo primero localhost y leo el error (validado / bloqueado / puerto cerrado)?
4. ¿Uso Intruder (1-254 + diccionario de puertos web) para descubrir el back-end sin forzar la máquina?
5. ¿Reconozco cuándo aplica cada bypass: blacklist, open redirect o whitelist?
6. ¿Sé desglosar una URL: esquema, userinfo, host, puerto, ruta, query y fragmento?
7. ¿Recuerdo el payload de whitelist con # doble-encodeado (%2523)?
8. ¿Codifico solo lo necesario y borro los saltos de línea al pegar payloads?

# **Actualización del registro de herramientas**

Cambios de nivel respecto al registro acumulado (copiar a la base de conocimiento del proyecto):

| **Herramienta** | **Nivel** |
| --- | --- |
| Burp Suite — Repeater | Practicada |
| Burp Suite — Intruder (Sniper / Cluster bomb) | Practicada |
| Burp Suite — Decoder (URL-encode / decode, doble encode) | Practicada |
| Burp Suite — Proxy (intercept / Forward) | Practicada |
| draw.io | Introducida |
| Claude / Claude Code (apoyo: diccionarios) | Mencionada |

# **Próximos temas (en el horizonte)**

- **SSTI — Server-Side Template Injection** vía PortSwigger: anunciado para la semana siguiente. *Se complica más en detectar la tecnología que en explotar la vulnerabilidad.* Pendiente de desarrollar.
- Cierre del bloque **web** y repaso de metodología completa (de cara a septiembre).
- A la vuelta: **Hack The Box**, ruta **eJPTv2 → OSCP**, **Blue Team** con Edu y **Directorio Activo**.

| **ℹ Pendiente / logística**  Recordatorio administrativo: la **Práctica 1** se publicará en el apartado de evaluación (pendiente de que Miquel lo habilite), con plazo durante el verano. Confirmar horarios de la próxima semana (lunes 18:00, martes 18:00, miércoles 16:00, provisionales). |
| --- |

# **Actualización de memoria del proyecto**

| **Campo** | **Valor** | **Certeza** |
| --- | --- | --- |
| Sesión | Repaso Semanal III — SSRF | Alta |
| Instructor | Carlos Castillo | Alta |
| Fecha | 24/07/2026 (viernes) | Alta |
| Tema / bloque | SSRF (repaso y cierre) | Alta |
| Laboratorios | PortSwigger: bypass por open redirect y bypass de whitelist | Alta |
| Herramientas practicadas | Burp Repeater, Intruder, Decoder, Proxy | Alta |
| Técnicas web nuevas | Doble URL-encode (%2523), abuso de userinfo y fragmento (#) | Alta |
| Descubrimiento interno | Back-end en 192.168.0.12:8080/admin (Lab 1) | Media |
| Correcciones de transcripción | Claude/Claude Code (‘cloud decode’), Burp (‘Buró/Bour’), SSRF (‘SCRF’), SSTI (‘SCTI/STI’), Nmap, Netdiscover, Dirsearch, draw.io, Red Team (‘Revting’) | Alta |
| Tema pendiente | SSTI (Server-Side Template Injection) — anunciado, no desarrollado | Alta |
| Conexión con sesiones previas | Path Traversal, Intruder/fuzzing, open redirect, URL-encoding, metodología web | Alta |
| RedNotes Academy | Sin novedades en esta sesión | Alta |
| **✓ Bloque copiable**  Bloque para memoria acumulativa (texto plano): SSRF cerrado el 24/07/2026 con Carlos Castillo en la sesión 'Repaso Semanal III'. Resueltos dos labs de PortSwigger: (1) bypass por open redirect reapuntando el enlace 'nextProduct' a 192.168.0.12:8080/admin; (2) bypass de whitelist con http://localhost%2523@stock.weliketoshop.net/admin (fragmento # doble-encodeado). Herramientas practicadas: Burp Repeater/Intruder/Decoder/Proxy. Próximo tema anunciado: SSTI vía PortSwigger. |
