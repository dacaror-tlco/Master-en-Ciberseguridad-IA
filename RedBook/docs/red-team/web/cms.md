---
tags:
- Auditoría web
date: '2026-09-28'
author: Carlos Gómez
---

# CMS

<p class="note-meta">2026-09-28 · Carlos Gómez</p>

![Portada de cómic con Carlos, John, Syra, Kristina y el tractor amarillo](../../assets/img/cms/img001.png)

# Mapa de la clase

**CMS WordPress y Drupal**

De conocer los componentes a justificar los hallazgos y comprender el acceso inicial. Las ramas y relaciones de esta página son editables en Word.

| **Rama** | **Conceptos y relaciones** |
| --- | --- |
| Proyectos y formación | Revisión de informes → entregas individuales Formación + simulación → concienciación Métricas y necesidades del usuario → evolución del producto |
| Gobernanza de IA | Datos enviados → detección de información sensible → políticas Tokens de entrada y salida → coste → modelo adecuado a la tarea Guardarraíles y permisos → reducción del riesgo |
| Arquitectura de un CMS | Núcleo + tema + extensiones + configuración + base de datos Proveedores y actualizaciones → superficie de ataque Identificación de componentes → revisión de versiones |
| Auditoría de WordPress | Wappalyzer → indicios tecnológicos WPScan → componentes y versiones API de WPScan → información de vulnerabilidades Prerrequisitos + contexto + prueba → hallazgo defendible |
| Laboratorio Drupal | Red local → descubrimiento → servicios → web y rutas Drupal 7 → análisis de avisos → prueba controlada Meterpreter → shell → lectura de configuración → base de datos |
| Límite de la sesión | Se relata acceso inicial y lectura de usuarios y hashes Pendiente: descifrado y escalada de privilegios Una shell más cómoda no significa más privilegios |

## Método de auditoría

**Planificación → Recogida de información → Análisis de vulnerabilidades → Pruebas de explotación controladas**

**Idea central** No saltarse los preliminares: primero identificar el objetivo y entender lo observado; después decidir qué probar.

# 1 Objetivos y contexto de la sesión

La clase estudia cómo se compone un gestor de contenidos y cómo esa arquitectura condiciona su auditoría. El objetivo es pasar de una lista de tecnologías o alertas a una explicación razonada del riesgo: qué componente está afectado, qué condiciones exige el fallo y qué resultado se ha demostrado.

Profesor: Carlos Gómez Pintado. Fecha: 28/09/2026. El laboratorio utiliza Drupal 7. La transcripción recoge el nombre de la máquina como «Tenon», pero su denominación exacta queda pendiente de confirmar con el ZIP o una captura del campus.

## Qué debes poder explicar al terminar

- Distinguir el núcleo de WordPress, sus temas y sus plugins, y relacionarlos con la cadena de suministro.
- Explicar para qué sirve el token de WPScan y separar identificación de componentes, avisos de vulnerabilidad y validación.
- Interpretar una dirección IPv4 y su prefijo, distinguir puertos de servicios y justificar la selección del objetivo.
- Diferenciar exploit, payload, sesión Meterpreter, shell del sistema y escalada de privilegios.
- Relacionar la configuración de Drupal con su base de datos sin confundir las distintas cuentas.

## Informes y entrega de proyectos

Contenido de clase. Carlos pide revisar el informe generado con IA, completar nombres y campos pendientes y comprobar que la portada y el contenido tienen sentido. Cada integrante debe subir su entrega, aunque el informe sea compartido, para que quede registrada en Classroom. La participación y el conocimiento del trabajo realizado también se comentan como criterios de valoración.

Se aclara cómo localizar la invitación y los enunciados en Classroom. Para revisar el código, se propone facilitar el enlace del repositorio o invitar al profesor si es privado. Las referencias orales al plazo no son consistentes entre sí; conviene confirmar la fecha en el enunciado oficial.

## Evolución del producto de concienciación

Se propone sustituir una integración de Teams bloqueada por una pregunta diaria dentro de la plataforma y recordatorios por correo con enlace directo. La formación explica; la simulación comprueba si el usuario aplica lo aprendido. El producto de análisis de QR podría evolucionar hacia campañas de concienciación con métricas, filtros por fechas y formación asociada a los errores observados.

La práctica 2 se presenta como un laboratorio web con elementos dinámicos; la práctica 3, como una mejora de la primera. La recomendación comercial de priorizar concienciación es una opinión del profesor, no una garantía de rentabilidad. Los requisitos de licencias e integración comentados por los alumnos no se verifican en esta sesión.

# 2 Gobernanza de IA y uso de recursos

Contenido de clase. Antes de entrar en los CMS, Carlos muestra un monitor de uso de IA. Su finalidad declarada es observar qué se envía a los modelos, detectar datos sensibles, registrar actividad y estimar el coste. La demostración sirve para plantear un problema de seguridad: cuando una organización incorpora agentes, debe conocer qué recursos pueden leer, qué pueden modificar y qué información sale de su entorno.

## Datos y controles

La confidencialidad protege frente a accesos o divulgaciones indebidas. La integridad trata de preservar la información frente a modificaciones no autorizadas. La disponibilidad busca que los datos y servicios estén accesibles cuando corresponda. La gobernanza incluye además responsabilidades, políticas, supervisión y decisiones sobre el ciclo de vida del dato; no se reduce a saber dónde está almacenado.

| **Función presentada** | **Qué intenta resolver** |
| --- | --- |
| Inspección del prompt | Detectar información personal o claves antes de su envío. |
| Eventos y alertas | Permitir revisar solicitudes e incidencias. |
| Políticas y guardarraíles | Limitar usos o contenidos que la organización no permite. |
| Consumo por equipo y modelo | Relacionar tokens de entrada y salida con el gasto. |
| Selección de modelo | Ajustar la capacidad y el coste al trabajo solicitado. |

## La metáfora del tractor

La comparación entre una pala y un tractor ilustra el sobredimensionamiento: una tarea pequeña puede resolverse con una herramienta menos costosa. El criterio útil es elegir el modelo que alcance la calidad necesaria con un coste y un tiempo aceptables. Un modelo pequeño también puede necesitar más reintentos; por eso el ahorro debe evaluarse sobre la tarea terminada, no solo sobre el precio de un token.

El monitor descrito cuenta entradas y salidas y propone cambiar de modelo según la tarea. Esto se presenta como comportamiento de la herramienta del profesor; la transcripción no permite auditar su cobertura real sobre todas las aplicaciones, ni confirmar las cifras empresariales comentadas.

## Qué significa un guardarraíl

Carlos lo compara con una regla de firewall aplicada a la IA. La analogía ayuda a entender una restricción, pero una instrucción en el prompt no equivale a un control de acceso técnico. Como ampliación conceptual, los permisos de las herramientas y los controles de salida deben aplicarse también fuera del texto que recibe el modelo. Un agente con acceso excesivo sigue teniendo un problema aunque se le pida comportarse bien.

**Para recordar** Contexto es la información disponible durante una interacción; no es entrenamiento del modelo. Añadir instrucciones o referencias a una herramienta modifica su contexto o configuración, no demuestra que sus parámetros se hayan entrenado.

# 3 Arquitectura de los CMS

Un CMS, del inglés Content Management System, es un sistema de gestión de contenidos. Permite crear, organizar y publicar información mediante una interfaz de administración. La clase menciona WordPress, Drupal, Magento, Shopify y Wix como ejemplos del ecosistema; no todos comparten el mismo modelo de despliegue ni ofrecen el mismo grado de control sobre el servidor.

## Las piezas de WordPress

| **Pieza** | **Función** | **Qué revisar** |
| --- | --- | --- |
| Núcleo o core | Funciones básicas y mecanismos comunes del CMS. | Versión, mantenimiento y configuración. |
| Tema o theme | Presentación y estructura visual del contenido. | Código, versión, origen y actualizaciones. |
| Plugin | Añade o modifica funcionalidades. | Permisos, rutas, dependencias y avisos aplicables. |
| Base de datos | Almacena contenidos, cuentas y configuración. | Acceso, privilegios y protección de datos. |
| Servidor y runtime | Sirven HTTP y ejecutan el código. | Configuración del servidor y del intérprete. |

Carlos utiliza la imagen de un corcho al que se añaden piezas. Un tema cambia la presentación; un plugin puede añadir formularios, funciones de comercio o integración con otros servicios. La separación es útil para estudiar, aunque temas y plugins pueden contener lógica y no están aislados por una frontera de seguridad.

## Cadena de suministro

Cada componente introduce código de un proveedor. Mantener actualizado el núcleo no elimina un fallo en una extensión. También importa la procedencia de las actualizaciones, el mantenimiento del proyecto y los permisos con los que se ejecuta. Una extensión vulnerable y una actualización comprometida son problemas relacionados con las dependencias, pero describen causas distintas.

La clase insiste en revisar núcleo, tema y plugins por separado. Como matiz, la explotación puede depender de combinaciones de versiones, roles o ajustes; no basta con afirmar que sus vulnerabilidades son siempre independientes. Tampoco cada versión de cada plugin tiene necesariamente un fallo conocido. La popularidad y el precio no prueban la seguridad.

## Tecnología y despliegue

WordPress utiliza PHP y puede desplegarse con servidores como Apache o Nginx. Linux es habitual, pero encontrar PHP no demuestra el sistema operativo, y encontrar Apache no demuestra por sí solo el lenguaje de la aplicación. Wappalyzer aporta indicios que deben corroborarse. [R1]

**Ampliación técnica** La medida de base es mantener núcleo, temas y plugins, reducir componentes innecesarios y proteger permisos y credenciales. Un resultado de identificación tecnológica no equivale a una vulnerabilidad confirmada. [R1]

# 4 WPScan y el papel de su API

Contenido de clase. WPScan se presenta como un escáner especializado en WordPress. Se comparan ejecuciones con y sin token y se revisan componentes y avisos en la pantalla compartida. Las incidencias con el dominio y el pegado del token recuerdan que, antes de interpretar una salida, hay que comprobar el destino y la sintaxis introducidos.

## Enumerar y consultar vulnerabilidades son funciones distintas

Corrección técnica. WPScan puede identificar componentes y versiones sin un token de su API. El token permite consultar el servicio de información sobre vulnerabilidades; no desbloquea de forma general la detección de plugins. Tampoco es una credencial de la web examinada ni concede acceso a su administración. La documentación distingue expresamente los metadatos locales de los datos de vulnerabilidades. [R2, R3]

| **Sin token de API** | **Con token de API** |
| --- | --- |
| Puede obtener indicios sobre WordPress, temas y plugins según las opciones y lo que exponga el sitio. | Añade la consulta de avisos asociados a las versiones detectadas. |
| La ausencia de avisos de la API no acredita seguridad. | Un aviso requiere revisar versión, configuración y prerrequisitos. |
| La calidad del inventario depende de la detección. | El token no sustituye la validación manual ni los permisos de auditoría. |

## Lectura de las opciones comentadas

| **Opción** | **Significado** |
| --- | --- |
| --url | Dirección base de la instalación que se analiza. |
| --api-token | Token del servicio de WPScan; debe tratarse como un secreto. |
| -e u o --enumerate u | Enumeración de usuarios, mencionada en clase. |
| --passwords | Opción documentada para comprobaciones de contraseñas; la referencia oral a «-p» es imprecisa. |

Los ejemplos de clase se dirigieron a webs mencionadas por los participantes. Estos apuntes documentan la explicación; no trasladan una autorización de clase a nuevas pruebas. No se reproduce el token dictado ni se ejecuta ningún escaneo al elaborar el documento.

## Cómo interpretar el inventario

La salida comentada incluye servidor web, versión del CMS, tema, robots.txt, XML-RPC, readme y WP-Cron. Son datos que orientan la revisión. La presencia de un fichero o una función no demuestra un impacto. La versión de WordPress reconocida por voz como «7 1 2» y las versiones de plugins citadas quedan pendientes de contraste con la salida original; no se convierten en datos confirmados.

# 5 De una alerta a un hallazgo defendible

La idea más importante del análisis de WPScan es que una lista de avisos no sustituye una auditoría. Para cada candidato hay que comprobar el componente instalado, la versión, la funcionalidad afectada y los permisos necesarios. Después se determina si la condición existe en el entorno y qué impacto puede demostrarse.

| **Pregunta** | **Decisión que permite tomar** |
| --- | --- |
| ¿Coincide el componente y su versión? | Descartar coincidencias erróneas o conservar una hipótesis. |
| ¿Requiere autenticación o un rol concreto? | Determinar el escenario de acceso y los prerrequisitos. |
| ¿La función vulnerable está habilitada y es accesible? | Evaluar si el recorrido afectado existe en este despliegue. |
| ¿Qué prueba se ha realizado y qué demuestra? | Separar posibilidad técnica de resultado confirmado. |
| ¿Qué datos o funciones quedan afectados? | Valorar impacto y justificar la prioridad. |

## Autenticación y autorización

Autenticarse es acreditar una identidad. La autorización determina qué puede hacer esa identidad. Un aviso de missing authorization describe una ausencia o un fallo de comprobación de permisos; no implica necesariamente acceso anónimo. Hay que leer sus condiciones concretas.

Si una vulnerabilidad exige una cuenta y no se dispone de ella, puede quedar sin validar dentro del alcance actual. Eso no demuestra que el sistema esté libre del fallo: puede existir un escenario con usuarios legítimos, cuentas comprometidas o un rol específico. Se registra la condición pendiente y se justifica la prioridad, en lugar de borrar el riesgo.

## Qué permite un XSS almacenado

Un XSS almacenado conserva contenido que después se interpreta de forma insegura en el navegador de otra persona. La clase lo relaciona con el robo de cookies, pero su impacto es más amplio: puede modificar lo mostrado o realizar acciones dentro del contexto de la víctima. Una cookie HttpOnly no puede leerse directamente desde JavaScript, pero esa protección no elimina el XSS. [R4, R5]

La ausencia de un login público no basta para descartar el impacto: pueden existir administradores, otras interfaces o información accesible al navegador. Deben estudiarse el punto donde se almacena el contenido, quién lo visita y qué controles limitan la ejecución. La solución principal es tratar los datos de forma segura según su contexto, no confiar en que el sitio parezca estático. [R4]

**Ejemplo de redacción** «Se identifica una versión asociada a un aviso que exige un rol autenticado. No se ha validado su explotación porque no se dispone de ese rol en el alcance actual». Es más preciso que afirmar «es explotable» o «no existe riesgo».

# 6 Los preliminares del laboratorio

Contenido de clase. John guía la práctica y Carlos insiste en no empezar por un escaneo sin conocer antes la red y el objetivo. Se revisa la configuración de la máquina local, se descubre el segmento y se contrastan varios equipos. La lección es metodológica: disponer de una IP no explica todavía qué representa ni si pertenece al alcance.

## IPv4 y prefijo de red

Una dirección IPv4 tiene 32 bits, agrupados en cuatro octetos. En una red /24, los primeros 24 bits identifican la red y quedan 8 para la parte de host. Si la dirección es 10.0.2.18/24, la red es 10.0.2.0/24; en el caso ordinario, 10.0.2.0 identifica la red y 10.0.2.255 es broadcast. El prefijo y la dirección de red describen cosas distintas.

Matiz de la explicación oral: 10.0.0.0/24 no es todo Internet ni un rango mayor que 10.0.2.0/24; son dos subredes distintas con el mismo tamaño. El error consiste en examinar el segmento equivocado. La conectividad real y la autorización determinan qué redes pueden revisarse.

ifconfig  
sudo netdiscover -r 10.0.2.0/24

Sintaxis normalizada a partir de la clase. ifconfig muestra interfaces y parámetros de red. En Netdiscover, -r delimita el rango; el uso de ARP requiere trabajar en el segmento de red local correspondiente y disponer de los permisos necesarios. El resultado esperado es una relación de equipos detectados, no una lista de vulnerabilidades. [R6]

## Direcciones que se consolidan durante la práctica

| **Dato** | **Lectura prudente** |
| --- | --- |
| 10.0.2.18 | Dirección del equipo local, confirmada después al explicar la conexión de retorno. |
| 10.0.2.17 | Objetivo usado al analizar el servicio web. |
| 10.0.2.3 | Otra respuesta examinada durante el descubrimiento; no se demuestra su identidad exacta. |

## Qué aporta el TTL

Se compara una respuesta con TTL 64 con otra de TTL 255. Estos valores pueden orientar una hipótesis sobre el sistema o dispositivo, pero no lo identifican de manera concluyente. El TTL inicial depende de la implementación y el observado puede disminuir al atravesar routers. La detección de sistemas de Nmap combina varias pruebas, no una equivalencia rígida entre un número y un sistema operativo. [R7]

**Resultado de esta fase** Se selecciona el objetivo del laboratorio y se pasa a estudiar sus servicios. La selección combina contexto de virtualización, direcciones y respuestas; el TTL solo es un indicio.

# 7 Servicios y enumeración de la web

nmap -sV -sC 10.0.2.17

Sintaxis normalizada de las opciones identificables en clase. -sV intenta reconocer servicios y versiones; -sC ejecuta los scripts de la categoría predeterminada. La transcripción menciona una opción de tasa con valor 1500, pero no permite distinguir el parámetro exacto y se conserva como pendiente. No se añade a la línea reconstruida. [R8, R9]

| **Elemento comentado** | **Interpretación** |
| --- | --- |
| SSH | Es un protocolo y un servicio, no el nombre de un puerto. No se obtiene acceso SSH en la sesión. |
| 80 con HTTP | Sirve la aplicación web que se abre en el navegador. |
| 111 y RPC | Se relaciona con servicios RPC; su presencia no demuestra por sí sola una compartición de archivos. |
| Apache 2.2.22 | Versión mencionada para investigar avisos; el banner requiere corroboración. |
| Drupal 7 | Identificación del CMS del laboratorio; falta fijar la versión menor. |

## Por qué leer toda la salida

La práctica muestra que el resultado de Nmap puede aportar mucho más que puertos abiertos. Los scripts y la detección de servicios ayudan a localizar rutas e identificar aplicaciones. Un banner puede ser incompleto, estar modificado o no reflejar los parches aplicados; una coincidencia de versión orienta la investigación, pero necesita contexto.

## robots.txt y navegación manual

Se inspeccionan robots.txt, rutas de administración y endpoints de usuarios. robots.txt expresa instrucciones de rastreo para robots que las respeten. No es un mecanismo de autenticación ni una garantía de que una URL no aparezca indexada. Una ruta indicada allí sigue necesitando controles de acceso si contiene información privada. [R10]

En el laboratorio, la combinación admin/admin falla y también se prueba otra contraseña frecuente sin éxito. El registro de una cuenta queda pendiente de aprobación administrativa. La recuperación de contraseña utiliza correo y no proporciona acceso durante la prueba. Se comenta una prueba básica de SQLi y se continúa con la navegación y la inspección del código fuente, sin demostrar una evasión del login.

## Enumerar rutas y conservar hipótesis

Se propone Gobuster y se utiliza dirsearch mientras se sigue revisando la web. La transcripción no conserva el comando completo ni un inventario fiable de rutas encontradas. El análisis de Apache se aplaza y se prioriza Drupal; no entender un aviso no es motivo suficiente para descartarlo como falso positivo. Debe quedar anotado para investigación posterior.

# 8 Drupalgeddon y verificación de versiones

Contenido de clase. Se investiga una ejecución remota de código en Drupal y se elige un módulo relacionado con Drupalgeddon 2. RCE significa Remote Code Execution: ejecución de código en el sistema remoto dentro de los permisos y condiciones que permita el fallo. La versión principal Drupal 7 es una pista, pero por sí sola no decide qué aviso se aplica.

## Cronología técnica corregida

| **Aviso** | **Fallo y fechas** | **Referencia para Drupal 7** |
| --- | --- | --- |
| SA-CORE-2014-005 CVE-2014-3704 | SQL injection. Publicado en octubre de 2014. | Corregido en 7.32. [R11] |
| SA-CORE-2018-002 CVE-2018-7600 | RCE. Publicado el 28/03/2018. Asociado a Drupalgeddon 2. | Afecta a versiones desde 7.0 anteriores a 7.58. [R12] |
| SA-CORE-2018-004 CVE-2018-7602 | RCE relacionada con el aviso de marzo. Publicado el 25/04/2018. | Afecta a versiones desde 7.0 anteriores a 7.59. [R13] |

Estos avisos no son una única vulnerabilidad. La narración de que el parche de 2014 produjo Drupalgeddon 2 al día siguiente no concuerda con su cronología. El aviso de abril de 2018 sí declara una relación con el de marzo. Las puntuaciones orales y la explicación del reparto de mercado no se utilizan como datos verificados.

La mención de «7.59» en la investigación no debe confundirse con el límite de 7.58 de CVE-2018-7600. Para seleccionar una prueba hay que contrastar el aviso exacto y el módulo, no combinar los rangos de fallos distintos. La sesión relata una conexión conseguida; eso no recupera automáticamente la versión menor que falta en la fuente.

## La frase de la portada y las credenciales

Corrección técnica. Drupal 7 solicita definir usuario y contraseña de la cuenta administrativa durante la instalación. admin/admin no es una credencial universal predeterminada de Drupal. Tampoco admin con contraseña vacía lo es. La frase de Carlos se mantiene como guiño ilustrado, mientras que el contenido técnico conserva el resultado de clase: ese intento de acceso falló. [R14]

## Vigencia del laboratorio

Ampliación técnica. Drupal 7 alcanzó el fin de soporte comunitario el 5 de enero de 2025. Las versiones de corrección anteriores se incluyen para comprender avisos históricos, no como recomendación de despliegue actual. El laboratorio permite estudiar fallos conocidos; un entorno de producción requiere una versión mantenida y un plan de migración adecuado. [R15]

# 9 Exploit payload y Metasploit

Contenido de clase. Se revisa un ejemplo en Exploit-DB y después se abre Metasploit con msfconsole. El interés didáctico es entender qué hace la herramienta y por qué la selección de un módulo necesita criterio. La comodidad de un framework no elimina la necesidad de comprender su destino, sus requisitos y sus resultados.

## Conceptos que no deben confundirse

| **Concepto** | **Significado** |
| --- | --- |
| Vulnerabilidad | Debilidad que permite un comportamiento no previsto bajo determinadas condiciones. |
| Exploit | Técnica o código que aprovecha esa debilidad. |
| Payload | Carga útil que realiza una acción dentro del contexto obtenido. |
| Handler | Componente que gestiona una conexión de sesión; no es necesariamente Netcat. |
| Meterpreter | Payload y entorno de sesión de Metasploit con comandos propios. [R16] |

La caja y el contenido sirven como analogía de exploit y payload. La comunicación necesita un transporte compatible, pero HTTP, TCP y UDP no son alternativas del mismo nivel: HTTP puede utilizar TCP como transporte. Tampoco todas las explotaciones necesitan una conexión de retorno ni los mismos parámetros.

## Direcciones y sentido de la conexión

| **Parámetro** | **Cómo se interpreta en una sesión inversa** |
| --- | --- |
| RHOST o RHOSTS | Objetivo o conjunto de objetivos que espera el módulo. |
| RPORT | Puerto del servicio remoto al que se dirige la prueba. |
| LHOST y LPORT | Dirección y puerto del extremo que debe recibir el retorno. |
| TARGETURI | Ruta base o URI que espera ese módulo; debe leerse su descripción. |

En una reverse shell el objetivo inicia la conexión de retorno. En una bind shell se conecta el operador a un servicio de escucha del objetivo. LHOST no significa siempre 127.0.0.1: debe ser una dirección alcanzable en ese escenario. Una configuración válida depende de red, cortafuegos y compatibilidad del payload. [R16]

## Elegir e interpretar el módulo

Se comenta una ruta de tipo exploit/unix/webapp y el payload PHP Meterpreter reverse TCP. «Unix» es una familia o categoría de compatibilidad; Linux es un sistema de tipo Unix, no la base histórica de Unix. La fecha más reciente de un módulo no demuestra que sea mejor para el caso. Hay que comprobar vulnerabilidad, versión, plataforma y condiciones.

show options muestra parámetros y obligatoriedad. Los comandos use, set y run se explican durante la demostración. Los índices numéricos del buscador son circunstanciales y no identificadores estables. Un módulo auxiliary puede realizar tareas diversas; no debe suponerse que todos sus módulos son pasivos o inocuos.

# 10 Sesión obtenida y configuración de Drupal

Contenido de clase. La demostración relata la apertura de una sesión Meterpreter. Algunos comandos habituales de Linux no se interpretan como se esperaba, por lo que se consulta información con comandos propios de Meterpreter y después se obtiene una shell del sistema. Se describe el uso de Python y una pseudoterminal para mejorar la interacción.

## Una sesión más cómoda no da más privilegios

Meterpreter no es Bash. Que un comando falle en su intérprete no prueba que el programa no exista en el sistema remoto. El comando shell de Meterpreter abre una shell del sistema, si la plataforma lo permite. La función pty.spawn se menciona para crear una pseudoterminal; eso mejora la interacción, pero no equivale por sí solo a una estabilización completa con control de trabajos.

Durante la sesión se identifica el contexto www-data y un directorio de la aplicación en /var/www. Es coherente con un proceso del servidor web, pero ni ese usuario ni esa ruta son universales. El DocumentRoot depende de la configuración de Apache; usar un CMS no obliga a eliminar el componente html del nombre del directorio.

## Qué se enumera tras el acceso inicial

Se revisan ficheros de la aplicación y una pista del laboratorio que dirige hacia la configuración. También se visita /home. Este directorio contiene habitualmente carpetas personales, pero no es un inventario completo de cuentas: pueden existir usuarios de servicio, cuentas con otros directorios y fuentes externas de identidad. La alusión a /etc/passwd es pertinente para estudiar cuentas locales.

| **Elemento** | **Observación y significado** |
| --- | --- |
| web.config | Se abre inicialmente, pero no es el archivo del que se extrae la conexión a la base de datos. |
| sites/default/settings.php | Ruta de configuración examinada en el laboratorio. |
| Usuario y contraseña de base de datos | Permiten a la aplicación conectarse al motor de datos; no son necesariamente credenciales del panel o de SSH. |
| Pistas o flags | Orientan el ejercicio; la transcripción no conserva valores de flags que deban copiarse. |

## Lectura local y exposición web

Que la cuenta del proceso web pueda leer la configuración no significa que el archivo se descargue en texto claro por HTTP. En la práctica se accede después de obtener ejecución. Los datos de conexión pueden estar en settings.php, en un archivo incluido o en otra fuente de secretos según el despliegue. La ruta sites/default es habitual; Drupal también admite configuraciones multisitio. [R14]

**Riesgo demostrado en el relato** El acceso inicial al proceso de la aplicación permite llegar a información que esta necesita para funcionar. La defensa debe limitar los privilegios de esa cuenta y el alcance de las credenciales de base de datos.

# 11 Base de datos y límite del resultado

Contenido de clase. Tras leer la configuración se abre una sesión de MySQL con el usuario de base de datos. Se listan bases, se selecciona la correspondiente a Drupal y se inspeccionan tablas. La lectura de users muestra nombres de cuenta y hashes de contraseña; se mencionan admin y Fred. No se recuperan contraseñas en texto claro durante el fragmento final.

## Tres identidades diferentes

| **Ámbito** | **Para qué sirve la cuenta** | **Qué no demuestra** |
| --- | --- | --- |
| Sistema operativo | Ejecuta el proceso web; en la sesión se identifica www-data. | Ser administrador del sistema. |
| Base de datos | Autoriza consultas sobre los datos de la aplicación. | Poder iniciar una sesión SSH. |
| Aplicación Drupal | Gestiona usuarios y permisos dentro del CMS. | Disponer de una cuenta local equivalente. |

## Hash no es contraseña cifrada recuperable

Un hash de contraseña es un verificador derivado de la contraseña mediante una función de almacenamiento. No se descifra como un mensaje cifrado. Un ataque de adivinación compara candidatos procesados con los parámetros adecuados. Su éxito depende del algoritmo, el coste, la sal y la resistencia de la contraseña; disponer del hash no garantiza recuperar el secreto.

El profesor propone estudiar el tipo de hash y continuar con posibilidades de escalada. Quedan anunciadas la revisión de sudo, permisos SUID, tareas programadas y recursos como GTFOBins. El relato no demuestra una escalada a root ni un acceso posterior con las cuentas de Drupal. La referencia a Mimikatz aparece como ejemplo de herramientas, no como uso real en este laboratorio.

## Qué queda conseguido y qué queda pendiente

| **Estado** | **Resultado** |
| --- | --- |
| Relatado como conseguido | Identificación del objetivo y del servicio web; sesión inicial; shell del sistema; lectura de configuración; conexión a MySQL; consulta de usuarios y hashes. |
| Pendiente de la siguiente clase | Identificar y probar la resistencia de los hashes, estudiar vías locales de escalada y completar el laboratorio. |
| Pendiente de evidencia exacta | Nombre de la máquina, versión menor de Drupal, salidas completas y valores literales de flags. |

## Corrección sobre el motor de datos

Drupal no utiliza siempre MySQL. Drupal 7 también contempla PostgreSQL y SQLite. Que esta práctica utilice MySQL no convierte ese motor en una propiedad universal de todos los CMS. Del mismo modo, una cuenta de base de datos no debe suponerse válida para otros servicios. [R17]

**Conclusión del laboratorio** El acceso al servicio web y a su base de datos está descrito; el control administrativo del sistema todavía no. «Estabilizar la shell» y «escalar privilegios» son resultados diferentes.

# 12 Registro de comandos y lectura de resultados

Se recogen comandos identificables o sintaxis normalizada, sin ejecutar pruebas. Los valores no preservados por la transcripción no se reconstruyen como si fueran evidencia. Las opciones de escaneo producen tráfico y requieren un alcance de laboratorio definido.

| **Comando o uso** | **Objetivo y opciones** | **Resultado e interpretación** |
| --- | --- | --- |
| ifconfig | Consultar interfaces y parámetros de red. | Se revisa la IP local; no identifica por sí solo el objetivo. |
| netdiscover -r | Descubrir equipos por ARP en el rango indicado. | Se comparan direcciones; ARP trabaja en el segmento local. |
| ping | Comprobar respuestas ICMP y observar TTL. | Una respuesta confirma conectividad de ese tipo; el TTL no acredita un sistema. |
| nmap -sV -sC | Detectar servicios y ejecutar scripts predeterminados. | La clase comenta HTTP, RPC, Apache y Drupal; falta la salida completa. |
| wpscan --url | Seleccionar la instalación WordPress. | Obtiene información técnica según detección y opciones. |
| --api-token y -e u | Consultar avisos de WPScan y enumerar usuarios, respectivamente. | El token pertenece a WPScan; no autentica en el sitio. |
| dirsearch | Buscar rutas web; se usa durante la navegación. | No se conserva la orden completa ni sus resultados detallados. |
| msfconsole; show options | Abrir Metasploit y leer la configuración del módulo. | Revisar destino, parámetros requeridos y contexto antes de interpretar la prueba. |
| sysinfo; getuid; shell | Comandos comentados en Meterpreter. | Consultan contexto o abren la shell del sistema; no son comandos equivalentes de Bash. |
| ls; ls -la; cd; cat | Listar, ver detalles, cambiar de directorio y leer archivos. | Permiten estudiar el contexto accesible. Leer un secreto no convierte la cuenta en root. |
| mysql -u dbuser -p | -u selecciona la cuenta; -p solicita su contraseña. | Se relata acceso al motor de datos. La contraseña no se reproduce. |
| SHOW DATABASES; SHOW TABLES; | Consultar bases visibles y tablas de la base seleccionada. | Los resultados dependen de los permisos del usuario conectado. |
| SELECT \* FROM users; | Sintaxis normalizada de la consulta comentada. | Se relatan nombres y hashes. El asterisco selecciona todas las columnas. |
| sudo -l | Consultar permisos sudo del usuario. | Se menciona para continuar la revisión; no hay un resultado de escalada confirmado. |

La consulta USE se explica como selección de base de datos, pero no se fija un nombre literal a partir de la transcripción ambigua. La estabilización con Python se documenta por su función; no se inventa la línea ejecutada. Las órdenes de lectura pueden mostrar información sensible, por lo que sus resultados se conservan solo en la evidencia necesaria.

# 13 Herramientas y vocabulario

| **Herramienta** | **Objetivo y fase** | **Nivel en esta sesión** |
| --- | --- | --- |
| Wappalyzer | Identificación tecnológica · Recogida de información. | Practicada en demostración |
| WPScan | Inventario y avisos · Recogida de información y Análisis de vulnerabilidades. | Practicada |
| Netdiscover y ping | Descubrimiento y conectividad · Recogida de información. | Practicadas |
| Nmap | Servicios y versiones · Recogida de información. | Practicada |
| dirsearch | Rutas web · Recogida de información. | Practicada |
| Gobuster | Alternativa de enumeración de rutas. | Mencionada |
| Exploit-DB | Consulta de información de una prueba · Análisis de vulnerabilidades. | Consultada en clase |
| Metasploit y Meterpreter | Prueba y sesión del laboratorio · Pruebas de explotación controladas. | Practicadas |
| MySQL | Consulta de datos tras el acceso · Pruebas de explotación controladas. | Practicada |
| Shodan | Búsqueda de tecnologías expuestas · Recogida de información. | Mostrada |
| Hydra, Burp Suite, Netcat | Comparaciones y ejemplos de herramientas. | Mencionadas |
| GTFOBins y Mimikatz | Referencia a posibles tareas posteriores. | Mencionadas; uso no demostrado |

## Glosario de estudio

| **Término** | **Definición** |
| --- | --- |
| CMS / core / plugin | Gestor de contenidos / núcleo / extensión funcional. |
| CVE / CVSS | Identificador de una vulnerabilidad publicada / sistema de puntuación de severidad. |
| RCE / XSS | Ejecución remota de código / ejecución de contenido activo inseguro en el navegador. |
| ARP / TTL | Resolución de direcciones en la red local / límite de vida o saltos de un paquete IP. |
| Endpoint / URI | Punto de acceso de una aplicación / identificador de un recurso. |
| SUID / sudo | Permiso especial de ejecución de Unix / mecanismo para ejecutar con la autorización de otra cuenta. |
| Hash / sal | Verificador derivado de una contraseña / dato que diferencia el cálculo entre contraseñas almacenadas. |
| Token de API | Credencial para utilizar una API; no debe confundirse con los tokens de texto de un LLM. |

# 14 Riesgos buenas prácticas y repaso

## Medidas derivadas de la clase

Ampliación técnica. Mantener un inventario de núcleo, temas, módulos y plugins permite localizar dónde aplicar una corrección. Las actualizaciones deben probarse y proceder de fuentes confiables. Conviene retirar componentes que no se necesitan y reducir los permisos de escritura y administración. Las copias de seguridad y la capacidad de restauración completan esa protección. [R1]

Las credenciales de base de datos deben limitarse a las necesidades de la aplicación. La cuenta del servicio web no debería administrar todo el sistema. También hay que proteger archivos y copias de configuración, evitar su exposición directa y revisar la actividad ante indicios de compromiso. Si un secreto se ha divulgado, cambiarlo exige actualizar sus consumidores y comprobar que siguen funcionando.

En el informe de auditoría, cada hallazgo debe relacionar evidencia, condiciones, impacto y corrección. Un endpoint de XML-RPC, un readme o robots.txt no se califican como vulnerabilidad solo por existir. Un aviso con autenticación puede seguir siendo relevante aunque todavía no se haya validado. La prioridad debe explicarse con el escenario real.

## Lista de comprobación

- ¿Se conocen la red, el objetivo y el alcance antes de generar tráfico?
- ¿Se han separado servicio, puerto, tecnología y versión?
- ¿La versión vulnerable y sus prerrequisitos se han contrastado con el aviso adecuado?
- ¿Se distingue lo inferido de la salida realmente observada?
- ¿Se ha documentado el usuario efectivo de la sesión y el alcance de sus permisos?
- ¿Las credenciales del sistema, del CMS y de la base de datos se tratan por separado?
- ¿El cierre enumera lo conseguido y lo que sigue pendiente?

## Preguntas de autoevaluación

| **Pregunta** | **Respuesta breve** |
| --- | --- |
| ¿El token de WPScan es del sitio auditado? | No. Autoriza el acceso a los datos del servicio de WPScan. |
| ¿TTL 64 demuestra Linux? | No. Es un indicio que necesita corroboración. |
| ¿Una shell con Bash demuestra escalada? | No. Hay que comprobar el usuario y los privilegios efectivos. |
| ¿Una contraseña de MySQL permite entrar por SSH? | No necesariamente; son ámbitos de autenticación distintos. |
| ¿Qué se dejó para continuar? | El análisis de los hashes y las vías de escalada local. |

# Referencias técnicas

Ampliaciones y correcciones consultadas el 28/09/2026. Las referencias oficiales contrastan conceptos; los resultados de la práctica proceden de la transcripción de la clase. Los identificadores R enlazan con las aclaraciones del cuerpo.

[R1 WordPress · Hardening WordPress](https://developer.wordpress.org/advanced-administration/security/hardening/)

[R2 WPScan · Repositorio y funcionamiento de la API](https://github.com/wpscanteam/wpscan)

[R3 WPScan · Documentación de usuario y enumeración](https://github.com/wpscanteam/wpscan/wiki/WPScan-User-Documentation)

[R4 OWASP · Prevención de Cross Site Scripting](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html)

[R5 OWASP · Gestión de sesiones y HttpOnly](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html)

[R6 Netdiscover · Repositorio oficial del escáner ARP](https://github.com/netdiscover-scanner/netdiscover)

[R7 Nmap · Métodos de fingerprinting de sistemas](https://nmap.org/book/osdetect-methods.html)

[R8 Nmap · Detección de servicios y versiones](https://nmap.org/book/man-version-detection.html)

[R9 Nmap · Scripting Engine y scripts predeterminados](https://nmap.org/book/man-nse.html)

[R10 Google Search Central · Qué hace robots.txt](https://developers.google.com/search/docs/crawling-indexing/robots/intro)

[R11 Drupal · FAQ de SA-CORE-2014-005](https://www.drupal.org/forum/general/news-and-announcements/2014-10-15/faq-on-sa-core-2014-005)

[R12 Drupal · SA-CORE-2018-002](https://www.drupal.org/sa-core-2018-002)

[R13 Drupal · SA-CORE-2018-004](https://www.drupal.org/sa-core-2018-004)

[R14 Drupal 7 · Instalador y cuenta administrativa](https://www.drupal.org/docs/7/install/step-4-run-the-installation-script)

[R15 Drupal · Fin de soporte de Drupal 7](https://www.drupal.org/about/announcements/blog/drupal-7-has-reached-end-of-life-psa-2025-01-06)

[R16 Rapid7 · Working with Payloads](https://docs.rapid7.com/metasploit/working-with-payloads/)

[R17 Drupal 7 · Requisitos de sistema y bases de datos](https://www.drupal.org/docs/7/system-requirements/overview)

## Lectura de la fuente de clase

La transcripción facilitada abarca desde 07:33 hasta 03:06:27. Se han retirado repeticiones del reconocimiento de voz, incidencias de audio, conversaciones de descanso y datos personales ajenos al estudio. Se conserva el original en la sesión. Los errores técnicos relevantes se aclaran en el cuerpo y las dudas sobre resultados exactos permanecen identificadas.

# Ideas importantes de la transcripción

| **Tema** | **Idea importante** | **Referencia** |
| --- | --- | --- |
| Entrega e IA | Revisar informes y completar campos; cada integrante registra su entrega. | 09:37–23:41 |
| Proyecto formativo | Pregunta diaria y recordatorios como alternativa a la integración no disponible. | 25:53–28:25 |
| Concienciación | Unir formación con simulaciones y medir resultados para orientar mejoras. | 30:40–40:08 |
| Prácticas | Práctica 2 web; práctica 3 como evolución de la primera. Confirmar enunciados y plazos. | 40:23–42:12 |
| Gobernanza de IA | Monitorizar datos, uso, permisos y coste de los modelos. | 42:13–55:44 |
| Modelo adecuado | La metáfora del tractor explica el sobredimensionamiento de recursos. | 44:25–49:56 |
| CMS | Núcleo, presentación y funcionalidades forman una aplicación compuesta. | 56:19–01:08:59 |
| Suministro | Las dependencias amplían la superficie que debe revisarse. | 01:12:05–01:19:18 |
| WPScan | Comparación con y sin token; la API aporta información de vulnerabilidades. | 01:20:03–01:27:24; 01:48:18–02:06:49 |
| Priorización | Leer requisitos de autenticación, contexto e impacto antes de reportar. | 02:01:17–02:05:10 |
| Red | Revisar IP y prefijo, descubrir equipos y seleccionar el objetivo. | 02:12:25–02:20:35 |
| Servicios | Interpretar Nmap y distinguir puertos de servicios. | 02:20:36–02:25:47 |
| Web | Examinar rutas, registro, recuperación y credenciales; admin/admin falla. | 02:24:11–02:32:33 |
| Drupalgeddon | Se investiga RCE y se revisa un exploit; rangos corregidos con avisos oficiales. | 02:32:49–02:36:24 |
| Metasploit | Seleccionar módulo, entender payload y comprobar opciones. | 02:36:24–02:48:34 |
| Acceso inicial | Se relata sesión Meterpreter y paso a una shell del sistema. | 02:48:34–02:54:28 |
| Configuración | La pista dirige a settings.php y a las credenciales de base de datos. | 02:56:24–02:59:59 |
| Datos y continuación | Se consultan usuarios y hashes; descifrado y escalada quedan pendientes. | 03:00:03–03:03:21 |
| Portada | Preliminares, tractor, errata y frase de admin/admin se conservan como guiños. | 03:03:29–03:06:17 |

# Actualización de memoria del proyecto

Registro de esta sesión. Las observaciones siguientes pertenecen a la clase del 28/09/2026 y no se convierten por sí solas en reglas generales ni en resultados de otras prácticas.

| **Categoría** | **Información nueva** | **Certeza** | **Acción futura** |
| --- | --- | --- | --- |
| Arquitectura | Núcleo, tema y extensiones exigen una revisión diferenciada. | Alta | Mantener inventario y justificar avisos aplicables. |
| WPScan | El token consulta datos de vulnerabilidades; no es una cuenta del objetivo. | Alta | Distinguir inventario, correlación y validación. |
| Laboratorio | Se relata acceso al proceso web y consulta de la base de datos de Drupal. | Alta sobre el relato | Conservar salidas originales cuando se aporten. |
| Identidad de máquina | «Tenon» es la grafía reconocida; falta confirmación documental. | Baja | Verificar nombre en el ZIP o campus. |
| Versiones | Se identifica Drupal 7; no queda fijada la versión menor. | Media | Contrastar con captura o archivo del laboratorio. |
| Continuación | Hash y escalada se proponen para el siguiente día. | Alta | No registrar root ni contraseñas recuperadas sin prueba. |
| Gobernanza de IA | Se muestran control de datos y seguimiento de coste como funciones del monitor. | Alta sobre la presentación | Distinguir demostración de cobertura auditada. |
| Portada | Carlos, John, Syra y Kristina protagonizan la portada creada para esta fecha. | Alta | Reutilizar la imagen conservada para revisiones de estos apuntes. |

## Síntesis para estudiar

El recorrido de la clase une arquitectura, enumeración y criterio. Primero se identifica qué existe; después se comprueba qué avisos pueden aplicarse y con qué requisitos. La práctica de Drupal muestra cómo un acceso al proceso web puede abrir la lectura de su configuración y, con ella, el acceso a los datos de la aplicación. Esa progresión debe describirse sin confundirla con control total del sistema.

Las aclaraciones que conviene retener son concretas: admin/admin no es una contraseña universal de Drupal; el token de WPScan no crea la capacidad de detectar plugins; un TTL no confirma un sistema operativo; un XSS puede tener impacto más allá de las cookies; una shell estabilizada conserva los privilegios que tenía; y una credencial solo prueba acceso en el servicio donde se ha validado.
