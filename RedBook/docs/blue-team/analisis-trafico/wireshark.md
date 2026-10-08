---
tags:
- Análisis de tráfico
---

# Wireshark

EVOLVE ACADEMY - MASTER EN CIBERSEGURIDAD

**Wireshark: el Tiburón de las Redes**

Evolve Academy · Análisis de tráfico

*Temas: Captura de paquetes · Filtros BPF · Filtros de visualización · Análisis de protocolos · Man in the Middle · Detección de ataques*

# **① ¿Qué es Wireshark?**

Wireshark es el **analizador de protocolos de red** más utilizado del mundo. Captura y muestra en detalle el tráfico que pasa por una interfaz de red. Es fundamental tanto para pentesting como para defensa.

| **💡 COMUNICACIONES** | Una red existe cuando dos o más dispositivos intercambian información y hay respuesta. Wireshark captura exactamente ese intercambio, paquete a paquete. |
| --- | --- |

# **② Interfaz de Wireshark**

| **Elemento** | **Descripción** |
| --- | --- |
| Barra de captura | Botones para iniciar/parar captura. Selección de interfaz. |
| Filtro de captura | BPF syntax. Se aplica ANTES de capturar (menos datos). |
| Filtro de visualización | Se aplica DESPUÉS. Más flexible, no descarta paquetes. |
| Lista de paquetes | Panel superior: resumen de cada paquete capturado. |
| Detalle de paquete | Panel medio: desglose por capas (OSI). |
| Vista hex/ASCII | Panel inferior: bytes crudos del paquete. |
| Barra de estado | Paquetes capturados, filtrados, tiempo de captura. |

# **③ Filtros de captura (BPF)**

Los filtros BPF (Berkeley Packet Filter) se aplican **durante la captura**. Son más eficientes pero menos flexibles. Se escriben en la barra de filtro verde antes de iniciar.

| # Filtros BPF comunes:  host 192.168.1.1 # solo tráfico de/hacia esa IP  src host 192.168.1.1 # solo tráfico que SALE de esa IP  dst host 192.168.1.1 # solo tráfico que VA a esa IP  port 80 # solo tráfico por el puerto 80  port 80 or port 443 # HTTP o HTTPS  not port 22 # todo excepto SSH  tcp # solo protocolo TCP  udp # solo UDP  icmp # solo ICMP (pings)  # Combinaciones:  host 192.168.1.1 and port 80  src net 192.168.1.0/24 # toda la red local  tcp and port 443 and host 10.0.0.5 |
| --- |

# **④ Filtros de visualización**

Los filtros de visualización se aplican **después de capturar**. Son más potentes y permiten buscar por campos específicos de los protocolos.

| # Por protocolo:  http # todo HTTP  dns # consultas y respuestas DNS  arp # tráfico ARP  tcp # solo TCP  ssl or tls # tráfico cifrado  # Por IP:  ip.addr == 192.168.1.1  ip.src == 192.168.1.1  ip.dst == 192.168.1.1  ip.addr == 192.168.1.0/24 # red completa  # Por puerto:  tcp.port == 80  tcp.dstport == 443  udp.port == 53  # HTTP específico:  http.request.method == 'POST'  http.response.code == 200  http contains 'password' # texto en el paquete  http.request.uri contains '/login'  # DNS:  dns.qry.name == 'google.com'  dns.flags.response == 1 # solo respuestas  # TCP flags:  tcp.flags.syn == 1 && tcp.flags.ack == 0 # solo SYN (inicio conexión)  tcp.flags.rst == 1 # RST (conexión rechazada/reseteada) |
| --- |

# **⑤ Análisis del TCP Handshake**

Wireshark muestra perfectamente el proceso de establecimiento de conexión TCP:

| **→ SYN (cliente)** | -> | **← SYN-ACK (servidor)** | -> | **→ ACK (cliente)** | -> | **[DATOS]** | -> | **→ FIN/← FIN** |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

| # Filtrar solo el handshake TCP:  tcp.flags.syn == 1  # Ver todas las conversaciones TCP:  # Statistics → Conversations → TCP  # Reconstruir una sesión HTTP completa:  # Click derecho en paquete HTTP → Follow → TCP Stream  # Muestra la conversación completa en texto legible  # Aplicable también a:  # UDP Stream → protocolos UDP  # TLS Stream → tráfico cifrado (no desencripta)  # HTTP Stream → sesión HTTP completa |
| --- |

| **🔐 CREDENCIALES** | En HTTP sin cifrar (puerto 80), el Follow TCP Stream puede mostrar usuario y contraseña en texto plano en peticiones POST. Esto es por lo que HTTPS es obligatorio. |
| --- | --- |

# **⑥ Detección de ataques con Wireshark**

## **SYN Flood (DoS)**

| # Filtro para detectar SYN Flood:  tcp.flags.syn == 1 && tcp.flags.ack == 0  # Si ves miles de SYN desde múltiples IPs sin completar handshake  # → está ocurriendo un SYN Flood / DDoS |
| --- |

## **ARP Poisoning / Spoofing**

| # Filtro ARP:  arp  # Señales de ARP Poisoning:  # 1. Muchos ARP Replies gratuitous (sin previa solicitud)  # 2. Misma IP respondida por dos MACs diferentes  # 3. ARP Replies desde la IP del gateway pero con MAC diferente  # En Statistics → Resolved Addresses puedes ver MAC → IP  # Si el gateway tiene dos entradas = ARP Poisoning en curso |
| --- |

## **Port Scan (Nmap)**

| # Un escaneo Nmap genera un patrón muy reconocible:  # Muchos SYN hacia diferentes puertos de la misma IP destino  # Filtro para detectar:  tcp.flags.syn == 1 && ip.dst == 192.168.1.1  # Si ves peticiones a puertos 1,2,3,4... es un escaneo secuencial  # Nmap -sS (SYN scan) deja RST en los puertos cerrados:  tcp.flags.rst == 1 |
| --- |

# **⑦ Análisis de protocolos específicos**

## **HTTP — Ver contraseñas en texto plano**

| # Capturar y analizar login en HTTP:  http.request.method == 'POST'  # → Seguir TCP Stream para ver las credenciales  # Buscar cookies de sesión:  http.cookie  # Las cookies de sesión permiten secuestrar sesiones (session hijacking) |
| --- |

## **DNS — Detección de tunelización**

| # DNS Tunneling: usar DNS para exfiltrar datos (bypass firewalls)  # Señales: consultas DNS muy largas o con muchos subdominios  dns.qry.name contains '.' # ver todas las consultas  # Si ves nombres como 'aGVsbG8gd29ybGQ=.malware.com' (base64)  # → posible DNS tunneling  # Estadísticas de DNS:  # Statistics → DNS → muestra dominios más consultados |
| --- |

# **⑧ tshark — Wireshark por línea de comandos**

| # tshark es Wireshark sin interfaz gráfica (ideal para scripts)  # Listar interfaces disponibles:  tshark -D  # Capturar en interfaz eth0:  tshark -i eth0  # Capturar con filtro BPF:  tshark -i eth0 -f 'port 80'  # Guardar captura a fichero:  tshark -i eth0 -w captura.pcap  # Leer y filtrar un .pcap:  tshark -r captura.pcap -Y 'http'  # Extraer campos específicos:  tshark -r captura.pcap -Y 'http.request.method == POST' -T fields -e http.host -e http.request.uri  # Extraer credenciales HTTP básicas:  tshark -r captura.pcap -Y 'http.authorization' -T fields -e http.authorization |
| --- |

| **💡 AUTOMATIZACIÓN** | tshark permite analizar capturas en scripts. Por ejemplo: capturar durante 60 segundos, filtrar credenciales HTTP y guardarlas en fichero. Muy útil en post-explotación. |
| --- | --- |
