---
tags:
- Máquinas y prácticas
date: '2026-10-05'
author: Carlos Castillo
---

# Facultad

<p class="note-meta">2026-10-05 · Carlos Castillo</p>

![](../../assets/img/facultad/img001.png)

# Mapa de la clase

De la enumeración web al control de privilegios en Linux. Todas las cajas de este esquema son texto y tablas editables.

| **Etapa** | **Relación entre ideas** |
| --- | --- |
| PLANIFICACIÓN | Arctic se inicia y se abandona por incidencias. Facultad pasa a ser el laboratorio principal. |
| RECOGIDA DE INFORMACIÓN | Nmap → SSH y HTTP. Navegador y dirsearch → WordPress en /education. Dominio facultad.thl. |
| ANÁLISIS DE VULNERABILIDADES | WPScan y revisión manual → usuarios, XML-RPC, rutas y componentes. Un hallazgo no demuestra por sí solo una vulnerabilidad. |
| PRUEBAS DE EXPLOTACIÓN CONTROLADAS | Credencial del CMS → panel administrador → gestor de archivos → shell del servicio web. |
| CAMBIOS DE CONTEXTO | www-data → PHP autorizado por sudo → gabri → archivo Brainfuck → vivian por SSH. |
| ESCALADA FINAL | vivian modifica un script autorizado por sudo → cambio de permisos de Bash → contexto root comprobado. |
| CONCEPTOS TRANSVERSALES | Autenticación ≠ autorización · NOPASSWD depende de la regla · SUID y EUID · Enumeración manual y automatizada. |
| LÍMITES Y PREVENCIÓN | Burp y LinPEAS no dan una ruta completa. Cron no queda acreditado. Mínimo privilegio, secretos protegidos y scripts no modificables. |

Resultado observado: www-data → gabri → vivian → root. La vía final comprobada usa sudo, no una ejecución periódica de cron.

Facultad

WordPress y escalada de privilegios en Linux

Carlos Castillo · 5 de octubre de 2026

Esta práctica conecta el reconocimiento de servicios con la enumeración de WordPress, el acceso al servidor y el análisis de permisos de Linux. El objetivo de estudio es entender por qué cada hallazgo permite el siguiente paso y qué controles habrían interrumpido la cadena.

La clase alcanza root en Facultad. Arctic queda como intento inicial abandonado. La transcripción se ha contrastado con 22 fotogramas seleccionados del vídeo; los detalles sin verificación visual específica se indican donde afectan a la interpretación. Las contraseñas del laboratorio se omiten.

## Índice de contenidos

01 La clase y sus objetivos

02 Metodología para interpretar la práctica

03 Reconocimiento inicial y cambio de máquina

04 De la portada a WordPress

05 Enumeración de WordPress y análisis de resultados

06 Acceso al panel prueba de diccionario y permisos

07 WP File Manager y la primera shell

08 Enumeración local y movimiento a gabri

09 Búsqueda manual, Brainfuck y acceso a vivian

10 Escalada final script, sudo y SUID

11 Lecciones defensivas y repaso

12 Referencias técnicas de las ampliaciones

Registro de herramientas · Glosario · Ideas importantes de la transcripción · Actualización de memoria del proyecto

# 01 La clase y sus objetivos

Contenido de clase. Hacking Web Machine I, impartida por Carlos Castillo el 5 de octubre de 2026, desarrolla principalmente la máquina Facultad de The Hackers Labs. El recorrido une reconocimiento web, acceso a WordPress, ejecución de código en el servidor y revisión de permisos en Linux. El resultado final es una sesión con identidad root. El interés del ejercicio está en comprender por qué cada hallazgo permite avanzar y qué condición de seguridad falla en cada transición.

La sesión comienza con Arctic, una máquina Windows de Hack The Box, pero los problemas de conexión y carga impiden continuar con normalidad. Se abandona ese intento y se importa Facultad en el entorno local. Arctic no queda resuelta durante esta clase. Las referencias a una práctica Windows anterior son un repaso oral y no forman parte de la cadena demostrada en Facultad.

Al terminar el estudio, deberías poder distinguir enumeración de explotación, interpretar resultados incompletos de un escáner, reconocer el alcance de una cuenta administradora de un gestor de contenidos y explicar la diferencia entre cambiar de usuario y obtener privilegios de root. También debes poder justificar por qué una shell recibida, una herramienta descargada o una entrada de configuración no bastan por sí solas para acreditar un resultado.

El recorrido confirmado sigue esta secuencia: web inicial → WordPress en /education → acceso de administración → WP File Manager → shell de www-data → ejecución delegada de PHP como gabri → archivo local con información sensible → acceso como vivian → script modificable autorizado mediante sudo → root. Esta secuencia resume el laboratorio; las alternativas comentadas se distinguen de las acciones que tuvieron éxito.

# 02 Metodología para interpretar la práctica

La metodología evita encadenar herramientas sin saber qué se busca. Cada acción debe responder a una pregunta: qué servicio existe, qué información expone, qué permiso está concedido o qué resultado permite confirmar una hipótesis. Si una prueba falla, hay que conservar ese resultado y revisar su causa antes de afirmar que el camino es imposible.

## Planificación

El laboratorio define el objetivo y el entorno de las pruebas. La clase reajusta su planificación cuando Arctic no responde de forma útil y continúa con Facultad. El cambio obliga a revisar dirección, sistema operativo y servicios; no es correcto trasladar las conclusiones del objetivo Windows al nuevo objetivo Linux. Mantener una carpeta de trabajo por máquina ayuda a separar resultados y evita confundir sesiones o terminales.

## Recogida de información

Se comprueba conectividad, se reconocen puertos y se inspecciona la aplicación web. Nmap, Netcat, WhatWeb, el navegador y dirsearch aportan perspectivas distintas. Después, WPScan recoge información específica de WordPress. El resultado de esta fase es un inventario razonado de servicios, rutas, tecnologías, usuarios y funciones, todavía sin dar por demostrada una explotación.

## Análisis de vulnerabilidades

Se relacionan los datos con debilidades concretas: respuestas de autenticación que revelan usuarios, credenciales débiles, capacidad de cargar código, delegaciones sudo y archivos sensibles accesibles. Una versión detectada o una coincidencia en un buscador de exploits es una pista. Hay que comprobar componente, condiciones y comportamiento antes de atribuirle una vulnerabilidad aplicable.

## Pruebas de explotación controladas

La clase valida las hipótesis dentro de la máquina de práctica. El acceso al panel, la shell de www-data, el cambio a gabri, el acceso a vivian y la comprobación final de root son resultados distintos que deben documentarse por separado. Una prueba satisfactoria modifica el contexto y exige volver a recoger información: una nueva identidad puede leer otros archivos o disponer de permisos diferentes.

# 03 Reconocimiento inicial y cambio de máquina

En Arctic se observa conectividad mediante ping y se revisan puertos asociados a servicios de Windows y a una web en el puerto 8500. Se intenta usar Netcat para observar una respuesta directa, pero no se obtiene una interacción útil. También se prueban la carga en el navegador y distintas condiciones de conexión. No queda demostrada una causa única de los problemas: aparecen hipótesis relacionadas con recursos locales, la VPN y la plataforma.

La explicación sobre el tiempo de vida de los paquetes, TTL, sirve como orientación inicial del sistema operativo. Debe tratarse como indicio, no como identificación concluyente. El valor recibido depende de condiciones de red y configuración. La distinción importa porque una hipótesis de Windows orienta las siguientes comprobaciones, pero no sustituye a la evidencia que proporcionan servicios y sistema.

Facultad se despliega como máquina local. El reconocimiento identifica los puertos 22 y 80, asociados en la práctica a SSH y HTTP. SSH queda como una posible vía posterior de acceso autenticado y la investigación se concentra primero en la web. Que un servicio esté abierto no implica que exista una vulnerabilidad aprovechable ni que la única alternativa sea probar contraseñas.

## Qué aporta Netcat frente al navegador

Netcat permite establecer una conexión con un puerto y observar los datos que devuelve el servicio. En Facultad se obtiene una respuesta HTTP incluso aunque la solicitud no sea la adecuada. El error de petición aporta información sobre el protocolo; no significa que se haya accedido a contenido protegido. Del mismo modo, el silencio de un servicio que espera un intercambio específico no demuestra que esté cerrado.

Nmap identifica servicios y WhatWeb ayuda a reconocer tecnologías web. Sus resultados se contrastan con la navegación. La portada presenta una asignatura de administración de sistemas y enlaces con poca funcionalidad visible. En lugar de concluir que no hay superficie de interés, se pasa a descubrir rutas que no aparecen enlazadas desde la página principal.

## Comandos de reconocimiento observados

Los siguientes comandos pertenecen al laboratorio grabado. La dirección identifica aquella máquina local y no se propone como destino de una ejecución actual.

Observado

sudo nmap -p- --min-rate 5000 192.168.0.123

-p- solicita todos los puertos TCP del barrido y --min-rate 5000 una tasa mínima de envío. El objetivo es descubrir puertos; la observación relevante fue 22 y 80 abiertos. Ampliación técnica: una tasa elevada puede cargar el entorno o perjudicar la fiabilidad; no garantiza más calidad.

Observado

sudo nmap -p22,80 -sVC 192.168.0.123

Restringe la comprobación a 22 y 80. -sV solicita detección de servicios/versiones y -sC los scripts predeterminados, combinados en la opción vista. Se observaron SSH y HTTP. Las versiones y los scripts ayudan a describir el servicio; no demuestran por sí solos una vulnerabilidad.

# 04 De la portada a WordPress

Con dirsearch y un diccionario de rutas se encuentran directorios de imágenes y la subruta /education. Este hallazgo cambia el foco: una web aparentemente sencilla contiene otra aplicación con su propia autenticación y estructura. El profesor utiliza el ejemplo para explicar que un servidor puede acumular pruebas, blogs o proyectos que no se aprecian desde la portada.

Los listados de directorios permiten conocer nombres y organización de archivos. Su relevancia depende de lo expuesto: una imagen pública no tiene el mismo impacto que una copia de seguridad o un archivo de configuración. Además, que una ruta no muestre listado no permite generalizar que todas las demás estén protegidas de la misma forma. En clase se comprueban rutas de temas donde el comportamiento difiere.

La instalación utiliza el nombre facultad.thl y WordPress se encuentra en /education. El código fuente contiene referencias a ese dominio. Acceder únicamente por dirección IP puede dejar recursos o enlaces apuntando a un nombre que el equipo no resuelve. Se revisa la resolución local y se emplea la dirección prevista por la aplicación. El protocolo también importa: escribir una dirección con HTTPS cuando el servicio utilizado es HTTP introduce otro problema diferente.

La enumeración debe dirigirse a la ubicación real del CMS, es decir, del sistema de gestión de contenidos. Analizar solo la raíz del servidor no equivale a analizar la instalación de WordPress alojada en una subruta. Esta idea se aplica tanto al navegador como a WPScan: antes de interpretar un fallo de detección hay que comprobar que la dirección de entrada es correcta.

## Leer sin saturar

La clase llama la atención sobre el volumen de peticiones de los diccionarios y los hilos concurrentes. Más velocidad puede consumir recursos y dificultar la interpretación de los resultados. En una auditoría se ajustan intensidad y duración al alcance acordado y a la disponibilidad del servicio. La enseñanza útil es medir y controlar el impacto, no asumir que el ajuste más rápido es siempre el mejor.

## Enumeración de la subruta

La comprobación de rutas dentro de la instalación también se detuvo antes de recorrer todo el diccionario. Debe describirse como exploración parcial, conservando los hallazgos de wp-content y wp-includes.

Observado

dirsearch -u http://192.168.0.123/education -w /usr/share/wordlists/seclists/Discovery/Web-Content/directory-list-2.3-medium.txt

-u establece la dirección de entrada y -w el diccionario de nombres. Se buscan rutas y se interpretan sus respuestas y redirecciones. La prueba fue interrumpida con Ctrl+C; no acredita una enumeración exhaustiva y genera múltiples peticiones al servicio.

# 05 Enumeración de WordPress y análisis de resultados

WordPress combina un núcleo, temas y plugins. El núcleo proporciona las funciones generales; los temas organizan la presentación y los plugins añaden capacidades. Cada componente mantiene su propia versión. Al buscar información en SearchSploit y Exploit-DB, la clase insiste en leer a qué componente se refiere un resultado. Una versión incluida en el título de un plugin no debe confundirse con la versión del núcleo.

La versión 6.7.1 del núcleo aparece en la explicación oral; no se ha cotejado visualmente en la revisión dirigida de fotogramas. Se conserva como dato de la transcripción, sin utilizarla para afirmar que exista una vulnerabilidad concreta. La comparación oral con una supuesta versión más reciente no se adopta como dato verificado.

La búsqueda por coincidencia exacta también tiene límites. Un aviso puede describir un intervalo de versiones y no escribir literalmente la versión observada. Para valorar su aplicabilidad hay que leer las condiciones, no limitarse a la presencia de una palabra o un número. En esta práctica no se demuestra una explotación del núcleo basada en un exploit público: el acceso se consigue a través de credenciales y capacidades administrativas.

WPScan examina la instalación, identifica información del sitio, el tema Twenty Twenty-Five y un usuario. Se revisan también el archivo readme, información RSS y el endpoint XML-RPC. RSS es un formato de sindicación de contenidos y puede aportar metadatos; conocerlos ayuda al reconocimiento, pero no significa disponer de acceso administrativo.

Ampliación técnica verificada. El token de la interfaz de programación de aplicaciones, API, de WPScan permite consultar datos de vulnerabilidades. No es un requisito absoluto para enumerar WordPress. Un resultado que no descubre plugins tampoco demuestra que no existan: posteriormente el panel muestra WP File Manager activo. Ese contraste enseña a separar lo que una herramienta ha detectado de todo lo que el sistema contiene.

## XML-RPC y autenticación

Ampliación técnica verificada. XML-RPC es una interfaz de llamadas remotas utilizada por WordPress. Su presencia no constituye, por sí sola, una vulnerabilidad confirmada. Hay que evaluar qué funciones están disponibles, qué autenticación requieren y qué controles se aplican. En este laboratorio, la salida de WPScan identifica XML-RPC como el mecanismo empleado para la prueba de contraseña que tiene éxito.

El formulario de acceso devuelve mensajes distintos para un usuario inexistente y para una contraseña incorrecta. Esa diferencia permite confirmar nombres de cuenta y reduce la incertidumbre de las pruebas posteriores. La debilidad observada es la revelación de existencia de usuarios; debe distinguirse del hallazgo posterior de una contraseña válida.

## Consulta específica del CMS

Observado

wpscan --url http://facultad.thl/education -e ap,u

--url apunta a la instalación y -e selecciona enumeración: ap corresponde a plugins y u a usuarios. La salida identifica el sitio y una cuenta, pero no descubre todos los componentes. El objetivo esperado es ampliar el inventario; la ausencia de un hallazgo no prueba ausencia del componente.

# 06 Acceso al panel prueba de diccionario y permisos

Se prepara una petición de autenticación en Burp Suite y se envía a Intruder, seleccionando el campo de contraseña para variar los valores de entrada. La carga del diccionario y los intentos producen bloqueos o saturación que impiden completar el trabajo con normalidad. La clase no demuestra un resultado satisfactorio con Intruder; el éxito posterior corresponde a WPScan.

El cambio de herramienta conserva lo ya aprendido: existe un usuario identificado y la ubicación del WordPress es conocida. WPScan realiza una prueba de diccionario dirigida a esa cuenta y obtiene una combinación válida. La entrada al panel confirma el acceso. La contraseña no se reproduce en estos apuntes; lo relevante es que la autenticación débil abre una nueva superficie de análisis.

Durante el cambio a WPScan aparecen opciones escritas en singular que la herramienta rechaza. La forma corregida utiliza --usernames y --passwords. Este pequeño error ilustra por qué conviene leer la respuesta del programa: una opción inválida impide que la prueba se inicie como se pretendía, pero no dice nada sobre la resistencia de la autenticación del objetivo.

Autenticación y autorización responden a preguntas diferentes. La autenticación determina con qué cuenta se entra; la autorización define las acciones que esa cuenta puede realizar. Dentro del panel se verifica el rol administrador. Eso permite revisar usuarios, plugins, temas, páginas y opciones que no eran visibles desde el exterior, pero no significa ser ya root del sistema operativo.

El profesor insiste en detenerse a entender el panel. La pregunta deja de ser únicamente «qué exploit busco» y pasa a ser «qué funciones están disponibles con estos permisos». Poder publicar contenido, leer archivos o subirlos son capacidades distintas. También interesa comparar el inventario autenticado con la enumeración externa: en este caso, el plugin de gestión de archivos no había sido identificado por WPScan.

## Decidir con el contexto

Una herramienta especializada facilita tareas repetitivas, pero no sustituye la comprensión de la petición web ni del permiso concedido. Por eso se muestra primero la lógica de Burp y luego se utiliza WPScan. La lección no es que una herramienta falle siempre o que otra garantice éxito, sino que hay que reconocer limitaciones, conservar evidencias y elegir el siguiente paso según el estado real de la prueba.

# 07 WP File Manager y la primera shell

El panel muestra WP File Manager 8.0.1 activo. El gestor permite navegar por archivos de la instalación y utilizar la función de subida. Leer el contenido de un PHP desde un gestor de archivos es diferente de solicitarlo al servidor web: en la segunda situación el servidor puede interpretarlo y devolver su resultado, mientras que el acceso administrativo al archivo permite inspeccionar su código.

La prueba aprovecha la posibilidad de subir un archivo PHP y solicitarlo después por HTTP. Una shell inversa establece una conexión desde el sistema del laboratorio hacia el punto de escucha del auditor. Para que la prueba funcione deben coincidir archivo accesible, ejecución del código, conectividad y escucha preparada. Subir el archivo, por sí solo, no acredita que se haya recibido una shell.

El primer intento devuelve conexión rechazada porque aún no se había preparado la escucha. Tras corregir esa condición y volver a solicitar el archivo, se recibe la shell. La identidad comprobada es www-data, vinculada al servicio web. El hallazgo muestra cómo el acceso administrativo de la aplicación puede permitir ejecución en el servidor cuando las funciones de archivos y los permisos lo hacen posible.

La alternativa de modificar un archivo PHP existente se comenta, pero el gestor bloquea la edición en la prueba mostrada. La referencia a 404.php pertenece a esa explicación alternativa y no a una vía ejecutada con éxito. Tampoco se debe atribuir el acceso a una vulnerabilidad específica del plugin únicamente por su nombre o versión: aquí se observa el uso de funciones disponibles tras autenticarse.

## Una shell no equivale a una terminal completa

La shell recibida presenta limitaciones de interacción. Se intenta mejorarla con Python, pero el intérprete no está disponible mediante los nombres probados. Más adelante se intentan otros ajustes de terminal con resultados problemáticos. La estabilización mejora la comodidad, el control de señales y la interacción; no concede por sí misma permisos de otro usuario.

# 08 Enumeración local y movimiento a gabri

Una vez dentro se comprueban identidad, usuarios, directorios y permisos. Revisar /home aporta pistas, pero la ausencia de una carpeta personal no demuestra que una cuenta no exista. Por eso se consulta también /etc/passwd y se analiza el contexto de las cuentas. El objetivo es obtener un mapa de lo que la identidad actual puede leer y ejecutar, sin reducir la enumeración a una sola orden.

Los archivos de WordPress, incluido wp-config.php, contienen información de configuración de la base de datos. Durante la clase se examina esa configuración y se valora si entrar en MySQL aportaría algo nuevo. No se realiza ese acceso. Se explica que podría resultar útil si existieran otros usuarios o bases accesibles, pero esas posibilidades no se comprueban en la sesión.

La salida de sudo -l revela una delegación concreta: www-data puede ejecutar /usr/bin/php como gabri sin contraseña. Este permiso no autoriza genéricamente cualquier comando como root. Sin embargo, PHP es un intérprete capaz de ejecutar código, por lo que delegarlo de esa forma permite crear una shell bajo la identidad autorizada. El cambio a gabri queda confirmado.

El movimiento se produce por una autorización sudo, no porque se haya descubierto la contraseña de gabri. La distinción explica por qué disponer de una shell de ese usuario no proporciona automáticamente sus credenciales para una conexión SSH. Tras cambiar de identidad hay que volver a revisar capacidades y archivos; no basta con asumir que se ha avanzado directamente hasta root.

## Lectura de una delegación

En la regla, el nombre entre paréntesis identifica la cuenta de destino, NOPASSWD indica que no se exige contraseña para esa autorización y la ruta limita el programa autorizado. La clase consulta GTFOBins para comprender las capacidades del intérprete y recuerda prestar atención al usuario de destino y a la ruta del ejecutable. Los errores deben leerse antes de descartar una hipótesis.

El intento previo sin seleccionar gabri no funcionó; la ejecución que sí lo hizo indicó ese usuario de destino. Aunque la regla muestra /usr/bin/php, el comando satisfactorio utilizó php sin ruta absoluta. Por tanto, no debe atribuirse el éxito a haber escrito una ruta completa que no aparece en esa ejecución.

Observado

sudo -l

Lista las autorizaciones sudo visibles para la cuenta actual. En la práctica revela primero PHP como gabri y después el script permitido a vivian. La salida debe interpretarse para cada usuario; no es una orden que eleve privilegios por sí sola.

Observado

(gabri) NOPASSWD: /usr/bin/php

Fragmento de salida observado. Describe la delegación a gabri y el ejecutable autorizado, no una contraseña ni un permiso general de administración.

Observado en la práctica controlada

sudo -u gabri php -r 'system("/bin/sh -i");'  
whoami

Lectura documental de la ejecución en el laboratorio. -u gabri selecciona la identidad autorizada; php -r evalúa el código indicado; system invoca la shell interactiva. La consulta de identidad devuelve gabri. El riesgo es delegar un intérprete con capacidad de lanzar programas, no una vulnerabilidad de PHP demostrada. Esta prueba no proporciona la contraseña de gabri.

# 09 Búsqueda manual, Brainfuck y acceso a vivian

Se intenta transferir LinPEAS mediante un servidor HTTP local y wget. Aparecen problemas de escritura y ejecución, junto con las limitaciones de la terminal. La transferencia de una herramienta y el intento de iniciarla no equivalen a disponer de un análisis completo. No queda acreditada una salida limpia y final de LinPEAS; la investigación continúa manualmente.

La revisión busca archivos interesantes en ubicaciones como /tmp, /opt y /var/mail, prestando atención a los ocultos. Un nombre que empieza por punto puede quedar fuera de un listado sencillo. Chema plantea si se podría usar una búsqueda por nombres para evitar recorrer cada carpeta. La respuesta metodológica es combinar búsquedas y revisión manual: un archivo relevante puede tener un nombre inesperado o no ser destacado por una herramienta.

En /opt aparece un script relacionado con vivian. Con gabri se puede leer, pero los intentos de modificarlo o renombrarlo fallan por permisos. Esto impide aprovecharlo directamente desde esa identidad. La explicación sobre una posible ejecución periódica es una hipótesis que requiere comprobar usuario ejecutor, permisos y funcionamiento real; no constituye todavía la vía demostrada de escalada.

En /var/mail/gabri se encuentra el archivo oculto .password\_vivian.bf. Su contenido se identifica como Brainfuck, un lenguaje de programación esotérico, y se utiliza dCode para interpretarlo. La salida proporciona una credencial que permite acceder como vivian. CyberChef se comenta y se prueba como ayuda de identificación, pero la recuperación narrada se apoya en dCode.

Conviene usar la terminología adecuada: interpretar un programa que produce texto no equivale necesariamente a descifrar un mensaje protegido criptográficamente. La extensión y el patrón de símbolos son pistas para reconocer el formato. El defecto de seguridad relevante es que información sensible recuperable queda accesible a otra cuenta. Los apuntes conservan el mecanismo y omiten el valor de la credencial.

Con la credencial recuperada se cambia a vivian y se establece acceso mediante SSH. Ahora existe una vía autenticada con una terminal más cómoda. El contraste con gabri es claro: antes se disponía de ejecución bajo otra identidad por sudo; ahora también se conoce una credencial válida para el servicio de acceso remoto mostrado.

## Comprobaciones básicas de archivos y acceso

Estas órdenes permiten distinguir el contenido accesible, la conectividad y la identidad conseguida. Sus salidas deben revisarse antes de interpretar una operación posterior.

Observado

ls -la

-l muestra el detalle de permisos y propietario; -a incluye nombres que comienzan por punto. En la carpeta de correo de gabri permitió ver .password\_vivian.bf. Listar un archivo no implica poder modificarlo.

Observado

ip a

Muestra interfaces y direcciones de red. En la shell del laboratorio funcionó después de que ifconfig no estuviera disponible. Es una consulta de configuración, no un cambio de red.

Observado

ssh vivian@192.168.0.123  
whoami  
sudo -l

SSH inicia una conexión autenticada como vivian en la máquina local grabada. Después, whoami confirma vivian y sudo -l muestra su delegación. El resultado esperado depende de credenciales y servicio disponibles; la clase confirma ambos mediante la sesión abierta. No se incluye la contraseña.

# 10 Escalada final script, sudo y SUID

La cuenta vivian dispone de una autorización sudo para /opt/vivian/script.sh y puede modificar el contenido de ese archivo. La combinación es el problema central: el usuario controla las instrucciones de un programa que después se permite ejecutar con privilegios elevados. Restringir sudo a una ruta no protege suficientemente si esa ruta o su contenido están bajo control de la cuenta delegada.

En la práctica se modifica el script para que su ejecución privilegiada altere los permisos de /bin/bash. Después se ejecuta la ruta autorizada mediante sudo y se comprueba la aparición del bit SUID. La escalada final demostrada utiliza sudo; no necesita esperar a una tarea periódica. No se acredita que la entrada de cron comentada en clase se ejecute correctamente ni que lo haga como root.

Ampliación técnica. SUID, Set User ID, permite que un ejecutable adquiera como identidad efectiva la de su propietario en las condiciones aplicables. No significa siempre «ejecutar como root»: eso depende, entre otros factores, de quién sea el propietario. En la situación observada, Bash pertenece a root y la modificación de permisos crea la condición relevante para la prueba final.

Ampliación técnica verificada. /etc/crontab requiere, además de los cinco campos temporales, un campo de usuario antes del comando. La línea observada carece de ese campo, de modo que no acredita una tarea funcional de root. Esta limitación refuerza la necesidad de separar la hipótesis de cron de la ejecución mediante sudo efectivamente mostrada.

Ampliación técnica verificada. La opción -p de Bash activa su modo privilegiado y permite conservar una identidad efectiva distinta de la identidad real al iniciarse. No busca privilegios ni los concede por sí misma. En el laboratorio, ejecutar Bash sin esa opción devuelve el contexto de vivian, mientras que la ejecución con -p conserva la identidad efectiva privilegiada; whoami devuelve root.

El resultado debe apoyarse en esa comprobación de identidad, no solo en el aspecto del prompt ni en la presencia de una letra en los permisos. La cadena causal es control del script, autorización de ejecución privilegiada, modificación de permisos y conservación de la identidad efectiva. Si cualquiera de esas condiciones faltase, no se podría deducir el mismo resultado.

## Evidencias que conviene interpretar por separado

La regla sudo y los permisos del archivo son evidencias complementarias. La primera explica quién puede ejecutar qué como otra identidad; los segundos explican quién puede cambiar el contenido. Una entrada de planificación de tareas requiere su propia validación. Mezclar esos mecanismos lleva a atribuir a cron un resultado que, en esta sesión, se obtiene mediante sudo.

La regla válida es NOPASSWD. La petición de contraseña que aparece en otro intento corresponde a invocar script.sh sin su ruta y acaba en un error de comando no encontrado. El intento satisfactorio usa la ruta absoluta autorizada; no hay evidencia de que la regla válida exigiera contraseña.

Observado

(ALL) NOPASSWD: /opt/vivian/script.sh

Fragmento de la autorización observada para vivian. El riesgo se materializa porque el script autorizado es modificable por esa misma cuenta.

Observado

whoami

Muestra el nombre asociado a la identidad efectiva. En la comprobación final devuelve root. Es una verificación del contexto alcanzado, no el mecanismo que lo produce.

Observado tras ejecutar el script autorizado

ls -la /bin/bash  
bash  
whoami  
bash -p  
whoami

Comparación final observada después de la modificación privilegiada de permisos. El listado muestra SUID; la primera consulta de identidad devuelve vivian y la segunda root. -p preserva el contexto efectivo ya obtenido y no concede privilegios por sí solo. Alterar permisos de una shell del sistema debilita el equipo; aquí se documenta únicamente el resultado del laboratorio.

# 11 Lecciones defensivas y repaso

Síntesis defensiva derivada de la práctica. La cadena combina varias debilidades, por lo que existen distintos puntos donde interrumpirla. En la web, conviene reducir la exposición innecesaria de archivos y revisar aplicaciones alojadas en subrutas. En autenticación, importa evitar contraseñas previsibles y limitar las diferencias de respuesta que permiten confirmar cuentas. La intensidad de pruebas y los registros deben revisarse conjuntamente con la disponibilidad del servicio.

En el CMS, el inventario autenticado ayuda a detectar plugins y funciones que un escáner externo no ve. Debe revisarse quién necesita gestionar archivos y qué directorios puede modificar el proceso web. La subida de un archivo no debería convertirse sin control en ejecución de código. También hay que proteger la configuración y reducir el alcance de los permisos de las cuentas de aplicación y base de datos.

En Linux, deben revisarse las delegaciones de intérpretes y los programas ejecutados con privilegios. Los scripts privilegiados y sus rutas no deben poder ser sustituidos o modificados por usuarios con menor confianza. Las credenciales no deben guardarse en archivos accesibles a cuentas ajenas, aunque estén ocultos o presentados en un formato poco familiar. El bit SUID y el propietario de los ejecutables requieren una revisión específica.

Los errores de la sesión tienen valor formativo: la carga fallida de Arctic no demuestra una vulnerabilidad; el bloqueo de Intruder no demuestra que la contraseña sea resistente; una shell rechazada puede deberse a que falta la escucha; un escáner incompleto no certifica ausencia de hallazgos; y una ruta prometedora no sirve si la cuenta actual carece del permiso necesario.

## Preguntas de repaso con respuesta orientativa

¿Por qué había que incluir /education al analizar WordPress? Porque la instalación estaba en esa subruta y la raíz del servidor mostraba otra página. La herramienta necesita apuntar al objeto real que se pretende estudiar.

¿Qué diferencia hay entre no detectar plugins y no tener plugins? La primera es una observación sobre la cobertura de una herramienta; la segunda es una afirmación sobre el sistema. El panel mostró un plugin activo que la enumeración externa no había identificado.

¿Por qué ser administrador de WordPress no equivale a ser root? Porque son ámbitos de autorización distintos. La cuenta administradora controla funciones de la aplicación; el código ejecutado por el servicio web se recibe inicialmente como www-data.

¿Qué permitió cambiar de www-data a gabri? Una regla sudo que autorizaba ejecutar PHP como gabri sin contraseña. No se obtuvo la credencial de esa cuenta por ese mecanismo.

¿Qué hizo útil el archivo Brainfuck? Su contenido producía información sensible utilizable para autenticarse como vivian. El problema era la exposición del secreto, no la mera existencia de un lenguaje poco habitual.

¿Por qué era peligrosa la regla sudo final? Porque permitía ejecutar con privilegios un script cuyo contenido controlaba vivian. La confianza en la ruta no garantizaba la confianza en sus instrucciones.

¿Basta bash -p para ser root? No. La opción conserva determinadas condiciones de privilegio ya presentes; no las crea. En el laboratorio esas condiciones procedían de la modificación privilegiada de un Bash propiedad de root.

¿Qué quedó sin demostrar? La resolución de Arctic, un análisis completo de LinPEAS, una explotación exitosa mediante edición de 404.php, el acceso a MySQL y una ejecución funcional de cron responsable de la escalada. Deben permanecer separados de los resultados confirmados.

# 12 Referencias técnicas de las ampliaciones

Las siguientes referencias respaldan las precisiones técnicas y no se utilizan como prueba de que una acción ocurriera en clase. Fecha de consulta: 6 de octubre de 2026.

GNU Bash Reference Manual: modo privilegiado y relación entre identidad real y efectiva. https://www.gnu.org/software/bash/manual/bash.html

WPScan User Documentation: enumeración y acceso a datos de vulnerabilidades mediante API token. https://github.com/wpscanteam/wpscan/wiki/WPScan-User-Documentation

WordPress Developer Resources, XML-RPC: naturaleza y funciones de la interfaz. https://developer.wordpress.org/apis/xml-rpc/

crontab(5), formato de la tabla del sistema y campo de usuario. https://man7.org/linux/man-pages/man5/crontab.5.html

Nmap Reference Guide y opciones de rendimiento: selección de puertos, detección y tasa de envío. https://nmap.org/book/man.html · https://nmap.org/book/man-performance.html

# Registro de herramientas

El nivel describe el uso en esta sesión. Una mención no equivale a manejo demostrado; los intentos fallidos conservan su estado.

| **Herramienta** | **Objetivo y fase** | **Uso visto y nivel** |
| --- | --- | --- |
| ping | Comprobar conectividad Fase: Recogida de información | Pruebas sobre Arctic y Facultad Nivel: Practicada El TTL es una pista, no prueba concluyente del sistema operativo. |
| Nmap | Reconocer puertos y servicios Fase: Recogida de información | Enumeración de los objetivos Nivel: Practicada Facultad: puertos 22 y 80 narrados. |
| Netcat | Observar respuestas y recibir la conexión del laboratorio Fase: Recogida de información / Pruebas de explotación controladas | Conexión a servicios y escucha de la shell Nivel: Practicada Intento inicial sin respuesta útil en Arctic. |
| WhatWeb | Identificar tecnologías web Fase: Recogida de información | Reconocimiento de la web inicial Nivel: Practicada |
| dirsearch y SecLists | Descubrir rutas web Fase: Recogida de información | Diccionario sobre la web; hallazgo de /education Nivel: Practicada Controlar volumen de peticiones e hilos. |
| SearchSploit / Exploit-DB | Buscar referencias de vulnerabilidades Fase: Análisis de vulnerabilidades | Búsqueda por producto y versión Nivel: Practicada No se demuestra explotación de un resultado de esa búsqueda. |
| WPScan | Enumerar WordPress y comprobar autenticación Fase: Recogida de información / Pruebas de explotación controladas | Análisis de /education y prueba de diccionario Nivel: Practicada Éxito de autenticación por XML-RPC; no detectó todos los plugins. |
| Burp Suite / Intruder | Preparar pruebas sobre el formulario Fase: Pruebas de explotación controladas | Petición interceptada y diccionario de contraseñas Nivel: Practicada Intento con bloqueos; no completado con éxito. |
| WP File Manager | Gestionar archivos desde el panel Fase: Pruebas de explotación controladas | Lectura y subida de PHP; versión visible 8.0.1 Nivel: Practicada La edición alternativa aparece bloqueada. |
| sudo y utilidades de shell | Revisar identidades, permisos y delegaciones Fase: Recogida de información / Pruebas de explotación controladas | sudo -l, whoami y revisión de archivos Nivel: Practicada Distinguir permiso, ejecución y resultado. |
| PHP / GTFOBins | Comprender el intérprete autorizado Fase: Análisis de vulnerabilidades / Pruebas de explotación controladas | Consulta de capacidades y cambio a gabri Nivel: Practicada No se obtiene la contraseña de gabri. |
| Python HTTP server / wget | Transferir una herramienta local Fase: Pruebas de explotación controladas | Transferencia de LinPEAS Nivel: Practicada Python utilizado en el equipo local no acredita Python en el objetivo. |
| LinPEAS | Ayudar a enumerar posibles rutas locales Fase: Análisis de vulnerabilidades | Descarga e intentos de ejecución Nivel: Practicada No se acredita una ejecución completa y limpia. |
| dCode | Identificar e interpretar el archivo Brainfuck Fase: Análisis de vulnerabilidades | Interpretación del archivo .bf Nivel: Practicada Credencial omitida en el documento. |
| CyberChef | Explorar identificación de formato Fase: Análisis de vulnerabilidades | Prueba de identificación Nivel: Practicada No se atribuye a esta herramienta la recuperación confirmada. |
| SSH | Acceder de forma autenticada como vivian Fase: Pruebas de explotación controladas | Conexión con la credencial recuperada Nivel: Practicada |
| BloodHound / Hydra | Ejemplificar otras herramientas Fase: Recogida de información / Pruebas de explotación controladas | Menciones orales Nivel: Mencionada No se utilizan como vías ejecutadas de esta práctica. |

# Glosario

| **Término** | **Significado en la práctica** |
| --- | --- |
| CMS | Sistema de gestión de contenidos; en la práctica, WordPress. |
| Enumeración | Recogida organizada de información sobre servicios, usuarios, rutas y permisos. |
| Autenticación | Comprobación de la identidad presentada al acceder. |
| Autorización | Conjunto de acciones permitidas a una identidad. |
| Plugin | Componente que añade funciones a una aplicación. |
| Directory listing | Listado de archivos de un directorio servido al cliente. |
| XML-RPC | Interfaz de llamadas remotas basada en mensajes XML; su presencia no demuestra vulnerabilidad. |
| Shell inversa | Sesión de comandos cuya conexión inicia el sistema del laboratorio hacia una escucha. |
| Movimiento lateral de usuario | Cambio a otra cuenta del mismo entorno sin implicar necesariamente privilegios máximos. |
| sudo | Mecanismo de delegación de ejecución sujeto a una política de permisos. |
| NOPASSWD | Marca de sudo que elimina el requisito de contraseña para la autorización indicada. |
| SUID | Bit que puede hacer que un ejecutable use como identidad efectiva la de su propietario. |
| Identidad efectiva | Identidad relevante para las comprobaciones de permisos del proceso. |
| Brainfuck | Lenguaje esotérico cuyo programa puede producir texto al interpretarse. |
| Cron | Mecanismo de programación periódica; debe verificarse su configuración y ejecución real. |
| API token | Credencial para acceder a una API; en WPScan habilita la consulta de datos de vulnerabilidades. |

# Contraste audiovisual

Comprobaciones dirigidas de pantalla que precisan la narración oral. Los tiempos de esta tabla pertenecen al vídeo.

| **Tema** | **Evidencia de pantalla** | **Referencia** |
| --- | --- | --- |
| Contraste audiovisual | Las identidades www-data, gabri, vivian y root aparecen en comprobaciones de pantalla. | Vídeo · 02:24:02; 02:31:58; 02:56:35; 02:59:40 |
| Plugins | WP File Manager 8.0.1 activo contradice interpretar plugins no detectados como plugins inexistentes. | Vídeo · 01:34:30; 02:08:30 |
| Cron y sudo | La línea de /etc/crontab está incompleta; el final satisfactorio usa sudo con ruta absoluta. | Vídeo · 02:44:45; 02:59:40 |

# Ideas importantes de la transcripción

Los tiempos de esta tabla corresponden a la transcripción; puede haber pequeños desfases respecto al vídeo.

| **Tema** | **Idea importante** | **Referencia** |
| --- | --- | --- |
| Arctic | La máquina inicial se abandona tras problemas de funcionamiento. | F001 · 23:55–24:40; 40:42–52:10 |
| Facultad | Cambio a la práctica principal y reconocimiento Linux. | F001 · 52:55–58:44 |
| Respuesta HTTP | Netcat aporta información del servicio aunque haya error de petición. | F001 · 58:52–01:00:12 |
| Descubrimiento web | La ruta /education contiene WordPress. | F001 · 01:02:13–01:05:56 |
| Resolución local | El dominio esperado y el protocolo afectan a la navegación. | F001 · 01:07:12–01:10:25 |
| Componentes | Las versiones del núcleo, temas y plugins no son intercambiables. | F001 · 01:12:52–01:15:49 |
| Usuarios | El formulario diferencia usuario inexistente de contraseña incorrecta. | F001 · 01:16:06–01:17:15; 01:34:40–01:35:17 |
| WPScan | La instalación debe analizarse en su subruta. | F001 · 01:19:47–01:21:21 |
| Herramientas | Burp se bloquea; WPScan obtiene acceso. | F001 · 01:36:10–01:44:23 |
| Panel | Revisar el rol y las funciones tras autenticarse. | F001 · 02:06:34–02:11:38 |
| Archivos PHP | Subida y solicitud del PHP; primera conexión rechazada por falta de escucha. | F001 · 02:14:08–02:18:16 |
| Alternativa | La edición se comenta, pero aparece bloqueada. | F001 · 02:18:17–02:20:29 |
| Cuenta del servicio | La shell corresponde a www-data. | F001 · 02:23:24–02:24:04 |
| Configuración | Se revisa wp-config.php, sin entrar a MySQL. | F001 · 02:27:25–02:30:18 |
| Cambio de identidad | La delegación de PHP permite pasar a gabri. | F001 · 02:30:26–02:31:53 |
| LinPEAS | Los intentos no acreditan un análisis completo. | F001 · 02:34:14–02:40:39 |
| Permisos | Con gabri fallan escritura y renombrado del script. | F001 · 02:42:05–02:46:48 |
| Brainfuck | El archivo local proporciona una credencial para vivian. | F001 · 02:48:34–02:52:32 |
| Búsqueda manual | Las herramientas no garantizan detectar todos los archivos interesantes. | F001 · 02:53:39–02:55:41 |
| Root | La vía final utiliza sudo sobre el script y comprobación de identidad. | F001 · 02:55:55–03:00:50 |

# Actualización de memoria del proyecto

Registro de esta sesión para futuras consultas expresas. Los hechos siguientes no se trasladan automáticamente a otras clases.

| **Categoría** | **Información nueva** | **Certeza** | **Acción futura** |
| --- | --- | --- | --- |
| Sesión | Carlos Castillo · 5 de octubre de 2026 · Hacking Web Machine I. | Alta | Conservar la identidad de esta clase. |
| Práctica | Facultad es la máquina principal; Arctic queda abandonada. | Alta | No presentar Arctic como resuelta. |
| Método | Contrastar enumeración externa con permisos y componentes visibles tras autenticarse. | Alta | Aplicar el contraste al repasar este laboratorio. |
| Linux | Cadena observada: www-data → gabri → vivian → root. | Alta | Repasar qué permiso o evidencia permite cada transición. |
| Límites | No se confirma análisis completo de LinPEAS ni cron como vía funcional. | Alta | Conservar esas limitaciones al reutilizar esta entrega. |
| Precisión técnica | bash -p conserva privilegios efectivos existentes; no los crea. | Alta | Relacionarlo con propietario, SUID e identidad efectiva. |
