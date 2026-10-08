---
tags:
- Auditoría web
---

# Auditoria Web LFI Escalada Linux

**EVOLVE ACADEMY · MÁSTER EN CIBERSEGURIDAD**

**Auditoría web y escalada de privilegios en Linux**

Path Traversal · LFI/RFI · IDOR · SUID vs Sudoers · chattr/lsattr · Cron

Instructor: Carlos Gómez Pintado · 08/07/2026

Sesión de repaso práctico dentro del módulo de auditoría web. Se combinan dos bloques: por un lado, vulnerabilidades web basadas en rutas y parámetros (**Path Traversal**, **LFI**, **RFI**, **IDOR**); por otro, un adelanto de **escalada de privilegios en Linux** (permisos, **SUID** frente a **sudoers**, bit inmutable con chattr/lsattr, y tareas programadas **cron**). El vehículo práctico es la máquina **“Banco” de TheHackerLabs**, resuelta en directo de principio a fin.

| **ℹ Contexto del módulo**  El instructor recalca varias veces que la escalada de privilegios se ve aquí "por encima", como cimientos. El módulo completo y dedicado de escalada llega a la vuelta de verano. El objetivo hoy es que los conceptos suenen, no dominarlos. |
| --- |

# **Objetivos de la sesión**

- Entender qué es un **path** (ruta) y en qué consiste una vulnerabilidad de **Path Traversal** (salto de directorio con ../).
- Diferenciar **Path Traversal**, **LFI** (Local File Inclusion), **RFI** (Remote File Inclusion) e **IDOR**.
- Repasar el modelo de **permisos de Linux**: las 10 posiciones, owner/group/others y el cálculo binario (4-2-1).
- Distinguir un bit **SUID** de un permiso **sudoers** (sudo -l).
- Comprender el atributo **inmutable** y el uso de chattr/lsattr como técnica de escalada.
- Resolver la máquina **Banco** (TheHackerLabs) end-to-end: enumeración, acceso vía LFI y escalada a root.

# **Conceptos clave**

## **Permisos de Linux**

Al listar un fichero (ls -l), la primera columna tiene **10 posiciones**. La primera indica el **tipo** (- archivo, d directorio, l enlace de log/registro). Las **9 restantes** se dividen en tres grupos de tres: **owner** (propietario, un usuario), **group** (grupo de usuarios; si no hay grupo definido, por defecto es el propio owner) y **others** (el resto de usuarios).

Cada grupo tiene tres permisos en orden fijo: **lectura (r)**, **escritura (w)** y **ejecución (x)**.

El valor binario de cada permiso es una potencia de 2: **r = 4**, **w = 2**, **x = 1**. La suma máxima por grupo es **7** (rwx). Así, 755 significa owner con todo (7 = rwx), y grupo y others con lectura y ejecución (5 = r-x).

| **Octal** | **Binario** | **Permisos** | **Significado** |
| --- | --- | --- | --- |
| 7 | 111 | rwx | Lectura + escritura + ejecución |
| 6 | 110 | rw- | Lectura + escritura |
| 5 | 101 | r-x | Lectura + ejecución |
| 4 | 100 | r-- | Solo lectura |
| 1 | 001 | --x | Solo ejecución |
| 0 | 000 | --- | Sin permisos |

chmod (change mode) cambia permisos. Con letras se puede sumar (+) o quitar (-) un permiso a la vez sobre las tres posiciones: chmod -x fichero quita ejecución a owner, group y others simultáneamente. Con números octales se especifican los tres grupos de golpe, que es lo más cómodo y exacto.

## **Path — la ruta**

Un **path** es la ruta a un archivo concreto, p. ej. /etc/hosts. El punto (.) representa el directorio actual, y .. representa el directorio superior (padre). Por eso cd ../../../ retrocede tres niveles.

| **⚠ Matiz importante**  Poner cd .. para retroceder NO es Path Traversal: ahí estás ejecutando un comando. El Path Traversal aparece cuando un **parámetro** que apunta a un fichero (una variable que la aplicación usa para abrir/leer un archivo) está mal controlado y permite inyectar ../ para escapar del directorio previsto. |
| --- |

## **Path Traversal, LFI y RFI**

**Path Traversal (Directory Traversal)**: se da cuando una variable/parámetro que la app usa para localizar un fichero no está validada, y se puede inyectar ../../../ para salir del directorio base y acceder a otros ficheros del sistema.

**LFI (Local File Inclusion)**: es la **consecuencia** del Path Traversal. Permite acceder a (o incluir) un fichero **local** del sistema a través de esa variable mal controlada. Ejemplo clásico de lectura: /etc/passwd.

**RFI (Remote File Inclusion)**: en lugar de leer un fichero local, la aplicación hace una **llamada remota** (a un servidor externo) e incluye/ejecuta un fichero que nosotros alojamos. Se explota levantando un servidor propio (p. ej. python3 -m http.server) y forzando a la máquina objetivo a solicitarlo.

| **⚠ Patrón vulnerable (LFI)**  Ejemplo de código PHP vulnerable descrito en clase: se toma el nombre del fichero de un parámetro ($\_GET['nombre'] o similar), se concatena directamente a un directorio base y se hace readfile() / file\_open() sin validación. Si el nombre es ../../../etc/passwd, se escapa del directorio base y se lee el fichero del sistema. |
| --- |

## **IDOR (Insecure Direct Object Reference)**

Distinto del Path Traversal. Se da cuando un recurso se referencia por un identificador directo (p. ej. ?id=3) sin control de acceso. Cambiando ese identificador (?id=4, ?id=5...) se accede a ficheros o registros que no deberían corresponder al usuario. En la sesión se mostró sobre una URL con un id numérico que, al modificarse, devolvía documentos distintos.

## **Enumeración: código fuente y ficheros PHP comunes**

Revisar el **código fuente** de una web es un paso fundamental: es frecuente encontrar credenciales *hardcodeadas* o comentarios de desarrolladores. En la máquina Banco, el usuario y contraseña del panel de login estaban en el código fuente.

Ficheros PHP habituales que conviene mirar en cualquier servidor PHP/Apache/Linux, especialmente si hay Path Traversal/LFI: **config.php** (suele contener credenciales o rutas de base de datos), **phpinfo.php**, **php.ini** y **phpMyAdmin**. Además del clásico /etc/passwd.

| **ℹ NOTA**  /etc/passwd solo habilita saber qué usuarios existen y hacer fuerza bruta; no contiene contraseñas. El verdadero premio en un LFI suele ser config.php u otros ficheros de configuración con credenciales reales. |
| --- |

## **SUID frente a sudoers**

Son dos mecanismos distintos y es clave no confundirlos:

- **sudoers / `sudo -l`**: afecta al **usuario**. Lista los ficheros/comandos que **mi usuario concreto** puede ejecutar como otro usuario (no necesariamente root). Es específico de quién lo ejecuta: www-data, root y otro usuario obtendrían resultados distintos.
- **SUID (Set User ID)**: es un **bit de permiso especial** del fichero. Donde está ese bit, **cualquier usuario** del sistema ejecuta ese binario **con los privilegios del propietario** (típicamente root). Afecta al fichero, es común a todos.

| **ℹ Cómo se ve el SUID**  En ls -l, el bit SUID aparece como una **s** en la posición de ejecución del owner (-rws...) en lugar de la x. Ejemplo visto en clase: chsh aparecía como -rwsr-xr-x. |
| --- |

## **Atributo inmutable — chattr / lsattr**

Más allá de los permisos rwx existen **atributos extendidos**. El atributo **i (inmutable)** hace que un fichero **no se pueda modificar, borrar, renombrar ni enlazar, ni siquiera por root**. Está por encima del modelo de permisos normal.

- lsattr (**l**i**s**t **attr**ibutes): lista los atributos extendidos de ficheros/directorios.
- chattr (**ch**ange **attr**ibutes): cambia atributos. chattr +i pone inmutable; chattr -i lo quita.

| **ℹ ¿Para qué sirve la inmutabilidad?**  Utilidad legítima: proteger ficheros. Un backup que solo debe ejecutarse en momentos concretos se deja preparado y se marca inmutable para que una tarea programada no lo dispare hasta que se le retire el atributo. |
| --- |

# **Desarrollo técnico — Máquina Banco (TheHackerLabs)**

Escenario planteado en clase: hemos conseguido acceso a la red interna de un banco (vía WiFi / phishing) y atacamos desde dentro. Resolución completa paso a paso.

## **1. Descubrimiento de red y escaneo**

Primero identificamos nuestra IP y descubrimos máquinas activas en la red con **Netdiscover**. Aparece el objetivo 10.0.2.15. A continuación escaneamos con **Nmap**.

| netdiscover  nmap -sCV -Pn --min-rate 5000 10.0.2.15 |
| --- |

Parámetros vistos: -sCV (detección de versión de servicios + scripts por defecto), -Pn (no hacer ping/host discovery previo) y --min-rate para acelerar el escaneo. Resultado: puerto **22 (SSH)** y puerto **80 (HTTP)** abiertos. El 22 no interesa de momento (requiere usuario/contraseña); nos centramos en el 80.

| **⚠ AVISO**  El instructor usa la forma abreviada -sCV. En la propia clase se comenta que --min-rate es la forma correcta con doble guion. Verifica siempre los parámetros con nmap --help o man nmap. |
| --- |

## **2. Enumeración web**

Abrimos el puerto 80 en el navegador: aparece un **panel de login**. Buenas prácticas antes de nada: probar credenciales triviales (**admin/admin**) y detectar tecnología con **Wappalyzer** (revela Debian + **Apache 2.4.66**). Se muestra cómo buscar CVEs/vulnerabilidades de esa versión de Apache, aunque en este caso no aportan vector útil.

El paso decisivo es **revisar el código fuente** de la página: al final del HTML hay un script y, en las primeras líneas, un **usuario y una contraseña hardcodeados** que permiten autenticarse. También se identifica un botón de descarga que apunta a descargar.php mediante un campo oculto (hidden).

| **ℹ NOTA**  Al autenticarse, el escenario cambia por completo: código fuente nuevo, directorios enumerable nuevos, etc. Conviene re-enumerar como usuario autenticado. |
| --- |

En paralelo se lanza fuzzing de directorios con **Dirsearch** (\_Dirsearch\_ con wordlist media) para descubrir rutas ocultas, dejándolo trabajar en segundo plano mientras se explora la web.

| dirsearch -u http://10.0.2.15/ |
| --- |

## **3. Análisis de descargar.php e identificación del LFI**

El botón “descargar” envía una petición **POST** a descargar.php con un parámetro archivo (formato application/x-www-form-urlencoded). Ese parámetro es la variable que la app usa para localizar el fichero: candidato perfecto a **Path Traversal → LFI**.

Se intercepta la petición con **Burp Suite** (Proxy → interceptar) y se envía al **Repeater** (clic derecho → *Send to Repeater*, o Ctrl+R). Desde Repeater se manipula el parámetro archivo.

| **⚠ Errores comunes en Burp**  En Repeater hay que pulsar **Send** para ver la respuesta (pestaña Response). Si aparece vacía es porque no se ha enviado la petición. Ojo también con el salto de línea: pegar un valor con un \n accidental (pulsar Enter al escribir) rompe la petición. |
| --- |

## **4. Explotación del LFI**

Inyectando ../ repetidamente en el parámetro archivo se escapa del directorio base hasta la raíz y se leen ficheros del sistema. El instructor usa **9 niveles** de ../ ("la ruta más larga que me encontré"): con pasarse de niveles no ocurre nada, hay un límite natural (no se puede subir más allá de /).

| archivo=../../../../../../../../../etc/passwd |
| --- |

Del /etc/passwd se extraen los usuarios con shell válida (los que interesan para loguear). Aparecen entre otros **www-data (wwwveretz/similar)** y **root**. Pero el paso realmente productivo es leer el fichero de configuración.

| archivo=../../../../../../../../../var/www/html/config.php |
| --- |

config.php define en sus primeras líneas la ruta del fichero de base de datos (algo tipo db\_supersecret...json). Leyendo ese JSON aparecen credenciales de varios usuarios (admin, root de base de datos, www-data, debian...). Hay que distinguir usuarios de **servicio/base de datos** de usuarios de **sistema**.

| **ℹ Distinguir usuario de servicio vs. sistema**  La credencial de “root” del JSON era del usuario root de la base de datos (MySQL), no del sistema — por eso SSH con root falló. La que funcionó por SSH fue la del usuario **www-data**, que casualmente compartía nombre y contraseña entre servicio y sistema. |
| --- |

## **5. Acceso inicial por SSH**

Con las credenciales válidas del usuario de sistema, entramos por SSH y obtenemos la primera flag (user).

| ssh www-data@10.0.2.15 |
| --- |

## **6. Enumeración para escalada de privilegios**

Orden de comprobaciones que el instructor fija como rutina al entrar en cualquier máquina Linux:

1. whoami — quién soy.
2. pwd — en qué ruta estoy (al entrar por SSH, típicamente /home/usuario).
3. uname -a — versión del kernel (por si hay exploit de kernel, p. ej. Dirty Cow).
4. sudo -l — qué puedo ejecutar como otro usuario/root.
5. find / -perm -4000 -type f 2>/dev/null — binarios con bit SUID.

En Banco, sudo -l **no da resultados útiles** (incluso da error de resolución de host y no permite listar). Por tanto se pasa a la segunda vía: **buscar binarios SUID**.

| whoami  pwd  uname -a  sudo -l  find / -perm -4000 -type f 2>/dev/null |
| --- |
| **ℹ NOTA**  -perm -4000 busca SUID; -perm -2000 buscaría SGID. En clase se recuerda que el valor 4000 es el peso binario del bit SUID (equivalente en la familia de los especiales a lo que 7 es para rwx). |

## **7. Identificación del binario vulnerable (chattr) con GTFOBins**

El find de SUID devuelve una lista. La mayoría son binarios normales y esperables (sudo, su, mount, umount, passwd, chsh, chfn, newgrp, gpasswd...): buscarlos en **GTFOBins** no aporta nada. Lo que **chirría** es encontrar chattr (y justo encima lsattr), comandos que no son habituales en esa lista.

En **GTFOBins** (Get The F\* **Out Bins) se busca `chattr`: aparece con sección** SUID **(la técnica que hemos usado para encontrarlo) y** Privilege Escalation\*\*. GTFOBins indica cómo abusar del binario.

| **ℹ NOTA**  Regla de oro de GTFOBins: si encuentras el binario por la vía SUID (find -perm -4000), en GTFOBins consultas la sección **SUID**. Si lo hubieras encontrado por sudo -l, consultarías la sección **Sudo**. La técnica de consulta debe coincidir con cómo lo encontraste. |
| --- |

La presencia de chattr **con SUID** más lsattr justo al lado es una pista deliberada de la máquina: chattr permite quitar la inmutabilidad de cualquier fichero (aun de root) porque se ejecuta con privilegios del propietario, y lsattr sirve para **localizar** qué fichero es inmutable.

## **8. Localización del fichero inmutable**

Se listan los ficheros con atributo inmutable. Puede hacerse con find recursivo o, como sugiere la propia máquina al dejar lsattr con SUID, listando atributos. Aparece **un único** fichero inmutable:

| find / -type f -exec lsattr {} \; 2>/dev/null | grep -i '\----i' |
| --- |

Fichero encontrado: **/usr/local/bin/backup.sh** (referido en clase como backup.sh/backup.bill.sh), propiedad de **root:root**, con atributo inmutable.

| **ℹ Ampliación**  Este comando find ... -exec lsattr es una ampliación para automatizar la búsqueda; en clase el comando exacto se obtuvo pidiéndoselo a la IA. Verifica su comportamiento antes de usarlo y ajústalo a tu entorno. |
| --- |

## **9. Explotación: quitar inmutabilidad, modificar y esperar al cron**

Con el SUID de chattr retiramos la inmutabilidad del backup y comprobamos que ya no aparece como inmutable:

| chattr -i /usr/local/bin/backup.sh  lsattr /usr/local/bin/backup.sh |
| --- |

Ahora tenemos permiso de escritura sobre el script (others con rwx). El razonamiento crítico de la clase: **no** basta con meter /bin/bash y ejecutarlo, porque lo ejecutaríamos como www-data, no como root. La escalada funciona porque **una tarea programada (cron) ejecuta ese backup como root** periódicamente. Por tanto, dejamos el script preparado para que, al ejecutarse como root, otorgue SUID a una shell.

| echo 'chmod +s /bin/bash' > /usr/local/bin/backup.sh |
| --- |

Se espera a que el cron ejecute el script como root (se puede confirmar viendo cambiar el *timestamp* del fichero con ls -l repetido). Tras la ejecución, /bin/bash queda con bit SUID y podemos lanzar una shell con privilegios de root:

| ls -la /bin/bash  /bin/bash -p |
| --- |
| **✓ Root conseguido**  La -p es clave: mantiene los privilegios del SUID al lanzar bash. Sin ella, bash suele descartar los privilegios efectivos. Al ejecutarla obtenemos shell de root y la flag final. |

## **Analogía de la clase (SUID + cron)**

El instructor lo explicó con una analogía: tener SUID escribible sin poder ejecutarlo como root es como dejar en el felpudo de una casa un bote de pintura rosa, un rodillo y una brocha. Tú no puedes entrar, pero sabes que **cada día a una hora fija** alguien (la tarea cron, “la madre”) le dirá al dueño que pinte. El dueño (root) ejecuta sin pensar con lo que le has dejado preparado, y la casa acaba pintada de rosa. Has aprovechado una causística que se repite (el cron) para que **otro con más privilegios** ejecute tu preparación.

# **Regla mental de escalada en CTF (resumen del instructor)**

Esquema condicional que sintetiza las vías vistas:

- **Si** hay un fichero en sudo -l que puedo ejecutar como otro usuario **y** tengo permiso de escritura sobre él → escalada directa (lo modifico y lo ejecuto con sudo).
- **Si** hay un fichero **SUID** ejecutable **y** puedo escribirlo pero **no** ejecutarlo como root → hay (casi seguro en CTF) una **tarea cron** que lo ejecuta como root: lo preparo y espero.
- **Si** no se da ninguna de las dos → buscar un script que al ejecutarse revele una contraseña, o tirar de **exploit de kernel**.

# **Comandos importantes**

| netdiscover  nmap -sCV -Pn --min-rate 5000 10.0.2.15  dirsearch -u http://10.0.2.15/  archivo=../../../../../../../../../etc/passwd  archivo=../../../../../../../../../var/www/html/config.php  ssh www-data@10.0.2.15  whoami  pwd  uname -a  sudo -l  find / -perm -4000 -type f 2>/dev/null  lsattr /usr/local/bin/backup.sh  chattr -i /usr/local/bin/backup.sh  echo 'chmod +s /bin/bash' > /usr/local/bin/backup.sh  ls -la /bin/bash  /bin/bash -p |
| --- |
| **⚠ AVISO**  Rutas, nombres de fichero y credenciales concretos (config.php, backup.sh, usuario www-data) proceden de la resolución en directo y pueden variar en tu instancia. Trátalos como referencia, no como valores fijos: enumera y confirma en tu máquina. |

# **Herramientas utilizadas en la sesión**

| **Herramienta** | **Objetivo** | **Fase de auditoría** | **Comando o uso visto** | **Nivel** | **Notas** |
| --- | --- | --- | --- | --- | --- |
| Netdiscover | Descubrir hosts en la red | Reconocimiento | netdiscover | Practicada | Localiza el objetivo 10.0.2.15 |
| Nmap | Puertos, servicios y versiones | Enumeración | nmap -sCV -Pn --min-rate 5000 IP | Recurrente | Banner grabbing revela versiones |
| Wappalyzer | Detectar tecnología web | Enumeración web | Extensión de navegador | Practicada | Detecta Apache 2.4.66 / Debian |
| Dirsearch | Fuzzing de directorios | Enumeración web | dirsearch -u URL | Practicada | En 2.º plano mientras se explora |
| Burp Suite (Proxy/Repeater) | Interceptar y manipular peticiones | Explotación web | Ctrl+R → Send | Practicada | Manipula el parámetro archivo |
| FoxyProxy | Gestionar proxy del navegador | Explotación web | Activar/desactivar proxy | Practicada | Recordar desactivarlo tras Burp |
| GTFOBins | Vías de abuso de binarios | Escalada de privilegios | Buscar chattr → SUID | Practicada | Coincidir técnica (SUID/Sudo) |
| chattr / lsattr | Gestionar atributo inmutable | Escalada de privilegios | chattr -i fichero | Introducida | Vector SUID de la máquina |
| SSH | Acceso remoto autenticado | Acceso inicial | ssh usuario@IP | Recurrente | Login con credenciales del JSON |
| **ℹ NOTA**  Se mencionan pero no se desarrollan en profundidad: la máquina Responder (HTB Tier 1) como ejemplo de RFI con python3 -m http.server, y las alternativas de fuzzing Feroxbuster/ffuf/Gobuster ("dirbuster recursiva"). |

# **Riesgos, errores comunes y buenas prácticas**

| **⚠ No uses 777**  Nunca poner 777 a un fichero "por si acaso": es una mala práctica de seguridad grave que se comentó explícitamente en clase. Da permisos totales a cualquiera. |
| --- |
| **⚠ AVISO**  En Burp Repeater, si la Response sale vacía es que falta pulsar Send. Y cuidado con pegar valores con saltos de línea accidentales: un \n rompe la petición. |
| **⚠ AVISO**  Recordar desactivar FoxyProxy/el proxy de Burp al terminar, o el navegador dejará de cargar páginas normalmente. |
| **✓ Buena práctica**  Revisar SIEMPRE el código fuente y ficheros de configuración (config.php). Es donde con más frecuencia aparecen credenciales hardcodeadas. |
| **✓ Buena práctica**  Al leer /etc/passwd, distinguir usuarios de sistema (con shell) de usuarios de servicio/base de datos. No toda credencial encontrada sirve para SSH. |

# **Conexión con sesiones anteriores**

**Escalada Linux y `sudo -l`**: enlaza directamente con la sesión de la máquina **Rockstar**, donde ya se trabajó el chain de movimiento lateral, sudo -l y el modelo de permisos de Linux. Aquí se añade la vía **SUID + cron** y el atributo inmutable, que amplían el repertorio de escalada.

**Enumeración web**: nmap (puertos/servicios) sigue siendo el primer paso, y el fuzzing con **Dirsearch** cumple el mismo rol que Feroxbuster/ffuf en sesiones previas: descubrir rutas ocultas mientras se inspecciona la web.

**RFI y Responder**: se retoma la máquina **Responder** (HTB Tier 1) ya conocida, ahora como ejemplo conceptual de **RFI** (hostear un fichero propio con python3 -m http.server y forzar su inclusión remota).

**Burp Suite**: se reutiliza el flujo Proxy → Repeater visto en sesiones anteriores, ahora aplicado a manipular un parámetro POST para LFI.

# **Resumen final**

La sesión encadena una auditoría web completa sobre la máquina Banco (TheHackerLabs) con un adelanto de escalada de privilegios en Linux. El acceso inicial se logra explotando un **LFI** en descargar.php (parámetro archivo sin validar), leyendo config.php y de ahí las credenciales de base de datos; un usuario de servicio compartía credencial con uno de sistema, habilitando SSH. La escalada a root se apoya en un binario **SUID inesperado (`chattr`)** identificado vía find -perm -4000 y **GTFOBins**: se retira la inmutabilidad de un script de backup, se modifica para dar SUID a /bin/bash, y una **tarea cron** que corre como root lo ejecuta, permitiendo /bin/bash -p. Conceptos transversales: permisos de Linux (4-2-1), diferencia SUID vs sudoers, y atributo inmutable con chattr/lsattr.

# **Checklist de repaso**

1. ¿Sé calcular permisos octales (r=4, w=2, x=1) y explicar las 10 posiciones de ls -l?
2. ¿Distingo Path Traversal, LFI, RFI e IDOR con un ejemplo de cada uno?
3. ¿Sé por qué ../ en un parámetro es peligroso pero cd .. en shell no es Path Traversal?
4. ¿Reviso el código fuente y los ficheros PHP comunes (config.php, phpinfo.php, php.ini, phpMyAdmin)?
5. ¿Manejo el flujo Burp Proxy → Repeater y recuerdo pulsar Send?
6. ¿Explico la diferencia entre SUID y sudoers sin dudar?
7. ¿Ejecuto la rutina de escalada: whoami → pwd → uname -a → sudo -l → find -perm -4000?
8. ¿Sé consultar GTFOBins coincidiendo la técnica (SUID vs Sudo) con cómo encontré el binario?
9. ¿Entiendo el rol del cron en la escalada SUID+escritura y la analogía del bote de pintura?
10. ¿Recuerdo lanzar /bin/bash -p (con -p) para conservar el SUID?

# **Actualización del registro de herramientas**

Herramientas nuevas y cambios de nivel respecto al registro acumulado, listos para copiar a la base de conocimiento del proyecto:

| **Herramienta** | **Nivel** |
| --- | --- |
| GTFOBins | Practicada (nueva) |
| chattr / lsattr | Introducida (nueva) |
| FoxyProxy | Practicada (nueva) |
| Dirsearch | Practicada (confirmada) |
| Wappalyzer | Practicada (sube de Introducida) |
| Netdiscover | Practicada (sube de Introducida) |
| Burp Suite (Proxy/Repeater) | Practicada (confirmada) |
| SSH | Recurrente |

**Bloque para memoria acumulativa** (texto plano): En la sesión de auditoría web + escalada Linux (Carlos Gómez Pintado, 08/07/2026) se resolvió la máquina Banco de TheHackerLabs. Vector web: LFI en descargar.php (parámetro archivo) → lectura de config.php → credenciales de BBDD → SSH con usuario de sistema. Escalada: binario SUID inesperado chattr hallado con find -perm -4000 y confirmado en GTFOBins; se quita inmutabilidad de backup.sh con chattr -i, se inyecta chmod +s /bin/bash y un cron que corre como root lo ejecuta; root con /bin/bash -p. Conceptos: permisos 4-2-1, SUID vs sudoers, atributo inmutable (chattr/lsattr), IDOR, Path Traversal/LFI/RFI. Nuevas: GTFOBins, chattr/lsattr, FoxyProxy.
