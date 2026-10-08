---
tags:
- Máquinas y prácticas
date: '2026-10-02'
author: Carlos Castillo
---

# Repaso semanal VII - Devel

<p class="note-meta">2026-10-02 · Carlos Castillo</p>

![](../../assets/img/repaso-semanal-vii-devel/img001.png)

Mapa de la sesión

Devel → dos vías de acceso → diagnóstico de privilegios

| **Rama** | **Conceptos y relaciones** |
| --- | --- |
| 1 Contexto y método | Planificación → Recogida de información → Análisis de vulnerabilidades → Pruebas de explotación controladas |
| 2 Servicios publicados | FTP anónimo + HTTP / IIS → archivos comunes → comprobar escritura con TXT → comprobar publicación e interpretación |
| 3 Ruta Metasploit | MSFvenom → ASPX → handler coherente → Meterpreter. Arquitectura x86 y sesiones. Suggester y módulos fallan; no se acredita escalada automática. |
| 4 Ruta manual | ASPX generado o archivo RAW adaptado → FTP → navegador → shell en Netcat. Transferencia por HTTP y certutil. |
| 5 Identidad y tokens | whoami + systeminfo → Windows 7 Enterprise x86. whoami /priv → SeImpersonatePrivilege Enabled. Token primario y de suplantación. |
| 6 Escalada y evidencia | JuicyPotato x86 + componente compatible → token privilegiado → proceso → consola SYSTEM. Corregir arquitectura, argumentos, CLSID y escucha. |

Idea central: cada cambio de fase necesita una comprobación. Una herramienta sugerida, una descarga o un intento no equivalen a un resultado obtenido.

# Devel y el propósito del repaso

La clase del 2 de octubre de 2026, impartida por Carlos Castillo Sanjuan, utiliza la máquina Devel de Hack The Box para comparar una resolución apoyada en Metasploit con una vía manual. El acceso inicial parte de la relación entre FTP y el servidor web IIS. La segunda mitad profundiza en la identidad de una cuenta de servicio, los tokens de Windows y el uso de JuicyPotato en un Windows 7 Enterprise de 32 bits.

El objetivo de estudio es comprender las decisiones que conectan la enumeración, el acceso inicial y la escalada de privilegios. La demostración manual termina con una consola identificada como SYSTEM, después de corregir varios problemas concretos. Conocer esos fallos permite interpretar mejor qué acredita cada prueba y evita confundir una transferencia de archivos o un intento de ejecución con un acceso privilegiado confirmado.

El profesor insiste en disponer de varias herramientas y en elegirlas según el contexto. La comparación entre automatización y trabajo manual no se plantea como una competición: una herramienta automatizada puede agilizar una tarea, mientras que la vía manual permite comprender las dependencias y diagnosticar errores. Las referencias a SQLmap y otras herramientas en la introducción son comparaciones metodológicas; no significan que se hayan utilizado para resolver Devel.

La práctica también sirve para reforzar un hábito: repetir máquinas y justificar cada paso. La dificultad no depende solo de que haya más comandos, sino de relacionar información obtenida en fases anteriores. Una cuenta, un archivo o una configuración pueden adquirir valor más adelante. La sesión introduce conceptos de Windows que se retomarán con mayor detalle al estudiar escalada de privilegios y Directorio Activo.

## Metodología de auditoría aplicada

| **Fase** | **Pregunta que orienta el trabajo** | **Evidencia de la sesión** |
| --- | --- | --- |
| Planificación | Qué laboratorio y qué vías se van a comparar | Devel y comparación Metasploit frente a vía manual |
| Recogida de información | Qué servicios, sistema e identidad aparecen | FTP, HTTP, IIS, sistema operativo y contexto del servicio |
| Análisis de vulnerabilidades | Qué condiciones permiten avanzar y qué requisitos faltan | Relación FTP y web, permisos de escritura, arquitectura y privilegios |
| Pruebas de explotación controladas | Qué resultado se demuestra realmente en el laboratorio | Acceso inicial y comprobación del contexto privilegiado final |

## Primeras pistas de red

La respuesta de ping muestra un TTL de 127. El profesor lo utiliza como pista de un sistema Windows. Esa señal orienta la enumeración, pero el reconocimiento posterior de servicios y la información del propio sistema son los elementos que permiten sostener la identificación con mayor precisión.

Nmap detecta el puerto 21 de FTP y el puerto 80 de HTTP. El reconocimiento más detallado muestra Microsoft FTP, acceso anónimo permitido y Microsoft IIS 7.5. El listado de FTP incluye elementos propios de una raíz web, entre ellos aspnet\_client, iisstart.htm y welcome.png. Su presencia sugiere una relación entre el espacio accesible por FTP y lo que publica HTTP; esa relación debe comprobarse durante la práctica.

El valor de la enumeración no está en ejecutar siempre el mismo comando sin leerlo. El puerto, el servicio, el acceso permitido y los archivos presentes aportan hipótesis distintas. Un FTP accesible no implica por sí mismo permisos de escritura, ni un archivo subido implica que IIS lo interprete como código. La práctica conecta estas comprobaciones para avanzar de una pista a un resultado.

# Relacionar FTP con el contenido publicado por IIS

**Contenido de clase.** La enumeración presenta dos servicios que conviene estudiar juntos: FTP con acceso anónimo y una web cuyo servidor se identifica como Microsoft IIS 7.5. En el listado del FTP aparecen un directorio asociado a ASP.NET, una página de inicio y una imagen de bienvenida. Al abrir la web se reconoce esa misma imagen. La coincidencia de nombres constituye un indicio de que ambos servicios exponen contenido relacionado; todavía hace falta comprobar qué relación existe y qué operaciones permite cada servicio.

El razonamiento parte de una pregunta sencilla: si un archivo está disponible por FTP y también por HTTP, ¿qué ocurrirá con un archivo nuevo subido al FTP? Antes de responder hay que separar varios hechos. Poder autenticarse de forma anónima no demuestra que se permita escribir. Ver archivos comunes no demuestra que todas las rutas estén sincronizadas. Poder descargar un archivo tampoco equivale a que el servidor web vaya a interpretarlo como código. Estas condiciones se investigan durante la práctica en lugar de darlas por resueltas desde el principio.

Se plantean dos líneas de trabajo. La primera consiste en descargar contenido accesible y analizarlo por si revela rutas, credenciales u otros datos útiles. La segunda consiste en comprobar si existe escritura en una ubicación que la web publique. Esta segunda posibilidad podría convertirse en ejecución remota de código si el servidor interpreta el tipo de archivo subido. En este laboratorio se relaciona esa posibilidad con ASP y ASPX, formatos que el profesor asocia al entorno de IIS y ASP.NET observado.

La revisión de la web permite reconocer la página de inicio y la imagen de bienvenida. En el FTP se recorren los directorios disponibles, incluidos los relacionados con ASP.NET y un subdirectorio de versión. El profesor no encuentra contenido adicional de interés en esos directorios y decide que una descarga indiscriminada aportaría poco a esta investigación concreta. Se trata de una decisión basada en lo que acaba de enumerar, no de una regla que haga innecesario revisar archivos en cualquier FTP.

## Respuestas HTTP y comprobación de rutas

Las peticiones a ciertas rutas conocidas devuelven una prohibición de acceso, mientras que una ruta de prueba inexistente devuelve una respuesta de recurso no encontrado. El profesor utiliza esa diferencia para reforzar la correspondencia entre los directorios del FTP y la estructura web. El propósito es contrastar la hipótesis de publicación compartida; no pretende obtener un listado web de cada directorio.

**Precisión pendiente de verificación técnica.** En la explicación oral se simplifica la respuesta 403 como prueba de existencia y se presenta el bloqueo del listado de directorios como una configuración generalmente aplicable a todo el árbol. Los apuntes conservan el uso que se hizo de esas respuestas como indicios del laboratorio, sin convertir esas formulaciones en garantías generales sobre cualquier servidor.

La comprobación también ayuda a contemplar alternativas: el FTP podría contener una copia antigua o un respaldo del contenido web, en lugar de alimentar directamente la publicación. La semejanza visual no resuelve por sí sola la dirección de esa relación. Para resolverla se necesita una prueba de escritura cuyo efecto pueda observarse después desde el otro servicio.

## Descubrimiento de contenido y límites del diccionario

Se realiza descubrimiento de rutas con dirsearch y un diccionario pequeño. La herramienta encuentra el directorio relacionado con ASP.NET, que ya se había identificado por FTP. A partir de esa ruta se puede continuar de forma manual o utilizar búsqueda recursiva para repetir el descubrimiento dentro de los directorios encontrados.

Una intervención plantea utilizar la opción de recursividad. El profesor explica que suele avanzar por rutas concretas para controlar el alcance de la revisión: en sitios con muchos directorios, explorar automáticamente cada rama puede prolongar mucho la búsqueda. También señala que no siempre confía en los resultados de la recursividad. Su preferencia de trabajo no implica que la búsqueda recursiva sea inútil; responde a la necesidad de seleccionar qué comprobar y entender qué está haciendo la herramienta.

El resultado depende de las palabras propuestas. Un directorio con un nombre de versión poco habitual puede no aparecer si ese nombre no forma parte del diccionario. Por tanto, que el descubrimiento no encuentre una ruta no elimina la evidencia que ya se tiene de ella por FTP. Las dos vías de enumeración se complementan: una permite ver nombres existentes y la otra comprueba su exposición desde la web.

# Probar primero con un archivo inocuo

La comprobación decisiva utiliza un archivo de texto de prueba dedicado a Chema. Se sube mediante FTP y se consulta desde la web. El profesor da por conseguida la visualización del archivo, lo que confirma en esta práctica que el contenido escrito por FTP se publica por HTTP.

Esta prueba responde a dos preguntas de forma separada: el acceso utilizado permite subir un archivo y ese archivo queda accesible desde el servicio web. Reduce la incertidumbre antes de introducir un contenido ejecutable. La recomendación de clase es empezar por un texto sencillo, una imagen o un archivo vacío apropiado para la prueba. El archivo elegido debe ser inocuo y adecuado al entorno autorizado.

La disponibilidad del texto no demuestra todavía que se pueda ejecutar código. El siguiente paso del laboratorio comprueba una condición adicional: si un archivo de un tipo interpretado por la aplicación puede activar una conexión desde el servidor. Conviene conservar esta progresión al explicar el hallazgo: acceso anónimo, escritura, publicación y ejecución son observaciones diferentes.

# Integrar el acceso inicial con Metasploit y Meterpreter

Se elige primero una vía integrada en Metasploit. El propósito es disponer de una sesión con la que utilizar después los módulos del entorno. Para ello se prepara con MSFvenom un archivo ASPX orientado a Windows y a una conexión inversa de Meterpreter por TCP. La selección debe corresponder al sistema objetivo, al formato que interpreta la web y al tipo de sesión que recibirá el manejador.

La configuración explicada utiliza una dirección de retorno y un puerto de escucha. El profesor repite la dirección 10.10.15.226 y el puerto 6767. Estos valores pertenecen a su laboratorio y no constituyen valores universales. La transcripción describe los componentes del proceso, pero no conserva una línea íntegra y fiable de generación; por ello no se reconstruye aquí un comando ejecutable juntando fragmentos de voz.

Meterpreter se presenta como una sesión con funciones propias, distinta de limitarse a una consola ordinaria del sistema. La ventaja buscada es conservar un contexto sobre el que ejecutar módulos posteriores. Desde esa sesión también se puede abrir una consola del sistema, pero hacerlo no convierte ambos niveles en la misma interfaz.

## Leer los errores de transferencia

Durante la subida del archivo la conexión FTP se interrumpe. El primer intento fallido podría confundirse con una restricción de escritura, pero el profesor identifica la caída de conexión, vuelve a conectar y continúa. Después comprueba el listado para confirmar la presencia del archivo.

Esta incidencia deja una enseñanza metodológica concreta: un fallo operativo no invalida por sí solo la hipótesis que se está probando. Antes de concluir que el servidor rechaza un tipo de archivo, hay que leer el error y distinguir problemas de conexión, permisos y comportamiento de la aplicación. En este caso, la causa indicada durante la clase es la desconexión del FTP.

## El manejador debe esperar el mismo tipo de sesión

En Metasploit se utiliza el módulo exploit/multi/handler para recibir la conexión. Se revisan sus opciones y se ajustan dirección y puerto. El profesor insiste especialmente en el payload: tener bien esos dos valores no basta si el manejador espera una shell genérica mientras el archivo generado intenta establecer una sesión Meterpreter.

Se muestra también una opción relacionada con la continuidad del manejador tras una sesión y se deja la escucha en segundo plano. La explicación permite comprender por qué resulta útil conservar el receptor mientras se trabaja con otras opciones de la consola. La transcripción no recoge de forma suficientemente limpia todos los literales de configuración para publicarlos como una receta exacta.

Al solicitar el archivo desde el navegador, la página permanece cargando y el profesor señala la apertura de una sesión Meterpreter. Después revisa la sesión identificada con el número 1, entra en una consola del sistema y contrasta la información de red con la máquina objetivo. Esta es una obtención de acceso inicial declarada en clase; no representa todavía una escalada de privilegios.

# Enumeración local y arquitectura

Tras obtener acceso se plantea estudiar el sistema con WinPEAS o mediante las funciones de Metasploit. Se recuerda que hay versiones de WinPEAS para arquitecturas distintas y que debe escogerse la compatible con el sistema. En la sesión se identifica un entorno x86 y se señala la variante de 32 bits como la pertinente. WinPEAS se presenta como alternativa, pero no se ejecuta en este tramo.

También se realiza una exploración manual de directorios de usuarios en busca de las flags. Algunas rutas no contienen lo esperado y otras presentan denegaciones de acceso. El profesor no confirma dónde están las flags ni obtiene una durante estas comprobaciones. La posible ubicación dentro de otro perfil de usuario queda como hipótesis.

Una observación práctica se refiere a nombres con espacios: si el autocompletado no ayuda, se propone introducir la ruta entre comillas para evitar problemas de interpretación. La transcripción contiene nombres de perfiles y rutas deformados, por lo que no se normalizan como si se hubieran leído directamente en pantalla.

# Sugerencias de explotación local: función esperada y fallo observado

La alternativa integrada es Local Exploit Suggester. Su finalidad explicada consiste en estudiar información del sistema a través de una sesión ya abierta y proponer módulos locales potencialmente aplicables. Se selecciona la sesión mediante su identificador y se revisan las opciones requeridas.

Es importante distinguir una sugerencia de una vulnerabilidad demostrada. El resultado esperado es una lista de candidatos que todavía deben comprobarse. La herramienta no convierte automáticamente cada candidato en una escalada viable, ni elimina la necesidad de revisar arquitectura, condiciones del sistema y resultado de la ejecución.

En la demostración real el módulo devuelve errores y no produce el resultado esperado. Se consideran distintas posibilidades: un problema al identificar la arquitectura, el estado de la sesión, características del Windows antiguo o el funcionamiento de la máquina del laboratorio. Ninguna de estas explicaciones queda confirmada como causa raíz.

Se abre otra sesión durante las pruebas. Un alumno advierte que debe seleccionarse el identificador de la sesión nueva, en lugar de continuar utilizando el de la anterior. La corrección es relevante aunque no solucione el fallo: las opciones de un módulo deben apuntar a la sesión viva y adecuada, no a un número memorizado de un intento previo.

Para enseñar qué aspecto tendría una salida satisfactoria, el profesor consulta un write-up y muestra una imagen de referencia. Esa imagen sirve para explicar la lista de candidatos y sus estados. No es una salida obtenida en su ejecución de ese momento. La diferencia debe conservarse: la clase explica el funcionamiento esperado, mientras que la prueba en directo sigue fallando.

# Intentos de escalada automatizada y límites del diagnóstico

Se prueba un módulo local asociado en la explicación a MS10-015. El profesor consulta una descripción que lo relaciona con escalada desde una sesión de bajos privilegios, arquitectura de 32 bits y una vulnerabilidad del núcleo. La transcripción no ofrece el nombre completo del módulo ni un identificador CVE verificable; esos datos no se completan por intuición.

Los intentos no establecen la nueva sesión esperada. Se revisan parámetros, se cambian puertos y se investiga un posible conflicto con un manejador existente. El profesor contempla que procesos o sesiones anteriores estén interfiriendo y recomienda reiniciar la máquina del laboratorio si resulta necesario. Cambiar parámetros y repetir intentos constituye aquí una actividad de diagnóstico; no demuestra que los conflictos sospechados sean la explicación del problema.

También se mencionan otros módulos mediante referencias parciales, entre ellas MS10-092 y otros identificadores incompletos. La fuente no permite recuperar todos sus nombres ni sus condiciones. El resultado de conjunto permanece igual: no se acredita una escalada automatizada satisfactoria. Más adelante se observa que algunas sesiones han muerto; se vuelve a obtener una sesión, pero el nuevo intento tampoco resuelve la escalada.

El profesor resume las ventajas y dificultades del enfoque integrado. MSFvenom facilita preparar formatos y payloads; Metasploit organiza sesiones y módulos. Esa comodidad puede dificultar entender un fallo si se desconoce qué hace cada módulo. La práctica se orienta entonces a repetir el acceso inicial con una shell convencional y continuar con un análisis manual. Las afirmaciones sobre saturación de binarios, procesos o cambios de la plataforma se conservan como explicaciones propuestas, no como diagnósticos probados.

Se anuncia que el camino manual permitirá explicar la suplantación de identidad y la familia de técnicas conocida como Potato. También se anticipa la importancia de las versiones. Estas materias quedan anunciadas en este tramo; su desarrollo corresponde a la continuación de la clase.

# Repetir el acceso inicial con una shell convencional

Después del descanso se reinicia la máquina del laboratorio como medida de preparación. El profesor indica que, tras el reinicio, los archivos anteriores ya no están disponibles. A continuación presenta dos maneras de preparar un ASPX para establecer una shell convencional: generarlo con MSFvenom o utilizar un archivo obtenido de un repositorio de GitHub.

En la primera vía se cambia el tipo de payload respecto al usado para Meterpreter. La idea es obtener una shell de Windows que pueda recibirse con Netcat. Se crea un archivo nombrado como shell manual, se vuelve a conectar al FTP y se sube el archivo. Se organiza el trabajo en terminales dedicadas a generación, transferencia y recepción para evitar confundir funciones.

Se prepara la escucha y se solicita el ASPX desde el navegador. El profesor muestra que la shell llega a Netcat. Este resultado confirma un segundo modo de acceso inicial y permite continuar sin depender de una sesión Meterpreter. No confirma todavía privilegios elevados.

## Alternativa basada en un archivo de GitHub

La segunda vía parte de una reverse shell ASPX localizada en GitHub. Se recomienda trabajar con la vista RAW para obtener el contenido del archivo, en vez de guardar la página de presentación del repositorio. Se mencionan wget para descargar y nano para editar, aunque la fuente no aporta una URL fiable ni una secuencia completa de comandos.

Se adapta la dirección de retorno y se prepara un receptor con el puerto correspondiente. Durante la transferencia vuelve a caer la conexión FTP, por lo que se reconecta antes de completar la subida. Tras solicitar el archivo por HTTP, el profesor da por establecida también esta shell.

Las dos vías conservan el mismo mecanismo del laboratorio: preparar un archivo compatible, escribirlo por FTP, disponer de un receptor coherente con su configuración y provocar su interpretación desde la web. Lo que cambia es el origen del archivo y la interfaz receptora. La enseñanza de fondo consiste en comprender las condiciones de la cadena y comprobar cada una, sin confundir la herramienta que prepara el archivo con el servicio que lo publica o con el programa que recibe la conexión.

# Identidad del proceso y privilegios de Windows

El acceso inicial a la web sitúa la sesión en el contexto de una cuenta de servicio. Ese contexto no equivale a administrar el equipo. Antes de elegir una escalada es necesario saber quién está ejecutando la consola, qué sistema operativo hay y qué privilegios conserva su token. La clase utiliza whoami, systeminfo, whoami /priv y whoami /all para reunir esa información.

systeminfo identifica el laboratorio como Microsoft Windows 7 Enterprise. La arquitectura que condiciona la demostración es x86, es decir, 32 bits. No basta con reconocer la familia Windows: un ejecutable preparado para otra arquitectura puede fallar antes de que se llegue a comprobar la técnica elegida. Esta diferencia explica uno de los errores de la práctica y afecta tanto a JuicyPotato como al binario de Netcat.

whoami /priv concentra la salida en los privilegios del contexto actual. whoami /all reúne también identidad, identificador de seguridad o SID e información de grupos. La lectura útil no consiste en buscar un nombre y detenerse: hay que interpretar su descripción y el estado que aparece junto a él. En el laboratorio se observa SeImpersonatePrivilege con estado Enabled. También aparecen otros privilegios habilitados y deshabilitados; no se demuestra una escalada para cada uno de ellos.

La cuenta del grupo de aplicaciones de IIS se compara didácticamente con una cuenta de servicio web de Linux. La comparación ayuda a situar el nivel inicial de acceso, pero no implica que los modelos de permisos de ambos sistemas sean idénticos. La sesión de la aplicación y la cuenta SYSTEM representan contextos distintos, y el cambio debe comprobarse mediante la identidad de la consola resultante.

# Tokens y suplantación

Un token de acceso representa la identidad y los permisos asociados a un contexto de ejecución. El profesor usa la analogía de un carné: permite entender por qué una operación puede estar autorizada para una identidad y denegada para otra. El valor de la analogía es separar a la persona o proceso que ejecuta una acción del contexto de seguridad que Windows utiliza para decidir si la permite.

La explicación distingue un token primario, asociado al proceso, y un token de suplantación, empleado para actuar en el contexto de otra identidad. La palabra suplantación se utiliza aquí para traducir impersonation. No debe confundirse con conocer la contraseña de ese usuario ni con haber iniciado una sesión interactiva normal con sus credenciales.

SeImpersonatePrivilege permite suplantar a un cliente después de la autenticación. La clase lo presenta como una capacidad que puede formar parte del funcionamiento de servicios web o de bases de datos. Por ello, su mera presencia no demuestra que un sistema esté comprometido. En el laboratorio resulta relevante porque se combina con una vía que permite obtener un token privilegiado y usarlo para iniciar un proceso con otro contexto.

El mecanismo explicado puede resumirse en cuatro relaciones: una cuenta de servicio dispone del privilegio; se provoca una autenticación de un servicio privilegiado hacia un punto controlado; la herramienta obtiene el token en ese intercambio; y se utiliza ese contexto para ejecutar un proceso. El objetivo mostrado es llegar a NT AUTHORITY\SYSTEM. No se deduce que cualquier usuario con ese privilegio pueda suplantar incondicionalmente a cualquier otro: la demostración depende también de la versión, arquitectura y componentes disponibles.

La distinción central es entre disponer de un permiso y disponer además de una técnica compatible para aprovecharlo. El profesor insiste en inspeccionar el estado Enabled de la práctica. La clase no estudia en detalle todos los casos en los que un privilegio presente pero deshabilitado podría activarse, por lo que ese punto queda fuera de la conclusión demostrada.

# Selección de JuicyPotato y límites de la comparación

Se mencionan distintas herramientas de la familia Potato y otras técnicas de suplantación: JuicyPotato, JuicyPotatoNG, RoguePotato, GodPotato y PrintSpoofer, además de otros nombres encontrados durante la búsqueda. La enumeración sirve para mostrar que no existe un único binario válido para todos los equipos. En esta sesión, la herramienta que se utiliza y se depura es JuicyPotato para x86.

La orientación oral relaciona JuicyPotato con Windows 7 y versiones antiguas de Windows Server, y menciona alternativas para Windows 10 y Server 2019. Esta orientación se debe conservar como una comparación introductoria de clase, no como una matriz exhaustiva o vigente de compatibilidad. No se prueban esas alternativas en sus respectivos sistemas. Elegirlas exige comprobar requisitos y condiciones concretas; el resultado de Devel no acredita su funcionamiento en otras versiones.

El profesor advierte también de que los intentos fallidos pueden alterar procesos y complicar el diagnóstico. Una cadena de errores no siempre indica que el concepto sea incorrecto: puede deberse a un binario de arquitectura distinta, un argumento mal escrito, un componente que no cumple las condiciones o un estado del laboratorio modificado por intentos anteriores. Conviene identificar qué requisito ha fallado en lugar de cambiar varias cosas a la vez.

# Transferencia de archivos en la vía manual

La práctica necesita llevar al sistema Windows dos elementos con funciones diferentes. JuicyPotato se ocupa de la parte de suplantación y creación del proceso; Netcat proporciona el canal de conexión inversa usado en la demostración. No son herramientas intercambiables. Tampoco se presupone que Netcat esté instalado en Windows, de modo que se prepara y transfiere un ejecutable compatible.

En Kali se abre un servidor HTTP con Python para servir los archivos. En Windows se utiliza certutil como mecanismo de descarga, ya que en ese entorno no se dispone de las mismas utilidades que se suelen usar en Linux. La explicación de clase distingue la dirección del recurso y el nombre con el que se guarda localmente. A continuación se verifica la presencia del archivo mediante un listado de directorio.

La evidencia relatada muestra solicitudes HTTP con respuesta 200 y la comprobación de los archivos descargados. Esas señales acreditan la transferencia, pero por sí solas no prueban que el binario sea adecuado ni que la escalada haya funcionado. Esa separación resulta importante: el primer ejecutable de JuicyPotato se descarga correctamente y, aun así, se sustituye porque el profesor había elegido una arquitectura incorrecta.

El trabajo en una carpeta temporal facilita localizar los ejecutables durante la práctica. Las rutas de Windows, la separación entre argumentos y las comillas requieren especial atención. La sintaxis completa no debe reconstruirse de oído cuando la transcripción la fragmenta o el profesor está corrigiendo una tentativa todavía fallida.

# Diagnóstico de la escalada manual

La primera incidencia relevante es la selección del binario. El profesor reconoce que ha obtenido uno que no corresponde al sistema y busca la variante x86. La nueva copia se identifica como jp86.exe. El aprendizaje no es memorizar ese nombre local, sino comprobar que el archivo transferido corresponde a la arquitectura del objetivo antes de interpretar sus errores.

Después se revisan los argumentos de JuicyPotato. En la explicación, el puerto local de escucha de la herramienta y el puerto usado para recibir la conexión inversa cumplen funciones distintas. Confundirlos lleva a buscar un fallo en la técnica cuando el problema está en el canal de comunicación. También se corrige la separación entre el programa que se desea lanzar y los argumentos que se le entregan.

| **Elemento explicado** | **Función en la demostración** | **Precaución de interpretación** |
| --- | --- | --- |
| -l | Puerto local utilizado por JuicyPotato | No equivale al puerto de recepción de la consola inversa |
| -p | Programa que se desea ejecutar | Se corrige una confusión con otro argumento durante la clase |
| -a | Argumentos destinados al programa | Las comillas y rutas forman parte de la sintaxis y no se pueden omitir |
| -c | Identificador CLSID seleccionado | Debe corresponder a un componente y contexto compatibles |
| -t | Selección del método de creación del proceso | Se usa el comodín en la explicación de clase; no se desarrollan sus variantes |

El CLSID aparece cuando el intento sigue fallando después de corregir otros detalles. La clase lo introduce como el identificador utilizado para seleccionar el componente correspondiente. Se consulta una lista del repositorio organizada según el sistema operativo y se presta atención a la identidad bajo la que se ejecuta. Para el objetivo de la práctica interesa SYSTEM, no una cuenta con otro nivel de privilegios como LOCAL SERVICE.

No se conserva un identificador numérico como receta universal. La idea verificable es la necesidad de relacionar el componente elegido con el Windows concreto y con el contexto que se pretende obtener. El profesor indica que una entrada puede no funcionar en un entorno determinado. La explicación introductoria no desarrolla todas las condiciones internas de COM ni convierte la lista consultada en una garantía.

Finalmente aparece una incidencia de escucha: la técnica se había lanzado sin que estuviera preparado el receptor de la conexión. Tras corregirlo, se recibe una consola y whoami devuelve nt authority\system. Este resultado queda confirmado en el fotograma del vídeo y permite distinguir el éxito final de los intentos anteriores, que habían quedado en error o sin conexión visible.

Un alumno añade otro ejemplo de diagnóstico: había configurado un puerto distinto del esperado y perdió tiempo revisando el resto del procedimiento. La observación refuerza la necesidad de comparar los extremos de la comunicación y comprobar los valores efectivos, en lugar de asumir que dos números parecidos son iguales.

# Resumen de estudio y buenas prácticas de laboratorio

La sesión muestra que un acceso inicial sencillo puede llevar a una fase de escalada que exige más atención a los detalles. Metasploit reduce parte del trabajo operativo; la ruta manual obliga a explicitar la arquitectura, transferencia, identidad, privilegios, componentes y canal de conexión. Las dos rutas sirven para comprender el mismo laboratorio desde niveles de abstracción distintos.

La secuencia de repaso consiste en identificar el acceso obtenido, anotar el sistema operativo y su arquitectura, revisar los privilegios del token, justificar la herramienta elegida, comprobar cada transferencia y validar la identidad al final. Una descarga correcta, un mensaje de prueba o la aparición del nombre de un privilegio son evidencias parciales. La prueba del cambio de contexto se encuentra en la sesión resultante.

Para estudiar, el profesor recomienda repetir la práctica con calma y explicar qué hace cada elemento. La finalidad es entender qué información obliga a elegir una opción y qué evidencia permite descartar un error. No se exige seguir a la vez el ritmo del directo, escribir todos los comandos y procesar la teoría sin pausas. Se propone retomar los conceptos en clases posteriores, sin que esa propuesta pruebe que el repaso posterior ya haya ocurrido.

# Preguntas de repaso

1. ¿Por qué reconocer Windows no basta para seleccionar un ejecutable? Porque hay que comprobar también su arquitectura y los requisitos concretos de la técnica.

2. ¿Qué diferencia hay entre whoami /priv y whoami /all? El primero concentra los privilegios; el segundo añade identidad y grupos al conjunto de información.

3. ¿Por qué ver SeImpersonatePrivilege no demuestra por sí solo una escalada? Porque aún falta una vía compatible para obtener y utilizar un contexto privilegiado.

4. ¿Qué papel desempeña Netcat frente a JuicyPotato? En la práctica, Netcat transporta la consola inversa; JuicyPotato interviene en la suplantación y en el lanzamiento del proceso.

5. ¿Qué demuestra un HTTP 200 al descargar un ejecutable? Que la petición recibió una respuesta satisfactoria; no acredita compatibilidad ni ejecución privilegiada.

6. ¿Qué resultado confirma la escalada manual? La nueva consola devuelve nt authority\system al consultar su identidad.

# Comandos de observación y resultados

Los siguientes literales se conservan como operaciones de consulta o como elementos visibles de la clase. Su finalidad aquí es interpretar la evidencia; no se han ejecutado contra el laboratorio durante la elaboración de los apuntes.

| **Comando** | **Objetivo y opciones** | **Resultado e interpretación** | **Precaución** |
| --- | --- | --- | --- |
| whoami | Mostrar la identidad del contexto actual | La consola final devuelve nt authority\system | Repetir la consulta en la consola correcta; otra sesión puede conservar otra identidad |
| whoami /priv | Limitar la consulta a privilegios | SeImpersonatePrivilege figura como Enabled | Presencia y estado son datos diferentes |
| whoami /all | Mostrar identidad, grupos y privilegios | Permite relacionar el contexto de servicio con sus capacidades | No equivale a que todos los privilegios del equipo pertenezcan a esa cuenta |
| systeminfo | Consultar información del sistema | Windows 7 Enterprise y arquitectura x86 en la práctica | La compatibilidad depende del sistema real, no de la máquina del auditor |
| dir | Listar archivos y directorios de Windows | Ayuda a comprobar los archivos transferidos | La existencia del archivo no prueba que se ejecute ni que eleve privilegios |

# Registro de herramientas

| **Herramienta** | **Objetivo** | **Fase de auditoría** | **Comando/uso visto** | **Nivel** | **Notas** |
| --- | --- | --- | --- | --- | --- |
| Nmap | Aportar el listado de servicios y parte del contenido FTP | Recogida de información | Se interpreta su salida previa | Practicada | No se reconstruye el comando de escaneo. |
| Cliente FTP | Enumerar y transferir archivos | Recogida de información / Pruebas de explotación controladas | Acceso anónimo, listado y subida | Practicada | Se producen desconexiones que requieren reconectar. |
| Navegador | Contrastar contenido FTP/web y solicitar los ASPX | Recogida de información / Pruebas de explotación controladas | Acceso a rutas y al archivo de prueba | Practicada | No se inventan URL completas. |
| dirsearch | Descubrir rutas web | Recogida de información | Diccionario pequeño y discusión de recursividad | Practicada | Las opciones exactas quedan pendientes de contraste. |
| MSFvenom | Preparar archivos ASPX con distintos tipos de sesión | Pruebas de explotación controladas | Generación para Meterpreter y shell convencional | Practicada | Sin línea íntegra verificable en el tramo. |
| Metasploit | Recibir sesiones y probar módulos locales | Pruebas de explotación controladas | exploit/multi/handler y módulos locales | Practicada | Acceso inicial conseguido; escalada automatizada no acreditada. |
| Local Exploit Suggester | Proponer candidatos de escalada | Análisis de vulnerabilidades | Selección de sesión y ejecución con errores | Practicada | La salida satisfactoria mostrada procede de una referencia. |
| WinPEAS | Enumerar condiciones para escalada | Análisis de vulnerabilidades | Consulta de versiones y propuesta de uso | Introducida | No se ejecuta en este tramo. |
| Python 3 | Servir ejecutables por HTTP | Pruebas de explotación controladas | Servidor HTTP local | Practicada | Transferencia comprobada en la continuación. |
| Netcat | Recibir la shell convencional | Pruebas de explotación controladas | Receptor de las dos variantes manuales | Practicada | No se reconstruyen opciones dudosas. |
| GitHub | Obtener un archivo de referencia | Pruebas de explotación controladas | Búsqueda de ASPX y vista RAW | Practicada | Repositorio y URL no recuperables con certeza. |
| wget / nano | Descargar y editar el archivo | Pruebas de explotación controladas | Descarga propuesta y edición de parámetros | Practicada | Sin receta ejecutable reconstruida. |
| JuicyPotato | Suplantación y proceso privilegiado | Pruebas de explotación controladas | Variante x86 y selección de CLSID | Practicada | SYSTEM confirmado después de correcciones |
| certutil | Transferir archivos a Windows | Pruebas de explotación controladas | Descarga HTTP | Practicada | HTTP 200 y listado local |
| whoami / systeminfo | Identidad, privilegios y sistema | Recogida de información | Consultas del contexto local | Practicada | No elevan privilegios por sí mismas |

# Glosario de servicios y acceso

| **Término** | **Significado en la práctica** |
| --- | --- |
| FTP anónimo | Acceso al servicio FTP sin una cuenta personal; los permisos reales se comprueban aparte. |
| IIS | Servidor web de Microsoft identificado en el laboratorio. |
| ASPX | Tipo de archivo utilizado en la clase para que la aplicación web procese el contenido preparado. |
| Listado de directorios | Presentación del contenido de una carpeta desde el servicio web. |
| Descubrimiento de contenido | Prueba de nombres de rutas para localizar recursos publicados. |
| Recursividad | Repetición del descubrimiento sobre las rutas encontradas. |
| RCE | Ejecución remota de código, planteada al relacionar escritura de archivos e interpretación web. |
| Reverse shell | Conexión iniciada desde el sistema objetivo hacia el receptor configurado. |
| Payload | Componente preparado para producir el comportamiento deseado, compatible con el receptor y el sistema. |
| Meterpreter | Tipo de sesión utilizado dentro del flujo de Metasploit, con funciones propias y acceso a una shell. |
| Handler | Manejador que recibe la conexión y debe corresponder al payload preparado. |
| Sesión | Contexto de conexión identificado dentro de Metasploit para interactuar o aplicar módulos. |
| x86 | Arquitectura de 32 bits identificada durante la práctica. |
| Escalada local | Paso desde el acceso ya obtenido a un contexto de mayores privilegios. |
| RAW | Vista del contenido de un archivo en GitHub utilizada para su descarga. |

# Glosario de Windows

| **Término** | **Significado en la sesión** |
| --- | --- |
| Token de acceso | Contexto de identidad y permisos utilizado por Windows para autorizar operaciones |
| Token primario | Token asociado al proceso en la explicación de clase |
| Token de suplantación | Contexto que permite actuar con la identidad de un cliente |
| SID | Identificador de seguridad de una identidad o grupo de Windows |
| SeImpersonatePrivilege | Privilegio de suplantar a un cliente después de la autenticación |
| SYSTEM | Contexto privilegiado obtenido al final de la demostración manual |
| CLSID | Identificador del componente utilizado al seleccionar la vía de JuicyPotato |
| IIS AppPool | Contexto del grupo de aplicaciones de IIS desde el que se estudian los privilegios |
| x86 | Arquitectura de 32 bits que determina los binarios de esta práctica |
| Escucha | Receptor preparado para aceptar la conexión configurada en el otro extremo |

# Límites y dudas que conviene conservar

La escalada automatizada con Metasploit no queda acreditada como satisfactoria. Los errores del Suggester y de los módulos locales no permiten atribuir una causa raíz única. La imagen de una salida satisfactoria mostrada desde un write-up explica un resultado esperado; no sustituye la evidencia de ejecución del directo.

La compatibilidad de las distintas familias Potato se presenta de forma introductoria y no se valida con demostraciones de todas ellas. La clase prueba JuicyPotato en el contexto concreto de Devel. Tampoco confirma recuperación de flags ni permite reconstruir de forma segura todos los comandos, rutas, URL e identificadores pronunciados entre correcciones.

La transcripción aportada no abarca los primeros minutos del vídeo y contiene repeticiones y errores de reconocimiento. Se ha preservado completa como fuente, y se han contrastado tres fotogramas del vídeo para servicios, privilegios y resultado final. Los primeros minutos del vídeo y los intervalos sin contenido transcrito no se completan con información supuesta.

# Ideas importantes de la transcripción

| **Tema** | **Idea importante** | **Referencia** |
| --- | --- | --- |
| FTP e IIS | La coincidencia de archivos plantea la hipótesis de publicación compartida. | 39:53–44:57 |
| Permisos | Acceso anónimo, lectura, escritura y ejecución son condiciones que deben diferenciarse. | 43:16–45:17; 50:04–50:35 |
| Rutas HTTP | Se contrastan respuestas de rutas conocidas y de una ruta inexistente para apoyar la correlación. | 45:20–49:29 |
| Enumeración | El recorrido FTP no descubre contenido adicional relevante para el profesor. | 46:29–51:33 |
| Diccionarios | La recursividad amplía las búsquedas; los nombres ausentes del diccionario pueden no encontrarse. | 51:35–54:38 |
| Prueba inocua | La subida y visualización de un TXT confirma el flujo FTP hacia la web en la práctica. | 54:40–56:54 |
| Meterpreter | El archivo se prepara para Windows, ASPX y el tipo de sesión esperado. | 57:39–01:01:03 |
| Errores FTP | La desconexión no debe confundirse con una prohibición de subida. | 01:01:06–01:02:05 |
| Manejador | Dirección, puerto y payload deben corresponder con el archivo preparado. | 01:02:07–01:05:44 |
| Acceso inicial | El profesor señala una sesión Meterpreter abierta y comprueba la red desde una shell. | 01:05:46–01:06:58 |
| Arquitectura | Se identifica x86; WinPEAS se propone sin llegar a ejecutarlo. | 01:07:31–01:08:33 |
| Flags | La exploración de perfiles no confirma ubicación ni recuperación de flags. | 01:08:35–01:10:04; 01:44:23–01:45:12 |
| Suggester | La función esperada es proponer candidatos; la ejecución en directo falla. | 01:10:08–01:14:38 |
| Sesiones | Una nueva sesión requiere seleccionar el identificador correcto. | 01:18:15–01:19:30 |
| Evidencia externa mostrada | La lista satisfactoria se enseña mediante una imagen de un write-up. | 01:22:19–01:25:49 |
| Escalada automática | Se prueban módulos y puertos sin acreditar una sesión elevada. | 01:25:50–01:35:24 |
| Diagnóstico | Las hipótesis sobre arquitectura, procesos y plataforma no quedan confirmadas. | 01:14:11–01:14:21; 01:29:14–01:30:16; 01:41:11–01:43:34 |
| Método manual | Se plantea continuar con una shell convencional y estudiar suplantación/Potato. | 01:35:30–01:45:58 |
| Reinicio | Se reinicia el laboratorio antes de repetir el acceso inicial. | 02:04:39–02:06:19 |
| MSFvenom y Netcat | Se consigue una shell convencional usando un ASPX generado. | 02:06:21–02:09:49 |
| GitHub y RAW | Se prepara otra shell desde un archivo de GitHub, se adapta y se conecta. | 02:09:52–02:12:56 |
| Planteamiento | Devel compara Metasploit y vía manual | F002 · 27:20–30:40 |
| Sistema | Windows 7 Enterprise y contexto de servicio | F002 · 02:13:18–02:18:49 |
| Privilegios | SeImpersonatePrivilege Enabled | F002 · 02:17:07–02:18:49; F004 · 02:18:40 |
| Tokens | Primario y de suplantación; analogía del carné | F002 · 02:18:54–02:25:25 |
| Familias Potato | Selección introductoria según versión; alternativas no probadas | F002 · 02:25:29–02:36:47 |
| Transferencia | JuicyPotato y Netcat cumplen funciones diferentes | F002 · 02:37:03–02:44:35 |
| Diagnóstico | Se corrige arquitectura, argumentos y CLSID | F002 · 02:44:36–02:54:32 |
| Resultado | Consola final identificada como SYSTEM | F002 · 02:54:35–03:00:23; F005 · 02:55:02 |
| Estudio | Repetir con calma y verificar puertos y requisitos | F002 · 03:02:42–03:05:55 |

# Actualización de memoria del proyecto

| **Categoría** | **Información nueva** | **Nivel de certeza** | **Acción futura** |
| --- | --- | --- | --- |
| Sesión | 2 de octubre de 2026 · Carlos Castillo Sanjuan · Devel | Alta | Conservar esta entrega y sus fuentes |
| Acceso | FTP y web relacionados; dos tipos de sesión | Alta | Repetir justificando cada comprobación |
| Escalada | Vía manual llega a SYSTEM; automática no acreditada | Alta | Distinguir fallos y resultados en el repaso |
| Compatibilidad | Alternativas Potato citadas sin prueba de todas | Media | Verificar requisitos antes de otro laboratorio |
| Dudas | Causa raíz de errores de módulos no resuelta | Baja | No promover hipótesis a conclusión |
