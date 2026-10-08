---
tags:
- Fundamentos
---

# Intro Redes

EVOLVE ACADEMY - MASTER EN CIBERSEGURIDAD

**Introducción a Redes: cómo funcionan las comunicaciones**

Evolve Academy · Fundamentos de redes

*Temas: Modelo OSI · TCP/IP · Virtualización · Protocolos · Puertos · DNS · HTTP*

# **① ¿Qué es una red de comunicaciones?**

Una red existe cuando dos o más dispositivos intercambian información **y hay respuesta de ambas partes**. Sin respuesta, no hay comunicación. El concepto fundamental es el intercambio bidireccional.

| **💡 DEFINICIÓN** | Para que haya red tiene que haber mínimo una respuesta por parte de cada equipo. Un paquete enviado sin respuesta no constituye comunicación. |
| --- | --- |

# **② Modelo OSI — Las 7 capas**

El modelo OSI divide la comunicación en 7 capas. Cada capa solo habla con la de arriba y la de abajo. Permite diagnosticar en qué punto falla algo.

| **Capa** | **Función y protocolos** |
| --- | --- |
| 7 — Aplicación | HTTP, FTP, DNS, SMTP. Lo que ve el usuario. |
| 6 — Presentación | Cifrado, compresión, formato de datos (SSL/TLS aquí). |
| 5 — Sesión | Gestión de sesiones entre aplicaciones. |
| 4 — Transporte | TCP / UDP. Puertos. Control de flujo y errores. |
| 3 — Red | IP. Enrutamiento entre redes. Routers. |
| 2 — Enlace de datos | MAC. Switches. Comunicación en la misma red local. |
| 1 — Física | Cables, WiFi, señales eléctricas / ópticas. |

| **🔐 HACKING** | Los ataques se clasifican por capa: ARP poisoning (L2), IP spoofing (L3), SYN flood (L4), SQLi/XSS (L7). Saber en qué capa operas es fundamental. |
| --- | --- |

# **③ TCP/IP — El modelo real**

En la práctica se usa el modelo TCP/IP de 4 capas (simplificación del OSI):

| **Capa TCP/IP** | **Protocolos** |
| --- | --- |
| Aplicación | HTTP, HTTPS, DNS, FTP, SSH, SMTP, IMAP... |
| Transporte | TCP (fiable, con ACK) / UDP (rápido, sin confirmación) |
| Internet | IP, ICMP, ARP |
| Acceso a red | Ethernet, WiFi, PPP |

## **TCP vs UDP**

| **TCP — Fiable**   - Orientado a conexión (handshake SYN/SYN-ACK/ACK) - Garantiza entrega y orden - Más lento por el control de errores - Usado en: HTTP, HTTPS, SSH, FTP, SMTP | **UDP — Rápido**   - Sin conexión previa, sin ACK - No garantiza entrega ni orden - Más rápido, menor overhead - Usado en: DNS, DHCP, streaming, VoIP, videojuegos |
| --- | --- |

# **④ Puertos y servicios**

Los puertos identifican servicios dentro de un host. Rango 0-65535. Los conocidos (**well-known**) son el 0-1023.

| **Puerto** | **Servicio** |
| --- | --- |
| 20/21 | FTP (transferencia de ficheros) |
| 22 | SSH (administración remota segura) |
| 23 | Telnet (remota sin cifrar — ¡no usar!) |
| 25 | SMTP (envío de correo) |
| 53 | DNS (resolución de nombres) |
| 80 | HTTP (web sin cifrar) |
| 110 | POP3 (recepción de correo) |
| 143 | IMAP (correo, acceso remoto) |
| 443 | HTTPS (web cifrada) |
| 445 | SMB (recursos compartidos Windows) |
| 3306 | MySQL |
| 3389 | RDP (escritorio remoto Windows) |
| 8080 | HTTP alternativo / proxies |

| **🔐 NMAP** | nmap -sV -p- <IP> descubre qué servicios corren en cada puerto abierto. El primer paso de cualquier auditoría. |
| --- | --- |

# **⑤ Direccionamiento IP**

## **IPv4**

| # Formato: 4 octetos de 8 bits = 32 bits total  # Ejemplo: 192.168.1.100  # Clases de redes privadas (RFC 1918) — no enrutables en internet:  10.0.0.0/8 # Clase A (grandes empresas)  172.16.0.0/12 # Clase B (medianas empresas)  192.168.0.0/16 # Clase C (hogares y oficinas pequeñas)  # Especiales:  127.0.0.1 # loopback (yo mismo)  0.0.0.0 # cualquier interfaz  255.255.255.255 # broadcast (todos en la red) |
| --- |

## **Máscara de subred y CIDR**

| 192.168.1.0/24 # /24 = 255.255.255.0 = 256 hosts (254 usables)  192.168.1.0/16 # /16 = 255.255.0.0 = 65.536 hosts  192.168.1.0/8 # /8 = 255.0.0.0 = 16M hosts  # Calcular rango:  # Red: 192.168.1.0/24  # Primera IP: 192.168.1.1 (router normalmente)  # Última IP: 192.168.1.254  # Broadcast: 192.168.1.255 |
| --- |

# **⑥ DNS — Sistema de Nombres de Dominio**

El DNS traduce nombres legibles (google.com) a IPs. Es una base de datos distribuida y jerárquica.

| **Navegador solicita google.com** | -> | **Caché local / hosts** | -> | **Servidor DNS** | -> | **Respuesta: IP 142.x.x.x** |
| --- | --- | --- | --- | --- | --- | --- |

| # Tipos de registros DNS:  A → nombre → IPv4  AAAA → nombre → IPv6  MX → servidor de correo  CNAME → alias a otro nombre  TXT → texto libre (SPF, DKIM...)  NS → servidores de nombres autoritativos  PTR → IP → nombre (DNS inverso)  # Herramientas:  nslookup google.com # consulta básica  dig google.com ANY # consulta avanzada  dig -x 8.8.8.8 # DNS inverso  host google.com # simple y rápido |
| --- |

| **🔐 HACKING** | El DNS es crítico en OSINT: subdominios, transferencias de zona (dig axfr), registros MX revelan infraestructura. Herramientas: dnsrecon, subfinder. |
| --- | --- |

# **⑦ Virtualización**

Permite correr múltiples sistemas operativos dentro del mismo equipo físico. Fundamental para crear laboratorios de ciberseguridad.

| **Hipervisor** | **Notas** |
| --- | --- |
| VirtualBox | Gratuito, open source. Bueno para empezar. |
| VMware Workstation | Más rendimiento y estabilidad. Preferido en el máster. |
| Hyper-V | Integrado en Windows Pro/Enterprise. |
| UTM / Parallels | Soluciones para macOS (especialmente Apple Silicon). |

| **💡 LABS** | Para este máster: 2 VMs máximo simultáneas en una máquina con 8GB RAM. Con 16GB+ puedes levantar un directorio activo completo. |
| --- | --- |
