---
tags:
- Máquinas y prácticas
date: '2026-10-07'
author: Carlos Gómez
---

# Nibbles - Apuntes

<p class="note-meta">2026-10-07 · Carlos Gómez</p>

![](../../assets/img/nibbles-apuntes/img001.png)

# Mapa editable de la clase

Dos ramas de una misma clase: el valor profesional de la IA y un laboratorio guiado. Sigue las flechas para ver cómo cada pista se convirtió en una decisión comprobable.

|  |
| --- |
| **IDEA CENTRAL · una pista propone; una prueba observada confirma** |

**↓**

|  |  |
| --- | --- |
| **01 TRABAJO E IA**  Valor del trabajo, alcance y mantenimiento. PLC y agentes: observar prompts, modelos, costes y secretos. | **02 LABORATORIO NIBBLES**  VPN y modo guiado. Chema ejecuta; Carlos plantea preguntas y pide justificar cada decisión. |

**↓**

|  |
| --- |
| **RECORRIDO DE NIBBLES · cuatro fases de auditoría** |

**↓**

|  |  |
| --- | --- |
| **01** | **Planificación** *· ¿Cuál es el alcance?*  Máquina Nibbles, VPN y modo guiado. Chema opera; Carlos orienta y pide justificar cada paso. |

**↓**

|  |  |
| --- | --- |
| **02** | **Recogida de información** *· ¿Qué servicios y rutas existen?*  Ping como indicio → Nmap: 22 y 80 → HTTP y código fuente → pista /nibbleblog/. Se revisan raíz y subruta. |

**↓**

|  |  |
| --- | --- |
| **03** | **Análisis de vulnerabilidades** *· ¿Qué vía cumple requisitos?*  Se descarta Apache como atajo. Nibbleblog y My Image requieren autenticación: content/private, users.xml, admin.php, README y endpoint. |

**↓**

|  |  |
| --- | --- |
| **04** | **Pruebas de explotación controladas** *· ¿Qué quedó demostrado?*  TXT confirma escritura y ruta → solicitar la URL del PHP produce conexión → user.txt → sudo -l y monitor.sh con NOPASSWD → shell root. |

**↓**

|  |  |
| --- | --- |
| **✓ RUTA OBSERVADA**  Se vio la flag de usuario y se llegó a una shell root. No consta lectura de root.txt. | **↶ DESVÍO FINAL**  Metasploit se configuró, pero no abrió sesión; apareció bloqueo temporal. |

Lectura del mapa: cada flecha resume una decisión; los resultados se afirman solo cuando quedaron observados.

Nibbles y la ruta razonada hacia root

Apuntes de la clase del 07/10/2026 · Profesor Carlos Gómez · Máster de Ciberseguridad Ofensiva

# Qué se aprendió en la sesión

Carlos Gómez convirtió Nibbles en un ejercicio de toma de decisiones. Chema operó la máquina y Carlos pidió justificar cada paso: reconocer servicios, mapear rutas, comprobar requisitos de una vulnerabilidad y distinguir una subida de archivo de su ejecución. Se vio la flag de usuario y se obtuvo una shell root. La lectura de root.txt no consta. El tramo previo trató el valor profesional del trabajo con IA y la gobernanza de agentes, separado del laboratorio.

# El contexto antes del laboratorio

## Trabajo profesional y valor de una herramienta

La conversación inicial abordó la participación en un proyecto, la titularidad del trabajo y la diferencia entre construir una herramienta y mantenerla. Carlos insistió en delimitar alcance, horas, coste de implantación, mantenimiento y dependencia de un cliente. Las cifras y ejemplos fueron anécdotas y propuestas del profesor; no constituyen asesoramiento contractual ni precios de referencia.

## IA industrial y gobernanza de agentes

Carlos describió una propuesta para un entorno industrial con PLC, sensores y sistemas HMI o SCADA. Su pregunta central fue de dónde salen los datos, con quién se comunican los componentes y qué tarea concreta podría automatizar un agente. Mostró o explicó un panel de observabilidad que relaciona solicitudes, modelos, tokens, adjuntos, posibles secretos y conexiones de agentes. Presentó la medición de tiempo y coste como argumento para priorizar tareas repetitivas. Son ejemplos expuestos en clase; estos apuntes no validan por sí mismos el despliegue ni las prestaciones de esa solución.

En medio de la sesión, los compañeros felicitaron a Carlos por su cumpleaños. Él agradeció la felicitación y comentó que esperaba la portada de ese día. Esa escena explica el motivo festivo discreto de la ilustración; el contenido técnico empieza después con la elección de Nibbles.

# Preparar y reconocer Nibbles

## Planificación y acceso al laboratorio

Se seleccionó Nibbles en modo guiado y se comprobó la conexión VPN antes de trabajar. Chema llevaba el teclado; Carlos proponía preguntas y corregía inferencias. La colaboración forma parte del método: explicar por qué se sigue una ruta vale más que acertar por casualidad.

## Recogida de información de red

La respuesta a ping y el TTL se usaron como indicios de conectividad y de un posible sistema Linux, sin identificarlo de forma concluyente. El barrido de puertos mostró SSH en 22 y HTTP en 80. Después se buscaron detalles de servicio y versión con los scripts predeterminados y la detección de versiones de Nmap. Un banner o versión orienta la investigación, pero no prueba por sí mismo que un CVE sea explotable en esa instancia.

|  |  |  |
| --- | --- | --- |
| **Uso visto** | **Qué aporta** | **Precaución de interpretación** |
| ping <IP\_LAB> | Comprueba respuesta y muestra TTL. | TTL observado no demuestra el sistema operativo. |
| nmap -p- --open <IP\_LAB> | Revisa los puertos TCP 1 a 65535 y presenta los abiertos. | Un puerto abierto identifica superficie, no vulnerabilidad. |
| nmap -sC -sV -p 22,80 <IP\_LAB> | Ejecuta scripts por defecto y detecta versiones en puertos elegidos. | Interpretar cada salida; los scripts pueden interactuar con el servicio. |

Contraste técnico: la documentación de Nmap sitúa el escaneo predeterminado en los 1.000 puertos más frecuentes por protocolo; -p- cubre 1–65535. Esta corrección evita trasladar una cifra oral inexacta de la grabación.

## Del servicio web al mapa de rutas

HTTP mostró una página mínima. Al mirar su código fuente apareció una pista hacia /nibbleblog/. Carlos frenó el salto inmediato a esa subruta: primero había que auditar la raíz y luego repetir la enumeración sobre la ruta descubierta. Esa secuencia impide que una pista atractiva se convierta en un callejón sin salida y permite relacionar directorios, paneles, plugins y ficheros. En una prueba de curl se escribió dos veces el esquema http://; el error se corrigió y la petición respondió con Hello world!.

En la subruta se reconoció Nibbleblog. La navegación, el listado de directorios, Wappalyzer y la lectura de páginas del CMS ayudaron a construir un mapa: admin.php para autenticarse; content/private con datos internos; plugins y My Image como funcionalidad de interés. Un comentario HTML era una pista de contenido, no una redirección HTTP. Wappalyzer y los banners ayudan a orientar la búsqueda, pero sus resultados requieren comprobación.

# Elegir una vía y comprobar sus requisitos

## Análisis de vulnerabilidades

Se buscaron vulnerabilidades relacionadas con Apache y se descartaron candidatos que no encajaban o no daban una vía útil. La línea prometedora fue una subida de archivos autenticada asociada al plugin My Image de Nibbleblog. Antes de usar una prueba de concepto, Carlos pidió leer su README y código: versión afectada, condición de autenticación, ruta exacta de admin.php, parámetros y archivo que recibe la petición. Una prueba de concepto dirigida al directorio equivocado puede fallar aunque la hipótesis sea válida.

La clase planteó tres posibles caminos para conseguir la cuenta administradora: credenciales predeterminadas, búsqueda de contraseñas y una eventual inyección SQL. En ese punto eran hipótesis, no resultados. La exploración de content/private y users.xml permitió identificar el usuario admin; después se probaron credenciales de laboratorio y se accedió al panel. El audio no ofrece una transcripción estable de la contraseña, por lo que no se fija aquí un literal.

## La exploración del panel

Ya autenticados, revisaron publicaciones, comentarios, temas y plugins. Escribir PHP en una publicación produjo texto mostrado por la aplicación, no ejecución en servidor. Carlos discutió por qué SQLi, XSS o SSTI no aportaban la vía buscada en ese momento. Esta prueba negativa describe el comportamiento observado; no demuestra ausencia general de esas clases de fallo. El recorrido condujo a la configuración del plugin My Image, donde la interfaz ofrecía seleccionar un fichero.

## Prueba de escritura y localización

Antes de introducir código se subió un TXT de prueba. Aunque la aplicación mostró avisos, la exploración posterior encontró el fichero bajo la ruta del plugin. Se separaron así tres afirmaciones: el panel aceptó la acción, el servidor guardó el archivo y se pudo localizar en la estructura expuesta. El mapa construido con anterioridad permitió relacionar la interfaz My Image con content/private/plugins/my\_image. Un aviso de la aplicación no invalida por sí mismo una observación posterior del archivo.

# De la subida a la shell y la flag de usuario

Chema propuso aprovechar la subida para una shell PHP en el entorno autorizado. Carlos prefirió explicar el mecanismo manualmente antes que dejarlo oculto tras un exploit. Se preparó una escucha local y se cargó el archivo. La primera espera no produjo sesión: subir el fichero no lo ejecuta. Tras solicitar en el navegador la URL del archivo almacenado, la conexión apareció en el listener. La página quedó cargando mientras el proceso permanecía activo; la prueba decisiva fue la conexión observada, no el indicador de carga por sí solo.

Con la sesión como usuario nibbler se localizó user.txt. La grabación muestra la lectura de la flag de usuario, pero este documento omite su valor deliberadamente. La ruta seguida muestra la diferencia entre posibilidad de escritura, posibilidad de ejecución, ejecución real y control del proceso resultante.

# Escalada por un script permitido en sudo

El resultado de sudo -l indicó que nibbler podía ejecutar como root, sin contraseña, una ruta concreta terminada en /home/nibbler/personal/stuff/monitor.sh. Se examinó personal.zip y el estado de la ruta y sus permisos. Carlos explicó que controlar el script que sudo ejecuta permite cambiar el comportamiento efectivo de ese comando autorizado. La demostración terminó en una shell root. La regla no se extiende a cualquier entrada de sudo: dependen de la ruta exacta, el fichero y la capacidad real de modificarlo o sustituirlo.

En una segunda explicación se recreó o ajustó el script y se mencionó chmod 777. Ese permiso es excesivo en un sistema real y aquí debe leerse como parte de una demostración en laboratorio, no como buena práctica. La lección defensiva es evitar que un usuario menos privilegiado pueda escribir en un script, en sus directorios padres o en los recursos que ejecuta una regla sudo de root. No consta que se leyera root.txt ni el valor de una segunda flag.

# El desvío de Metasploit y el cierre

Al final se buscó el módulo de Metasploit para la subida del plugin y se ajustaron opciones de destino, URI, credenciales y conexión de retorno. En esta grabación no se obtuvo una nueva sesión por esa vía: aparecieron errores de configuración o autenticación y el mecanismo de bloqueo temporal de Nibbleblog tras varios intentos. Carlos comentó otras posibilidades para una sesión posterior; no son éxitos demostrados hoy. Valoró la máquina por permitir pensar en varias rutas hacia un mismo objetivo.

# Los callejones que dieron información

|  |  |  |
| --- | --- | --- |
| **Desvío o problema** | **Qué se observó** | **Aprendizaje** |
| Buscar un CVE de Apache | Se revisaron candidatos y se aparcaron. | Una versión visible genera una hipótesis, no una explotación demostrada. |
| Saltar a /nibbleblog/ sin revisar la raíz | La pista del comentario parecía suficiente. | El alcance de una auditoría exige mapear la raíz y la subruta. |
| Pegar PHP en un post | La aplicación mostró el texto; no lo ejecutó. | La ubicación donde se almacena una entrada determina su tratamiento. |
| Avisos al subir el TXT | El archivo apareció luego en la carpeta del plugin. | Separar mensajes de interfaz de evidencia observada en el servidor. |
| Esperar una shell tras subir el archivo | No hubo conexión hasta solicitar su URL. | La subida y la ejecución son dos eventos diferentes. |
| Usar Metasploit al final | No se abrió sesión y hubo bloqueo temporal. | Una vía alternativa necesita su propia prueba y su propio resultado. |

# Comandos y resultados interpretados

Los literales siguientes proceden de la transcripción o de pantallas cotejadas. Se omiten la IP, la contraseña, el valor de la flag y el código de shell. Cuando el vídeo no permite leer todos los argumentos, se conserva la función de la herramienta en lugar de completar un comando inventado.

|  |  |  |
| --- | --- | --- |
| **Uso de clase** | **Objetivo y resultado esperado** | **Resultado observado y límite** |
| curl http://<IP\_LAB> | Pedir la página HTTP desde terminal. | Tras corregir un http:// duplicado, respondió Hello world!. No enumera por sí solo toda la aplicación. |
| dirsearch sobre raíz y /nibbleblog/ | Encontrar rutas accesibles y relacionar contenido. | La enumeración contribuyó al mapa del CMS y del plugin; los argumentos exactos no son legibles en la transcripción. |
| Ctrl+U en el navegador | Leer el HTML recibido, incluidos comentarios. | Apareció la pista /nibbleblog/; un comentario no implica redirección del servidor. |
| searchsploit y lectura de README | Identificar pruebas de concepto y sus requisitos. | Se localizaron alternativas; leerlas no demuestra que funcionen en esta instalación. |
| Listener de Netcat | Observar si el archivo PHP inicia una conexión de retorno. | La conexión se vio después de solicitar la URL del archivo; el código concreto no se reproduce. |
| sudo -l | Conocer permisos sudo del usuario nibbler. | Mostró NOPASSWD para una ruta concreta a monitor.sh; no para cualquier script. |
| msfconsole con módulo Nibbleblog | Probar la alternativa automatizada en la máquina del laboratorio. | No creó sesión en el tramo final y surgió un bloqueo temporal. |

# Método que conviene conservar

|  |  |
| --- | --- |
| **01** | **Planificación** *· ¿Qué permiso de práctica hay?*  Nibbles, VPN, modo guiado y reparto de tareas. |

**↓**

|  |  |
| --- | --- |
| **02** | **Recogida de información** *· ¿Qué existe?*  Ping, Nmap, HTTP, código fuente, raíz, subruta y panel. |

**↓**

|  |  |
| --- | --- |
| **03** | **Análisis de vulnerabilidades** *· ¿Qué hipótesis cumple requisitos?*  Descartar Apache como atajo; revisar CMS, plugin, autenticación y endpoint. |

**↓**

|  |  |
| --- | --- |
| **04** | **Pruebas de explotación controladas** *· ¿Qué se demostró?*  TXT almacenado, archivo solicitado, shell, user.txt y root; Metasploit sin éxito. |

- Mapear la raíz aunque un comentario señale una subruta; registrar cada bifurcación y volver al mapa cuando una vía no aporta evidencia.
- Leer el README y el código de una prueba de concepto para comprender sus precondiciones y su punto de entrada.
- Separar hallazgo, hipótesis, prueba y resultado; una subida no equivale a ejecución y una versión no equivale a explotación.
- Guardar las rutas exactas que importan, especialmente cuando sudo concede permisos sobre un único fichero.

# Registro de herramientas

El estado distingue lo que se practicó, lo que se consultó y lo que solo se propuso. Los enlaces abiertos en el navegador se documentan debajo; una dirección impresa por una herramienta o una IP temporal del laboratorio no cuenta como página consultada.

|  |  |  |  |
| --- | --- | --- | --- |
| **Herramienta** | **Objetivo** | **Fase** | **Nivel en esta clase** |
| VPN de HTB | Acceso al laboratorio | Planificación | Practicada |
| ping | Comprobar respuesta y TTL | Recogida de información | Practicada |
| Nmap | Puertos y servicios | Recogida de información | Practicada |
| Firefox, Ctrl+U | Navegación y código fuente | Recogida de información | Practicada |
| curl | Petición HTTP; se corrigió un esquema duplicado | Recogida de información | Practicada |
| Enumerador de rutas | Raíz y /nibbleblog/; nombre dirsearch probable | Recogida de información | Practicada |
| Wappalyzer | Tecnologías orientativas | Recogida de información | Practicada |
| Buscador web | Explorar Apache, CMS y credenciales | Análisis de vulnerabilidades | Practicada |
| Exploit Database | Consultar ficha 38489 | Análisis de vulnerabilidades | Consultada |
| GitHub y Python 3 | Leer y clonar script y README | Análisis de vulnerabilidades | Consultada; sin shell |
| searchsploit | Buscar pruebas de concepto locales | Análisis de vulnerabilidades | Practicada |
| PHP y web shell local | Prueba en post y archivo del plugin | Pruebas de explotación controladas | Practicada |
| Reverse Shell Generator | Seleccionar variante PHP PentestMonkey | Pruebas de explotación controladas | Practicada |
| Netcat | Escuchar la conexión de retorno | Pruebas de explotación controladas | Practicada |
| Shell y sudo -l | Examinar usuario, rutas y privilegios | Pruebas de explotación controladas | Practicada |
| Metasploit / msfconsole | Probar alternativa automatizada | Pruebas de explotación controladas | Practicada sin sesión |
| Burp Suite | Ataque a login sugerido | Análisis de vulnerabilidades | Mencionada; no usada |
| python3 -m http.server y wget | Transferencia alternativa propuesta | Pruebas de explotación controladas | Mencionada; descartada |

También se nombraron Claude, ChatGPT, Supabase, Google API, Google Analytics y Discord en el tramo de IA o como opciones del panel; la transcripción no acredita que se usaran en esta práctica. Apache, PHP, Nibbleblog y My Image son componentes analizados. WordPress, Drupal y Wix fueron comparaciones, no herramientas usadas sobre Nibbles.

# Enlaces que se abrieron durante la clase

URLs recuperadas de la barra del navegador en fotogramas dirigidos del vídeo; F001 por sí sola no contiene URL literales. El minuto indica el momento visible, no una revisión continua de la grabación. Son enlaces de clase, separados de la documentación técnica añadida como contraste.

|  |  |  |
| --- | --- | --- |
| **Recurso abierto** | **Enlace exacto** | **Uso y momento del vídeo** |
| Hack The Box · Nibbles | <https://app.hackthebox.com/machines/Nibbles?sort_by=created_at&sort_type=desc> | Máquina elegida, 01:17:45. |
| Nibbleblog | <https://www.nibbleblog.com> | Consulta del CMS, 01:41:10. |
| Exploit Database · 38489 | <https://www.exploit-db.com/exploits/38489> | Ficha de subida, 02:08:00 y 02:09:40. |
| GitHub · hadrian3689 | <https://github.com/hadrian3689/nibbleblog_4.0.3> | README y código leídos; clonado, 02:09:44–02:10:40. |
| Reverse Shell Generator | <https://www.revshells.com> | Variante PHP PentestMonkey, 02:48:00. |

Al consultar el 07/10/2026, la página nibbleblog.com mostraba contenido diferente del CMS estudiado; se conserva aquí como URL histórica visible en clase, sin tomar su contenido actual como referencia técnica. La IP 10.129.72.186 pertenecía a la instancia temporal del laboratorio. nmap.org apareció en un banner, pero no se observó su visita. Otros enlaces escritos dentro de código o README tampoco se presentan como páginas abiertas.

# Glosario breve

|  |  |
| --- | --- |
| **Término** | **Significado en la sesión** |
| Rabbit hole | Pista que consume tiempo sin aportar la evidencia necesaria; obliga a volver al mapa. |
| CMS | Gestor de contenidos; Nibbleblog organiza el sitio y su panel. |
| RCE | Ejecución de código en el servidor; exige demostrar que el código se ejecutó. |
| Reverse shell | Conexión iniciada desde la máquina del laboratorio hacia un listener del operador. |
| sudo -l | Lista los comandos que una cuenta puede ejecutar mediante sudo. |
| NOPASSWD | Regla de sudo que no pide contraseña para el comando autorizado. |

# Fuentes y límites de verificación

Fuente principal: transcripción entregada por Chema y fotogramas muestreados del vídeo de esta clase. El vídeo se consultó por HLS y se cotejaron pantallas clave, sin afirmar un visionado continuo. El writeup Nibbles aportado por Chema se utilizó solo como referencia secundaria. La transcripción tiene dos huecos temporales grandes y errores de reconocimiento de nombres, contraseñas y comandos; los literales inseguros se han omitido o normalizado con cautela.

Contraste técnico externo consultado el 07/10/2026: Nmap, Port Specification and Scan Order (https://nmap.org/book/man-port-specification.html), Service and Version Detection (https://nmap.org/book/man-version-detection.html) y Nmap Scripting Engine (https://nmap.org/book/man-nse.html). Estas páginas corrigen y explican las opciones de Nmap; no acreditan un paso ejecutado en Nibbles.

# Ideas importantes de la transcripción

|  |  |  |
| --- | --- | --- |
| **Tema** | **Idea importante** | **Referencia** |
| Trabajo e IA | Valorar alcance, mantenimiento y coste de una herramienta; medir tareas y agentes. | F001 19:29–01:10:55 |
| Cumpleaños | La clase felicita a Carlos y él espera la portada del día. | F001 01:13:28–01:16:13 |
| Modo guiado | Chema opera Nibbles y Carlos convierte cada paso en una pregunta. | F001 01:17:19–01:19:43 |
| Red | Se observan SSH 22 y HTTP 80; se distinguen descubrimiento y versión. | F001 01:20:17–01:23:42 |
| Mapa web | La pista /nibbleblog/ no sustituye revisar la raíz. | F001 01:27:53–01:34:37 |
| Requisitos | La vía My Image exige CMS, plugin, autenticación y ruta correcta. | F001 01:43:05–02:15:43 |
| Panel | users.xml y el panel ayudan a elegir la vía; PHP en un post no se ejecuta. | F001 02:16:15–02:35:10 |
| Subida | El TXT aparece en la ruta del plugin pese a avisos de la interfaz. | F001 02:35:43–02:42:46 |
| Ejecución | La conexión llega al solicitar el archivo subido, no al subirlo. | F001 02:46:22–02:54:35 |
| Privilegios | sudo permite el monitor.sh concreto y la clase llega a root. | F001 02:55:10–03:03:45 |
| Alternativa | Metasploit no consigue sesión y aparece bloqueo temporal. | F001 03:04:04–03:08:58 |

# Actualización de memoria del proyecto

|  |  |  |  |
| --- | --- | --- | --- |
| **Categoría** | **Información nueva** | **Certeza** | **Acción futura** |
| Sesión | Nibbles fue un laboratorio guiado por Carlos Gómez. | Alta | Conservar en esta sesión. |
| Método | Mapear raíz y subruta; demostrar cada resultado. | Alta | Usar para repasar esta clase. |
| Resultado | user.txt y shell root observados; root.txt sin constancia. | Alta | No completar la segunda flag. |
| Enlaces | Cinco sitios abiertos: HTB Nibbles, Nibbleblog, EDB 38489, GitHub hadrian3689 y revshells.com. | Alta: vídeo muestreado | Conservar URLs y capturas. |
| Herramientas | Nmap, curl, web, Wappalyzer, searchsploit, PHP, Netcat y sudo; Metasploit sin sesión. Burp y servidor HTTP solo propuestos. | Alta/Media | Consultar el registro detallado. |
| Pendiente | Metasploit con bloqueo temporal y sin resultado final. | Alta | Revisar si llega continuación. |
