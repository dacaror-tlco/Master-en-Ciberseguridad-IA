---
tags:
- Máquinas y prácticas
---

# Auditoria WordPress Academy

**EVOLVE ACADEMY · MÁSTER EN CIBERSEGURIDAD OFENSIVA**

**Auditoría de CMS — WordPress (máquina Academy)**

*Auditoría web de un gestor de contenidos (CMS) WordPress*

Instructor: Carlos Castillo (apoyo: Yuba González)

Fecha: 1 de julio de 2026

Plataforma: TheHackerLabs · Máquina: Academy

Entorno: Kali Linux (VMware)

| **ℹ INFORMACIÓN**  Estos apuntes reconstruyen la clase para poder estudiarla sin volver a ver la grabación. Se distingue entre **contenido visto en clase**, **explicación complementaria** y **buena práctica añadida para estudio**.  La máquina se audita hasta el **acceso inicial** (usuario www-data). La fase de **escalada de privilegios queda pendiente** y se verá en el módulo correspondiente, tal como indicó el instructor. |
| --- |

# **Contexto de la sesión**

La sesión continúa el bloque de **auditoría web**. Tras haber visto en clases anteriores el **OWASP Top 10** y **Burp Suite**, se aplica ahora la metodología a un tipo concreto de aplicación: los **CMS** (gestores de contenidos), usando **WordPress** como caso práctico sobre la máquina **Academy** de TheHackerLabs.

Se decidió realizar toda la práctica desde **Kali Linux**, ya que Kali trae por defecto las dependencias necesarias (WPScan, diccionarios, etc.) y hacerlo desde Windows complicaba la instalación de dependencias.

| **ℹ INFORMACIÓN**  **Contenido visto en clase.** El instructor recorre la \*kill chain\* completa hasta el acceso inicial: reconocimiento → enumeración web → detección del CMS → WPScan → obtención de credenciales → RCE mediante el editor de temas → reverse shell → usuario www-data. |
| --- |

# **Objetivos de aprendizaje**

1. Diferenciar una **web nativa** (PHP, .NET, Java…) de una web basada en **CMS** (WordPress, Joomla, Drupal…) y entender por qué se auditan de forma distinta.
2. Comprender que en WordPress **la mayor superficie de ataque está en los plugins**, no en el núcleo.
3. Enumerar un WordPress con **WPScan**: versión, usuarios, plugins y sus vulnerabilidades.
4. Entender la diferencia entre lanzar WPScan **con y sin API token**.
5. Reconocer la **enumeración de usuarios por mensajes de error** en el login.
6. Situar la **fuerza bruta como último recurso** y saber por qué en WordPress se prefiere WPScan frente a Hydra o Burp Intruder.
7. Conseguir **RCE** subiendo una \*reverse shell\* PHP a través del **editor de temas** (plantilla 404.php).
8. Entender la transición de tráfico **HTTP → TCP** al obtener la shell y estabilizarla.

# **Conceptos clave**

| **Concepto** | **Explicación sencilla** | **Uso en auditoría** | **Visto en la clase** |
| --- | --- | --- | --- |
| CMS | Gestor de contenidos: un núcleo desarrollado por una empresa (WordPress) al que se añaden extensiones. | Cambia la forma de auditar respecto a una web nativa. | Sí |
| Plugin | Conector/extensión que añade funciones al CMS. Muchos son de terceros y nadie revisa su seguridad. | Principal vector de entrada en WordPress. | Sí |
| Web nativa | Web programada directamente (PHP, .NET, Java). | Más habitual encontrar SQLi, XSS, etc. de forma directa. | Sí |
| Enumeración recursiva | Al hallar un directorio, el fuzzer repite el escaneo dentro de él automáticamente. | Descubre rutas ocultas dentro de /wordpress. | Sí (flag -r) |
| User enumeration | El login revela si un usuario existe según el mensaje de error. | Reduce la fuerza bruta de exponencial a lineal. | Sí |
| API token (WPScan) | Clave que conecta WPScan con su base de datos de vulnerabilidades. | Sin token solo lista; con token añade CVEs. | Sí |
| Binomio uploader/upload | Poder subir un fichero + poder ejecutarlo = RCE. | Vía típica de acceso inicial en web. | Sí |
| Reverse shell | La máquina víctima se conecta de vuelta al atacante. | Acceso inicial al sistema operativo. | Sí |

# **Desarrollo técnico**

## **1. CMS frente a web nativa**

El instructor distingue dos tipos de páginas web:

- **Nativas**: programadas directamente en PHP, .NET, Java, etc. Es más sencillo encontrar directamente inyecciones SQL, XSS y similares.
- **CMS**: WordPress, Joomla, Drupal, plataformas de e-commerce, etc. Tienen un **núcleo** (la "troncal") mantenido por la empresa y se les añaden **plugins**.

| **ℹ INFORMACIÓN**  **Idea central de la clase.** El núcleo de WordPress rara vez es vulnerable: está muy revisado. Las grandes vulnerabilidades aparecen en los **plugins**, porque hay miles, cualquiera los publica y **nadie audita su seguridad**.  Por muy fortificado que esté el WordPress, si instalas un plugin vulnerable estás abriendo una puerta de entrada. |
| --- |

## **2. Reconocimiento y enumeración de puertos**

Primer paso habitual en el laboratorio: localizar el host en la red con **netdiscover**, y luego escanear puertos con **nmap**.

| sudo netdiscover -r 10.0.2.0/24  sudo nmap -sV -p- {IP\_OBJETIVO} |
| --- |

**Resultado observado en clase:** la máquina expone el puerto **22 (SSH)** y el **80 (HTTP)**. El interés se centra en el 80.

| **⚠ AVISO / ERROR COMÚN**  **Nota (fidelidad).** netdiscover se usó de forma explícita en clase sobre el rango 10.0.2.0/24. El comando exacto de nmap no se detalló literalmente en la grabación; se incluye el comando de enumeración de puertos habitual del máster con un placeholder {IP\_OBJETIVO}. Solo se confirmó el resultado: puertos 22 y 80 abiertos. |
| --- |
| **ℹ INFORMACIÓN**  **Explicación complementaria.** netdiscover funciona con el protocolo **ARP**, que **no** está permitido en la infraestructura de red de AWS. Por eso no sirve para descubrir hosts en entornos cloud de Amazon. |

## **3. Enumeración web y descubrimiento del CMS**

Al abrir http://{IP\_OBJETIVO} en el navegador se identifica un servidor **Apache**. Sobre cualquier web, el paso siguiente es el \*fuzzing\* de directorios. En clase se usó **Dirsearch** (el instructor lo prefiere por su interfaz), pero es equivalente a Gobuster, Feroxbuster o ffuf: lo importante es el **diccionario** que se use.

| dirsearch -u http://{IP\_OBJETIVO}/ -r -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt |
| --- |

El flag **`-r`** activa la **enumeración recursiva**: cuando encuentra /wordpress, relanza el escaneo dentro de esa ruta, y así sucesivamente. Sin recursividad no se habrían descubierto las rutas internas.

**Rutas descubiertas en clase:** /wordpress (código 301, redirección), wp-login.php y wp-content/uploads.

| **ℹ INFORMACIÓN**  **Explicación complementaria: por qué un 301.** Al acceder a /wordpress la web responde con **301 Moved Permanently** porque redirige al dominio real. La máquina usa el dominio academy.thehackerlabs, así que hay que añadirlo al fichero /etc/hosts para que resuelva: |
| --- |
| sudo nano /etc/hosts  # añadir la línea: {IP\_OBJETIVO} academy.thehackerlabs |
| **⚠ AVISO / ERROR COMÚN**  **Error común.** Un mismo diccionario lanzado solo sobre la raíz **no** encuentra rutas que sí están bajo /wordpress (p. ej. wp-content/uploads). La palabra puede estar en el diccionario, pero si no se enumera recursivamente sobre la subruta correcta, no aparece. Distintas herramientas traen distintos diccionarios por defecto → distintas salidas. |

## **4. WPScan: enumeración de la tecnología**

**WPScan** es la herramienta de referencia para auditar WordPress. Se lanza siempre **apuntando al directorio que contiene el WordPress** (/wordpress), no a la raíz del dominio: un exploit o escaneo lanzado contra una tecnología que no está ahí no sirve de nada.

| wpscan --url http://academy.thehackerlabs/wordpress |
| --- |

**Resultado observado:** WordPress **versión 6.5.3**, presencia de xmlrpc.php, readme.html y wp-content/uploads. A partir de la versión ya se puede buscar (wordpress 6.5.3 vulnerabilities) una primera idea de ataque.

| **ℹ INFORMACIÓN**  **Explicación complementaria: XML-RPC.** xmlrpc.php es una API antigua de WordPress. En el contexto de esta auditoría el instructor la descarta como vía útil de entrada. También se aprecia en las cabeceras (vistas con Burp) que el servidor es **Apache** sobre **Linux**. |
| --- |

## **5. WPScan: enumeración de usuarios**

El objetivo intermedio es conseguir un **usuario** válido. WPScan tiene una función propia de enumeración de usuarios (-e u, con **U mayúscula** para pasarle un diccionario de nombres):

| wpscan --url http://academy.thehackerlabs/wordpress -e u  wpscan --url http://academy.thehackerlabs/wordpress --enumerate u -U /usr/share/seclists/Usernames/top-usernames-shortlist.txt |
| --- |
| **ℹ INFORMACIÓN**  **Nota (fidelidad).** En clase se usó un diccionario de **usernames de SecLists** (se eligió una lista de "top usernames"). El nombre exacto del fichero no se dictó con precisión en la grabación; se indica una ruta representativa de SecLists como placeholder editable. |

## **6. WPScan: enumeración de plugins y API token**

Para enumerar los plugins se usa --enumerate ap (\*all plugins\*). Aquí aparece la diferencia clave con el **API token**:

- **Sin** API token → WPScan **lista** los plugins y sus versiones (p. ej. se detectó **Elementor**), pero **no** dice qué vulnerabilidades tienen.
- **Con** API token → WPScan consulta su **base de datos de vulnerabilidades** y añade los **CVE** asociados a cada plugin y a la versión de WordPress.

| wpscan --url http://academy.thehackerlabs/wordpress --enumerate ap  wpscan --url http://academy.thehackerlabs/wordpress --enumerate vp --api-token {API\_TOKEN} |
| --- |
| **ℹ INFORMACIÓN**  **Explicación complementaria.** El API token **no** aporta capacidades ofensivas extra; solo es la conexión a la base de datos de vulnerabilidades de WPScan. Se obtiene gratis registrándose en el portal de WPScan (wpscan.com). |
| **⚠ AVISO / ERROR COMÚN**  **Matiz importante de la clase: no toda vulnerabilidad listada es explotable.**  Muchas vulnerabilidades de plugins requieren estar **autenticado** o un **rol** concreto (p. ej. distribuidor), o afectan a una funcionalidad que **no está accesible/activa** en la web. Como todavía se busca el **acceso inicial**, se **descartan** temporalmente y no se pierde tiempo con ellas.  El trabajo del auditor es entender **en qué función y en qué endpoint** aplica cada CVE y si es realmente accesible. Ahí está la auditoría web de verdad. |

## **7. Enumeración de usuarios por mensajes de error (login)**

El login de WordPress puede **filtrar** si un usuario existe: si escribes un usuario inexistente responde \*"el nombre de usuario X no está registrado en este sitio"\*. Eso confirma qué usuarios existen.

| **⛔ RIESGO / EXPLOTACIÓN EN LABORATORIO**  **Riesgo / concepto de seguridad.** Un login **mal implementado** distingue entre "usuario no existe" y "contraseña incorrecta". Eso convierte la búsqueda de credenciales de **exponencial** (adivinar usuario y contraseña a la vez) a **lineal** (primero el usuario, luego su contraseña).  Un login **bien implementado** responde siempre lo mismo: \*"usuario o contraseña incorrectos"\*, sin dar pistas. |
| --- |
| **ℹ INFORMACIÓN**  **Nota (fidelidad).** El instructor demostró este comportamiento sobre un sitio **de un cliente propio** (con autorización) a modo de ejemplo real, no sobre la máquina Academy. Se recoge aquí como **concepto**, no como paso de la máquina. |

## **8. Fuerza bruta con WPScan (último recurso)**

Solo cuando se han agotado otras vías se recurre a la fuerza bruta. WPScan puede hacer el ataque de contraseñas con --passwords:

| wpscan --url http://academy.thehackerlabs/wordpress --enumerate ap --passwords /usr/share/wordlists/rockyou.txt |
| --- |

**Resultado observado en clase:** se obtuvo un usuario válido — **Dylan** — con una contraseña débil del tipo **`password1`** (presente en rockyou.txt).

| **✔ OBJETIVO / BUENA PRÁCTICA**  **Buena práctica (regla de oro).** La **fuerza bruta es el último recurso**: es ruidosa y "funciona 1 de cada 10 veces". Antes conviene enumerar usuarios, reutilizar credenciales, buscar fugas de información, etc.  Para WordPress se prefiere **WPScan** frente a **Hydra** (que suele no responder bien al login de WordPress) o **Burp Intruder** (más lento). Además, el plugin **Wordfence** actúa como "antivirus/WAF" de WordPress y limita el número de intentos. |
| --- |
| **⚠ AVISO / ERROR COMÚN**  **Nota (fidelidad).** La transcripción recoge la credencial como "Dylan" con "password 1". Se interpreta como usuario Dylan / contraseña password1 (una entrada típica de rockyou.txt). Es un **valor de laboratorio** de esta máquina; adáptalo a tu instancia. |

## **9. Acceso inicial: RCE por el editor de temas**

Con las credenciales se inicia sesión en el panel (/wp-admin). Desde **Apariencia → Editor de temas** (Herramientas → Editor de archivos de tema) se puede editar el código de las plantillas del tema. La idea: **inyectar código PHP** en una plantilla que luego se ejecute al visitarla.

Se elige la plantilla **`404.php`** y se pega dentro una **reverse shell PHP** (misma técnica que en la máquina **Mr. Robot**).

| **⛔ RIESGO / EXPLOTACIÓN EN LABORATORIO**  **Explotación en laboratorio.** La plantilla objetivo debe ser **PHP**. Si la plantilla es **HTML** (como ocurrió con una 404 en clase), el código PHP **no se ejecuta**. Hay que buscar un fichero de plantilla .php. |
| --- |
| **ℹ INFORMACIÓN**  **Explicación complementaria: servidor → lenguaje.** Como regla general (≈99,9 %):  • **Apache / Linux → PHP** (webshells .php).  • **IIS / Windows → ASP.NET (`.aspx`)**.  • Casos raros: Perl, Ruby, Go, Python, Node/JS, etc. Si subes una shell en el lenguaje equivocado, no se ejecuta. |

## **10. Reverse shell: de HTTP a TCP**

Tras guardar la 404.php maliciosa, se pone **Netcat** a la escucha y se **dispara** la shell visitando la página 404 en el navegador:

| nc -lvnp 1234 |
| --- |

Al acceder a la página, la **máquina víctima se conecta de vuelta** al puerto 1234 del atacante. En ese instante el tráfico deja de ser peticiones de navegador (HTTP) y pasa a ser una conexión **TCP** directa (handshake SYN → SYN/ACK → ACK).

| **ℹ INFORMACIÓN**  **Explicación complementaria (se conectó con el forense visto antes).** En una captura de red, una ráfaga de HTTP que de repente cambia a **TCP** es una señal típica de reverse shell. Además, una vez dentro del servidor, el **WAF** (Wordfence) ya no protege: actúa a nivel de aplicación; dentro solo queda el firewall del sistema. |
| --- |

## **11. Estabilización de la shell y usuario obtenido**

La shell inicial es limitada. Se estabiliza (técnica ya vista en el máster):

| python3 -c 'import pty; pty.spawn("/bin/bash")'  export TERM=xterm  # Ctrl+Z ; luego en Kali:  stty raw -echo; fg |
| --- |

Se comprueba el usuario con whoami / id: somos **`www-data`**. Revisando /etc/passwd se ve qué shell usan los demás usuarios (aquí **bash**), lo que confirma que la shell interactiva funcionará.

| **✔ OBJETIVO / BUENA PRÁCTICA**  **Acceso inicial conseguido:** usuario www-data en la máquina Academy. |
| --- |
| **⚠ AVISO / ERROR COMÚN**  **Nota (fidelidad).** La **escalada de privilegios a root quedó pendiente**. El instructor indicó que esta máquina se guarda y su escalada (descrita como "una fumada") se verá en el módulo de escalada de privilegios. |

# **Flujo de trabajo de la sesión**

Kill chain seguida en el laboratorio (hasta acceso inicial):

|  | Reconocimiento de red (netdiscover) |  |
| --- | --- | --- |
|  | **↓** |  |
|  | Enumeración de puertos (nmap) → 22 y 80 |  |
|  | **↓** |  |
|  | Fuzzing web recursivo (dirsearch -r) → /wordpress |  |
|  | **↓** |  |
|  | Ajuste de /etc/hosts (academy.thehackerlabs) |  |
|  | **↓** |  |
|  | Detección del CMS + versión (WPScan) → WP 6.5.3 |  |
|  | **↓** |  |
|  | Enumeración de usuarios y plugins (WPScan) |  |
|  | **↓** |  |
|  | Credenciales válidas (fuerza bruta WPScan) → Dylan |  |
|  | **↓** |  |
|  | Login en /wp-admin |  |
|  | **↓** |  |
|  | RCE: reverse shell PHP en 404.php (editor de temas) |  |
|  | **↓** |  |
|  | Netcat a la escucha (1234) → shell www-data |  |
|  | **↓** |  |
|  | Estabilización de la shell |  |
|  | **↓** |  |
|  | Escalada de privilegios (PENDIENTE — próximo módulo) |  |

# **Herramientas utilizadas en la sesión**

| **Herramienta** | **Objetivo** | **Fase** | **Comando o uso visto** | **Nivel** | **Notas** |
| --- | --- | --- | --- | --- | --- |
| netdiscover | Localizar hosts en la red | Reconocimiento | netdiscover -r 10.0.2.0/24 | Practicada | Usa ARP; no vale en AWS |
| nmap | Puertos y servicios | Enumeración | nmap -sV -p- {IP} | Recurrente | Resultado: 22 y 80 |
| dirsearch | Fuzzing de directorios | Enum. web | dirsearch -u URL -r -w dic | Practicada | -r = recursivo; equivale a Gobuster/ffuf |
| WPScan | Auditar WordPress | Enum. / Explotación | wpscan --url URL/wordpress … | Usada en auditoría | Núcleo de la sesión |
| SecLists | Diccionarios | Enumeración | top-usernames-shortlist.txt | Introducida | Listas de usuarios |
| rockyou.txt | Diccionario de contraseñas | Fuerza bruta | /usr/share/wordlists/rockyou.txt | Introducida | Contraseñas comunes |
| Burp Suite | Interceptar/analizar HTTP | Enum. web | Proxy + FoxyProxy 127.0.0.1:8080 | Practicada | Ver cabeceras y cookies |
| Netcat | Listener reverse shell | Explotación | nc -lvnp 1234 | Practicada | Recibe la shell (TCP) |
| /etc/hosts | Resolver dominio local | Enum. web | IP academy.thehackerlabs | Practicada | Necesario por la redirección 301 |
| **ℹ INFORMACIÓN**  **Nota.** Wordfence aparece **mencionado** como el plugin "antivirus/WAF" de WordPress que limita intentos de login, pero **no se explota ni se configura** en el material. |

# **Comandos importantes**

## **Reconocimiento y enumeración**

| sudo netdiscover -r 10.0.2.0/24  sudo nmap -sV -p- {IP\_OBJETIVO}  dirsearch -u http://{IP\_OBJETIVO}/ -r -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt |
| --- |

netdiscover -r: descubre hosts vía ARP en el rango indicado. nmap -sV -p-: escanea los 65 535 puertos TCP e intenta detectar versiones. dirsearch -r: fuzzing **recursivo** de directorios.

## **Ajuste de /etc/hosts**

| sudo nano /etc/hosts  # {IP\_OBJETIVO} academy.thehackerlabs |
| --- |

Mapea el dominio de la máquina a su IP para que el navegador y WPScan resuelvan correctamente tras la redirección 301.

## **WPScan**

| wpscan --url http://academy.thehackerlabs/wordpress  wpscan --url http://academy.thehackerlabs/wordpress -e u -U /usr/share/seclists/Usernames/top-usernames-shortlist.txt  wpscan --url http://academy.thehackerlabs/wordpress --enumerate ap  wpscan --url http://academy.thehackerlabs/wordpress --enumerate vp --api-token {API\_TOKEN}  wpscan --url http://academy.thehackerlabs/wordpress --enumerate ap --passwords /usr/share/wordlists/rockyou.txt |
| --- |

De arriba a abajo: escaneo base (detecta versión), enumeración de **usuarios** (-e u, -U = diccionario de nombres), enumeración de **plugins** (ap = all plugins), enumeración de **plugins vulnerables** con **API token** (añade CVEs), y **fuerza bruta** de contraseñas con rockyou.txt.

## **Reverse shell y estabilización**

| nc -lvnp 1234  python3 -c 'import pty; pty.spawn("/bin/bash")'  export TERM=xterm  stty raw -echo; fg  whoami; id |
| --- |

nc -lvnp 1234: pone Netcat a la escucha para recibir la conexión de vuelta. El resto estabiliza la TTY y confirma que somos www-data.

# **Riesgos, errores comunes y buenas prácticas**

| **⚠ AVISO / ERROR COMÚN**  **Apuntar al directorio equivocado.** WPScan/exploits deben lanzarse contra /wordpress (donde vive el CMS), no contra la raíz del dominio. Contra una ruta sin WordPress no obtendrás nada. |
| --- |
| **⚠ AVISO / ERROR COMÚN**  **Confiar en toda vulnerabilidad listada.** Muchas requieren autenticación, un rol concreto o una funcionalidad accesible. Verifica endpoint y contexto antes de invertir tiempo. |
| **⚠ AVISO / ERROR COMÚN**  **Lenguaje de la webshell.** Subir una shell en el lenguaje equivocado (p. ej. HTML o .aspx en un Apache/Linux) hace que no se ejecute. |
| **✔ OBJETIVO / BUENA PRÁCTICA**  **Fuerza bruta al final.** Agota antes enumeración, reutilización de credenciales y fugas de información. Es ruidosa y poco fiable. |
| **✔ OBJETIVO / BUENA PRÁCTICA**  **Documenta** cada comando, su resultado y tu interpretación: no basta con lanzar herramientas, hay que entender qué devuelven y por qué. |
| **⛔ RIESGO / EXPLOTACIÓN EN LABORATORIO**  **Alcance.** Todo lo anterior se aplica **solo** en laboratorios y auditorías autorizadas. La demostración de \*user enumeration\* sobre un sitio real la hizo el instructor sobre un **cliente propio** con permiso. |

# **Conexión con sesiones anteriores**

Esta sesión enlaza directamente con varios bloques ya trabajados en el máster:

- **OWASP Top 10 y auditoría web**: se aplica la metodología web a un CMS concreto.
- **Burp Suite / FoxyProxy**: se reutilizan para inspeccionar peticiones, cabeceras (Server: Apache) y cookies del login.
- **Fuzzing de directorios** (Gobuster, Feroxbuster, ffuf, Dirsearch): misma fase de enumeración web vista en máquinas anteriores; aquí destaca la recursividad -r.
- **Máquina Mr. Robot**: la técnica de RCE es idéntica — reverse shell PHP inyectada en una plantilla del tema (404.php) y disparada desde el navegador.
- **Análisis forense con PCAP**: se retoma la idea de detectar el cambio HTTP → TCP como firma de una reverse shell.
- **Escalada de privilegios**: queda pendiente y conecta con el módulo de \*privesc\* (como en Oopsie, Archetype o Mr. Robot).

# **Resumen final**

Qué debe llevarse Chema de esta clase:

1. En WordPress, **el peligro está en los plugins**, no en el núcleo.
2. **WPScan** es la navaja suiza del CMS: versión, usuarios, plugins y, con **API token**, sus CVEs.
3. Enumerar **antes** de forzar; la **fuerza bruta es el último recurso** y en WordPress se hace con WPScan.
4. El **editor de temas** es una vía clásica de **RCE** si consigues acceso al panel: PHP en 404.php.
5. La **reverse shell** convierte el juego de HTTP a TCP; luego se **estabiliza** y se comprueba el usuario (www-data).
6. La máquina llega hasta **acceso inicial**; la **escalada a root** se verá más adelante.

# **Checklist de repaso**

☐ Sé diferenciar una web nativa de un CMS y por qué se auditan distinto.

☐ Entiendo por qué la superficie de ataque de WordPress está en los plugins.

☐ Sé lanzar netdiscover y nmap para reconocimiento y enumeración de puertos.

☐ Sé por qué uso el flag -r (recursivo) en el fuzzing de directorios.

☐ Sé por qué una ruta da 301 y cómo arreglar la resolución con /etc/hosts.

☐ Sé enumerar versión, usuarios y plugins con WPScan.

☐ Entiendo la diferencia entre WPScan con y sin API token.

☐ Reconozco la enumeración de usuarios por mensajes de error del login.

☐ Sé por qué la fuerza bruta es el último recurso y por qué uso WPScan en WordPress.

☐ Sé conseguir RCE con una reverse shell PHP en el editor de temas (404.php).

☐ Entiendo la transición HTTP → TCP al obtener la shell y cómo estabilizarla.

☐ Sé identificar el usuario obtenido (www-data) y que la escalada queda pendiente.

# **Actualización del registro de herramientas**

Cambios de nivel derivados de esta sesión (para copiar a la base de conocimiento del proyecto):

| **Herramienta** | **Nivel anterior** | **Nivel nuevo** | **Motivo del cambio** | **Notas para futuras sesiones** |
| --- | --- | --- | --- | --- |
| WPScan | Introducida | Usada en auditoría | Enumeración de versión, usuarios y plugins + fuerza bruta dentro de la kill chain de una máquina. | Repasar --enumerate (u/ap/vp) y el uso del API token. |
| Dirsearch | Mencionada | Practicada | Uso real con enumeración recursiva (-r) sobre /wordpress. | Comparar diccionarios por defecto entre herramientas. |
| Netcat | — | Practicada | Listener de la reverse shell (nc -lvnp 1234). | Ligado a la fase de acceso inicial. |
| SecLists | Introducida | Practicada | Diccionarios de usernames para WPScan. | Localizar las listas de usuarios más útiles. |
| rockyou.txt | — | Introducida | Diccionario de contraseñas en la fuerza bruta con WPScan. | Diccionario por defecto en /usr/share/wordlists. |
| Netdiscover | Practicada | Practicada | Uso confirmado en reconocimiento (sin cambio de nivel). | Recordar: ARP, no válido en AWS. |
| Burp Suite | Practicada | Practicada | Apoyo para inspección de cabeceras/cookies (sin cambio de nivel). | Reutilizado del bloque anterior. |
| **ℹ INFORMACIÓN**  **Herramientas nuevas registradas en esta sesión:** Netcat (como listener) y el diccionario rockyou.txt. WPScan sube a **Usada en auditoría**. |
