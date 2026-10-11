---
tags:
- Máquinas y prácticas
date: '2026-10-08'
author: Carlos Castillo
---

# Nibbles Blunder

<p class="note-meta">2026-10-08 · Carlos Castillo</p>

!!! success "Blunder, resuelta"
    La parte que quedó pendiente en clase (contraseña de hugo y escalada a root por la versión
    de sudo, **CVE-2019-14287**) está completada en el
    [walkthrough de Blunder](../walkthroughs/web.md#blunder-htb).

![Ilustración de la clase Nibbles y Blunder: Carlos Castillo guía la investigación y Santino, con gafas y sudadera mostaza, trabaja ante el monitor. No representa una escalada final en Blunder.](../../assets/img/nibbles-blunder/img001.png)

# Mapa de la clase

Una investigación con dos CMS: comprobar antes de concluir, adaptar las pruebas a cada respuesta y distinguir lo conseguido de lo pendiente.

|  |
| --- |
| **IDEA CENTRAL · De Nibbles a Blunder** |

↓

|  |  |  |
| --- | --- | --- |
| **1 NIBBLES  Nibbleblog → módulo de Metasploit → sesión → monitor.sh y sudo → root mostrado en esta máquina.** | **2 BLOQUEO  Cinco intentos → Burp → cabecera X-Forwarded-For → prueba positiva tras corregir sintaxis. Intruder requiere interpretar respuestas.** | **3 BLUNDER  Blog Bludit → todo.txt y Fergus → CeWL → credencial → módulo autenticado → shell www-data.** |

Nibbles enseña el mecanismo de bloqueo → Blunder obliga a volver a enumerar y probar la hipótesis

|  |  |
| --- | --- |
| **CONFIRMADO EN LA CLASE Sesión y escalada en Nibbles. En Blunder, acceso como www-data y examen de archivos.** | **PENDIENTE EN BLUNDER Contraseña protegida, cambio de usuario y root: Castillo explicó la continuación; no hubo tiempo para completarla.** |

Método transversal · Planificación → Recogida de información → Análisis de vulnerabilidades → Pruebas de explotación controladas → Comprobación del resultado

|  |
| --- |
| Lectura del mapa Una entrada de searchsploit o una versión sugerida por un archivo no confirma por sí sola una vulnerabilidad en la instancia. Cada salto exige una prueba y una salida interpretada. |

↓ Tres decisiones que ordenan la práctica

|  |  |  |
| --- | --- | --- |
| **PISTA  ¿De dónde sale? Versión, archivo, respuesta o palabra del sitio.** | **PRUEBA  ¿Qué cambia? Petición, cabecera, candidato y comparación de respuesta.** | **RESULTADO  ¿Qué se vio? Sesión, usuario y permisos; lo explicado queda pendiente.** |

# Nibbles y Blunder con Santino

Apuntes de la clase del 8 de octubre de 2026 · Profesor Carlos Castillo · Participación práctica de Santino.

|  |
| --- |
| Alcance de estos apuntes La transcripción de esta sesión se ha leído completa. Para revisar enlaces se inspeccionó un fotograma por minuto del vídeo y 24 fotogramas adicionales a 1080p; no se revisaron todos los fotogramas ni se contrastó el audio completo. Los comandos cuya grafía no es fiable se explican sin reconstruir una orden literal. |

## Qué se aprendió hoy

Castillo usa Nibbles para repasar la selección de módulos de Metasploit, la lectura de sus opciones y una escalada mediante un script que puede modificarse y ejecutarse con privilegios. Después utiliza el bloqueo del inicio de sesión para enseñar que una aplicación puede interpretar mal una IP comunicada en una cabecera HTTP. Tras el descanso, Santino conduce Blunder: identifica Bludit, busca pistas en archivos y en el contenido del blog, prueba credenciales y llega a una sesión como www-data. La clase termina antes de completar el cambio de usuario y la escalada de esta segunda máquina.

# Marco y método

Las máquinas son laboratorios de Hack The Box y las pruebas pertenecen a ese entorno controlado. La demostración no constituye una receta transferible a servicios ajenos. La secuencia útil para estudiar es: planificar el objetivo, recoger información, analizar si una pista indica un fallo aplicable y ejecutar solo la prueba necesaria para confirmarlo. Una búsqueda de exploit, un número de versión en CSS o una respuesta diferente son indicios hasta que se contrastan con la instancia.

| **Fase** | **Pregunta de trabajo** | **Aplicación en esta clase** |
| --- | --- | --- |
| Planificación | ¿Qué se quiere comprobar y en qué laboratorio? | Dos CMS en máquinas distintas; Nibbles como repaso y Blunder guiada por Santino. |
| Recogida de información | ¿Qué servicios, rutas y archivos hay? | Nmap, navegador, rutas web, código fuente, todo.txt y palabras del blog. |
| Análisis de vulnerabilidades | ¿La versión y el comportamiento hacen plausible el fallo? | searchsploit, respuestas HTTP, bloqueo por intentos y opciones del CMS. |
| Pruebas de explotación controladas | ¿Qué resultado real produce la prueba? | Módulos de Metasploit, verificación de sesión y usuario, revisión de permisos. |

# Nibbles Repaso de acceso y privilegios

Castillo no repite la resolución completa de Nibbles. Comprueba de forma abreviada los servicios, vuelve al directorio de Nibbleblog y señala una versión 4.0.3. A partir de una búsqueda con searchsploit localiza una entrada relacionada con subida de archivos y pasa a Metasploit. La mención de una entrada no demuestra por sí sola que sea aplicable: en la clase se configura el módulo y se observa el resultado.

## Leer y configurar el módulo

El profesor distingue el host de destino, la ruta base del CMS y la dirección de retorno de la conexión. En la consola se usan search, use, show options, set y run. Recomienda mirar los campos obligatorios y ejecutar de nuevo show options antes de lanzar la prueba. Advierte también que el payload debe corresponder al sistema y a la tecnología del objetivo; un valor por defecto equivocado puede invalidar la prueba. La documentación de Metasploit confirma la función de show options, set, RHOSTS, TARGETURI y LHOST; la configuración concreta de esta clase procede de la transcripción y no se publica con IP ni contraseña.

| **Elemento** | **Para qué sirve** | **Comprobación en clase** |
| --- | --- | --- |
| RHOSTS | Dirección del sistema del laboratorio que recibe la petición. | Se configura como destino; la IP literal no se conserva en estos apuntes. |
| TARGETURI | Ruta base bajo la que responde la aplicación web. | Castillo insiste en no confundir la raíz del host con la ruta de Nibbleblog. |
| LHOST | Dirección local a la que debe volver una conexión reversa. | Se revisa junto con el payload y las opciones requeridas. |
| show options | Muestra parámetros y requisitos del módulo. | Se consulta antes de la prueba y se recomienda repetir la revisión. |

En la demostración se abre una sesión Meterpreter. Castillo entra en una shell, comprueba la identidad del usuario y revisa archivos del directorio personal. Después muestra que monitor.sh se puede modificar y que su ejecución con sudo permite elevar privilegios; el diálogo cierra con la comprobación de root en Nibbles. La ruta exacta y la secuencia de edición tienen errores de reconocimiento de voz, por lo que no se reconstruyen como comandos literales.

|  |
| --- |
| Riesgo técnico Permitir ejecutar con privilegios un script modificable por un usuario sin privilegios rompe la separación entre cuentas. La revisión defensiva debe comprobar tanto la regla de sudo como propietario y permisos del archivo ejecutado. |

# Bloqueo de acceso y cabeceras HTTP

En el formulario de Nibbleblog se observa un bloqueo tras cinco intentos incorrectos. Castillo captura solicitudes en Burp y explica que la aplicación atribuye los intentos a una dirección de origen. Prueba una cabecera pronunciada como X-Forwarded-For. Tras detectar que faltaban dos puntos en la sintaxis de la cabecera, la respuesta vuelve a indicar credenciales erróneas en vez de mantener el bloqueo. La prueba de Client-IP no obtiene el mismo resultado. La duración del bloqueo se expresa de dos maneras en la propia clase; por eso no se fija aquí un tiempo exacto.

El hecho de que una aplicación acepte X-Forwarded-For no cambia la IP real de la conexión. La cabecera puede ser añadida por un cliente y solo es apta para decisiones de seguridad si la aplicación confía en los valores establecidos por proxies controlados. En este laboratorio se vio una elusión concreta de la atribución de intentos; no se debe generalizar a todas las aplicaciones.

Con Intruder se intenta variar candidatos y cabeceras. El primer ajuste no las combina como se esperaba y acaba generando bloqueos. Más tarde se muestra un script elaborado con ayuda de IA; se anuncia una credencial válida en el intento 2571 de una lista de 5000. La transcripción no contiene el código completo ni la contraseña y no permite atribuir ese hallazgo a la configuración inicial de Intruder.

|  |
| --- |
| Interpretar la respuesta Un cambio de código HTTP, longitud o redirección puede orientar una prueba, pero necesita comparación de mensajes y confirmación del efecto. Burp Intruder permite insertar candidatos en posiciones definidas y examinar respuestas; su ejecución no certifica por sí misma una credencial. |

# Blunder La investigación de Santino

Tras el descanso, Santino comparte la máquina Blunder. El grupo confirma conectividad, observa un TTL 63 y explora puertos. La conversación menciona el 21 cerrado y se concentra en HTTP. Castillo recomienda no aferrarse a un escaneo cuando sus resultados son dudosos: acotar y repetir la comprobación forma parte de la metodología.

## Del blog a una pista comprobable

La web se presenta como un blog. Se revisan páginas, directorios, panel de acceso, código fuente y hojas de estilo hasta identificar Bludit, un CMS basado en archivos. Una cadena 3.9.2 en CSS parece útil, pero Castillo no la toma como versión confirmada de la instancia. searchsploit muestra entradas de ejecución de código autenticada y de bypass de protección frente a intentos; faltan credenciales y la aplicabilidad todavía es una hipótesis. El grupo vuelve a enumerar archivos y encuentra todo.txt, que aporta el usuario Fergus y una referencia a actualizar el CMS. El contenido literal completo del archivo no es recuperable de la transcripción.

## Diccionario y pruebas de acceso

Castillo propone construir candidatos a partir de palabras del propio blog y demuestra CeWL. Esta herramienta rastrea una URL y extrae palabras para una lista contextual. Los parámetros de profundidad, longitud mínima y fichero de salida se explican oralmente, pero la línea completa no se publica como literal porque el reconocimiento de voz puede alterar su orden. La idea de una clave inspirada en los temas del blog es una hipótesis hasta que se comprueba.

Con Burp Repeater e Intruder comparan el formulario de acceso, respuestas 200 y redirecciones 301. Un primer intento de variar X-Forwarded-For no resuelve de modo claro la redirección, así que no se presenta como un bypass demostrado en Blunder. Se consulta material adicional durante la clase y se genera un script con IA. El diálogo posterior da por encontrada una credencial y permite continuar; la salida exacta y el candidato no están en F001. La utilidad de una ayuda de IA depende de revisar sus peticiones, su tratamiento de respuestas y el resultado real.

## Sesión como www-data y punto de parada

Con credenciales consideradas válidas, Santino y Castillo seleccionan un módulo autenticado de Metasploit para Bludit. Repasan el payload, la ruta base del CMS y LHOST. El resultado se celebra en clase y luego se identifica la cuenta www-data. Desde ella inspeccionan las carpetas de la web y llegan a un fichero de usuarios dentro de la instalación que querían revisar. Allí aparece una contraseña protegida. Castillo explica que el paso siguiente sería verificarla con una herramienta apropiada, cambiar de cuenta y examinar los permisos sudo, pero declara que no queda tiempo. La mención de sudo -l y de un shell permitido es explicación, no una prueba ejecutada de root en Blunder.

|  |
| --- |
| Estado al terminar Nibbles: sesión y root mostrados. Blunder: shell www-data y archivos inspeccionados. Descifrado de la contraseña, cambio de usuario y root en Blunder quedan pendientes. |

# Herramientas y comandos vistos

| **Herramienta** | **Objetivo** | **Fase de auditoría** | **Comando o uso visto** | **Nivel** | **Notas** |
| --- | --- | --- | --- | --- | --- |
| ping y nmap | Conectividad y servicios. | Recogida de información | ping, nmap, -p-, --min-rate | Practicada | Orden completa no fiable. |
| Navegador | Leer blog, login y CSS. | Recogida de información | Código fuente y navegación | Practicada | Versión en CSS provisional. |
| searchsploit | Buscar entradas de fallos. | Análisis de vulnerabilidades | Búsqueda para ambos CMS | Practicada | Entrada no confirma fallo. |
| Burp | Comparar peticiones y respuestas. | Análisis de vulnerabilidades | Proxy, Repeater, Intruder | Practicada | Primer ajuste de Intruder falló. |
| CeWL | Lista de palabras del sitio. | Recogida de información | Rastreo de blog | Practicada | Orden literal no fijada. |
| Metasploit | Configurar y probar módulo. | Pruebas de explotación controladas | show options, set, run | Usada en auditoría | Dos máquinas; opciones revisadas. |
| shell, whoami, ls, cd | Identidad y archivos. | Pruebas de explotación controladas | Comprobación tras acceso | Practicada | Sin rutas dudosas. |
| sudo y monitor.sh | Revisar privilegios. | Pruebas de explotación controladas | sudo -l y script | Practicada | Nibbles; Blunder solo explicado. |
| crunch | Patrones de candidatos. | Análisis de vulnerabilidades | Demostración de patrón | Introducida | Patrón literal no verificable. |
| hashcat y John | Contraseña protegida. | Pruebas de explotación controladas | Continuación propuesta | Mencionada | No ejecutadas en Blunder. |

# Errores frecuentes y práctica de repaso

- Confundir la ruta de la aplicación con la raíz del servidor al configurar TARGETURI.
- Aceptar una versión hallada en CSS como versión instalada sin otra prueba.
- Tratar el resultado de searchsploit como prueba automática de que el objetivo es vulnerable.
- Lanzar candidatos sin entender si Intruder modifica una posición, dos posiciones o la cabecera correcta.
- Interpretar un 200 o un 301 fuera del flujo completo de login.
- Dar por hecha la escalada a root de Blunder cuando el profesor la dejó como continuación.

La tarea recomendada por Castillo es repetir Blunder con calma, dejando constancia de cada hipótesis, la petición enviada y la respuesta que la confirma o descarta. Conviene reconstruir por separado la fase de enumeración, la prueba de credenciales y el alcance de la shell. El objetivo del repaso es comprender el método, no memorizar una cadena de órdenes.

# Contexto breve de la sesión

Al inicio se comentan herramientas de IA, agentes y formas de organizar proyectos y terminales. La revisión del vídeo confirma que Carlos muestra y recomienda Paseo (paseo.sh); también se menciona RTK, pero no se ve un enlace suyo. La idea didáctica es organizar el trabajo y revisar las propuestas y scripts generados. Castillo recuerda además el formulario para elegir la presentación de la práctica 1 y el próximo bloque de Blue Team. Estos avisos son contexto de curso y no pasos de los laboratorios.

# Glosario de la clase

| **Término** | **Sentido en estos apuntes** |
| --- | --- |
| CMS | Sistema que organiza y publica el contenido de una web; Nibbleblog y Bludit son los dos tratados hoy. |
| Payload | Componente que el módulo utiliza para producir el efecto o la conexión prevista; debe ser compatible con el objetivo. |
| Meterpreter | Tipo de sesión de Metasploit que se observa en el repaso de Nibbles. |
| X-Forwarded-For | Cabecera que puede transportar una IP cliente atribuida por un proxy; solo debe alimentar controles de seguridad con una cadena de proxies confiable. |
| Diccionario contextual | Lista de candidatos formada con palabras relacionadas con el sitio o el usuario investigado. |
| www-data | Cuenta de servicio web identificada tras el acceso a Blunder; no equivale a root. |

# Fuentes y comprobación

Contenido de clase: F001.txt, transcripción aportada por Chema, leída íntegramente. Chema identificó las fotografías F002–F008 como Santino y pidió usarlas como referencia visual de portada; las fotos no demuestran hechos técnicos de la clase. Vídeo HLS aportado en el chat: 181 fotogramas, uno por minuto, y 24 imágenes adicionales a 1080p para revisar enlaces. No se inspeccionaron todos los fotogramas ni el audio completo. La transcripción dice que el comienzo de la clase no se estaba grabando, por lo que el texto inicial y el vídeo no deben darse por equivalentes.

Ampliación técnica contrastada el 08/10/2026: documentación oficial de Metasploit sobre opciones de módulos (https://docs.metasploit.com/docs/using-metasploit/basics/using-metasploit.html), documentación de PortSwigger sobre Burp Intruder (https://portswigger.net/burp/documentation/desktop/tools/intruder/getting-started), referencia MDN sobre X-Forwarded-For (https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/X-Forwarded-For) y README del proyecto CeWL (https://github.com/digininja/CeWL). Estas fuentes explican herramientas; no prueban lo que ocurrió en la clase.

## Enlaces mostrados o recomendados en clase

La revisión dirigida de F001 y del vídeo recuperó estos cuatro destinos. Las fichas de Hack The Box se vieron en la pantalla de Carlos; sus URL mostraban además parámetros de ordenación, recogidos literalmente en el registro de enlaces. La web de HTB responde, pero su ficha no puede verificarse fuera de una sesión iniciada.

**Paseo, mostrado y recomendado por Carlos:** <https://paseo.sh/> — 18:00–27:00 del vídeo.

**Blunder, ficha abierta por Carlos:** <https://app.hackthebox.com/machines/Blunder> — 28:00–31:00; el enlace enviado por chat a 01:43 no es visible.

**Nibbles, ficha abierta por Carlos:** <https://app.hackthebox.com/machines/Nibbles> — 33:00–34:00 del vídeo.

**CeWL, abierto por Santino por indicación de Carlos:** <https://github.com/digininja/CeWL> — 02:19–02:21; no consta que Carlos pegase esta URL en el chat.

Pendientes de URL exacta: formulario de elección de fecha de la Práctica 1 y enlace de Blunder enviados por el chat del campus; el chat no aparece en la grabación. RTK y un post de escalada se mencionan sin mostrar dirección. Los enlaces de Metasploit, PortSwigger y MDN de la ampliación técnica son fuentes consultadas para estos apuntes, no enlaces atribuidos a Carlos.

# Ideas importantes de la transcripción

| **Tema** | **Idea importante** | **Referencia** |
| --- | --- | --- |
| Plan de clase | Nibbles es repaso; Blunder se hará con Santino. | F001 26:09–27:39 |
| Nibbles | Metasploit abre sesión y se muestra escalada a root mediante monitor.sh y sudo. | F001 39:19–47:52 |
| Bloqueo | Tras cinco intentos, X-Forwarded-For muestra una respuesta distinta al corregir su sintaxis. | F001 49:47–01:03:27 |
| Intruder | El primer ajuste falla; más tarde se anuncia una credencial desde un script generado con IA. | F001 01:03:33–01:17:58 |
| Blunder | Santino conduce el reconocimiento y se identifica Bludit. | F001 01:42:18–01:54:11 |
| Versión | Un número en CSS se trata como indicio, sin confirmar la versión instalada. | F001 01:56:44–02:01:00 |
| Pista | todo.txt aporta el usuario Fergus y una referencia de actualización. | F001 02:09:13–02:15:24 |
| Diccionario | CeWL crea candidatos a partir de palabras del blog. | F001 02:19:25–02:24:06 |
| Acceso | Tras pruebas y un módulo autenticado se identifica la cuenta www-data. | F001 02:37:03–02:53:42 |
| Límite | Contraseña posterior, cambio de usuario y root se explican, pero no se completan. | F001 02:55:17–02:56:52 |

# Preguntas de autoevaluación

**1 ¿Qué distingue un indicio de una vulnerabilidad confirmada?**

El indicio sugiere una hipótesis. La confirmación exige comprobar que el fallo afecta a la instancia y produce el efecto previsto.

**2 ¿Por qué se revisa TARGETURI en Metasploit?**

Porque el CMS puede vivir bajo una ruta distinta de la raíz del servidor; el módulo debe apuntar a la ruta correcta.

**3 ¿Qué demostró la cabecera X-Forwarded-For en Nibbles?**

En ese laboratorio, tras corregir la sintaxis, el bloqueo dejó de aplicarse a la petición probada. No cambió la IP de red ni prueba que cualquier web sea vulnerable.

**4 ¿Por qué volvió Santino a enumerar Blunder?**

Faltaban credenciales y la versión no estaba confirmada. La nueva búsqueda encontró todo.txt y la pista de Fergus.

**5 ¿Hasta dónde llegó realmente la práctica de Blunder?**

A una sesión como www-data y a la inspección de archivos. La contraseña posterior y root quedaron sin ejecutar en clase.

# Actualización de memoria del proyecto

| **Categoría** | **Información nueva** | **Nivel de certeza** | **Acción futura** |
| --- | --- | --- | --- |
| Clase | Castillo: Nibbles. Santino: Blunder. | Alta | Archivar con fuentes. |
| Resultado | Blunder llegó a www-data; root pendiente. | Alta según F001 | Repasar salida y permisos. |
| Método | Confirmar pistas y respuestas. | Alta | Aplicarlo en nuevos laboratorios. |
| Pendiente | Literales dudosos por errores del ASR. | Alta | Cotejar vídeo antes de citarlos. |
