---
tags:
- General
date: '2026-09-17'
author: Carlos Castillo
---

# Sesión 2026-09-17

<p class="note-meta">2026-09-17 · Carlos Castillo</p>

![](../../assets/img/apuntes-17-09-2026-carlos-castillo/img001.png)

**ESQUEMA VISUAL DE LA SESIÓN**

*De GoodGames a “Torrijas”: metodología, CMS, LFI, credenciales y escalada*

|  |  |  |
| --- | --- | --- |
| **1 · PLAN INICIAL** GoodGames SQL Injection manual ORDER BY / UNION SELECT | | |
| **↓ CAMBIO POR FALLOS** HTB/VPN inestable Se abandona GoodGames | | |
| **2 · RECOGIDA** Nmap → 22 / 80 / 3306 Web básica + dirsearch WordPress detectado | | |
| **3 · ANÁLISIS** CMS + WPScan Plugins / usuarios / versión Web Directory Free 1.7.2 | | |
| **4 · EXPLOTACIÓN** LFI no autenticado Lectura de /etc/passwd Enumeración de usuarios | | |
| **5 · ACCESO / DATOS** Hydra → SSH wp-config.php → credenciales BD MariaDB/MySQL | | |
| **6 · ESCALADA** sudo -l bpftrace ejecutable como root GTFOBins → escalada | | |

|  |
| --- |
| **Idea clave —** La sesión no completó GoodGames. El contenido práctico principal salió de la máquina alternativa “Torrijas”, utilizada para repasar metodología web, WordPress, LFI, acceso a base de datos y escalada de privilegios. |

# 1. Metadatos y contexto de la sesión

|  |  |
| --- | --- |
| **Fecha** | 17/09/2026 |
| **Profesor** | Carlos Castillo |
| **Tema principal** | Repaso de SQL Injection + práctica alternativa con WordPress, LFI y MariaDB/MySQL |
| **Máquina prevista** | GoodGames (HTB), no completada por problemas de disponibilidad/conexión |
| **Máquina práctica efectiva** | “Torrijas” (máquina compartida durante la clase; nombre usado en la sesión) |
| **Objetivo** | Practicar metodología de auditoría web y encadenar evidencias hasta acceso y escalada |

# 2. Objetivos y resumen

- Reforzar la metodología de SQL Injection: identificar columnas, validar qué columnas son visibles y progresar hacia tablas, columnas y datos.
- Recordar que una SQLi no implica automáticamente una shell: hay que valorar qué información o privilegios aporta y cómo encadenarlos.
- Practicar reconocimiento y enumeración en una máquina alternativa cuando GoodGames dejó de ser viable.
- Introducir WordPress como CMS y usar herramientas específicas como WPScan para enumerar versión, plugins y usuarios.
- Explotar una vulnerabilidad de lectura de archivos locales (LFI) en un plugin de WordPress y usarla para descubrir usuarios y rutas interesantes.
- Relacionar la información de configuración de WordPress con credenciales de base de datos y continuar la enumeración directamente en MariaDB/MySQL.
- Revisar la escalada de privilegios a partir de permisos de sudo sobre un binario, usando GTFOBins como referencia.

|  |
| --- |
| **Mensaje metodológico del profesor —** No hay que pensar siempre “necesito reverse shell”. La pregunta correcta es: «¿qué tengo ahora y hasta dónde puedo llegar con ello?». La práctica se orientó a encadenar información y privilegios, no a forzar un único camino. |

# 3. Fundamentos: metodología de SQL Injection

## 3.1. Detección y progresión

La sesión comenzó repasando la dificultad real de SQL Injection: muchas veces la vulnerabilidad existe en un punto concreto y hay que detectar el parámetro correcto antes de poder enumerar. Se recordó la secuencia conceptual:

- Detectar un punto potencialmente inyectable.
- Determinar el número de columnas (por ejemplo, mediante ORDER BY).
- Comprobar qué posiciones/columnas admiten el tipo de dato necesario y cuáles se reflejan en la respuesta.
- Enumerar bases de datos / tablas / columnas según el contexto.
- Extraer datos relevantes.
- Evaluar si los datos permiten escalar a otro acceso o vulnerabilidad.

|  |
| --- |
| ORDER BY ... UNION SELECT ... |

|  |
| --- |
| **Clase —** Carlos insistió en que `sqlmap` puede ayudar si detecta la inyección, pero no sustituye la comprensión del proceso manual. |

## 3.2. Qué hacer cuando la base de datos no da una shell directa

Se discutió que una base de datos de una aplicación puede contener usuarios de la propia web sin contener credenciales del servidor. Aun así, esos datos pueden abrir nuevas rutas:

- Obtener una cuenta administrativa de la aplicación y buscar funcionalidades adicionales vulnerables.
- Modificar atributos o registros de una aplicación cuando el usuario de base de datos tenga permisos suficientes.
- Consultar el usuario actual de la base de datos y sus capacidades para estimar si se pueden leer archivos o ejecutar acciones más avanzadas.
- Encadenar el hallazgo con otros fallos en la aplicación o el sistema.

|  |
| --- |
| **Buena práctica —** No asumir que una cuenta “admin” de una web equivale a administrador del sistema operativo. Son ámbitos de privilegio distintos. |

# 4. Intento inicial: máquina GoodGames

La máquina prevista era GoodGames, elegida para seguir trabajando SQL Injection. Se llegó a iniciar la conexión y el reconocimiento, pero la infraestructura de HTB/VPN presentó fallos e inestabilidad durante la clase. El profesor decidió no forzar una práctica que estaba funcionando de forma errática y cambió a una máquina alternativa.

|  |
| --- |
| **Pendiente de confirmar —** GoodGames no se completó en esta sesión. No deben mezclarse con esta fecha pasos o resultados de un walkthrough externo. La transcripción sí recoge que el profesor esperaba usarla para mostrar una situación con una única columna útil/visible durante UNION SELECT. |

# 5. Práctica efectiva: máquina “Torrijas”

## 5.1. Fase: Planificación

Objetivo: usar una máquina alternativa para continuar practicando metodología web. El profesor indicó que combinaba una parte de CMS/WordPress con contenidos de SQL y que serviría como repaso.

## 5.2. Fase: Recogida de información

### Reconocimiento con Nmap

El escaneo mostró tres superficies principales de ataque: SSH, HTTP y MySQL/MariaDB expuesto. La idea importante no fue solo “ver puertos”, sino pensar qué implica cada servicio dentro del contexto.

|  |  |
| --- | --- |
| **Comando** | nmap [opciones] 192.168.0.204 |
| **Opciones** | Durante la clase se mencionó un escaneo inicial y posteriormente `-sC -sV` sobre los puertos descubiertos. |
| **Objetivo** | Identificar servicios y versiones accesibles. |
| **Resultado esperado** | Puertos 22/tcp, 80/tcp y 3306/tcp visibles en la práctica. |
| **Interpretación** | 22 → SSH; 80 → aplicación web; 3306 → MySQL/MariaDB accesible desde red. La exposición de 3306 no implica por sí sola que se pueda autenticar desde fuera. |

|  |
| --- |
| **Evidencia de clase —** La IP usada en la máquina alternativa fue 192.168.0.204. Se trataba de un laboratorio privado/autorizado compartido para la sesión. |

### Inspección de la web

En el puerto 80 se encontró una web muy básica, con varias secciones poco funcionales. El profesor remarcó que antes de automatizar hay que comprobar manualmente si formularios y enlaces realmente realizan acciones.

- Revisar páginas, formularios, enlaces, código fuente y comportamientos de redirección.
- Prestar atención a integraciones externas (ej. APIs) y a posibles claves expuestas, sin asumir que exista una key solo por ver un mapa o recurso externo.
- No lanzar fuzzing o scripts “por reflejo” antes de entender qué superficies reales existen.

### Enumeración de directorios

Se utilizó `dirsearch` para descubrir rutas. El hallazgo importante fue una instalación de WordPress dentro de la aplicación.

|  |  |
| --- | --- |
| **Comando** | dirsearch -u http://<objetivo> -w <wordlist> |
| **Opciones** | Se mencionó una wordlist tipo directory-list-2.3-medium. |
| **Objetivo** | Descubrir directorios y recursos no enlazados. |
| **Resultado esperado** | Aparecen rutas y, en esta práctica, una ruta relacionada con WordPress. |
| **Interpretación** | La presencia de WordPress cambia la metodología: conviene enumerar versión, plugins, usuarios y rutas propias del CMS. |

### Resolución local del nombre

Para trabajar con el nombre usado por la aplicación se añadió una entrada a `/etc/hosts`. La transcripción recoge el nombre `torrija.thl` y la ruta de WordPress bajo ese host.

|  |
| --- |
| sudo nano /etc/hosts # añadir la IP del laboratorio asociada a torrija.thl |

|  |
| --- |
| **Precaución —** La transcripción contiene varias autocorrecciones del reconocimiento de voz alrededor del dominio. El nombre que se escucha con mayor consistencia es `torrija.thl`. |

# 6. WordPress y CMS

## 6.1. Concepto de CMS

CMS significa Content Management System (sistema de gestión de contenidos). Permite crear y administrar contenido web mediante un motor ya preparado, sin programar toda la aplicación desde cero.

- Ventaja: facilita la creación y gestión de sitios.
- Superficie de ataque: versiones del núcleo, temas, plugins, rutas predecibles y configuraciones.
- Metodología: reconocer qué CMS es, obtener la versión, enumerar extensiones y buscar fallos aplicables al componente exacto.

## 6.2. WPScan

WPScan se presentó como una herramienta específica para WordPress, comparable conceptualmente a un escáner especializado del CMS. Puede enumerar información que un escaneo genérico no presenta de forma directa.

|  |  |
| --- | --- |
| **Comando** | wpscan --url http://torrija.thl/wordpress --enumerate ap --plugins-detection aggressive |
| **Opciones** | `--url`: objetivo. `--enumerate ap`: todos los plugins. Se comentó también `vp` para plugins vulnerables y `u` para usuarios. `--plugins-detection aggressive`: detección más agresiva. |
| **Objetivo** | Enumerar WordPress, plugins, versiones y otros hallazgos. |
| **Resultado esperado** | Detección del WordPress y del plugin vulnerable usado en la práctica. |
| **Interpretación** | La salida debe analizarse: versión identificada, plugins, XML-RPC, archivos conocidos y otros indicadores. |

## 6.3. Información útil del árbol de WordPress

- `wp-admin`: zona administrativa.
- `wp-content`: contenido, plugins, temas y uploads.
- `wp-includes`: componentes internos del core.
- `wp-config.php`: archivo crítico de configuración; puede contener nombre de base de datos, usuario, contraseña y host.

|  |
| --- |
| **Idea clave —** Cuando se compromete el usuario que gestiona una web/CMS, una prioridad es revisar los archivos de configuración del propio framework. Suelen concentrar secretos y parámetros de conexión. |

# 7. Análisis de vulnerabilidades: plugin Web Directory Free

WPScan terminó identificando el plugin “Web Directory Free” versión 1.7.2. El profesor buscó vulnerabilidades públicas para esa versión y centró la práctica en una inclusión local de archivos (LFI) no autenticada.

|  |
| --- |
| **Pendiente de confirmar — CVE —** La transcripción automática alterna entre “CVE-2024-3673” y “CVE-2024-3669”. El número exacto no debe darse por confirmado sin revisar la fuente original usada en clase. En estos apuntes se conserva el tipo de vulnerabilidad y la versión del plugin, que sí aparecen de forma consistente. |

## 7.1. Path Traversal vs LFI

Durante la explicación se diferenció el acceso mediante rutas relativas del efecto final de incluir/leer archivos locales:

- Path Traversal: técnica/patrón de navegación mediante secuencias como `../` para salir del directorio esperado.
- LFI (Local File Inclusion): vulnerabilidad que permite incluir o leer archivos locales del sistema a través de la aplicación.

|  |
| --- |
| **Nota —** En la práctica el payload usa traversal (`../`) como mecanismo para alcanzar un archivo local, y el resultado explotado se trató como LFI. |

# 8. Pruebas de explotación controladas: LFI

## 8.1. Uso del exploit

Se descargó un exploit en Python y se ejecutó especificando la URL del WordPress y el archivo a leer. La transcripción sí conserva la lógica de los parámetros, pero no un nombre de fichero de exploit completamente fiable.

|  |  |
| --- | --- |
| **Comando** | python3 <exploit.py> --url http://torrija.thl/wordpress --file ../../../../../../etc/passwd |
| **Opciones** | `--url`: raíz del WordPress vulnerable. `--file`: archivo objetivo alcanzado mediante traversal. |
| **Objetivo** | Comprobar que la vulnerabilidad permite leer `/etc/passwd`. |
| **Resultado esperado** | Contenido del archivo devuelto por la aplicación/exploit. |
| **Interpretación** | Si se obtiene `/etc/passwd`, el LFI está confirmado y permite enumerar usuarios y rutas potenciales. |
| **Riesgo** | Solo en el laboratorio autorizado. No extrapolar el payload a sistemas ajenos. |

## 8.2. Qué buscar tras leer /etc/passwd

- Usuarios con shell interactiva (`/bin/bash` u otra shell válida).
- Directorios home asociados a usuarios reales.
- Posibles archivos SSH en `~/.ssh/`, si el usuario vulnerable tiene permisos para leerlos.
- Archivos de configuración conocidos del servicio o CMS.

Se probaron rutas de claves privadas SSH para varios usuarios. No se obtuvo una clave privada útil y se explicó que archivos como `/etc/shadow` requieren privilegios superiores.

## 8.3. Convertir el exploit en una petición comprensible

Carlos abrió el script para mostrar que un exploit público no es “magia”: puede traducirse a una petición HTTP. Se construyó conceptualmente un `curl` con método POST, URL, cabeceras/datos y el parámetro del archivo objetivo.

|  |
| --- |
| curl -X POST 'http://torrija.thl/wordpress/<ruta-del-plugin>' \  -d 'target\_file=../../../../../../etc/passwd' |

|  |
| --- |
| **Pendiente de confirmar —** La ruta exacta del endpoint del plugin no quedó legible de forma fiable en la transcripción. Se conserva la estructura del request, no una URL inventada. |

# 9. Obtención de acceso por SSH

Tras obtener nombres de usuario válidos desde el sistema, se planteó fuerza bruta controlada contra SSH usando Hydra y una wordlist. La clase creó un fichero con los posibles usuarios y usó una lista de contraseñas tipo rockyou.

|  |  |
| --- | --- |
| **Comando** | hydra -L usuarios.txt -P /usr/share/wordlists/rockyou.txt ssh://192.168.0.204 |
| **Opciones** | `-L`: lista de usuarios; `-P`: lista de contraseñas; `ssh://`: servicio objetivo. |
| **Objetivo** | Encontrar una combinación usuario/contraseña válida para SSH. |
| **Resultado esperado** | Una credencial válida en el laboratorio. |
| **Interpretación** | La clase acabó trabajando con un usuario cuyo nombre aparece como `premo` y una contraseña verbalizada como `Casandra`; la ortografía exacta debe conservarse con cautela por el ASR. |
| **Riesgo** | La fuerza bruta solo se realizó en la máquina de práctica autorizada. |

|  |
| --- |
| **Evidencia / incertidumbre —** La transcripción registra repetidamente `primo` y `premo` en distintos puntos. No se normalizan como si fueran el mismo usuario. Donde el audio no es inequívoco, se mantiene la ambigüedad. |

# 10. Post-explotación inicial: revisar WordPress desde el sistema

Una vez dentro del sistema por SSH, se recorrió el árbol de la web hasta la instalación de WordPress y se abrió `wp-config.php`. Ese archivo contenía las credenciales de la base de datos usadas por la aplicación.

|  |
| --- |
| cd /var/www/html cd wordpress cat wp-config.php |

|  |
| --- |
| **Buena práctica —** Después de obtener acceso a un usuario relacionado con una aplicación web, revisar la configuración del servicio suele ser más rentable que buscar al azar por todo el sistema. |

# 11. Acceso y enumeración de MariaDB/MySQL

## 11.1. Conexión

El puerto 3306 estaba expuesto, pero el acceso remoto dio problemas relacionados con TLS/SSL y con las credenciales. Al estar ya dentro del servidor, el camino fiable fue conectarse a la base de datos localmente con las credenciales de `wp-config.php`.

|  |
| --- |
| mysql -h localhost -u admin -p |

|  |
| --- |
| **Lección —** Que un puerto esté abierto no significa que la autenticación remota vaya a funcionar. Si ya se dispone de acceso al servidor, probar `localhost` puede evitar restricciones de red, TLS o grants remotos. |

## 11.2. Flujo básico de enumeración

|  |
| --- |
| SHOW DATABASES; USE <base\_de\_datos>; SHOW TABLES; SELECT \* FROM <tabla>; |

El profesor relacionó este flujo con la SQL Injection: cuando se está conectado directamente al motor, ya se dispone del contexto y se puede consultar; con UNION-based SQLi primero hay que descubrir la estructura necesaria para que la consulta inyectada sea válida y visible.

## 11.3. Bases de datos por defecto vs datos de aplicación

- `information\_schema`, `mysql`, `performance\_schema` y `sys` suelen pertenecer al propio motor o a su administración interna.
- Las bases con nombres ligados a la aplicación (WordPress, “torrijas”, etc.) tienen mayor prioridad de análisis.

|  |
| --- |
| **Matiz del profesor —** “Por defecto” no significa “ignorar para siempre”. Se prioriza, pero no se asume que un desarrollador no haya guardado algo relevante en una ubicación poco habitual. |

## 11.4. Consultas de contexto del servidor

También se repasaron funciones/variables útiles para conocer el contexto de la sesión de base de datos:

|  |
| --- |
| SELECT CURRENT\_USER(); SELECT VERSION(); SELECT @@hostname; SELECT @@datadir; SELECT @@port; STATUS; |

- `CURRENT\_USER()` → usuario efectivo de MySQL/MariaDB.
- `VERSION()` → versión del motor.
- `@@hostname` → nombre del host.
- `@@datadir` → ruta del directorio de datos.
- `@@port` → puerto configurado, típicamente 3306 en esta práctica.
- `STATUS` → resumen de estado de la conexión/servidor.

# 12. Relación con UNION-based SQL Injection

Carlos aprovechó el acceso directo a MariaDB/MySQL para reforzar el razonamiento de UNION SELECT. El objetivo final es el mismo —llegar a los datos—, pero el recorrido cambia porque en SQLi hay que construir una consulta compatible con la consulta original.

|  |  |
| --- | --- |
| 1. Número de columnas | ORDER BY / pruebas equivalentes |
| 2. Columnas visibles y tipos | Identificar dónde se reflejan datos útiles |
| 3. Tablas | Enumerar estructura accesible |
| 4. Columnas | Conocer campos disponibles |
| 5. Datos | Extraer valores concretos y filtrar cuando sea necesario |

|  |
| --- |
| **Rendimiento —** Se recordó que `SELECT \*` sobre tablas enormes puede ser innecesario o costoso. Conviene filtrar con `WHERE`, por ejemplo por `id` o usuario, cuando ya se conoce la estructura. |

# 13. Escalada de privilegios

## 13.1. Primer paso: sudo -l

Tras cambiar al usuario usado en la parte final de la máquina, se ejecutó `sudo -l` para comprobar qué comandos podía ejecutar con privilegios. La salida permitió identificar `bpftrace` como binario relevante.

|  |
| --- |
| sudo -l |

## 13.2. Investigación del binario y GTFOBins

La metodología explicada fue: tratar el binario como una herramienta desconocida, investigar qué hace y comprobar si existe una técnica documentada de abuso cuando puede ejecutarse con sudo. GTFOBins se usó como referencia para `bpftrace`.

- Identificar el binario permitido por sudo.
- Entender mínimamente qué ejecuta o qué capacidad expone.
- Consultar GTFOBins si existe entrada para ese binario.
- Usar la variante más sencilla compatible con el permiso de sudo observado.
- Verificar el contexto resultante con comandos como `whoami`, `id` o `ls`.

|  |
| --- |
| **Pendiente de confirmar — comando exacto —** La transcripción no conserva de forma legible el one-liner exacto de GTFOBins usado con `bpftrace`. No se inventa. Sí queda confirmado el flujo: `sudo -l` → `bpftrace` → consulta de GTFOBins → ejecución con sudo → verificación de privilegios. |

# 14. Errores, riesgos y buenas prácticas observadas

- No confundir un servicio expuesto con acceso garantizado: MySQL estaba abierto, pero la conexión remota tuvo restricciones/problemas.
- No automatizar antes de comprobar manualmente que una función de la web realiza una acción real.
- No confiar ciegamente en un exploit de GitHub: leer su README, argumentos y, si hace falta, el propio código.
- Distinguir vulnerabilidad confirmada de hipótesis. La versión de un producto “podría” ser vulnerable; hay que validar que el componente y la configuración aplican.
- No asumir que un usuario de aplicación es administrador del sistema.
- En LFI, no somos “adivinos”: hay que apoyarse en rutas conocidas, diccionarios de archivos y errores que revelen paths.
- Tras acceso web/sistema, buscar configuraciones y secretos del framework antes de explorar sin rumbo.
- En escalada, `sudo -l` es un paso de entrada prioritario; después se investiga el binario concreto.

# 15. Comandos y usos vistos en la sesión

|  |  |  |  |  |
| --- | --- | --- | --- | --- |
| **Herramienta / comando** | **Objetivo** | **Fase de auditoría** | **Uso visto** | **Nivel** |
| nmap | Reconocimiento de puertos/servicios | Recogida de información | Escaneo de 192.168.0.204; se identificaron 22, 80 y 3306 | Practicada |
| dirsearch | Enumeración de directorios web | Recogida de información | Localización de rutas y WordPress | Practicada |
| nano /etc/hosts | Resolver nombre local del laboratorio | Recogida de información | Asociación de IP con torrija.thl | Introducida/repasada |
| wpscan | Enumerar WordPress | Análisis de vulnerabilidades | Plugins, versión, usuarios / detección agresiva | Practicada |
| python3 <exploit> --url --file | Explotar LFI del plugin | Pruebas de explotación controladas | Lectura de archivos locales como /etc/passwd | Introducida/repasada |
| curl -X POST ... -d ... | Recrear manualmente la petición del exploit | Pruebas de explotación controladas | Comprender el request y el parámetro vulnerable | Introducida/repasada |
| hydra -L -P ... ssh://... | Probar credenciales contra SSH | Pruebas de explotación controladas | Fuerza bruta con usuarios enumerados y rockyou | Introducida/repasada |
| cat wp-config.php | Extraer configuración de WordPress | Post-explotación | Credenciales y parámetros de base de datos | Introducida/repasada |
| mysql -h localhost -u admin -p | Acceder a MariaDB/MySQL | Post-explotación | Conexión local usando credenciales de la aplicación | Practicada |
| SHOW DATABASES / USE / SHOW TABLES / SELECT | Enumerar y consultar la base de datos | Post-explotación | Bases, tablas y datos | Introducida/repasada |
| sudo -l | Listar privilegios sudo | Pruebas de explotación controladas | Identificación de bpftrace | Practicada |
| GTFOBins | Buscar abuso documentado de binarios | Pruebas de explotación controladas | Técnica de escalada con bpftrace | Introducida/repasada |

# 16. Conexión con sesiones anteriores

- SQL Injection: se reutiliza la misma lógica de estructura → tablas → columnas → datos, pero comparando inyección con acceso directo al motor.
- LFI: se recupera la metodología de lectura de archivos conocidos y enumeración de rutas.
- Post-explotación Linux: revisión de `/var/www/html`, configuraciones web y `sudo -l`.
- Enumeración: la clase refuerza que Nmap es un punto de partida, no el objetivo final.

# 17. Checklist de estudio

- ☐ Puedo explicar por qué GoodGames no fue la práctica principal del día.
- ☐ Puedo distinguir Planificación, Recogida de información, Análisis de vulnerabilidades y Pruebas de explotación controladas.
- ☐ Entiendo la secuencia ORDER BY → columnas visibles → tablas → columnas → datos.
- ☐ Sé qué es un CMS y por qué WordPress aumenta la superficie de enumeración.
- ☐ Sé qué aporta WPScan y qué significan `ap`, `vp` y `u` en la enumeración comentada.
- ☐ Puedo explicar la relación entre traversal y LFI en la práctica.
- ☐ Sé qué buscar en `/etc/passwd` después de confirmar un LFI.
- ☐ Sé por qué `wp-config.php` es un objetivo prioritario tras acceder a un WordPress.
- ☐ Sé conectarme conceptualmente a MySQL/MariaDB y enumerar bases/tablas/datos.
- ☐ Sé qué información aportan `CURRENT\_USER()`, `VERSION()`, `@@hostname`, `@@datadir` y `@@port`.
- ☐ Recuerdo que `sudo -l` es un paso prioritario al buscar escalada de privilegios.
- ☐ Entiendo cómo usar GTFOBins como referencia sin asumir que todos los binarios aparecen allí.

# 18. Glosario

|  |  |
| --- | --- |
| **CMS** | Content Management System; sistema para gestionar contenidos web. |
| **WPScan** | Herramienta de enumeración y análisis específica para WordPress. |
| **LFI** | Local File Inclusion; inclusión/lectura de archivos locales a través de una aplicación vulnerable. |
| **Path Traversal** | Uso de rutas relativas como `../` para escapar del directorio previsto. |
| **wp-config.php** | Archivo de configuración de WordPress que suele incluir parámetros y credenciales de base de datos. |
| **MariaDB/MySQL** | Motores de bases de datos relacionales usados en la práctica. |
| **UNION SELECT** | Técnica de SQLi para combinar resultados de la consulta original con datos controlados por el atacante. |
| **GTFOBins** | Repositorio de técnicas para aprovechar binarios Unix legítimos en contextos de sudo/SUID/capabilities, entre otros. |
| **bpftrace** | Herramienta de tracing del sistema basada en eBPF; en esta máquina fue relevante por sus permisos sudo. |

# 19. Pendientes de confirmar

- Número exacto del CVE del plugin Web Directory Free 1.7.2: la transcripción alterna dos numeraciones.
- Ortografía exacta de los usuarios `premo` / `primo` y de la contraseña verbalizada como `Casandra`.
- Endpoint exacto del plugin usado por el exploit LFI.
- One-liner exacto de GTFOBins/bpftrace usado al final para elevar privilegios.
- Nombre exacto de alguna tabla de la base “torrijas”, ya que el reconocimiento de voz alterna `prime/primo` en ese fragmento.

# 20. Actualización de memoria del proyecto

|  |  |  |  |
| --- | --- | --- | --- |
| **Categoría** | **Información nueva** | **Nivel de certeza** | **Acción futura** |
| Sesión | 17/09/2026, profesor Carlos Castillo. | Alta | Mantener fecha y profesor en continuidad. |
| Laboratorio | GoodGames se intentó pero no se completó; práctica efectiva con máquina “Torrijas”. | Alta | No atribuir resultados de Torrijas a GoodGames. |
| Herramientas | dirsearch, WPScan, Hydra, MySQL/MariaDB, GTFOBins, bpftrace. | Alta | Actualizar niveles según futuras sesiones. |
| Técnicas | Enumeración WordPress, LFI, lectura de /etc/passwd, credenciales en wp-config.php, enumeración SQL y escalada vía sudo. | Alta | Conectar con futuras prácticas de CMS/post-explotación. |
| Pendiente | CVE exacto, usuarios/credenciales y one-liner final de bpftrace. | Media/Baja | Confirmar con captura, comando copiado o material del profesor. |
