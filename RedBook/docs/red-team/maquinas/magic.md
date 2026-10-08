---
tags:
- Máquinas y prácticas
date: '2026-09-24'
author: Carlos Castillo
---

# Magic

<p class="note-meta">2026-09-24 · Carlos Castillo</p>

![](../../assets/img/magic/img001.png)

Mapa de la clase

Magic · Seguridad web y port forwarding

PREGUNTA CENTRAL ¿Qué acepta la web, qué interpreta el servidor y qué puede alcanzar cada equipo?

| **Rama** | **Conceptos y relaciones** |
| --- | --- |
| 01 Alcance | Laboratorio Magic → metodología de auditoría → separar indicios y resultados. |
| 02 Web | Servicios y tecnologías → galería, rutas y login → solicitudes, respuestas y redirecciones. |
| 03 Autenticación | SQL injection → decisión de acceso. Sesión → cookie, atributos y revocación. XSS como hipótesis no confirmada. |
| 04 Archivos | Flujo normal → nombre y Content-Type → contenido real → almacenamiento → interpretación del servidor. |
| 05 Sistema | Cuenta web → permisos y configuración. Servicio MySQL interno ≠ cliente de terminal instalado. |
| 06 Conectividad | Chisel → cliente y servidor → transporte, entrada local y destino. Un puerto ocupado impide abrir el extremo local. |
| 07 Resultado | Base de datos → riesgo de reutilización de contraseña → cambio de usuario narrado. SUID introducido; escalada final pendiente. |
| 08 Complemento | Portfolio → identidad, proyectos y accesibilidad. IA como apoyo sujeto a revisión. |

## Relación entre capas

NAVEGADOR → APLICACIÓN WEB → SERVIDOR → SERVICIO INTERNO

Cada flecha requiere una comprobación distinta: sesión y autorización, tratamiento del archivo, permisos del proceso y conectividad.

Idea de cierre: se practicó el reenvío de un servicio concreto. No se completó una segunda máquina ni la escalada a root.

**CONTENIDO DE CLASE**

# La clase y su alcance

## Qué se trabajó

La sesión del 24 de septiembre de 2026, impartida por Carlos Castillo Sanjuan, se centró en Magic, una máquina de Hack The Box presentada como Linux y de dificultad media. El objetivo fue comprender cómo se relacionan la autenticación de una web, la subida de archivos y el acceso a un servicio que solo está disponible dentro del sistema. GoodGames se menciona como práctica del día anterior; no fue una segunda máquina desarrollada en esta sesión.

El profesor narró un acceso a la aplicación mediante SQL injection, una demostración de ejecución de código asociada a la subida de archivos y una conexión a MySQL mediante Chisel. Después mostró una reutilización de contraseña que permitió cambiar de usuario. La escalada final no se completó: se introdujeron los permisos SUID y se dejó una investigación pendiente.

Objetivo de estudio: distinguir lo que la aplicación acepta, lo que el servidor interpreta y lo que resulta accesible desde cada equipo. Son preguntas diferentes y requieren evidencias diferentes.

## Metodología de auditoría

| **Fase** | **Aplicación en esta clase** |
| --- | --- |
| Planificación | Delimitar Magic como laboratorio y separar una práctica completa del alcance contratado de una auditoría web. |
| Recogida de información | Observar servicios, tecnologías, rutas, solicitudes y comportamiento normal de la aplicación. |
| Análisis de vulnerabilidades | Valorar indicios de fallos de autenticación, gestión de sesiones, subida de archivos y configuración. |
| Pruebas de explotación controladas | Documentar las demostraciones narradas y sus límites, sin dar por obtenidos resultados que quedaron pendientes. |

## Cómo leer estos apuntes

El contenido de clase se basa en la transcripción aportada. Las ampliaciones técnicas corrigen simplificaciones y se identifican con sus fuentes externas. Los resultados se describen como narrados en clase: no se han ejecutado ni reproducido las pruebas. Los apartados conservan la explicación conceptual, los problemas encontrados y sus consecuencias defensivas; no incluyen payloads, credenciales ni una cadena ejecutable de intrusión.

La portada es una recreación ilustrada: Xarxas aparece con camiseta blanca y brazos fuertes, Chema se despide y sale del aula con su camisa roja a cuadros, y Carlos continúa junto a la pizarra. El dibujo humorístico de Xarxas está descrito en la transcripción, pero no se aportó una captura original de esa pizarra. El bocadillo de despedida es un añadido narrativo solicitado para la portada, no una cita literal de clase.

**CONTENIDO DE CLASE**

# Reconocimiento web y autenticación

## Reconocer antes de interpretar

En el reconocimiento se mencionan los puertos externos 22 y 80. La web se presenta como una galería de imágenes con un formulario de acceso y una función de subida. El profesor utiliza Nmap y WhatWeb, revisa el código fuente y presta atención a las rutas y tecnologías visibles. Un banner o una versión aparente sirve como indicio; por sí solo no confirma que exista una vulnerabilidad explotable.

La enumeración de directorios devuelve respuestas Forbidden en algunas rutas. La enseñanza útil para el informe es registrar una prueba realizada y su resultado. Que una carpeta no muestre su listado no demuestra que todos sus archivos estén protegidos: el control sobre el listado y el control sobre cada recurso son independientes. Tampoco una respuesta 403 identifica por sí sola la causa exacta del bloqueo.

## Comparar respuestas con criterio

Burp Suite se emplea para observar las solicitudes de autenticación y sus respuestas. El profesor compara códigos de estado, longitud de respuesta, contenido y redirecciones. La diferencia entre dos respuestas orienta la investigación, pero hay que interpretarla: un cambio puede deberse a la validación de entrada, al estado de sesión o al comportamiento del formulario.

Durante la demostración, la redirección posterior al acceso produjo confusión al mirar la vista renderizada. Se insistió en revisar la respuesta y el destino de la redirección. Una respuesta 302 indica una redirección, no una autenticación correcta en todos los casos. El resultado necesita contexto y comprobación del estado de la aplicación.

## Qué significa SQL injection

SQL injection aparece cuando datos controlados por el usuario alteran la estructura o el significado de una consulta SQL. En la clase se muestra su efecto sobre la decisión de autenticación. La idea central es que una comprobación de credenciales deja de responder a la lógica prevista cuando se mezclan datos y sintaxis de consulta.

También se comentan posibles diferencias de respuesta asociadas a enumeración de usuarios o a una inyección ciega. Se mantienen como hipótesis, no como hallazgos confirmados. La alerta JavaScript visible en el acceso tampoco demuestra por sí misma un XSS: habría que acreditar ejecución de contenido controlado por el usuario en un contexto vulnerable.

Ampliación técnica · OWASP SQL Injection Prevention: las consultas parametrizadas separan datos y código. Deben acompañarse de permisos mínimos para la cuenta de base de datos y de validación adecuada al dato esperado. [E8]

**CONTENIDO DE CLASE Y ACLARACIONES**

# Cookies y gestión de sesiones

## La cookie representa una sesión

La clase utiliza una cookie de sesión de PHP para explicar cómo una aplicación reconoce peticiones posteriores al acceso. Se comenta su reutilización en otro navegador y el riesgo de que una persona ajena obtenga un identificador válido. El valor de la cookie se trata como un secreto; no se reproduce en estos apuntes.

Conviene distinguir autenticación y sesión. La autenticación comprueba quién puede entrar. La gestión de sesión mantiene esa relación durante la navegación. Si la aplicación acepta un identificador vigente, puede asociar las solicitudes a una sesión ya autenticada; por eso hay que proteger su transporte, almacenamiento, duración y revocación.

## Qué protege cada atributo

| **Control** | **Función y límite** |
| --- | --- |
| HttpOnly | Impide que JavaScript lea la cookie mediante las interfaces habituales. No elimina el XSS ni impide que el navegador envíe la cookie en solicitudes. |
| Secure | Restringe el envío de la cookie a conexiones seguras, con las excepciones de localhost documentadas por los navegadores. No sustituye a HttpOnly. |
| SameSite | Limita el envío de cookies en contextos entre sitios según su valor. Ayuda frente a determinados escenarios de CSRF; requiere ajuste al flujo real. |
| Caducidad y revocación | Reducen el periodo de validez y permiten invalidar sesiones. El cierre de sesión debe tener efecto en el servidor. |

Ampliación técnica: los atributos anteriores tienen responsabilidades distintas. No es correcto exigir que Secure y HttpOnly estén ambos desactivados para que exista cualquier riesgo de robo de sesión, ni afirmar que HTTPS elimina todos los riesgos de la aplicación. La explicación de atributos se contrasta con MDN. [E5]

## Dos navegadores no bastan para declarar un fallo

El profesor presenta la simultaneidad de sesiones como un riesgo, especialmente en paneles sensibles. La precisión necesaria es que permitir varias sesiones puede ser una decisión legítima de producto. Para calificarlo como vulnerabilidad hay que conocer la política exigida, el contexto y los controles de detección y revocación. Copiar el mismo identificador tampoco equivale necesariamente a crear dos sesiones independientes en el servidor.

Ampliación técnica · OWASP Session Management: definir una política de sesiones simultáneas, ofrecer mecanismos de cierre y considerar avisos ante accesos nuevos. El riesgo debe evaluarse contra esa política, no solo por contar navegadores abiertos. [E6]

Pendiente de confirmar: la transcripción habla de valores en false, pero no permite recuperar con seguridad todos los nombres y valores de la pantalla. Se conserva el comentario de clase sin inventar una captura ni una configuración exacta.

**CONTENIDO DE CLASE**

# Subida de archivos y validación

## Comprender el flujo legítimo

Antes de interpretar los rechazos, el profesor sube una imagen normal para comprobar el funcionamiento previsto. Se estudian el nombre conservado, la ubicación accesible desde la galería y la relación entre la página y el recurso. Esta observación del flujo normal evita confundir un fallo de interfaz con un problema de validación o de almacenamiento.

La aplicación anuncia formatos de imagen permitidos y rechaza determinadas entradas. En clase se comparan el nombre del archivo, el tipo declarado en la solicitud y su contenido. El resultado narrado es que una validación insuficiente, unida a la interpretación del servidor, permitió ejecución bajo la cuenta del servicio web. El aprendizaje no se reduce a que una subida devolviera un mensaje de éxito: aceptar, almacenar, servir e interpretar son operaciones distintas.

| **Elemento** | **Pregunta que ayuda a resolver** |
| --- | --- |
| Nombre y extensión | ¿Cómo clasifica la aplicación el archivo y qué reglas aplica al nombre? |
| Content-Type | ¿Qué tipo declara el cliente? Es información proporcionada por el remitente. |
| Contenido real | ¿El archivo puede analizarse de forma válida y segura como el formato esperado? |
| Almacenamiento | ¿Dónde se guarda y quién puede recuperarlo? |
| Interpretación | ¿El servidor lo entrega como datos o lo dirige a un componente capaz de ejecutarlo? |

## La extensión no es el contenido

Cambiar el nombre de un archivo no transforma sus datos internos. Del mismo modo, que un analizador reconozca un formato no demuestra que el archivo sea inocuo en todos los sistemas que lo procesarán. La clase muestra la importancia de entender qué comprueba cada componente y de no tomar una comprobación aislada como garantía completa.

También aparece un problema práctico con una imagen de gran tamaño: aumentó el volumen de datos y dificultó el manejo de la solicitud. La transcripción no permite atribuir con certeza el bloqueo a una causa única. La recomendación de estudio es separar tamaño, rendimiento y validez del formato al interpretar un fallo.

Ampliación técnica · OWASP File Upload: combinar lista de formatos permitidos, análisis real del archivo, límites de tamaño, nombres generados, autorización y almacenamiento seguro. Impedir la ejecución en la zona de subidas. Validar solo la extensión, Content-Type o firma inicial no basta. [E4]

**CONTENIDO DE CLASE Y AMPLIACIÓN TÉCNICA**

# Interpretación del servidor y cuenta web

## Qué significa que el servidor interprete un archivo

Un servidor puede entregar un archivo como contenido estático o remitirlo a un intérprete mediante una configuración concreta. Esta distinción explica por qué un recurso aceptado como imagen puede llegar a tener consecuencias diferentes si otra capa lo trata como código. En la demostración se narra ejecución con la identidad www-data, la cuenta del servicio web.

La cuenta que ejecuta la aplicación determina qué archivos y recursos puede utilizar ese proceso. Obtener ejecución en ese contexto no equivale a disponer de permisos de administrador. Para valorar el impacto hay que examinar sus privilegios y accesos efectivos, sin suponer que todas las instalaciones utilizan la misma cuenta o estructura de directorios.

## La precisión sobre Apache

El profesor resume el comportamiento diciendo que Apache atiende a la primera extensión. Esa frase no debe memorizarse como regla general. La documentación de mod\_mime explica que un nombre con varias extensiones puede aportar diferentes metadatos y asociaciones; la interpretación depende de la configuración y de los handlers aplicables. [E3]

Inferencia técnica: el resultado narrado es compatible con una asociación insegura del contenido a un intérprete. No se dispone de la configuración completa del servidor para identificar la directiva responsable ni demostrar que fuera exactamente un caso concreto de mod\_mime. Se evita atribuir un CVE o reconstruir una configuración que no aparece en las fuentes.

## Terminal y configuración de la aplicación

Tras la demostración web se obtiene una conexión de terminal y se mejora su interacción. Más adelante un cambio de usuario falla inicialmente por las características de la terminal. La lección es distinguir el canal de interacción de los permisos: disponer de una sesión cómoda no aumenta por sí mismo los privilegios del proceso.

La revisión del entorno de la aplicación revela un archivo de configuración con datos de conexión a la base de datos. Se menciona un archivo PHP con sufijo numérico y datos de usuario, contraseña, host y nombre de base. Que el navegador no muestre el código fuente de un archivo interpretado no evita que un proceso con permiso de lectura acceda a él en el sistema de archivos.

Consecuencia defensiva: reducir los permisos de la cuenta web y la exposición de secretos. La cuenta de base de datos de la aplicación debe disponer únicamente de las operaciones que necesita. Una credencial accesible al proceso amplía el impacto de comprometer ese proceso.

**CONTENIDO DE CLASE**

# Servicios internos y port forwarding

## La visibilidad depende del origen

La base MySQL se describe como un servicio interno de Magic. Los servicios observados desde el exterior eran SSH y HTTP; la configuración de la aplicación remitía a una base accesible localmente. Esto permite entender por qué un servicio puede estar en funcionamiento y no aparecer como accesible desde otro equipo.

Localhost siempre se interpreta desde el equipo o entorno que realiza la conexión. El localhost del portátil y el localhost de Magic no son el mismo destino. Para razonar sobre una conexión conviene nombrar quién la inicia, desde qué entorno se resuelve la dirección y dónde escucha el servicio.

## Servicio y cliente son componentes distintos

La transcripción utiliza varias veces la frase «no hay MySQL» al fallar una invocación de terminal. La precisión es que no estaba disponible el cliente de línea de comandos invocado. Eso no demuestra que faltara el servicio de base de datos: la propia aplicación lo utilizaba. Tampoco el número de tablas explica que el cliente esté o no instalado.

## Qué aporta el reenvío de un puerto

El port forwarding permite que una conexión a un extremo se transporte hasta un servicio accesible desde otro punto. La clase usa Chisel para explicar esta idea y diferencia el papel de cliente del de servidor. El puerto de transporte del túnel, el puerto de entrada para la aplicación local y el puerto del servicio de destino cumplen funciones diferentes.

| **Concepto** | **Cómo distinguirlo** |
| --- | --- |
| Puerto de transporte | Permite la comunicación entre los componentes del túnel. |
| Puerto de entrada local | Es el extremo al que se conecta la aplicación del equipo de trabajo. Debe poder abrirse sin conflicto. |
| Puerto del servicio | Pertenece al servicio final. Cambiar el puerto de entrada no modifica el puerto en el que escucha ese servicio. |
| Dirección de escucha | Determina desde dónde se puede acceder al extremo. Reenviar no obliga a publicarlo en Internet. |

Ampliación técnica: Chisel implementa túneles TCP/UDP sobre HTTP protegidos mediante SSH. Es un mecanismo de aplicación; no debe explicarse como si necesariamente creara reglas de iptables o cambiara las rutas del sistema. Sus extremos y direcciones de escucha determinan la exposición efectiva. [E2]

El profesor aclara al final que lo realizado fue port forwarding de un servicio concreto. Es una introducción útil para estudiar pivoting, pero no demuestra que se haya recorrido otra red ni comprometido una segunda máquina.

**CONTENIDO DE CLASE Y FUENTES REVISADAS**

# Chisel y el diagnóstico del fallo

## Qué ocurrió durante la demostración

El primer intento no permitió establecer el reenvío esperado. Se revisaron la dirección escrita, la arquitectura del binario, la versión, los puertos y la persistencia del proceso. El profesor probó una versión anterior y cambió el puerto de transporte, pero esas variaciones no resolvieron por sí solas el problema.

La explicación final fue un puerto local ocupado. El extremo que el túnel intentaba abrir entraba en conflicto con otro servicio del equipo de trabajo. Al elegir un puerto local diferente, el profesor narró que pudo conectar con la base de datos. La transcripción identifica 3307 como puerto local alternativo y 3306 como el del servicio de destino; estos valores documentan lo explicado, no una configuración que se haya verificado aquí.

Conclusión del incidente: el fallo no quedó atribuido a un defecto de Chisel 1.12.0. La causa explicada en clase fue el conflicto de escucha local. No se adjuntaron registros suficientes para efectuar un diagnóstico independiente.

## Cómo ordenar la revisión

Para estudiar un fallo de conectividad, separar disponibilidad del programa, compatibilidad con el sistema, comunicación entre extremos, apertura del puerto local y disponibilidad del servicio final. Cambiar varias cosas a la vez impide saber cuál resolvió el problema. Conviene registrar la hipótesis, el cambio realizado y la evidencia que la confirma o descarta.

## Los dos enlaces compartidos

[Chisel 1.12.0 — página oficial de la versión](https://github.com/jpillora/chisel/releases/tag/v1.12.0)

La página revisada presenta una versión de fiabilidad y seguridad, publicada el 29 de agosto de 2026. Sirve como referencia de cambios y como punto de acceso a los archivos disponibles. No acredita por sí misma qué archivo se ejecutó durante la clase. [E1]

[Descarga compartida — Chisel 1.12.0 para Linux ARM64](https://github.com/jpillora/chisel/releases/download/v1.12.0/chisel_1.12.0_linux_arm64.gz)

Este enlace concreto corresponde a Linux ARM64. En cambio, la transcripción insiste en seleccionar Linux AMD64. Son arquitecturas diferentes: el enlace compartido no debe presentarse como el binario universal para cualquier Kali o Linux. El inventario oficial confirma que existen ambas variantes. Se comprobó la presencia del archivo ARM64, sin descargarlo ni ejecutarlo. [E1a]

**CONTENIDO DE CLASE**

# Base de datos y límites del resultado

## Organización de la información

Tras resolver el reenvío, el profesor describe una conexión a MySQL y revisa las bases disponibles. Se mencionan information\_schema y Magic, y una tabla llamada login. La explicación diferencia la base, que agrupa información, de las tablas que organizan sus registros. information\_schema proporciona metadatos; no es la tabla de usuarios de la aplicación.

La consulta mostrada recupera datos de acceso de la web. Después se narra una comprobación del acceso al formulario y la reutilización de una contraseña para un usuario del sistema. Estos apuntes conservan el hecho y el riesgo, sin copiar los valores de las credenciales ni reconstruir consultas de extracción.

## Reutilización de contraseñas

Compartir una contraseña entre la aplicación y una cuenta del sistema conecta dos ámbitos de seguridad. Una exposición en la base de datos puede afectar a otro acceso si ambos utilizan el mismo secreto. La clase ilustra ese impacto con un cambio de usuario narrado como satisfactorio.

El acceso remoto por SSH no prosperó en el intento descrito, mientras que el cambio local de usuario sí se consiguió después de mejorar la interacción con la terminal. La diferencia importa: un puerto accesible no garantiza que un método concreto de autenticación esté permitido. La transcripción no aporta una causa definitiva del fallo de SSH.

Buena práctica: utilizar credenciales diferentes por servicio y propósito, limitar su lectura y rotarlas cuando se expongan. No asumir que una contraseña válida en la web será válida en el sistema ni que un fallo remoto demuestra que el secreto es incorrecto.

## SUID como introducción

Al final se muestran binarios con permisos SUID y se invita a investigar uno de ellos. SUID permite que, bajo las condiciones del sistema, un ejecutable adopte la identidad efectiva de su propietario. Solo implica identidad efectiva de root si el propietario es root y las condiciones de ejecución lo permiten. No concede automáticamente una terminal de administrador. Ampliación contrastada con execve(2). [E7]

No se completa la explotación de ese binario ni se documenta la obtención de root o de una flag final. El nombre exacto del binario y el del usuario local no se fijan en estos apuntes porque la transcripción no los conserva con suficiente claridad. No se han completado recurriendo a un walkthrough externo.

La alternativa de obtener información de la base mediante una herramienta disponible en el propio sistema fue propuesta por un alumno y aceptada como posible vía. Se conserva como alternativa mencionada, no como un segundo procedimiento demostrado íntegramente por el profesor.

**SÍNTESIS DE ESTUDIO**

# Registro de herramientas y conceptos

| **Herramienta** | **Objetivo y uso visto** | **Fase** | **Nivel** |
| --- | --- | --- | --- |
| Nmap | Reconocimiento de servicios externos. | Recogida de información | Practicada |
| WhatWeb | Identificación de tecnologías web. | Recogida de información | Practicada |
| Navegador | Código fuente, galería y almacenamiento de sesión. | Recogida de información | Practicada |
| dirsearch | Enumeración de rutas y lectura de rechazos. | Recogida de información | Practicada |
| Burp Suite | Proxy, Repeater e Intruder; inspección y comparación de peticiones. | Análisis y pruebas controladas | Practicada |
| Python y netcat | Interacción con la terminal durante la demostración. | Pruebas controladas | Practicada |
| Chisel | Demostración y diagnóstico de reenvío de puerto. | Pruebas controladas | Practicada |
| Cliente MySQL | Observación de la estructura y datos de la base. | Pruebas controladas | Practicada |
| file y uname | Tipo de archivo y arquitectura del sistema. | Recogida de información | Practicada |
| Socat y Ligolo | Otras herramientas para estudio posterior. | Sin fase aplicada | Mencionada |
| GTFOBins | Referencia citada al hablar de binarios. | Análisis de vulnerabilidades | Mencionada |

El nivel indica lo que aparece en esta sesión, no el dominio personal de cada alumno. «Pruebas controladas» abrevia en la tabla la fase «Pruebas de explotación controladas». Las herramientas de IA se utilizaron como apoyo de consulta y se discutieron durante el descanso; sus respuestas no se toman como prueba de un resultado.

## Glosario breve

| **Término** | **Significado** |
| --- | --- |
| SQLi | Alteración de una consulta SQL mediante entrada no separada correctamente del código. |
| XSS | Ejecución de contenido de script controlado por un atacante en un contexto web vulnerable. |
| Webshell | Interfaz web que permite ordenar acciones en el servidor. |
| Reverse shell | Canal de terminal cuya conexión se inicia desde el sistema remoto. |
| Handler | Componente al que el servidor asigna el tratamiento de un recurso. |
| Port forwarding | Reenvío de conexiones de un extremo a un servicio de destino. |
| Pivoting | Uso de un punto intermedio para alcanzar recursos o redes fuera del acceso directo inicial. |
| SUID | Permiso especial vinculado a la identidad efectiva del propietario del ejecutable. |

**SÍNTESIS DE ESTUDIO**

# Repaso y conversación complementaria

## Preguntas que deberías poder responder

¿Por qué una respuesta 302 no basta para confirmar un acceso? Porque solo describe una redirección; hay que comprobar el destino y el estado de sesión. ¿Por qué no basta una imagen aceptada para declarar segura la subida? Porque la aceptación, el almacenamiento y la interpretación posterior dependen de controles distintos.

¿Puede existir MySQL sin el cliente de terminal utilizado en clase? Sí: el servicio, sus bibliotecas y el cliente de línea de comandos son piezas diferentes. ¿Puede un túnel fallar aunque el servicio remoto esté activo? Sí: por ejemplo, si el puerto que necesita abrir localmente está ocupado.

¿Cambiar de usuario equivale a conseguir root? No. Hay que comprobar la identidad y los permisos efectivos. ¿Un ejecutable SUID se ejecuta siempre como root? No: importa quién es su propietario y qué restricciones aplica el sistema.

## Lista de repaso

| **Comprobación** | **Criterio de comprensión** |
| --- | --- |
| Evidencia | Distingues observación, hipótesis y resultado narrado. |
| Autenticación | Separas inyección SQL, gestión de sesión y autorización. |
| Archivos | Explicas nombre, tipo declarado, contenido y tratamiento posterior. |
| Conectividad | Identificas los extremos y los tres papeles de los puertos. |
| Diagnóstico | No atribuyes el fallo a una versión sin aislar la causa. |
| Alcance | Recuerdas que la escalada final de Magic quedó pendiente. |

## Portfolio y accesibilidad

Durante el descanso se revisó un portfolio y se propuso una experiencia interactiva para mostrar proyectos. El consejo del profesor fue mantener una presentación sencilla y accesible, con la interacción como opción, y asegurarse de que el visitante entiende quién es el autor y qué trabajo ha realizado. Se comentaron demostraciones, repositorios y una cronología de aprendizaje.

Los participantes señalaron problemas de contraste, brillo, tamaño del texto, repetición de información y consistencia del selector de idioma. También se discutieron el comportamiento en móvil y los retrasos al arrancar demostraciones alojadas en planes gratuitos. Son observaciones de esa conversación, no una auditoría formal de accesibilidad ni una verificación actual de precios o servicios.

La conversación sobre IA trató costes, manejo de datos y calidad de resultados. Las órdenes entre participantes para cambiar una web o crear agentes forman parte de la transcripción: no son encargos de Chema para esta tarea y no se han ejecutado.

**CONSULTADAS EL 24 DE SEPTIEMBRE DE 2026**

# Fuentes y verificaciones externas

La fuente de clase es la transcripción aportada por Chema, desde 12:46 hasta 03:03:21. Las dos imágenes adjuntas son referencias de identidad de Xarxas y Chema. Para Carlos se empleó su ficha ilustrada del proyecto. Las fuentes siguientes se usan como ampliación o contraste; no prueban lo que ocurrió en el laboratorio.

[E1 · Chisel 1.12.0 · página oficial compartida](https://github.com/jpillora/chisel/releases/tag/v1.12.0)

Notas de versión y acceso a los paquetes. Revisada para confirmar la versión enlazada.

[E1a · Descarga compartida · Linux ARM64 comprimido en gzip](https://github.com/jpillora/chisel/releases/download/v1.12.0/chisel_1.12.0_linux_arm64.gz)

[Inventario oficial de archivos de la versión 1.12.0](https://github.com/jpillora/chisel/releases/expanded_assets/v1.12.0)

El inventario confirma ARM64 y AMD64 como variantes distintas. La descarga binaria no se ejecutó ni se sometió a un análisis de seguridad.

[E2 · Chisel · documentación del proyecto](https://github.com/jpillora/chisel)

Naturaleza del túnel y funciones de cliente, servidor y reenvío.

[E3 · Apache HTTP Server · mod\_mime](https://httpd.apache.org/docs/2.4/mod/mod_mime.html)

Apartado Files with Multiple Extensions. Contraste de la simplificación sobre las extensiones.

[E4 · OWASP · File Upload Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html)

Controles de seguridad para recepción, tratamiento y almacenamiento de archivos.

[E5 · MDN · cabecera Set-Cookie](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Set-Cookie)

Funciones diferenciadas de Secure, HttpOnly y SameSite.

[E6 · OWASP · Session Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html)

Políticas de sesión, revocación y sesiones simultáneas.

[E7 · Linux man-pages · execve(2)](https://man7.org/linux/man-pages/man2/execve.2.html)

Identidad efectiva y condiciones de aplicación de SUID.

[E8 · OWASP · SQL Injection Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html)

Separación entre datos y consulta mediante parametrización.

**TRAZABILIDAD DE LA SESIÓN**

# Ideas importantes de la transcripción

| **Tema** | **Idea importante** | **Referencia F001** |
| --- | --- | --- |
| Alcance | Magic es la máquina seleccionada. GoodGames pertenece a la referencia del día anterior. | 17:24–21:47 |
| Metodología | No confundir completar un laboratorio con el alcance de una auditoría web. | 26:14–29:06 |
| Reconocimiento | Servicios externos, tecnologías y revisión de la galería. | 25:28–33:31 |
| Directorios | Registrar el rechazo de listado como resultado de una prueba. | 35:42–36:20 |
| Cookies | Se comentan atributos y riesgo sobre sesiones. | 36:23–37:59 |
| Autenticación | Comparar respuestas y revisar redirecciones en Burp. | 38:17–54:14 |
| Sesiones | Discusión sobre reutilización de cookie y acceso simultáneo. | 55:01–59:39 |
| Flujo normal | Subir una imagen válida y comprender dónde se sirve. | 01:02:14–01:07:51 |
| Validación | Nombre, tipo declarado, contenido e interpretación posterior. | 01:12:10–01:43:50 |
| Portfolio | Interacción opcional, identidad visible y contraste. | 01:45:41–02:07:42 |
| Entorno web | Cuenta del servicio y configuración de la base. | 02:10:07–02:16:45 |
| Xarxas | Dibujo humorístico de brazos y hombros junto a su PC. | 02:17:03–02:18:05 |
| Servicio interno | Diferenciar alcance externo y acceso desde la propia máquina. | 02:18:28–02:25:17 |
| Arquitectura | Selección de Linux AMD64 durante la explicación. | 02:27:43–02:28:35 |
| Diagnóstico | El profesor atribuye el fallo a un puerto local ocupado. | 02:43:33–02:46:21 |
| Datos y usuario | Base Magic, tabla login y reutilización de credencial. | 02:46:24–02:56:31 |
| SUID | Introducción a binarios con permisos especiales; sin escalada final. | 02:56:35–02:59:44 |
| Cierre | Lo practicado fue port forwarding; se propone terminar la máquina otro día. | 02:59:46–03:03:21 |

Los localizadores son las marcas del archivo aportado, no horas del reloj. Las formulaciones de la tabla sintetizan el contenido y deben leerse junto a las aclaraciones técnicas del cuerpo.

**REGISTRO LOCAL DE ESTA CLASE**

# Actualización de memoria del proyecto

| **Categoría** | **Información nueva** | **Certeza** | **Acción futura** |
| --- | --- | --- | --- |
| Sesión | 24/09/2026 · Carlos Castillo Sanjuan · Magic. | Alta | Conservar la identidad y fecha de esta entrega. |
| Temario | Autenticación, subida de archivos y port forwarding con Chisel. | Alta | Repasar las diferencias entre capas y extremos. |
| Diagnóstico | El profesor explicó un conflicto en el puerto local del reenvío. | Alta sobre lo narrado | Si se revisa el fallo, solicitar los registros originales. |
| Arquitectura | Enlace recibido ARM64 y selección oral AMD64. | Alta | Elegir el paquete según el sistema real, sin asumir que coinciden. |
| Resultado | Acceso y cambio de usuario narrados; root no completado. | Alta sobre el alcance | Mantener pendiente la escalada final. |
| Identidad visual | Xarxas de blanco, Chema de cuadros rojos y Carlos en la pizarra. | Alta | Conservar referencias y portada de esta sesión. |
| Apache | No se dispone de la configuración exacta del intérprete. | Baja sobre la causa concreta | No asignar una directiva o CVE sin evidencia. |
| Usuario local | El nombre no queda suficientemente claro en el texto. | Baja | Confirmarlo con una captura antes de fijar el literal. |

## Pendientes de confirmar

Quedan pendientes el nombre literal del usuario local, la configuración exacta que provocó la interpretación del archivo, los valores de cookies mostrados en pantalla y los registros del error de Chisel. La investigación SUID y la escalada final quedan fuera de los resultados completados de esta sesión.

No hay una captura original de la pizarra: el dibujo de portada se recreó a partir de la descripción oral y de las referencias visuales facilitadas. Las ilustraciones no se presentan como fotografías ni como evidencia técnica.

Esta memoria pertenece a la clase de Magic. Conserva decisiones, resultados y dudas de la entrega; no modifica las reglas generales ni se utiliza automáticamente como fuente para otras clases.
