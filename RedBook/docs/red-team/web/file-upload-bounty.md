---
tags:
- Auditoría web
date: '2026-10-01'
author: Carlos Castillo
---

# File Upload Bounty

<p class="note-meta">2026-10-01 · Carlos Castillo</p>

![](../../assets/img/file-upload-bounty/img001.png)

# Mapa de la teoría de la sesión

**Subida de archivos y repaso de Bounty**

Identificar el entorno → comprobar la validación → localizar el archivo → verificar su interpretación

| **Dónde se valida** | **Qué se analiza** |
| --- | --- |
| CLIENTE | 1. HTML y JavaScript ¿El servidor repite la comprobación? |
| NOMBRE Y EXTENSIÓN | 2. Lista de bloqueo 3. Lista de formatos permitidos Mayúsculas, alternativas, dobles extensiones y normalización. |
| TIPO Y CONTENIDO | 4. Content-Type / MIME 5. Magic bytes 6. Contenido políglota y metadatos. |
| SERVIDOR Y DESTINO | 7. Archivos de configuración 8. Ruta y sobrescritura Qué se almacena y qué interpreta realmente el servidor. |

**↓ Aplicación a la máquina Bounty ↓**

|  |
| --- |
| **IIS 7.5 → transfer.aspx → Burp Intruder → candidato .config → web.config** Aceptación observada; ejecución remota y conexión final pendientes de confirmar. |

|  |
| --- |
| **Defensa** Validar en servidor, limitar formatos y tamaño, generar nombres, aislar el almacenamiento y evitar ejecución o configuración activa en las subidas. |

Regla de razonamiento: aceptar un archivo, almacenarlo y ejecutarlo son hechos diferentes.

# Objetivos y alcance de la sesión

**Contenido de clase**

La clase estudia las vulnerabilidades de subida de archivos y vuelve a la máquina Bounty de Hack The Box. El objetivo es entender qué valida una aplicación, qué acepta su servidor y qué condiciones hacen falta para interpretar un archivo subido. El repaso de Magic mencionado por el profesor sirve para explicar validaciones de imágenes y dobles extensiones.

Al terminar el estudio deberías poder formular pruebas de una sola variable, distinguir señales de aceptación de evidencias de ejecución, comparar respuestas en Burp y explicar por qué un archivo de configuración puede ser sensible. También debes poder proponer medidas de defensa que ataquen la causa del problema.

|  |
| --- |
| **Resultado observado** Se identifica .config como candidato aceptado. La prueba aritmética y la conexión de vuelta no se verifican con éxito. La escalada con SeImpersonatePrivilege queda pendiente. |

## Metodología de auditoría

| **Fase** | **Aplicación a la clase** |
| --- | --- |
| Planificación | Delimitar Bounty como laboratorio y repasar la subida de archivos. |
| Recogida de información | Conectividad, puertos, servicio IIS, rutas web y metadatos. |
| Análisis de vulnerabilidades | Contrastar validaciones y estudiar las respuestas a cada extensión. |
| Pruebas de explotación controladas | Intentos de aplicar web.config y obtener un resultado verificable. El resultado final no queda confirmado. |

En el desarrollo se distingue el contenido de clase de las ampliaciones técnicas. Las inferencias y los puntos pendientes se indican expresamente. Las marcas de tiempo se reúnen al final para que el cuerpo pueda leerse de forma continua.

# Validaciones: del cliente al MIME

**Contenido de clase**

El esquema presentado agrupa ocho bloques. Es una guía para formular hipótesis: varias validaciones pueden actuar a la vez y una prueba aislada no explica todo el comportamiento de la aplicación.

## 1. Validación en el cliente

HTML y JavaScript pueden limitar el selector de archivos o impedir que se envíe una extensión. Esos controles pertenecen al navegador. La clase propone inspeccionar el HTML, modificar el comportamiento del cliente o interceptar una subida con Burp para comprobar qué acepta realmente el servidor.

**Qué observar:** si el navegador protesta pero una petición equivalente llega y se acepta, el filtro del cliente no está respaldado por una validación suficiente en el servidor. Burp modifica la petición; no convierte por sí solo un filtro del servidor en uno del cliente.

## 2. Lista de extensiones bloqueadas: blacklist

Una lista de prohibiciones puede dejar fuera variantes. Se comentan cambios de mayúsculas, extensiones alternativas del mismo lenguaje, dobles extensiones, puntos o espacios finales y bytes nulos. El objetivo de cada prueba es averiguar cómo se compara y normaliza el nombre.

Ejemplos citados o normalizados desde la explicación: **archivo.pHp**, **archivo.phtml** y **archivo.php.jpg**. Las extensiones alternativas solo son relevantes si existe un intérprete o manejador asociado. Los casos con bytes nulos o recortes dependen de implementaciones concretas; no son soluciones universales.

## 3. Lista de extensiones permitidas: whitelist

Permitir unos pocos formatos es mejor punto de partida, pero la comprobación puede estar mal escrita. La clase plantea dobles extensiones y discrepancias entre lo que verifica el filtro y lo que interpreta el servidor. Si basta con que el nombre contenga «.jpg», podría aceptarse algo que no termina realmente en esa extensión.

|  |
| --- |
| **Pregunta útil:** ¿la aplicación comprueba el nombre completo, la extensión final, una subcadena o el resultado de una normalización? Probar una variante cada vez ayuda a distinguir estas posibilidades. |

## 4. Content-Type y MIME

En una subida multipart, cada parte puede declarar un Content-Type, por ejemplo **image/png**. El cliente puede cambiarlo. Un filtro que se limita a confiar en esa declaración puede aceptar contenido distinto del anunciado. Mantener el MIME y cambiar el contenido permite estudiar esta hipótesis.

Conviene distinguir el Content-Type global de la petición, como multipart/form-data, del Content-Type de la parte que transporta el archivo. Alterar el primero o su boundary puede romper la petición antes de llegar al filtro que se quiere estudiar.

## Cómo diferenciar las validaciones

La misma respuesta de rechazo puede ocultar comprobaciones distintas. Si se cambia solo el nombre y el contenido permanece igual, la variación sirve para estudiar el filtro del nombre. Si se mantiene el nombre y se cambia solo el MIME, la comparación se centra en el tipo declarado. Si también se cambia el contenido, ya no puede atribuirse el resultado a una única condición.

|  |
| --- |
| **Ampliación técnica** Los puntos o espacios finales y los bytes nulos solo importan cuando dos componentes normalizan o interpretan el nombre de forma diferente. No debe asumirse que un servidor moderno acepte esas variantes. [R1] |

# Contenido, configuración y rutas

**Contenido de clase**

## 5. Magic bytes: la firma del archivo

Los primeros bytes de ciertos formatos permiten reconocerlos. La clase recuerda dos pruebas: anteponer una cabecera reconocible y conservar una imagen a la que se añade contenido. La pregunta es si el servidor valida solo la firma o analiza el archivo de forma más completa.

Se mencionan GIF y JPEG. Ver datos ilegibles en Burp no significa que estén cifrados: pueden ser datos binarios mostrados como texto. Una cabecera válida tampoco garantiza que todo el documento sea una imagen válida.

## 6. Archivos políglotas y metadatos

Un archivo puede satisfacer más de una interpretación. En el ejemplo de clase, una imagen conserva su estructura y lleva código adicional, incluso en un campo de comentario de sus metadatos. El interés está en combinar la aceptación como imagen con otra interpretación posterior.

**Condición imprescindible:** almacenar código dentro de una imagen no basta para ejecutarlo. Hace falta que el servidor, una inclusión o algún procesamiento posterior lo entregue a un intérprete capaz de ejecutarlo. Abrir una imagen como recurso estático no ejecuta PHP automáticamente.

## 7. Archivos de configuración del servidor

Bounty desplaza el foco desde el formato de imagen hacia un archivo de configuración. Se detecta la aceptación de .config y se estudia **web.config**. Su interés es que puede influir en la configuración efectiva de IIS si la ubicación y los permisos lo permiten. El mecanismo se desarrolla en la apartado sobre web.config.

## 8. Nombre del archivo y ruta de destino

También se comentan la manipulación de rutas y la sobrescritura de archivos existentes. El problema aparece si el servidor utiliza el nombre aportado por el cliente para construir rutas sin control suficiente o permite reemplazar archivos relevantes.

|  |
| --- |
| **Reconstrucción del repaso de Magic:** la explicación relaciona dobles extensiones, comprobación de formato y contenido mixto. La condición que une las piezas es una diferencia entre lo que acepta el filtro y lo que procesa después el servidor. Magic se usa como referencia de una clase anterior; no se resuelve de nuevo en esta grabación. |

## Cómo ordenar las pruebas

Empezar por un archivo normal que sirva de referencia. Después variar nombre, extensión, MIME y contenido por separado. Registrar qué cambia en la respuesta y comprobar el resultado almacenado cuando sea posible. Si se modifican cuatro cosas a la vez, un éxito o un fallo ofrece mucha menos información.

## La interpretación es una condición independiente

La validación responde a «¿puedo guardar este archivo?». La interpretación responde a «¿qué componente atenderá una petición a ese recurso?». El contenido puede superar el primer control y seguir sirviéndose como datos. Esta separación explica por qué no tiene sentido elegir un lenguaje únicamente porque resulte familiar: hay que relacionarlo con lo observado del servidor.

# Mitigaciones y explicación al cliente

**Contenido de clase**

La clase insiste en que una auditoría debe explicar tanto el problema como su solución. Obtener una prueba de impacto no sustituye a describir qué control ha fallado ni a proponer una corrección que el equipo pueda aplicar.

| **Medida comentada** | **Qué se busca conseguir** |
| --- | --- |
| Lista estricta de formatos | Aceptar únicamente los tipos de archivo que necesita la función de negocio y comprobarlos en el servidor. |
| Validación del contenido | Contrastar formato y firma; una extensión permitida o un MIME declarado no bastan por sí solos. |
| Renombrar los archivos | Generar el nombre en el servidor para reducir colisiones, manipulación del nombre y facilidad de localización. |
| Separar almacenamiento y ejecución | Evitar que una carpeta de subidas actúe como ubicación de scripts o de configuración activa. |
| Dominio o servicio separado | Aislar la entrega de archivos respecto de la aplicación principal y sus privilegios. |
| Límites de tamaño | Ajustar el tamaño permitido al uso esperado y evitar cargas desproporcionadas. |
| Antivirus o sandbox | Añadir análisis del contenido, sin convertirlo en el único control de seguridad. |

## Precisiones para no confiar en una sola barrera

Un nombre aleatorio dificulta encontrar un archivo, pero no neutraliza un contenido peligroso. Una carpeta sin listado tampoco garantiza que un archivo conocido no sea accesible por su URL. Y un límite pequeño de tamaño puede seguir permitiendo contenido dañino muy corto.

**Ampliación técnica**

Como complemento técnico, OWASP recomienda almacenar fuera de la raíz pública cuando sea viable, controlar autorización y nombres, y combinar varias comprobaciones. La firma y el Content-Type no deben actuar como únicos criterios. Si se procesan imágenes, la validación con una biblioteca adecuada y su reescritura pueden formar parte del diseño. [R1]

## Modelo de explicación del hallazgo

|  |
| --- |
| **Observación:** el formulario distingue la extensión .config de las rechazadas. **Riesgo:** si un archivo subido puede modificar la configuración efectiva, podría alterar el procesamiento del directorio. **Corrección:** impedir configuraciones activas en la zona de subidas y separar ese almacenamiento de la ejecución. **Validación posterior:** repetir la subida y comprobar tanto el rechazo como la ausencia de cambios en el servidor. |

Este modelo es una redacción de estudio, no un informe de explotación completada: en la sesión no se confirmó la ejecución remota final. Tampoco se toma como hecho técnico la comparación informal entre el análisis de Google Drive y VirusTotal.

# Bounty: reconocimiento inicial

**Contenido de clase**

El ejercicio retoma Bounty en Hack The Box. Antes de probar extensiones, el profesor identifica el entorno para decidir qué hipótesis tienen sentido. La relación entre tecnología observada y siguiente prueba es el hilo de toda la práctica.

## Conectividad y TTL

Se comprueba conectividad y se comenta un TTL de 127 como indicio compatible con un origen Windows cercano a 128. El TTL disminuye en los saltos; no se pierde un «paquete de TTL». Es una pista orientativa, no una prueba concluyente del sistema operativo.

## Puertos y servicio web

Se realiza una búsqueda de puertos y después una enumeración de versiones y scripts. En la explicación aparecen el puerto **80/TCP** y **Microsoft IIS 7.5**. La transcripción no conserva todas las líneas de terminal con precisión; las siguientes son plantillas equivalentes para estudiar el proceso.

**Ampliación técnica · plantilla explicativa**

|  |
| --- |
| # Sustituir IP\_LAB por la IP de la instancia del laboratorio ping -c 3 IP\_LAB nmap -p- -oN puertos.txt IP\_LAB nmap -sV -sC -p 80 -oN servicio-web.txt IP\_LAB |

La primera pasada delimita la superficie expuesta; la segunda obtiene detalles del puerto detectado. La clase también menciona ajustar la velocidad del escaneo. No se fija aquí un valor que la transcripción no permite recuperar con certeza.

## IIS y las extensiones relevantes

**Ampliación técnica**

IIS significa Internet Information Services. La clase orienta la búsqueda hacia ASP, ASPX y archivos de configuración. **ASP clásico y ASP.NET no son el mismo motor.** Qué se ejecuta realmente depende de los módulos y las asignaciones de manejadores instalados; IIS también puede servir recursos estáticos o alojar otros entornos. [R2]

## Inspección de la web y metadatos

La página inicial ofrece poca interacción y una imagen. Se propone revisarla con ExifTool para buscar pistas del software que la produjo. Una referencia a Photoshop en los metadatos describe el archivo; no demuestra que Photoshop esté instalado en el servidor. Su utilidad está en generar una hipótesis que luego habrá que contrastar.

**Ampliación técnica · plantilla explicativa**

|  |
| --- |
| exiftool imagen.jpg searchsploit "IIS 7.5" |

La búsqueda por versión sirve para investigar. Una coincidencia en SearchSploit no demuestra aplicabilidad: hay que comprobar componente, condiciones y superficie expuesta. En clase se comenta un resultado relacionado con FTP, mientras que el servicio observado en esta fase es HTTP.

# Descubrir rutas sin ir a ciegas

**Contenido de clase**

## Diccionarios y extensiones

Se empieza con dirsearch y un diccionario general. Después se añaden extensiones relacionadas con IIS y se reduce el diccionario para acotar el coste. La lección es que cada combinación extra aumenta las peticiones y que una lista enorme no sustituye a entender la aplicación.

Se mencionan **aspnet\_client**, el directorio de archivos subidos y **transfer.aspx**. Esta última ruta acaba utilizándose directamente durante la sesión. No se muestra una ejecución exitosa de Shortscan que descubra el nombre completo; por tanto, no se atribuye ese resultado a la herramienta.

**Ampliación técnica · plantilla explicativa**

|  |
| --- |
| # Ejemplo reconstruido: usar un diccionario disponible dirsearch -u http://IP\_LAB/ -w diccionario.txt -e asp,aspx,config |

## Qué aporta Shortscan

**Ampliación técnica**

El profesor propone una herramienta específica para IIS, pero encuentra problemas de instalación y después se bloquea la máquina Kali. La precisión importante es que **Shortscan enumera nombres cortos de IIS**, asociados a nombres 8.3 y al comportamiento con la tilde. No es simplemente otro diccionario de rutas comunes. Los nombres encontrados pueden requerir completar el nombre largo. [R3]

La sesión continúa con alternativas y con la ruta conocida para no consumir todo el tiempo en instalar una herramienta. El aprendizaje es conservar varias formas de investigar y dejar claro cuándo una ruta se descubre y cuándo se aporta como pista.

## Mayúsculas, minúsculas y códigos HTTP

**Ampliación técnica**

Se comparan variantes del nombre del directorio. La sensibilidad a mayúsculas depende del sistema de archivos, del servidor y del enrutado de la aplicación. Puede apoyar una hipótesis sobre el entorno, pero no identifica por sí sola Windows o Linux.

| **Respuesta** | **Lectura útil para la práctica** |
| --- | --- |
| 200 | La petición HTTP se atendió, pero el cuerpo puede indicar que la subida fue rechazada. |
| 403 | El servidor entiende la petición y rechaza atenderla. Puede deberse a permisos o al listado de directorio deshabilitado, entre otras causas. |
| 404 | El recurso no se encuentra o el servidor no quiere revelar su existencia. Revisar la ruta antes de concluir. |
| 500 | Error del servidor. Hay que investigar contenido, configuración y contexto; no demuestra ejecución. |

**Ampliación técnica**

En la explicación se asocia 403 a falta de directory listing. Es una posibilidad del caso, no la definición general del código. La lectura de la tabla sigue HTTP Semantics. [R4]

# Burp Intruder: probar extensiones

**Contenido de clase**

El formulario no indica claramente qué formatos admite. Renombrar y subir archivos manualmente sería repetitivo. Intruder permite repetir una petición y variar solo la extensión del nombre enviado en **filename**.

## Procedimiento explicado en clase

**1. Preparar una petición base.** Seleccionar un archivo real en el formulario, enviarlo e interceptar la subida. Comprobar que el cuerpo contiene el archivo; en clase una captura sin fichero acabó produciendo errores.

**2. Enviar a Intruder.** Limpiar posiciones automáticas y seleccionar únicamente el fragmento que se quiere sustituir. Para esta prueba basta con una posición y un ataque Sniper.

**3. Ajustar el punto.** Si la posición incluye solo «txt», la lista debe contener «asp», «aspx», «config», etc. Si la posición incluye «.txt», la lista debe llevar el punto. Evitar nombres como archivo..config.

**4. Revisar la lista y la codificación.** Una lista corta permite observar la prueba. Revisar la petición final generada: el procesamiento de los valores puede cambiar lo que realmente se está enviando.

**5. Comparar respuestas.** Mirar el estado HTTP, la longitud y el cuerpo. En la sesión varias respuestas devuelven 200; la extensión .config se diferencia por la longitud y por el comportamiento de la subida.

**6. Repetir el candidato.** Revisar manualmente la petición y su respuesta. Una longitud distinta sirve para seleccionar una prueba interesante, no para declarar una vulnerabilidad de ejecución.

**Ampliación técnica · plantilla explicativa**

|  |
| --- |
| Content-Disposition: form-data; name="file"; filename="prueba.txt"  Posicion a sustituir: txt Lista sin punto: asp | aspx | exe | txt | php | php5 | config |

El fragmento es esquemático: conservar el nombre real del campo, el boundary y los demás parámetros del formulario. La transcripción menciona longitudes próximas a 1331 y 1336, pero no permite asignar todos los valores con seguridad. Lo relevante es la diferencia reproducible y el mensaje del cuerpo.

## Qué demuestra este paso

|  |
| --- |
| La prueba estudia **aceptación de extensiones**. No verifica todavía que el archivo tenga una configuración válida, que esté en la ruta esperada o que ejecute código. El siguiente paso es entender por qué .config importa en ese servidor. |

Si se conservan tokens, cookies o campos de estado de una petición antigua y el formulario deja de funcionar, capturar una petición nueva. Cambiar de extensión no debe ir acompañado de cambios accidentales en otras partes de la subida.

## Interpretar una diferencia sin precipitarse

La longitud de respuesta funciona como una señal de clasificación. Antes de etiquetar una extensión como aceptada, abrir la respuesta correspondiente y buscar un mensaje coherente con ese resultado. Comparar además una petición de rechazo conocida. Si la respuesta cambia por un error interno o por un token caducado, su longitud será distinta sin que el formato se haya aceptado.

|  |
| --- |
| **Inferencia técnica** La variación de longitud orienta la siguiente prueba. La conclusión debe sostenerse con el cuerpo de la respuesta y una repetición controlada. El número de bytes, aislado, no identifica la causa. |

# web.config: por qué importa

**Contenido de clase**

La extensión .config conduce al archivo **web.config**, que IIS utiliza para configuración distribuida. La distinción es importante: que el filtro acepte un nombre terminado en .config no hace que cualquier archivo con ese sufijo sea una configuración activa.

## La cadena conceptual del ejercicio

**Aceptación.** El formulario permite subir un tipo de archivo que merece investigarse por su relación con IIS.

**Ubicación y nombre.** El archivo debe quedar donde IIS lo trate como configuración y con el nombre pertinente. También importan los permisos y las secciones que el administrador haya delegado.

**Configuración efectiva.** Si una sección está permitida, el archivo puede alterar el comportamiento del ámbito correspondiente. Si está bloqueada o es inválida, puede producir errores en lugar del efecto esperado. [R5]

**Interpretación.** Las asignaciones de manejadores determinan cómo se procesa una solicitud. En el mecanismo que se intenta explicar, la configuración y un bloque de código se combinan para que el contenido llegue a un intérprete. [R2]

**Prueba observable.** El profesor intenta primero una operación aritmética y después una conexión de vuelta. Ninguna queda confirmada como ejecución exitosa en la transcripción.

## Configuración y código son piezas diferentes

Durante la explicación se habla de una parte superior de configuración y un bloque inferior de código situado en un comentario. La idea es que dos componentes procesan el mismo archivo de forma distinta. Sin la configuración y el manejador adecuados, un comentario XML no se convierte en código ejecutable.

La frase de clase «esta parte no cambia» describe la plantilla usada en ese momento. No debe convertirse en una regla general: módulos, rutas, arquitectura, restricciones y secciones delegadas pueden variar. La transcripción no incluye el XML completo mostrado en pantalla; no se reconstruye un payload como si fuera el original.

## Prueba mínima antes de una conexión compleja

Una operación que devuelva un valor conocido permite separar la interpretación del código de los problemas de red. Si esa prueba ya falla, añadir una reverse shell introduce más variables: dirección de retorno, puerto, escucha, conectividad y sintaxis del comando.

|  |
| --- |
| **Repaso rápido:** archivo aceptado → archivo almacenado → configuración aplicada → contenido interpretado → resultado observado. Cada flecha necesita evidencia; no basta con el mensaje «subida completada». |

# Diagnóstico: qué falló en clase

**Contenido de clase**

Esta parte es útil precisamente porque la demostración no sale a la primera. Se prueban varios archivos, se corrigen nombres y ubicaciones locales, aparecen errores 500 y no llega la conexión. El profesor propone revisar el material y continuar al día siguiente.

| **Hecho observado** | **Qué permite concluir** |
| --- | --- |
| .config se diferencia en Intruder | Existe un candidato relevante para la aceptación del filtro. |
| Se muestra una subida completada | La aplicación indica aceptación; todavía falta comprobar el efecto real. |
| Aparecen errores 500 y de ejecución | Hay un fallo del lado del servidor; su causa no queda identificada. |
| No aparece el resultado aritmético esperado | La prueba mínima de interpretación no queda validada. |
| No se recibe la conexión esperada | No se demuestra una reverse shell funcional en esta sesión. |
| Se anuncia SeImpersonate para después | La escalada sigue pendiente y no hay resultado de SYSTEM que documentar. |

## Secuencia de revisión propuesta para estudiar el caso

**Archivo:** confirmar que se edita y se sube la misma copia. Revisar extensiones duplicadas, nombre exacto, codificación, comillas, etiquetas y tamaño. En la grabación hay confusión entre varias copias de web.config.

**Petición:** verificar que contiene el fichero y conserva los campos del formulario. Repetir desde una petición reciente si el comportamiento cambia. Guardar el cuerpo de la respuesta, no solo el código HTTP.

**Servidor:** separar acceso al directorio de acceso al archivo. Revisar qué cambia antes y después de la subida. Si se dispone de administración del laboratorio, consultar errores detallados y registros para distinguir XML inválido, secciones bloqueadas o fallos de ejecución.

**Conexión:** una vez confirmada la interpretación, comprobar la dirección de retorno, el puerto y la escucha. Que el equipo del alumno alcance la web no garantiza que el objetivo pueda iniciar una conexión de vuelta.

|  |
| --- |
| **No atribuir una causa sin comprobarla.** En clase se sospecha de comillas, saltos de línea, formato o etiquetas. Son hipótesis. La transcripción no identifica cuál causó el fallo ni muestra una corrección final verificada. |

SeImpersonatePrivilege y Juicy Potato se nombran como temas próximos. No se incluyen pasos de escalada ni comandos atribuidos a esta práctica porque no se desarrollaron en ella.

# PowerShell, comillas y codificación

**Contenido de clase**

Al introducir un comando dentro de otro lenguaje aparecen varias capas de interpretación: configuración, código del servidor, consola y PowerShell. Cada capa puede tratar comillas, barras y otros caracteres de una forma distinta.

## Qué se explica en la sesión

El profesor comenta la ejecución mediante **cmd /c** y después PowerShell. También explica por qué un comando largo puede romperse al copiarlo dentro de otra cadena y propone codificarlo. El procedimiento se presenta mientras la ejecución del laboratorio sigue sin resolverse.

## UTF-16LE primero; Base64 después

**Ampliación técnica**

Para **powershell.exe -EncodedCommand**, Microsoft especifica una cadena codificada en UTF-16LE antes de representarla en Base64. Base64 no cifra el comando: cambia su representación. Ayuda a transportar ciertas cadenas, pero no repara una configuración XML inválida ni un problema de conectividad. [R6]

**Ampliación técnica · plantilla explicativa**

|  |
| --- |
| # Ejemplo didactico local: solo imprime una suma $texto = "Write-Output (1 + 2)" $bytes = [Text.Encoding]::Unicode.GetBytes($texto) $base64 = [Convert]::ToBase64String($bytes) powershell.exe -NoProfile -EncodedCommand $base64 |

El resultado esperado de este ejemplo es **3**. Sirve para estudiar la codificación sin depender de IIS ni de una conexión de red. Es un ejemplo añadido a estos apuntes, no un comando recuperado literalmente de la grabación.

## Cómo comprobar que no se perdió contenido

**Ampliación técnica · plantilla explicativa**

|  |
| --- |
| [Text.Encoding]::Unicode.GetString([Convert]::FromBase64String($base64)) |

Revisar el comando recuperado permite detectar un truncado o una sustitución accidental. Una cadena puede estar perfectamente codificada y seguir conteniendo un comando incorrecto. Conviene validar la operación sencilla antes de introducir más capas.

## Errores concretos que se recuerdan en clase

• Cambiar el destino del ejemplo por el valor real del laboratorio; en la demostración se detecta un marcador de IP sin sustituir.

• Mantener coherentes dirección, puerto y proceso de escucha. No reutilizar sin revisar los valores de otra instancia.

• Comprobar comillas copiadas, cierres y saltos de línea; el formato visual de un editor puede ocultar diferencias.

• No interpretar un error HTTP como prueba suficiente de que el comando se ejecutó o de que no llegó a ejecutarse.

# Herramientas utilizadas en la sesión

Los niveles describen la exposición documentada en esta clase. No equivalen a dominio personal del alumno ni importan estados de otras sesiones.

| **Herramienta** | **Objetivo** | **Fase de auditoría** | **Comando/uso visto** | **Nivel** | **Notas** |
| --- | --- | --- | --- | --- | --- |
| Nmap | Puertos y servicios | Recogida de información | Búsqueda de puertos; versiones y scripts en 80 | Practicada | IIS 7.5 es el servicio comentado. |
| ping | Conectividad y TTL | Recogida de información | Comprobar respuesta; TTL 127 como pista | Practicada | El TTL es orientativo. |
| ExifTool | Metadatos de imagen | Recogida de información | Inspección de la imagen inicial | Practicada | El software de la imagen no prueba el del servidor. |
| SearchSploit | Investigar coincidencias | Análisis de vulnerabilidades | Búsqueda por IIS 7.5 | Introducida | Comprobar componente y requisitos. |
| dirsearch | Descubrir rutas | Recogida de información | Diccionario y extensiones de IIS | Practicada | No confundir 403 con recurso inexistente. |
| Shortscan | Nombres cortos de IIS | Recogida de información | Se propone; instalación con problemas | Introducida | No se observa ejecución exitosa. |
| Burp Suite | Variar subidas | Análisis de vulnerabilidades | Proxy e Intruder; Sniper en filename | Practicada | Comparar petición y cuerpo de respuesta. |
| PowerShell | Interpretar comandos | Pruebas de explotación controladas | Explicación de comando y codificación | Introducida | Conexión final no confirmada. |
| Netcat | Escuchar conexión | Pruebas de explotación controladas | Se prepara la escucha | Introducida | No se observa una sesión establecida. |
| Juicy Potato | Escalada Windows | Pruebas de explotación controladas | Mención vinculada a SeImpersonate | Mencionada | Desarrollo pendiente. |
| Caido | Proxy web alternativo | Análisis de vulnerabilidades | Mención como alternativa a Burp | Mencionada | No se practica en la sesión. |
| draw.io | Representar relaciones | Planificación | Herramienta del esquema mostrado | Mencionada | El diagrama original no está adjunto. |

# Comandos y parámetros importantes

Las líneas de terminal no se conservan completas en el texto recibido. Las siguientes fichas explican los fragmentos identificables y señalan las reconstrucciones. Los marcadores IP\_LAB, URL\_LAB y archivo representan valores de la instancia, no datos recuperados de clase.

## Enumeración del servicio web

**Ampliación técnica · reconstrucción explicativa del uso visto**

|  |
| --- |
| nmap -sV -sC -p 80 IP\_LAB |

**Opciones:** -sV identifica versiones; -sC aplica scripts por defecto; -p 80 selecciona el puerto.  
**Objetivo:** Describir el servicio encontrado después del barrido.  
**Resultado esperado:** Información del servicio HTTP y sus respuestas a los scripts.  
**Observado en clase:** Se comenta Microsoft IIS 7.5 en el puerto 80. La línea completa es reconstruida.  
**Riesgo o límite:** Genera tráfico activo. Los resultados pueden ser incompletos o depender de la configuración.

## Rutas relacionadas con IIS

**Ampliación técnica · reconstrucción explicativa del uso visto**

|  |
| --- |
| dirsearch -u URL\_LAB -w diccionario.txt -e asp,aspx,config |

**Opciones:** -u fija URL; -w el diccionario; -e las extensiones.  
**Objetivo:** Reducir la búsqueda a candidatos relacionados con la aplicación.  
**Resultado esperado:** Rutas y códigos de respuesta que orienten la inspección.  
**Observado en clase:** Se descubren rutas y se llega a transfer.aspx; no se demuestra que Shortscan haya descubierto esa ruta.  
**Riesgo o límite:** El coste crece con palabras y extensiones. Un listado incompleto no prueba ausencia.

## Metadatos de la imagen

**Ampliación técnica · reconstrucción explicativa del uso visto**

|  |
| --- |
| exiftool imagen.jpg |

**Opciones:** El argumento es el archivo que se quiere inspeccionar.  
**Objetivo:** Leer las etiquetas de una imagen descargada del laboratorio.  
**Resultado esperado:** Metadatos disponibles, si existen.  
**Observado en clase:** Se comenta información del software de edición de la imagen. El nombre se representa con un marcador.  
**Riesgo o límite:** Los metadatos pueden ser editados y no prueban software instalado en el servidor.

## Consulta de coincidencias

**Ampliación técnica · reconstrucción explicativa del uso visto**

|  |
| --- |
| searchsploit "IIS 7.5" |

**Opciones:** La cadena limita la búsqueda textual de la base local.  
**Objetivo:** Investigar referencias para el servicio observado.  
**Resultado esperado:** Entradas candidatas que requieren lectura y contraste.  
**Observado en clase:** Se menciona un resultado de FTP cuya aplicabilidad no está confirmada.  
**Riesgo o límite:** Una coincidencia de nombre o versión no acredita una vulnerabilidad del objetivo.

# Actualización del registro de herramientas

| **Herramienta o recurso** | **Nivel documentado** | **Qué se incorpora** | **Pendiente** |
| --- | --- | --- | --- |
| Burp Intruder | Practicada | Variación de filename con Sniper y lectura conjunta de estado, longitud y cuerpo. | Repetir con una petición base correcta. |
| Shortscan | Introducida | Finalidad de enumeración de nombres cortos de IIS. | Instalación y uso efectivo. |
| IIS y web.config | Introducida | Relación entre configuración, ubicación y manejadores. | Validar el ejemplo mostrado. |
| PowerShell y Base64 | Introducida | Separar comando, codificación y conexión. | Resolver la ejecución dentro del contexto de la práctica. |
| SeImpersonate y Juicy Potato | Mencionada | Tema de escalada anunciado. | Explicación y práctica posteriores. |

# Resumen y checklist de repaso

La clase enseña a razonar una subida de archivos desde la tecnología real del servidor. Los filtros de nombre, tipo y contenido pueden combinarse; por ello las pruebas deben aislar variables. Bounty muestra el interés de estudiar configuraciones activas como web.config y también la necesidad de verificar cada paso. La sesión termina con la conexión y la escalada pendientes.

☐ Identifico la tecnología antes de seleccionar formatos de prueba.

☐ Explico las ocho familias del mapa sin confundir MIME con contenido.

☐ Diferencio aceptación, almacenamiento, acceso e interpretación.

☐ Configuro una única posición de Intruder sin duplicar el punto.

☐ Comparo el cuerpo de las respuestas, además de su longitud.

☐ Distingo el resultado esperado del observado.

☐ Puedo explicar por qué un 403 o un 500 no basta para concluir.

☐ Relaciono cada debilidad con una medida de defensa.

☐ Reconozco los pasos que quedaron pendientes en Bounty.

# Glosario

| **Término** | **Significado** |
| --- | --- |
| File upload | Funcionalidad de subida de archivos a una aplicación. |
| Bypass | Forma de eludir una comprobación concreta. |
| MIME | Identificación declarada del tipo de contenido. |
| Magic bytes | Secuencia que ayuda a reconocer un formato. |
| Archivo políglota | Archivo que satisface más de una interpretación. |
| Handler | Componente asignado a procesar determinadas solicitudes. |
| Directory listing | Presentación del contenido de un directorio. |
| RCE | Ejecución remota de código. |
| Reverse shell | Consola cuya conexión inicia el objetivo hacia el equipo que escucha. |
| Codificación | Cambio de representación de datos; no equivale a cifrado. |

# Pendientes de la práctica

|  |
| --- |
| **Riesgo técnico** Aceptar archivos que puedan modificar la configuración del servidor puede afectar al procesamiento de solicitudes. Su impacto debe comprobarse por separado; en esta clase no se acredita ejecución remota. |

|  |
| --- |
| **Pendiente de confirmar** No se conoce la causa exacta del error 500 ni se acredita una reverse shell funcional. No se dispone del XML íntegro, de las capturas ni del esquema original compartido. SeImpersonatePrivilege se pospone. Estas ausencias no se rellenan con resultados de otras clases. |

# Referencias técnicas complementarias

Ampliaciones y comprobaciones consultadas el 2/10/2026. Las referencias explican conceptos; no certifican lo sucedido en la máquina de clase.

**R1 · OWASP File Upload Cheat Sheet** <https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html>

**R2 · Microsoft IIS handlers** <https://learn.microsoft.com/en-us/iis/configuration/system.webserver/handlers/>

**R3 · Shortscan** <https://github.com/bitquark/shortscan>

**R4 · HTTP Semantics** <https://www.rfc-editor.org/rfc/rfc9110.html#section-15>

**R5 · Delegación de configuración IIS** <https://learn.microsoft.com/en-us/iis/manage/managing-your-configuration-settings/how-to-use-configuration-delegation-in-iis>

**R6 · PowerShell EncodedCommand** <https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_powershell_exe?view=powershell-5.1>

# Ideas importantes de la transcripción

| **Tema** | **Idea importante** | **Referencia** |
| --- | --- | --- |
| Objetivo | Repasar las validaciones de subida y retomar Bounty. | F001 · 00:11:49-00:14:18 |
| Validación del cliente | Modificar el navegador o interceptar permite comprobar el control del servidor. | F001 · 00:26:49-00:29:21 |
| Extensiones | Listas de bloqueo y permitidas; variantes y dobles extensiones. | F001 · 00:29:24-00:38:08 |
| Tipo y contenido | MIME, firmas, imagen con código y metadatos. | F001 · 00:38:11-00:43:38 |
| Configuración y ruta | Archivos de configuración, rutas y sobrescritura. | F001 · 00:43:41-00:44:38 |
| Mitigación | Validar, renombrar, aislar, limitar y analizar. | F001 · 00:44:42-00:50:20 |
| Reconocimiento | TTL como pista e IIS 7.5 en el puerto 80. | F001 · 01:01:39-01:06:41 |
| Enumeración web | Diccionarios, estados HTTP y dificultades con Shortscan. | F001 · 01:14:23-01:37:26 |
| Intruder | Variar filename, cuidar puntos y comparar respuestas. | F001 · 02:08:35-02:20:28 |
| web.config | Explicación de configuración y código; intentos con errores. | F001 · 02:21:06-02:40:19 |
| Codificación | PowerShell, comillas y Base64; conexión no conseguida. | F001 · 02:41:10-02:50:57 |
| Continuación | Revisar los archivos y retomar la escalada. | F001 · 02:51:09-02:56:18 |

# Actualización de memoria del proyecto

Registro asociado exclusivamente a esta sesión. No modifica las instrucciones generales del proyecto.

| **Categoría** | **Información nueva** | **Nivel de certeza** | **Acción futura** |
| --- | --- | --- | --- |
| Sesión | Carlos Castillo Sanjuan; 1/10/2026; file upload y Bounty. | Alta | Conservar el material y esta revisión. |
| Validaciones | Se estudian ocho familias de comprobaciones. | Alta | Repasar condiciones y límites de cada una. |
| Laboratorio | IIS 7.5 y comportamiento diferencial de .config. | Alta | Conservar las evidencias cuando se disponga de capturas. |
| Ejecución | La conexión final no queda verificada. | Alta | Revisar el archivo y validar primero una prueba mínima. |
| Diagnóstico | Comillas, formato y etiquetas se proponen como causas. | Baja | Contrastar antes de asignar una causa raíz. |
| Escalada | SeImpersonate y Juicy Potato se anuncian para continuar. | Alta | No registrar escalada completada. |
| Recursos | No se aportan el XML completo ni el dibujo original. | Alta | Incorporarlos solo si se facilitan para esta sesión. |
