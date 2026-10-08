---
tags:
- General
---

# Sesion 25 Evolve

EVOLVE ACADEMY · MASTER EN CIBERSEGURIDAD

**Sesión 25 — Repaso, Mercado Laboral y Servicios**

Instructor: Yuba González · Metasploitable 2

*Temas: Metasploit · FTP · SMB · Mercado laboral · Marco mental · Nmap · Tmux*

# **① Nota sobre Metasploit**

| **⚠ AVISO** | Cuanto menos Metasploit, mejor. En OSCP y eCPPT está prohibido o muy limitado. Si aprendes con él, cuando te lo quiten no sabes qué pasa por debajo. |
| --- | --- |

| **✗ Evitar en general**  Reemplazar con herramientas específicas: scripts Python, Nmap, Hydra, NetExec. Así se entiende el protocolo subyacente. | **✓ Excepción: eJPT + pivoting**  En el eJPT no hay restricciones. En escenarios de pivoting (saltar entre redes) Metasploit centraliza las sesiones de forma práctica. |
| --- | --- |

| **💡 CLAVE** | Si aprendes SIN Metasploit → se convierte en una comodidad opcional. Si aprendes CON él → se vuelve un requisito del que no puedes prescindir. |
| --- | --- |

# **② Mercado laboral en seguridad ofensiva**

Mapa de servicios de un equipo de seguridad ofensiva, ordenados por nivel de entrada.

## **Perfil junior — foco del máster**

| **Nivel** | **Servicio** | **Descripción** |
| --- | --- | --- |
| **Junior ★★★** | **Auditorías web dinámicas** | El mayor foco de entrada. Apps web en ejecución, WordPress/WPScan, vulnerabilidades comunes. Es lo más demandado en perfiles junior. |
| **Junior ★★★** | **APIs y web services** | Similar a web dinámica, se trabaja con Burp Suite. Hay que conocer la diferencia entre REST y SOAP, pero el proceso de ataque es análogo. |
| **Junior ★★** | **Auditorías externas** | Simular atacante sin info previa. OSINT, enumeración de perímetro, búsqueda de servicios vulnerables. Caja negra. Objetivo: acceso inicial al servidor. |
| **Junior ★★** | **Vulnerability Management** | Escáneres: Nessus, OpenVAS, Qualys. Verificación de falsos positivos y comprobación manual. Rutinario pero habitual en equipos con poco personal. |
| **Junior ★** | **Auditorías WiFi** | Redes WPA2-PSK domésticas y redes Enterprise corporativas. Incluido en el máster. |

## **Perfil avanzado / senior**

| **Nivel** | **Servicio** | **Descripción** |
| --- | --- | --- |
| **Medio-senior** | **Auditorías internas / AD** | Infraestructura Windows interna. Kerberos, Pass-the-Hash, movimiento lateral. El máster lo toca pero no es el primer trabajo junior. |
| **Senior** | **Red Team** | Ejercicios de 4-5 meses simulando un APT real. Físico, ingeniería social, externa, interna y pivoting correlacionados. Requiere perfiles senior. |
| **Especialidad** | **Cloud (AWS/Azure/GCP)** | Mundo propio, hiper especializado. Queda fuera del máster. |
| **Medio** | **Ingeniería social** | Phishing con GoPhish, vishing (llamadas), baiting con USBs. El phishing sí entra en el máster. |
| **Especialidad** | **IoT y OT/ICS** | Dispositivos embebidos, PLCs, infraestructuras industriales. Especializaciones independientes. |

| **ℹ NOTA** | Caja negra / gris / blanca: la distinción no siempre implica diferencia de dificultad o precio. Depende de cuánta información facilita el cliente. Lo habitual es moverse entre caja negra y caja gris. |
| --- | --- |

**Especializaciones avanzadas (referencia cultural):** Car hacking · 5G / telcos · Guerra electrónica · ATMs · Auditorías de LLMs/IA · Pipelines CI/CD · Docker · OT/ICS industrial

# **③ Marco mental: 4 elementos para atacar servicios**

Aplicable a cualquier vulnerabilidad de servicio, independientemente del protocolo (FTP, SMB, SSH, HTTP...).

| **01**  **FUENTE**  Origen de la info que dispara la vulnerabilidad: entrada de usuario, cabecera HTTP, fichero de config, librería... | **02**  **PROCESO**  Qué hace el servicio con esa información. Aquí ocurre la mayoría de las vulnerabilidades. | **03**  **PRIVILEGIOS**  Con qué permisos corre el proceso. Un mismo fallo puede ser trivial o crítico según si es user o root. | **04**  **DESTINO**  Qué se hace con el resultado. A dónde llega la información procesada. |
| --- | --- | --- | --- |

## **Ejemplo aplicado: Log4Shell (CVE-2021-44228)**

| **01 FUENTE** | Cabecera User-Agent manipulada por el atacante con un payload JNDI malicioso. |
| --- | --- |
| **02 PROCESO** | Log4j interpreta y ejecuta la cadena en lugar de solo registrarla. |
| **03 PRIVILEGIOS** | Si el proceso de logging corre con permisos elevados, el comando ejecutado hereda esos permisos. |
| **04 DESTINO** | RCE (Remote Code Execution) en la máquina víctima. |

| **✓ RECUERDA** | Las vulnerabilidades suelen venir de malas configuraciones, no de zero-days: credenciales por defecto, autenticación anónima habilitada, permisos excesivos. |
| --- | --- |

# **④ Metodología: orden antes que velocidad**

## **Estructura de carpetas — primer paso siempre**

| mkdir metasploitable2  cd metasploitable2  mkdir recon  mkdir exploits |
| --- |

## **Nmap en tres fases**

| **1. Escaneo rápido (top 1000)** | → | **2. Todos los puertos (-p-)** | → | **3. Scripts sobre puertos hallados** |
| --- | --- | --- | --- | --- |

**Fase 1 —** escaneo básico rápido:

| nmap -oN recon/initial.txt <IP> |
| --- |

**Fase 2 —** todos los puertos:

| nmap -p- -oN recon/allports.txt <IP> |
| --- |

**Fase 3 —** scripts y versiones sobre puertos abiertos:

| nmap -sC --script default,vuln -sV -Pn -p <PUERTOS> -oA recon/full <IP> |
| --- |

- **-oA:** guarda en los 3 formatos: normal, grepeable y XML.
- **-Pn:** omite el host discovery (útil si no hay respuesta a ping).
- **-sC:** equivale a --script=default. Lanza scripts de la categoría default.
- **vuln:** scripts específicos de CVEs. Más intrusiva y lenta, pero puede revelar vulnerabilidades directamente. Usar con cautela en auditorías reales.

## **Tmux — trabajo en paralelo**

| Ctrl+B → " dividir horizontal | Ctrl+B → % dividir vertical |
| --- | --- |
| Ctrl+B → ↑↓←→ moverse entre paneles | Ctrl+B :source-file ~/.tmux.conf recargar config |

**Activar ratón:**

| echo "set -g mouse on" >> ~/.tmux.conf |
| --- |

| **📖 HackTricks** | Para cada servicio/protocolo consulta book.hacktricks.xyz/<servicio>. Cada página incluye comandos de enumeración, ataques típicos y recursos. |
| --- | --- |

# **⑤ FTP — flujo de ataque**

| **Identificar versión (Nmap)** | → | **searchsploit** | → | **Descargar exploit (-m)** | → | **Ejecutar → shell** |
| --- | --- | --- | --- | --- | --- | --- |

## **Búsqueda y descarga del exploit**

**Buscar exploits para la versión detectada:**

| searchsploit vsftpd 2.3.4 |
| --- |

**Descargar con flag -m (mirror):**

| searchsploit -m unix/remote/49757.py |
| --- |

**Ejecutar:**

| python3 49757.py -h <IP\_OBJETIVO> |
| --- |

| **ℹ NOTA** | Si la conexión se rechaza en el primer intento, relanzar. Las máquinas de laboratorio pueden tener estados intermedios. |
| --- | --- |

## **Autenticación anónima**

| ftp <IP>  # usuario: anonymous | contraseña: cualquiera |
| --- |

Si está habilitada, da acceso sin credenciales válidas. Siempre verificar.

| **✓ OBJETIVO** | FTP: versión → searchsploit → descargar exploit → ejecutar → obtener shell. |
| --- | --- |

# **⑥ SMB / Samba — enumeración y acceso**

SMB expone carpetas compartidas (shares) en red. La enumeración combina varias herramientas complementarias.

## **Listar shares — smbclient (sesión nula)**

| smbclient -N -L //<IP> |
| --- |

## **Ver permisos de lectura/escritura — NetExec**

| netexec smb <IP> -u '' -p '' --shares |
| --- |

Muestra qué carpetas permiten leer, escribir o ninguna de las dos. Las carpetas con escritura permiten subir ficheros.

## **Conectarse a un share concreto**

| smbclient //<IP>/tmp -N  ls # listar  get <fichero> # descargar  put <fichero> # subir |
| --- |

## **Enumeración completa — enum4linux**

| enum4linux <IP> |
| --- |

Extrae: nombre de dominio, versión Samba, **usuarios del sistema**, shares y políticas de contraseña. Los usuarios son valiosos para ataques posteriores de fuerza bruta.

## **Password Spraying — NetExec**

| netexec smb <IP> -u usuarios.txt -p 'admin' --continue-on-success |
| --- |

Prueba una sola contraseña contra todos los usuarios de la lista. Especialmente útil en Active Directory para evitar bloqueos de cuenta (no es fuerza bruta clásica).

| **⚠ CONTEXTO** | SMB/Samba es uno de los protocolos más utilizados en entornos corporativos (junto con LDAP) y uno de los más explotados. Eternal Blue (MS-17-010) es el ejemplo más conocido. |
| --- | --- |

| **✓ OBJETIVO** | SMB: listar shares → ver permisos → conectarse → enum4linux (usuarios) → password spraying si hay credenciales. |
| --- | --- |
