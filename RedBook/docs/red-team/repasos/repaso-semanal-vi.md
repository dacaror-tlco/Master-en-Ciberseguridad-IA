---
tags:
- Repasos
date: '2026-09-25'
author: Yuba
---

# Repaso semanal VI

<p class="note-meta">2026-09-25 · Yuba</p>

![Ilustración de Yuba comiendo espuma de café; laboratorios SQLi de la sesión.](../../assets/img/repaso-semanal-vi/img001.png)

Mapa de la clase: laboratorios y conceptos

Repaso semanal VI · Yuba González Parrilla · 25/09/2026  
Laboratorios de PortSwigger Web Security Academy

**SQL INJECTION → comprender la consulta y observar la respuesta**

**Scope → navegar y mapear → identificar parámetros → Repeater → comparar respuestas**

**1 · UNION con estructura conocida**

category → número de columnas → compatibilidad de texto → users / username / password. La respuesta HTTP muestra los datos.

**2 · Enumeración en PostgreSQL (no Oracle)**

Columnas → version() → information\_schema.tables → table\_name → information\_schema.columns → column\_name → datos de la tabla identificada.

**3 · Enumeración en Oracle**

Misma metodología → FROM DUAL para la prueba del laboratorio → marcador Yuba → ALL\_TABLES → ALL\_TAB\_COLUMNS → datos.

**4 · Blind SQLi con retardos e inferencia**

TrackingId → pg\_sleep → CASE WHEN → verdadero / falso → existencia de usuario → longitud → caracteres → Intruder.

**DOS FORMAS DE OBSERVAR  
UNION: leer datos en la respuesta.  
Blind temporal: deducir un dato por la diferencia de tiempo.**

Conceptos transversales: parámetros GET/POST, cookies, tipos compatibles, metadatos, sintaxis del gestor, codificación y evidencia. El cambio de gestor modifica la sintaxis; el razonamiento se conserva.

# 1. Qué se practica y cómo se organiza

La sesión busca afianzar la inyección SQL mediante práctica manual. Yuba empieza con un ejercicio de UNION en el que se conocen los nombres de la tabla y las columnas. Después retira esa ayuda: hay que descubrir la estructura de la base de datos. La misma tarea se repite en Oracle y el repaso termina con una inyección ciega basada en tiempos.

La inyección SQL aparece cuando una entrada que debería tratarse como un dato altera la consulta que ejecuta la aplicación. En las primeras prácticas, el filtro de categorías es el punto de entrada. En la última, lo es una cookie de seguimiento. Por tanto, revisar únicamente los campos visibles de un formulario deja fuera otras entradas relevantes.

## La metodología común

| **Fase de auditoría** | **Aplicación en esta clase** |
| --- | --- |
| Planificación | Delimitar el laboratorio y añadir su URL al scope. |
| Recogida de información | Navegar, enviar formularios, revisar el historial y construir el mapa de peticiones. |
| Análisis de vulnerabilidades | Elegir entradas distintas y comparar respuestas ante cambios controlados. |
| Pruebas de explotación controladas | Comprobar UNION, consultar metadatos e interpretar condiciones temporales dentro del laboratorio. |

## Una petición útil por cada contexto

Yuba ordena el Site map por parámetros y marca con colores las peticiones representativas. Varios valores de category en el mismo filtro no obligan a repetir toda la selección. En cambio, una petición GET y otra POST se conservan como contextos distintos. En la última práctica aparecen tres grupos: categorías, productId y el formulario de acceso.

Precisión técnica: el nombre del parámetro por sí solo no garantiza que dos entradas tengan el mismo tratamiento. También importan la ruta, el método, la ubicación y la lógica de la aplicación. Agrupar sirve para ordenar el trabajo, no para dar por probados contextos diferentes.

El objetivo de estudio es poder explicar qué información aporta cada prueba y cuál es el siguiente dato que falta. Memorizar una cadena sin comprender la consulta no permite adaptarse al cambio de gestor o a una respuesta que ya no muestra datos.

# 2. Burp Suite: preparar y observar

## Scope, proxy e historial

El scope delimita el conjunto de objetivos que interesa revisar. En clase se añade la URL del laboratorio y se filtra el historial para ver solo ese alcance. Al cambiar de ejercicio, Yuba retira el objetivo anterior de la selección para no confundir peticiones de laboratorios distintos.

La navegación recorre las categorías, el detalle de productos y My account; también envía el formulario de acceso. Burp registra las peticiones que pasan por su proxy. Repeater permite conservar una de ellas, modificarla y comparar la respuesta. El atajo Ctrl+R se utiliza para enviarla a esa herramienta.

Precisión técnica: registrar tráfico durante la navegación y ejecutar un rastreador automático son operaciones distintas. El historial y el Site map no prueban por sí solos que se haya realizado un rastreo activo completo.

## Qué hacer cuando falta tráfico

Durante la demostración hay problemas repetidos de captura y visualización. El profesor revisa el navegador integrado, el proxy, la interceptación, los filtros y el alcance; en un momento recurre a FoxyProxy. La lección práctica es comprobar que la petición existe en el historial antes de concluir que una funcionalidad no envía parámetros.

| **Elemento** | **Qué permite observar** |
| --- | --- |
| URL y método | Dónde se envía la petición y si utiliza GET o POST. |
| Parámetros y cookies | Entradas que llegan a la aplicación, como category o TrackingId. |
| Estado HTTP | Cambios entre respuestas, por ejemplo 200 y 500. |
| Cuerpo de respuesta | Texto reflejado, marcadores y datos devueltos. |
| Duración | Diferencias temporales relevantes cuando el contenido no cambia. |

## Codificación y representación

Los espacios y las comillas provocan varios errores de construcción. Se usa Ctrl+U para codificar texto en Burp y se comenta el uso de +. Deben distinguirse la expresión SQL y su transporte en la petición: el SQL sí contiene espacios; la codificación depende del lugar donde se introduce el valor.

En la práctica de PostgreSQL, la vista Render no muestra cómodamente todo el resultado. Yuba busca la salida en el contenido de la respuesta. Que un dato no se vea en una previsualización no significa que el servidor no lo haya devuelto.

# 3. UNION con tabla y columnas conocidas

El primer laboratorio sitúa la vulnerabilidad en el filtro de categorías y proporciona la estructura de interés: la tabla users y las columnas username y password. El objetivo del ejercicio es recuperar esos datos y utilizar la cuenta administrativa del propio laboratorio. La explicación comienza comprobando cómo cambia la respuesta al alterar las comillas.

## Del indicio a una prueba coherente

En la demostración, una modificación produce un error 500 y otra devuelve 200. La explicación es que la entrada altera la sintaxis de la consulta. Un error aislado es un indicio: para sostener la conclusión hay que relacionarlo con cambios controlados y resultados reproducibles. Del mismo modo, una respuesta 200 no descarta una SQLi.

## Número de columnas de la consulta

Se comparan dos métodos. ORDER BY prueba posiciones de la lista de resultados; en el ejemplo, 1 y 2 funcionan y 3 falla. UNION SELECT prueba una lista con distinto número de NULL; funciona con dos expresiones y falla con una o tres. Ambos resultados llevan a dos columnas en la consulta original, no a dos columnas en toda la tabla de la base de datos.

ORDER BY 1  
ORDER BY 2  
ORDER BY 3  
UNION SELECT NULL, NULL

Son fragmentos de sintaxis explicados en clase, separados del envoltorio HTTP. ORDER BY ordena por una posición del resultado; NULL sirve como valor de prueba en cada posición de UNION. La compatibilidad del número de expresiones es necesaria para combinar ambas consultas.

## Compatibilidad de texto y lectura de datos

Después se sustituye cada NULL, por separado, por un texto sencillo como 'a'. Se comprueba si la petición funciona y dónde aparece el marcador. En este laboratorio las dos posiciones aceptan texto. Eso identifica posiciones compatibles y visibles; no demuestra que todas las columnas físicas de una tabla tengan tipo textual.

SELECT username, password FROM users

La selección usa identificadores sin comillas de cadena para referirse a las columnas. El profesor describe los datos devueltos y menciona al usuario Carlos. La transcripción no conserva las contraseñas ni una confirmación inequívoca de resolución del primer ejercicio; no deben completarse a partir de suposiciones.

Riesgo demostrado: una consulta construida con entradas manipulables puede revelar datos de otras tablas. No confundir la compatibilidad de tipos con la autorización para leer esos datos.

# 4. PostgreSQL: descubrir la estructura

El segundo ejercicio añade la dificultad principal: los nombres de la tabla y de sus columnas no se conocen de antemano. Se repiten las pruebas de columnas y texto, y después se identifica el gestor para elegir una sintaxis adecuada. Yuba prueba una forma de consultar la versión que falla y otra que devuelve una cadena identificada como PostgreSQL 12.22. La versión procede de su lectura oral; no se dispone de una captura de esa salida.

SELECT version()

Conocer el gestor permite consultar sus referencias. Un error al probar @@version no basta por sí solo para descartar un producto: también puede haber un problema de contexto o sintaxis. Aquí la identificación útil procede del texto de versión que el profesor describe.

## Qué es information\_schema

information\_schema reúne vistas de metadatos: información sobre las tablas, las columnas y otros elementos de la base de datos. No es la tabla de usuarios. Su utilidad consiste en averiguar cómo se llaman y cómo están organizados los objetos que después se quieren consultar.

| **Vista o campo** | **Función en el razonamiento** |
| --- | --- |
| information\_schema.tables | Consultar metadatos de tablas y vistas visibles para el usuario. |
| table\_name | Obtener el nombre del objeto. |
| information\_schema.columns | Consultar metadatos de columnas. |
| column\_name | Obtener el nombre de una columna. |
| WHERE table\_name = … | Limitar los resultados al nombre de tabla identificado. |

La consulta combinada mantiene las dos expresiones que exige UNION. Utilizar \* sin revisar cuántas columnas devuelve la vista rompe esa compatibilidad. Por eso se selecciona el campo de interés y se mantiene una expresión de relleno en la otra posición.

## De nombres a datos

Primero se listan nombres de tablas y se localiza una candidata de usuarios. Después se consultan los nombres de sus columnas; filtrar por table\_name evita revisar el catálogo completo. El nombre buscado se expresa como una cadena entre comillas simples. Finalmente, se seleccionan las columnas identificadas sobre la tabla concreta.

Los sufijos de nombres cambian entre instancias del laboratorio y la transcripción no permite reconstruirlos con seguridad. Yuba describe la recuperación de la cuenta administrator, el acceso con su contraseña y la resolución del laboratorio. Se conserva ese resultado narrado, sin inventar identificadores ni credenciales.

Precisión verificada: las vistas de information\_schema muestran los objetos accesibles al usuario de la conexión; no garantizan revelar todos los objetos de todo el servidor. Véase R2 al final.

# 5. Oracle: mismo método, otra sintaxis

La tercera práctica repite el descubrimiento de tablas y columnas sobre Oracle. El orden de trabajo se mantiene: preparar Burp, revisar el filtro, determinar las columnas, comprobar texto y consultar los metadatos apropiados. La diferencia está en la sintaxis utilizada por ese gestor.

## La función de DUAL

En el laboratorio, una prueba con dos NULL falla hasta incorporar FROM DUAL. DUAL es una tabla auxiliar de Oracle útil para seleccionar expresiones constantes. No es una base de datos ni sustituye a la tabla real cuando la consulta ya necesita leer un objeto concreto.

SELECT NULL, NULL FROM DUAL

Actualización técnica verificada (R3): la regla oral «Oracle siempre necesita FROM» no debe generalizarse a todas las versiones. Desde Oracle Database Release 23, FROM DUAL es opcional para seleccionar expresiones. En el ejercicio se conserva porque es la solución mostrada.

## El marcador como punto de referencia

Yuba sustituye el texto de prueba por su nombre y por una segunda variante para localizar las posiciones reflejadas. Lo llama canary: un marcador reconocible que facilita buscar la salida. En este contexto sirve para seguir el dato dentro de la respuesta; no es una credencial ni demuestra por sí solo una vulnerabilidad adicional.

| **Tarea** | **PostgreSQL** | **Oracle** |
| --- | --- | --- |
| Listar tablas | information\_schema.tables | ALL\_TABLES |
| Campo del nombre | table\_name | TABLE\_NAME |
| Listar columnas | information\_schema.columns | ALL\_TAB\_COLUMNS |
| Campo de la columna | column\_name | COLUMN\_NAME |
| Prueba de constantes | SELECT con expresiones | FROM DUAL en el laboratorio |

El profesor consulta las referencias para localizar los campos exactos. Primero obtiene el nombre de la tabla de usuarios y después los de sus columnas. Durante la construcción aparece un error porque falta UNION; lo añade y la petición vuelve a funcionar. Es un ejemplo de por qué hay que revisar toda la expresión antes de atribuir un fallo a la inexistencia de datos.

Al final se describe la recuperación de las credenciales del laboratorio y su uso para acceder como administrador. No se conserva una contraseña legible ni un identificador completo de la tabla. La explicación incluye el impacto de una suplantación de cuenta; no consta una operación real con tarjetas o transferencias.

# 6. Blind SQLi: el tiempo como respuesta

El último laboratorio cambia el canal de observación. El enunciado sitúa el problema en TrackingId, una cookie de analítica cuyo valor se incorpora a una consulta SQL. La aplicación no devuelve los resultados de esa consulta ni refleja sus errores de una forma útil. Por eso las comillas pueden seguir produciendo respuestas 200 sin revelar lo que ocurre en la base de datos.

## Qué cambia respecto a UNION

| **Técnica** | **Información que se observa** |
| --- | --- |
| UNION, practicada | Los datos seleccionados aparecen en el cuerpo de la respuesta. |
| Blind booleana, mencionada | Una condición provoca un cambio observable de comportamiento o contenido. |
| Blind temporal, practicada | Una condición provoca un retardo distinguible en la respuesta. |

La idea central es sustituir «muéstrame el dato» por una pregunta con respuesta verdadera o falsa. Si la condición se cumple, se introduce una espera; si no se cumple, se mantiene el tiempo habitual. El contenido de la página puede ser idéntico en ambos casos.

## Retardo y condición

Yuba anticipa que el gestor es PostgreSQL y consulta pg\_sleep. También menciona || como operador de concatenación. Primero demuestra un retardo y luego incorpora CASE WHEN para decidir cuándo debe producirse. Se comparan 1=1 y 1=0 antes de formular preguntas sobre los datos.

SELECT CASE WHEN 1=1  
 THEN pg\_sleep(10)  
 ELSE pg\_sleep(0)  
END

La expresión anterior es una reconstrucción didáctica contrastada con R1, no una copia completa de la cookie usada en clase. CASE elige una rama; pg\_sleep(10) solicita una espera de diez segundos y pg\_sleep(0) representa la rama sin espera intencional. En la explicación oral se usa también un valor negativo; aquí se emplea cero para evitar una generalización sobre números negativos.

Una condición falsa no significa que la inyección no se haya ejecutado: puede haberse evaluado correctamente y haber tomado la rama sin retardo. Esta distinción es esencial para interpretar el resultado.

Las referencias orales a milisegundos se mezclan con esperas de cinco y diez segundos. No son medidas fiables de latencia. Lo que se describe con claridad es una diferencia perceptible. La documentación de PostgreSQL indica que la espera puede superar el tiempo solicitado por la carga y la resolución del sistema (R4).

# 7. Inferir existencia, longitud y caracteres

## Una pregunta cada vez

Una vez diferenciadas las dos respuestas temporales, el profesor cambia la condición constante por una pregunta sobre la existencia del usuario administrator en users. Compara ese nombre con otro inventado y describe una diferencia de respuesta. En este laboratorio esos nombres forman parte de la información disponible; no deben suponerse en una aplicación distinta.

El siguiente paso es preguntar por la longitud de la contraseña. La función LENGTH permite comparar ese número con un umbral. La pregunta «¿la longitud es mayor que n?» produce una sucesión de respuestas verdaderas hasta alcanzar un valor para el que deja de cumplirse.

LENGTH(password) > n  
SUBSTRING(password, posicion, 1) = 'a'

Son expresiones conceptuales del ejercicio: n y posicion son variables explicativas, no valores recuperados. La primera compara una longitud; la segunda comprueba un carácter concreto. En PostgreSQL, SUBSTRING también permite esta extracción: la referencia oral a MySQL no implica un cambio de gestor en el laboratorio.

## Cómo leer el salto sin equivocarse

Para la condición L > n, si n=18 da verdadero y n=19 da falso, L es 19. Si n=19 da verdadero y n=20 da falso, L es 20. El primer umbral falso identifica la longitud cuando se ha comprobado el umbral anterior y se mantiene la misma condición.

Pendiente de confirmar: durante la explicación se menciona primero 20 y después se concluye 19 caracteres. La transcripción no contiene la tabla de tiempos necesaria para decidir cuál corresponde a la ejecución. Se conserva 19 como conclusión verbal final, sin presentarlo como medición verificada.

## Qué aporta Intruder

Yuba envía la petición a Intruder, delimita una posición variable y utiliza una secuencia numérica para probar longitudes. Después plantea dos posiciones: el índice del carácter y el candidato que se compara. Selecciona Cluster bomb para combinar ambos conjuntos y explica que los retardos permiten localizar coincidencias.

La sesión muestra ajustes y dudas al elegir el generador de caracteres. No queda una configuración completa inequívoca ni una contraseña final recuperada. Sí queda explicado el mecanismo: cada comprobación aporta información parcial y la combinación de resultados permite reconstruir el dato.

Precisión técnica: una única petición lenta no confirma una respuesta verdadera. Para interpretar tiempos conviene comparar controles, repetir medidas y evitar que las peticiones concurrentes oculten la diferencia. Esta es una cautela de verificación, no un paso cuya ejecución quede documentada en la clase.

# 8. Errores que conviene reconocer

| **Situación** | **Interpretación y comprobación** |
| --- | --- |
| El Site map parece vacío | Revisar proxy, navegador, alcance y filtros; confirmar primero el tráfico real. |
| Una comilla devuelve 500 | Es un indicio que debe contrastarse con controles; puede haber otros errores. |
| UNION falla | Comprobar número de expresiones, tipos, cierre, comentarios y sintaxis del gestor. |
| La consulta usa \* | Puede devolver más columnas que las admitidas por el UNION. |
| El filtro por tabla falla | Distinguir el nombre usado como dato textual de los identificadores SQL. |
| No aparece el dato en Render | Buscar también en el cuerpo de la respuesta. |
| La página sigue devolviendo 200 | El estado no descarta una inyección ciega. |
| Una respuesta tarda más | Comparar controles y repetición antes de atribuirlo a la condición. |
| Se copia un nombre de otro alumno | Los identificadores de laboratorio pueden cambiar entre instancias. |

## Qué debe quedar aprendido

Antes de consultar datos, hay que comprender el contexto y las restricciones de la consulta. En UNION se necesita el mismo número de expresiones y tipos compatibles. Cuando faltan nombres de tablas o columnas, se recurre a metadatos. Cuando no se ven resultados, se busca una señal observable que permita evaluar condiciones.

Para repasar sin memorizar a ciegas, explica por qué ORDER BY 3 puede fallar cuando ORDER BY 2 funciona; qué aporta NULL; por qué se comprueba texto posición por posición; para qué sirve information\_schema; qué cambia en Oracle; y cómo un retardo puede responder a una pregunta sobre un dato que no se muestra.

## Impacto y prevención

La clase relaciona la lectura de credenciales con el acceso a cuentas ajenas. Conocer la estructura de una base de datos no equivale todavía a haber recuperado sus datos; recuperar un usuario tampoco demuestra por sí solo un acceso efectivo. Conviene registrar esos resultados por separado.

Ampliación técnica (R5): las consultas parametrizadas separan los datos de la estructura SQL. Deben acompañarse de permisos mínimos para la cuenta de base de datos y un tratamiento adecuado de los errores. Ocultar errores o respuestas no corrige la causa: la práctica temporal ilustra que puede seguir existiendo un canal de información.

# 9. Herramientas y vocabulario

| **Herramienta** | **Objetivo y uso visto** | **Fase / nivel** |
| --- | --- | --- |
| Burp Proxy y navegador | Capturar tráfico; navegar por el laboratorio. | Recogida de información · Practicada |
| Target / Site map / Scope | Delimitar y clasificar peticiones. | Planificación y recogida · Practicada |
| Burp Repeater | Modificar peticiones y comparar respuestas; Ctrl+R. | Análisis y pruebas controladas · Practicada |
| Burp Intruder | Variar números y candidatos; uso de Cluster bomb. | Pruebas controladas · Practicada |
| FoxyProxy | Ajustar el uso del proxy durante problemas de captura. | Recogida de información · Practicada |
| Web Security Academy | Entorno de los cuatro ejercicios. | Pruebas controladas · Practicada |
| Referencias de SQL | Consultar sintaxis de PortSwigger, PostgreSQL y Oracle. | Análisis · Practicada |

## Glosario de estudio

SQLi: inyección SQL. UNION: combinación de resultados de consultas compatibles. NULL: valor nulo utilizado en las pruebas de columnas. Metadatos: información sobre la estructura de los datos. Scope: alcance configurado. Repeater: herramienta de repetición manual de peticiones. Canary: marcador reconocible para localizar una salida.

Blind SQLi: inyección en la que no se obtiene directamente el resultado de la consulta. Time-based: inferencia mediante tiempos. CASE WHEN: selección condicional de una expresión. pg\_sleep: función de espera de PostgreSQL. LENGTH: longitud de una cadena. SUBSTRING: extracción de una parte de la cadena. Cluster bomb: combinación de conjuntos de valores para distintas posiciones de una petición.

## Comentarios complementarios de la sesión

Yuba comenta sus pruebas con agentes para auditoría web y menciona XBOW. La discusión se centra en cobertura, consumo de recursos, ruido y procedimiento. También habla del análisis de rutas de ataque de Active Directory y de priorizar puntos donde confluyen varias rutas. Son comentarios del profesor; no constituyen una práctica ni una validación de las capacidades comerciales citadas.

En otro intercambio se revisa de forma informal el rendimiento de una página con PageSpeed. No se conserva una puntuación concreta. La anécdota que inspira la portada ocurre al volver del descanso: Yuba aclara que está comiendo espuma de café. Picasso y Da Vinci son los roles de diseño y revisión, no personajes de la escena.

# 10. Referencias y cuestiones abiertas

## Fuente de clase

F001 · Transcripción aportada por Chema para la sesión del 25/09/2026, profesor Yuba. Cobertura leída: desde 10:50 hasta 03:08:23. Las afirmaciones sobre acciones y resultados son las narradas en esa fuente; no se aportaron capturas del laboratorio.

## Referencias de comprobación técnica

Consultadas el 26/09/2026. Estas referencias aclaran sintaxis y limitaciones; no demuestran lo que se ejecutó durante la sesión.

R1 · PortSwigger, SQL injection cheat sheet  
https://portswigger.net/web-security/sql-injection/cheat-sheet

R2 · PostgreSQL, information\_schema.tables  
https://www.postgresql.org/docs/current/infoschema-tables.html

R3 · Oracle, Selecting from the DUAL Table  
https://docs.oracle.com/en/database/oracle/oracle-database/26/sqlrf/Selecting-from-the-DUAL-Table.html

R4 · PostgreSQL, Delaying Execution  
https://www.postgresql.org/docs/current/functions-datetime.html#FUNCTIONS-DATETIME-DELAY

R5 · PortSwigger, prevención de SQL injection  
https://portswigger.net/web-security/sql-injection#how-to-prevent-sql-injection

R6 · PortSwigger, laboratorio de retardos e inferencia  
https://portswigger.net/web-security/sql-injection/blind/lab-time-delays-info-retrieval

## Pendientes que no deben rellenarse por intuición

No están disponibles las peticiones HTTP completas, los nombres aleatorios exactos de las tablas y columnas, las contraseñas ni las medidas de tiempo de cada prueba. La conclusión oral de 19 caracteres necesita cotejarse con la condición y el primer umbral falso. No consta en la transcripción una recuperación completa de la contraseña ni el cierre verificado del último laboratorio.

Las pausas de trabajo autónomo no contienen una explicación de cada alumno. Las conversaciones sobre proveedores, aplicaciones personales e incidencias ajenas no se utilizan para completar el procedimiento técnico. Los errores claros de reconocimiento de voz se normalizan; los datos dudosos permanecen señalados.

# Ideas importantes de la transcripción

| **Tema** | **Idea importante** | **Referencia F001** |
| --- | --- | --- |
| Objetivo | Práctica incremental y comprensión de SQLi manual. | 11:57–12:24 |
| Laboratorio inicial | Estructura conocida: users, username y password. | 19:21–20:05 |
| Metodología web | Alcance, navegación y clasificación de entradas. | 39:51–45:44 |
| Detección | Comparar cambios de respuesta al modificar comillas. | 45:46–47:22 |
| Columnas y texto | ORDER BY, NULL y marcadores de texto. | 47:23–49:56 |
| Datos conocidos | Consultar columnas proporcionadas por el ejercicio. | 50:17–52:00 |
| Gestor | Lectura oral de la versión PostgreSQL 12.22. | 01:19:09–01:22:28 |
| Metadatos | Descubrir tablas y columnas; filtrar por nombre. | 01:24:06–01:35:36 |
| Resultado no Oracle | Acceso como administrador y laboratorio resuelto. | 01:36:03–01:36:27 |
| Café | Yuba aclara que come espuma de café. | 02:01:48–02:02:16 |
| Oracle | DUAL, marcador Yuba, ALL\_TABLES y ALL\_TAB\_COLUMNS. | 02:16:25–02:26:59 |
| Blind | TrackingId; el resultado SQL no se muestra. | 02:44:32–02:46:49 |
| Retardos | pg\_sleep y comparación de comportamiento. | 02:47:26–02:51:50 |
| Condiciones | CASE y preguntas verdaderas o falsas. | 02:52:17–02:57:38 |
| Longitud | Umbrales numéricos; conclusión oral final de 19. | 02:58:05–03:03:53 |
| Caracteres | SUBSTRING e Intruder con dos posiciones. | 03:03:56–03:07:43 |

# Actualización de memoria del proyecto

Registro de esta sesión para su custodia. Los datos técnicos del laboratorio no se trasladan automáticamente a futuras clases.

| **Categoría** | **Información nueva** | **Certeza** | **Acción futura** |
| --- | --- | --- | --- |
| Sesión | Repaso semanal VI; Yuba; 25/09/2026. | Alta | Conservar fuente y entrega juntas. |
| Temario | UNION, metadatos en PostgreSQL y Oracle, SQLi ciega temporal. | Alta | Repasar qué evidencia aporta cada etapa. |
| Metodología | Clasificar entradas antes de probarlas en Repeater. | Alta | Distinguir método, ruta y contexto. |
| Resultado | Resolución narrada del laboratorio no Oracle. | Alta | No inventar credenciales ni sufijos. |
| Resultado blind | 19 caracteres es la conclusión verbal final, con ambigüedad previa. | Media | Confirmar con captura de tiempos y condición. |
| Portada local | Yuba con café y cuchara de espuma; los diseñadores no aparecen. | Alta | Mantener esta indicación en esta entrega. |
| Esquema local | Mapa inicial editable con laboratorios y conceptos. | Alta | Usarlo como guía de lectura de la sesión. |

## Repaso final

El recorrido empieza observando peticiones y termina interpretando respuestas. En los ejercicios UNION se leen datos; en la práctica ciega se hacen preguntas. En ambos casos, cada conclusión debe apoyarse en una prueba cuyo significado se entienda.

Para comprobar que has asimilado la clase, dibuja sin mirar dos recorridos: el que descubre una tabla desconocida hasta identificar sus columnas, y el que convierte una condición sobre una cadena en una diferencia de tiempo. Después explica en qué momento cambia la sintaxis por usar Oracle y qué partes del razonamiento permanecen iguales.
