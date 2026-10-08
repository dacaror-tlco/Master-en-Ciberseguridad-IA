---
tags:
- Máquinas y prácticas
---

# Repaso Metodologia Web SSTI CasaPaco

**EVOLVE ACADEMY · MÁSTER EN CIBERSEGURIDAD OFENSIVA**

**Repaso General: Metodología Web**

Cierre del bloque SSTI · Laboratorios PortSwigger · Máquina Casa Paco (TheHackerLabs)

Instructor: Carlos Castillo · 28/07/2026

# **1. Objetivos de la sesión**

- Cerrar el bloque de **SSTI** (Server-Side Template Injection): detección, identificación del motor de plantilla y explotación.
- Repasar con calma los **dos primeros laboratorios de SSTI de PortSwigger** (motor ERB/Ruby y motor Tornado/Python).
- Repasar la **metodología web completa** con la máquina **Casa Paco** de TheHackerLabs, una máquina muy sencilla pensada para practicar el método, no la dificultad.
- Aprender a **mapear cada paso práctico a las etapas de una auditoría** (norma fija del proyecto a partir de esta sesión).
- Interiorizar una idea clave: **no complicarse la vida**; muchas veces lo fácil (command injection simple, credenciales expuestas, fuerza bruta) resuelve la máquina.

# **2. Etapas de una auditoría (marco de referencia)**

Desde esta sesión, todo trabajo práctico se organiza y se etiqueta según las **etapas de una auditoría**. Sirven como hilo conductor para no perderse y para documentar de forma ordenada.

| **1. Planificación** |
| --- |

**↓**

| **2. Recogida de información** |
| --- |

**↓**

| **3. Análisis de vulnerabilidades** |
| --- |

**↓**

| **4. Pruebas de explotación controladas** |
| --- |
| **Etapa** | **En qué consiste** | **Ejemplo en esta sesión** |
| Planificación | Definir alcance, objetivos y reglas del ejercicio. | Confirmar que Casa Paco es una máquina de laboratorio autorizada. |
| Recogida de información | Descubrir hosts, puertos, servicios, dominios y superficie de ataque. | netdiscover, ping, nmap, virtual hosting (/etc/hosts). |
| Análisis de vulnerabilidades | Revisar la aplicación e identificar debilidades explotables. | Enumeración web, directory listing, blacklist de caracteres, dirsearch. |
| Pruebas de explotación controladas | Explotar de forma controlada para demostrar el impacto. | Command injection, lectura de /etc/passwd, fuerza bruta SSH con Hydra. |
| **ℹ Contexto de auditoría**  La infografía de referencia distingue además: **Tipos de auditoría** (interna o externa, técnica u organizativa); **Herramientas y metodologías** (OWASP, Nessus, Nmap, informes de evidencias); y **Normativas y protección** (cumplimiento, infraestructura y datos). Estos bloques dan contexto formal a lo que hacemos en el laboratorio. |

# **3. Conceptos clave — SSTI (Server-Side Template Injection)**

**SSTI** ocurre cuando una entrada del usuario (un mensaje, un comentario, el *nombre de perfil*…) se refleja dentro de una **plantilla que se procesa en el servidor**, sin sanitización adecuada. Al no validarse, podemos inyectar la sintaxis del motor de plantilla y hacer que la ejecute.

Ejemplo de la lógica: una plantilla montada como *«Hola, {nombre}»* debería devolver Hola Carlos. Si es vulnerable, en vez del nombre podemos conseguir que evalúe una expresión (49 a partir de 7\*7) o, en el peor caso, un **RCE** (ejecución de comandos).

## **Motor de plantilla ≠ lenguaje**

Hay que distinguir dos cosas: el **lenguaje** (Ruby, Python…) y el **motor de plantilla** que corre por detrás (ERB, Tornado, Jinja2, Mako, Freemarker…). Identificar el motor es lo que determina la sintaxis exacta que hay que inyectar.

| **⚠ AVISO**  Un mismo lenguaje puede tener varios motores. No te centres solo en los motores conocidos: pueden aparecer otros o salir nuevos. La lógica de detección es siempre la misma. |
| --- |

## **Las 3 fases del SSTI**

Dentro de las etapas de auditoría, el SSTI se trabaja sobre todo en **Análisis de vulnerabilidades** (fases 1 y 2) y en **Pruebas de explotación controladas** (fase 3):

1. **Indicio (detección)**: ver que una entrada mía se refleja en algún sitio (un Hola, nombre dinámico). Es la primera toma de contacto — «aquí me cuadra que pueda haber un SSTI».
2. **Identificación del motor/tecnología**: averiguar qué motor hay por detrás (ERB, Tornado, Jinja2…).
3. **Explotación**: una vez conocido el motor, inyectar la sintaxis concreta para conseguir la evaluación de expresiones o el RCE.

## **Cómo identificar el motor**

No tiene sentido probar un solo payload: puede salir o no. Tenemos varias vías, de menos a más ruido:

- **Cadena poliglota (polyglot)**: una única cadena que combina la sintaxis de muchos motores (la «navaja suiza»). Al inyectarla, el motor **devuelve todo menos los caracteres que sí interpreta**. Si en la salida desaparece <% y %>, el motor es **ERB (Ruby)**.
- \**Payload de prueba `{{7*7}}\*\* (genérico) o su variante por motor. Si aparece 49`, el motor ha evaluado la expresión.
- **Fuzzing con diccionario** (por ejemplo SecLists de SSTI) en **Burp Intruder**: se compara por código de estado o por longitud de respuesta para ver qué payload cuela.
- **Forzar un error**: los errores son oro. Suelen revelar el lenguaje/motor (Python 2.7, Tornado application, framework, etc.).
- **Pistas de Nmap**: a veces indica un servidor de Python → el motor será alguno de Python (habrá que acotar: Tornado, Jinja2, Mako…).

| **ℹ Cómo pensar la detección**  Analogía del profesor: el motor solo «come» su propia sintaxis. Si le das su plato (hamburguesa) lo procesa; si le metes un brócoli (caracteres ajenos), te lo escupe (los devuelve tal cual). Por eso el polyglot deja ver qué sintaxis pertenece a cada motor. |
| --- |

## **Payloads básicos por motor**

| {{7\*7}} # generico (Jinja2, Twig, Tornado...) -> 49  ${7\*7} # otra variante generica  <%= 7\*7 %> # ERB (Ruby) -> 49 |
| --- |
| **ℹ Ampliación — polyglot de detección**  Cadena poliglota estándar de PortSwigger/HackTricks para la fase de identificación (ampliación, no dictada literalmente en clase, pero es la referencia habitual): |
| ${{<%[%'"}}%\ |

# **4. Laboratorio 1 de PortSwigger — motor ERB (Ruby)**

**Fase de auditoría: Análisis de vulnerabilidades → Pruebas de explotación controladas.** Es el caso más sencillo y sirve para fijar la base.

El laboratorio parte de una petición **GET** con un parámetro (un mensaje del tipo *out-of-stock*). Ese parámetro se refleja directamente y **no hay ninguna expresión de plantilla envolviéndolo** ni al principio ni al final: nadie abre ni cierra la expresión por nosotros.

1. Detecto el indicio de SSTI en el parámetro reflejado.
2. Inyecto la cadena poliglota → me devuelve todos los caracteres **menos** <% %> ⇒ el motor es **ERB (Ruby)**.
3. Como no hay expresión envolvente, **borro el valor original e inyecto directamente** mi expresión.
4. Confirmo con <%= 7\*7 %> → obtengo 49.

A partir de ahí, la explotación depende del lenguaje. En Ruby/ERB podemos ir a RCE (system) o a lectura de archivos (File.open), que actúa como un **mini path traversal** (leer archivos sin ejecutar comando directo).

| **✓ CORRECTO**  El laboratorio 1 es fácil porque la inyección es directa: sin plantilla previa que cerrar. El salto de dificultad viene en el laboratorio 2. |
| --- |

# **5. Laboratorio 2 de PortSwigger — motor Tornado (Python) con Burp**

**Fase de auditoría: Recogida de información (superficie de la app) → Análisis de vulnerabilidades → Pruebas de explotación controladas.**

## **Superficie de la aplicación**

Un blog con: Home, My account (login) y Post (?postId=1). En cada post hay **comentarios**, y en My account se puede editar el *preferred name* (first name, nickname, username). El comentario refleja el nombre elegido ⇒ **indicio de SSTI** en user.name / user.nickname / user.first\_name.

| **⚠ AVISO**  Al comentar sin loguear, el nombre aparece como *anonymous*. Para ver el reflejo hay que estar logueado (usuario **wiener**) y que el post/comentario sea nuestro: no podemos cambiar el display de posts de Daisy, Andy o Anonymous. |
| --- |

## **Detección con Burp (forzar el error)**

Se intercepta con Burp la petición POST de My account que cambia el display del autor (blog-post-author-display = user.name). Si en vez de un valor normal metemos algo que rompa la expresión, el motor falla y el **error nos da la tecnología**:

| **ℹ El error como fuente de información**  El error revela **Python 2.7** y **Tornado application** ⇒ estamos ante un SSTI con el motor **Tornado**. Consejo del profesor: pega el error en un buscador o en la IA y te confirma la vulnerabilidad y el motor. Esto vale hasta para el OSCP. |
| --- |

## **La clave: la expresión ya viene puesta por el servidor**

La variable llega envuelta por el back end como {{ user.name }}. Las llaves {{ y }} **las pone el servidor**, no nosotros. Por eso, meter {{7\*7}} completo dentro rompe: sería una expresión dentro de otra expresión.

Hay **dos enfoques** para inyectar bien:

- **Enfoque del laboratorio (limitado)**: como el servidor ya aporta las llaves, borro user.name y dejo solo 7\*7. Sale 49. Funciona *si sabemos que no hay más expresiones por detrás*.
- **Enfoque genérico (recomendado)**: **cierro la expresión que hay por detrás y abro una nueva mía**. Así da igual lo que venga después. Es más robusto porque en un entorno real no sabemos cómo es la expresión completa.

| 7\*7 # enfoque del laboratorio (dentro de las llaves del servidor)  }}{{7\*7}} # enfoque generico: cierro la del servidor y abro la mia |
| --- |
| **ℹ Paralelismo con SQLi**  Misma lógica que un **SQL injection** de bypass de login: cerramos la comilla/expresión del back end y añadimos la nuestra. Ej. admin' or 1=1. No sabemos el resto de la consulta, así que la cerramos y controlamos lo que sigue. |

## **De la evaluación al RCE**

Con Tornado/Python, para ejecutar comandos hay que usar la librería os. Como no sabemos si está importada, la importamos en el propio payload:

| {% import os %}{{ os.system('whoami') }} |
| --- |
| **⚠ Errores frecuentes en Tornado**  Cuidado con dos trampas: (1) os puede no estar importado ⇒ hay que importarlo en el payload; (2) una **expresión vacía** {{ }} da error *empty expression*: siempre debe contener un valor válido. Los **espacios** hay que URL-encodearlos o quitarlos. |

## **Objetivo del laboratorio**

El objetivo es borrar el archivo /home/carlos/morale.txt. Con el RCE conseguido:

| {% import os %}{{ os.system('rm /home/carlos/morale.txt') }} |
| --- |
| **✓ CORRECTO**  Al recargar, *Congratulation*: laboratorio resuelto. Lo importante no es el comando final, sino haber entendido: indicio → identificar motor (Tornado) → cerrar y abrir expresión → importar os → ejecutar. |

# **6. Máquina Casa Paco (TheHackerLabs) — metodología web por etapas**

Máquina muy sencilla, elegida para **repasar la metodología** y demostrar que lo simple resuelve. A continuación cada paso va etiquetado con su etapa de auditoría.

## **Etapa 1 — Planificación**

Entorno de laboratorio autorizado (máquina descargada de TheHackerLabs, ejecutada en la VM propia). Alcance: enumerar y explotar de forma controlada la web y el servicio SSH.

## **Etapa 2 — Recogida de información**

Descubrimiento de red y de servicios:

| ifconfig # ver mi IP y el rango de red  netdiscover -r 192.168.0.0/24 # descubrir hosts activos en el /24  ping -c 1 192.168.0.184 # comprobar vida; TTL 64 -> Linux  sudo nmap -p- --min-rate 5000 192.168.0.184 # todos los puertos, rapido  nmap -p 22,80 -sV -sC 192.168.0.184 # versiones + scripts sobre 22 y 80 |
| --- |
| **⚠ Truco de identificación (solo laboratorio)**  En netdiscover, la máquina objetivo se identifica por el fabricante **PCS Systemtechnik GmbH** (OUI de VirtualBox); las máquinas descargadas suelen aparecer así. En un entorno real **no** filtres por ese fabricante. (Corrección de transcripción: «PC Systemic» → PCS Systemtechnik.) |

Resultado: puerto **22 (SSH)** y puerto **80 (HTTP, Apache 2.4.62, Debian)**. La versión de Apache no es vulnerable; no conviene obsesionarse con exploits de versión.

El puerto 80 hace un **redirect a `casapaco.thl`**. Estamos ante *virtual hosting*, así que hay que resolver el dominio en local:

| echo '192.168.0.184 casapaco.thl' | sudo tee -a /etc/hosts |
| --- |
| **ℹ Virtual hosting**  **Virtual hosting**: en la misma IP puede haber una web por IP y otra por dominio. Tras añadir el dominio a /etc/hosts, **relanza Nmap**: ahora resuelve el host y puede sacar el título y más información que antes no veía (por el redirect). |

## **Etapa 3 — Análisis de vulnerabilidades**

Enumeración web metódica de http://casapaco.thl:

- **Wappalyzer / WhatWeb**: visión general (Apache, Debian). Aporta poco aquí.
- **Ctrl+U** (código fuente): puro HTML, sin comentarios de interés.
- **Menú** (menu.html): platos (oreja a la plancha, callos, fabada, cocido madrileño…).
- **Directory listing** en /static (imágenes): eso ya es una **vulnerabilidad** de exposición de directorios.
- **Formulario «comida para llevar»**: parámetros name y dish (plato). Al meter caracteres raros en el plato salta *«no intentes hackearme»* ⇒ hay **validación / blacklist** de caracteres.

| dirsearch -u http://casapaco.thl |
| --- |
| **⚠ Fuzzing con cabeza**  El profesor cancela el dirsearch: en esta máquina no aporta y el **fuzzing es terreno pantanoso** (ruido, bloqueos, diccionario equivocado). En un examen, no satures la web mientras fuzeas; lanza a ritmo normal y con el diccionario adecuado. En una web con PHP, acota por tipo de archivo (.php). |
| **ℹ Dónde está de verdad el fallo**  Con Burp se ve que el campo name **acepta el polyglot sin bloqueo** (no es SSTI), mientras que el campo dish bloquea ;, |, etc. Es decir: la vulnerabilidad no está donde parecía (SSTI), sino en un **command injection**. Lección: prueba primero lo simple. |

## **Etapa 4 — Pruebas de explotación controladas**

La máquina es en realidad un **command injection** (inyección de comandos): un parámetro llama a la terminal por detrás y podemos encadenar comandos con ;.

| ; id # encadenar un comando tras el valor  ; cat /etc/passwd # lectura de usuarios (funciona en llevar1.php) |
| --- |

En llevar.php hay una **blacklist** que bloquea comandos como whoami, ls, pwd, cat, cd (entre otros). Existe un segundo archivo, llevar1.php (estilo CTF), donde sí se permite cat, y con cat /etc/passwd obtenemos los usuarios.

En /etc/passwd aparece un usuario con shell /bin/bash (el **gerente**, pacogerente). Con un usuario válido, pasamos a **fuerza bruta de SSH con Hydra**:

| hydra -l pacogerente -P /usr/share/wordlists/rockyou.txt ssh://192.168.0.184  ssh pacogerente@192.168.0.184 |
| --- |
| **ℹ Sintaxis de Hydra**  Recordatorio de Hydra: -l (minúscula) = **un solo usuario**; -L (mayúscula) = **lista de usuarios**. Igual con -p (una contraseña) y -P (diccionario, aquí rockyou.txt). |
| **ℹ Dato no disponible**  La **contraseña final y la resolución completa no se muestran** en el material de la sesión (el profesor no llega a mostrar la credencial). Queda **pendiente de confirmar**; no se inventa ninguna credencial ni flag. |
| **✓ Lo simple resuelve**  Moraleja de la máquina: no te compliques buscando siempre la vulnerabilidad más difícil (SSTI, SSRF, path traversal). Muchas veces basta con **enumerar bien**, un **command injection** simple, una **credencial expuesta** o **fuerza bruta**. De hecho, la mayoría de los grandes hackeos reales empiezan por credenciales robadas o ingeniería social. |

# **7. Herramientas utilizadas en la sesión**

| **Herramienta** | **Objetivo** | **Fase de auditoría** | **Uso visto** | **Nivel** | **Notas** |
| --- | --- | --- | --- | --- | --- |
| Burp Suite | Interceptar y manipular peticiones | Análisis / Explotación | Interceptar POST, Repeater, Intruder | Practicada | Clave para SSTI y command injection |
| Netdiscover | Descubrir hosts en la red local | Recogida de información | netdiscover -r 192.168.0.0/24 | Practicada | Filtrado por fabricante (VirtualBox) |
| Nmap | Puertos, versiones y scripts | Recogida de información | nmap -p- --min-rate; -p 22,80 -sVC | Recurrente | Relanzar tras editar /etc/hosts |
| Dirsearch | Descubrir rutas web | Análisis de vulnerabilidades | dirsearch -u http://casapaco.thl | Practicada | Aquí se descarta; fuzzing con cuidado |
| Wappalyzer / WhatWeb | Identificar tecnologías web | Análisis de vulnerabilidades | Revisión general del stack | Introducida | Poca info en esta máquina |
| Hydra | Fuerza bruta de credenciales | Pruebas de explotación controladas | hydra -l user -P rockyou ssh://IP | Practicada | -l/-L y -p/-P: único vs lista |
| SecLists | Diccionarios (SSTI, rutas...) | Análisis de vulnerabilidades | Lista SSTI para Intruder | Introducida | Base para fuzzing dirigido |

# **8. Comandos y payloads importantes**

## **SSTI (PortSwigger)**

| {{7\*7}} # prueba generica -> 49  <%= 7\*7 %> # ERB (Ruby)  }}{{7\*7}} # Tornado: cerrar y abrir expresion  {% import os %}{{ os.system('whoami') }} # RCE con Tornado/Python  {% import os %}{{ os.system('rm /home/carlos/morale.txt') }} # objetivo del lab |
| --- |

## **Casa Paco (metodología)**

| netdiscover -r 192.168.0.0/24  ping -c 1 192.168.0.184  sudo nmap -p- --min-rate 5000 192.168.0.184  nmap -p 22,80 -sV -sC 192.168.0.184  echo '192.168.0.184 casapaco.thl' | sudo tee -a /etc/hosts  dirsearch -u http://casapaco.thl  ; cat /etc/passwd  hydra -l pacogerente -P /usr/share/wordlists/rockyou.txt ssh://192.168.0.184  ssh pacogerente@192.168.0.184 |
| --- |
| **ℹ NOTA**  El valor --min-rate 5000 es un ejemplo típico para acelerar el escaneo (ampliación); ajústalo según la red. Todos los comandos van en una sola línea. |

# **9. Riesgos, errores comunes y buenas prácticas**

| **⚠ AVISO**  En SSTI no metas expresión dentro de expresión sin pensar ({{7\*7}} cuando el servidor ya pone {{ }}). Cierra la del back end y abre la tuya para un payload genérico y fiable. |
| --- |
| **⚠ RIESGO**  El **fuzzing** hace ruido y puede bloquearte o tumbar el servicio. Elige bien el diccionario, controla el ritmo y no lo lances «a lo loco» en exámenes o entornos reales. |
| **⚠ AVISO**  No te obsesiones con exploits de versión (más probabilidad de fallo por un cambio mínimo). Déjalo para el final; primero tira del hilo de lo fácil. |
| **✓ CORRECTO**  Buenas prácticas: lleva un **registro** (papel, bloc de notas) de lo revisado (funcionalidades, Ctrl+U, versiones, rutas). Tras editar /etc/hosts, **relanza Nmap**. Mantén el trabajo dentro del alcance autorizado. |

# **10. Conexión con sesiones anteriores**

- **SSTI** cierra el bloque de seguridad web tras **SSRF**, **path traversal**, **LFI** y **XXE**; comparte la lógica de *detectar → identificar → explotar*.
- El **command injection** de Casa Paco enlaza con lo ya visto de inyección de comandos vía ; en la terminal.
- **Hydra** ya se había introducido; aquí se practica contra SSH y se fija la diferencia -l/-L y -p/-P.
- La lógica de **cerrar y abrir la expresión** en SSTI es la misma que el bypass de login por **SQLi** (admin' or 1=1), que se verá a fondo más adelante.
- **Virtual hosting** y /etc/hosts ya aparecieron en auditorías web previas; se repasa el motivo del redirect y el relanzado de Nmap.

# **11. Resumen final**

Sesión de repaso para cerrar la parte técnica de web antes de vacaciones. Se consolidó el **SSTI**: qué es, cómo distinguir motor y lenguaje, cómo detectar el motor (polyglot, {{7\*7}}, fuzzing, errores, pistas de Nmap) y cómo explotarlo, con los dos laboratorios de PortSwigger (ERB/Ruby y Tornado/Python). Con **Casa Paco** se repasó la **metodología web completa**, mapeada a las etapas de auditoría, terminando en un **command injection** y **fuerza bruta SSH con Hydra**. La idea de fondo: dominar el método y no complicarse; lo simple resuelve muchas máquinas.

| **ℹ Pendiente / próximos temas**  Cierre de curso antes del parón: mañana clase con **Carlos Gómez** (práctica y tiempos de entrega). A la vuelta (septiembre) quedan por ver: **CMS**, **File Upload** y **SQL Injection**. Recomendación para el verano: seguir haciendo máquinas e investigar SQLi, CMS y File Upload. |
| --- |

# **12. Checklist de repaso**

1. ¿Sé distinguir motor de plantilla y lenguaje?
2. ¿Sé detectar el indicio de SSTI (entrada reflejada)?
3. ¿Sé identificar el motor con polyglot, {{7\*7}}, fuzzing y errores?
4. ¿Entiendo por qué cerrar y abrir la expresión es más genérico que solo 7\*7?
5. ¿Sé importar os y ejecutar comandos en Tornado?
6. ¿Sé mapear cada paso de Casa Paco a su etapa de auditoría?
7. ¿Sé montar /etc/hosts para virtual hosting y relanzar Nmap?
8. ¿Recuerdo la sintaxis de Hydra (-l/-L, -p/-P)?
9. ¿Interiorizo que lo simple (command injection, credenciales, fuerza bruta) suele bastar?

# **13. Actualización del registro de herramientas**

Cambios de nivel respecto al registro acumulado (copiar a la base de conocimiento):

| **Herramienta** | **Nivel nuevo** |
| --- | --- |
| Hydra | Practicada (antes Introducida) |
| Dirsearch | Practicada |
| SecLists | Introducida |
| Netdiscover | Practicada (antes Introducida) |

# **14. Actualización de memoria del proyecto**

| **Categoría** | **Información nueva** | **Certeza** | **Acción futura** |
| --- | --- | --- | --- |
| Sesión | Repaso General: Metodología Web (cierre SSTI + Casa Paco) | Alta | — |
| Instructor / Fecha | Carlos Castillo · 28/07/2026 | Alta | — |
| Máquina | Casa Paco (TheHackerLabs) | Alta | Máquina de repaso, estilo CTF |
| Vuln. web | SSTI cerrado (ERB/Ruby y Tornado/Python) | Alta | Bloque completado |
| Vuln. web | Command injection en Casa Paco | Alta | Repasar encadenado con ; |
| Comandos | netdiscover -r, nmap -p- --min-rate, hydra -l/-P ssh:// | Alta | Añadir al registro |
| Pendiente | CMS, File Upload, SQL Injection (a la vuelta) | Alta | Investigar en verano |
| Corrección | «PC Systemic» → PCS Systemtechnik; «Hacker Labs» → TheHackerLabs | Alta | — |
| Metodología | Mapear siempre los labs a las etapas de auditoría | Alta | Norma fija del proyecto |
| Dato faltante | Contraseña/flag final de Casa Paco no mostrada | Baja | Pendiente de confirmar con Chema |

## **Bloque para memoria acumulativa (texto plano)**

| Sesion: Repaso General - Metodologia Web (cierre SSTI + Casa Paco)  Instructor: Carlos Castillo | Fecha: 28/07/2026  SSTI cerrado: motor vs lenguaje; deteccion (polyglot, {{7\*7}}, fuzzing, errores, nmap);  explotacion (cerrar+abrir expresion; import os; os.system). Labs PortSwigger: ERB/Ruby y Tornado/Python.  Casa Paco (TheHackerLabs) por etapas de auditoria: netdiscover -> nmap -> /etc/hosts (vhost) ->  enum web (directory listing, blacklist) -> command injection (; cat /etc/passwd) -> hydra SSH.  Hydra practicada; Dirsearch practicada; Netdiscover practicada; SecLists introducida.  Pendiente (septiembre): CMS, File Upload, SQL Injection.  Norma: en los apuntes, mapear siempre los labs a las 4 etapas de auditoria. |
| --- |
