---
tags:
- Fundamentos
---

# Redes Typos Datagramas

EVOLVE ACADEMY - MASTER EN CIBERSEGURIDAD

**Redes: Tipologías, Datagramas y Paquetes de Red**

Evolve Academy · Infraestructura y protocolos

*Temas: LAN/WAN/MAN · Topologías · Encapsulación · TCP handshake · ICMP · ARP · Modelo OSI práctico*

# **① Tipos de redes por alcance**

| **Tipo** | **Descripción** |
| --- | --- |
| PAN | Personal Area Network. Alcance ~10m. Bluetooth, USB. |
| LAN | Local Area Network. Un edificio/campus. Ethernet, WiFi. |
| MAN | Metropolitan Area Network. Una ciudad. |
| WAN | Wide Area Network. Global. Internet es la WAN más grande. |
| VPN | Red privada virtual sobre red pública (Internet). |
| VLAN | Red local virtual — segmentación lógica dentro de una LAN. |

# **② Topologías de red**

| **Topología** | **Descripción** |
| --- | --- |
| Bus | Todos comparten un único cable. Un fallo corta la red. |
| Estrella | Todos conectados a un switch central. La más común en LAN. |
| Anillo | Cada nodo conectado al siguiente. Datos circulan en un sentido. |
| Malla | Cada nodo conectado a varios otros. Redundancia máxima. Internet. |
| Árbol | Jerarquía de switches. Entornos empresariales grandes. |

| **💡 PRÁCTICA** | En entornos reales casi siempre encontramos topología en estrella (switches) dentro de una LAN y topología en malla a nivel de WAN/Internet. |
| --- | --- |

# **③ Encapsulación: cómo viajan los datos**

Cada capa del modelo OSI añade su propia cabecera al bloque de datos (encapsulación). Al recibir, cada capa quita su cabecera (desencapsulación).

| **Datos (App)** | -> | **Segmento (TCP)** | -> | **Paquete (IP)** | -> | **Trama (Ethernet)** | -> | **Bits (Física)** |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

| # Nomenclatura por capa:  Capa 7 (Aplicación) → Datos / Mensaje  Capa 4 (Transporte) → Segmento (TCP) / Datagrama (UDP)  Capa 3 (Red) → Paquete (IP)  Capa 2 (Enlace) → Trama (Frame)  Capa 1 (Física) → Bits |
| --- |

# **④ TCP — Three-Way Handshake**

Antes de enviar datos, TCP establece una conexión con 3 mensajes:

| **SYN →** | -> | **← SYN-ACK** | -> | **ACK →** | -> | **[Conexión establecida]** |
| --- | --- | --- | --- | --- | --- | --- |

| # SYN → Cliente dice: 'quiero conectar, seq=X'  # SYN-ACK → Servidor dice: 'ok, seq=Y, ack=X+1'  # ACK → Cliente confirma: 'ack=Y+1'  # Cierre de conexión (4 mensajes):  # FIN → ACK → FIN → ACK  # Ataque SYN Flood: enviar miles de SYN sin completar el handshake  # → el servidor agota sus recursos esperando ACK que nunca llega |
| --- |

| **🔐 HACKING** | El SYN scan de Nmap (-sS) envía un SYN y espera SYN-ACK sin completar el handshake → el puerto está abierto. Rápido y sigiloso. |
| --- | --- |

# **⑤ Cabecera IP**

| # Campos principales de la cabecera IPv4:  Version (4 bits) → IPv4 = 4  TTL (8 bits) → Time To Live: se decrementa en cada router  0 → paquete descartado (evita bucles infinitos)  Protocol (8 bits) → 6=TCP, 17=UDP, 1=ICMP  Source IP (32 bits) → IP origen  Destination IP (32bits)→ IP destino  # TTL sirve para fingerprinting del OS:  # TTL=64 → Linux/Unix  # TTL=128 → Windows  # TTL=255 → Cisco / algunos dispositivos de red |
| --- |

# **⑥ ICMP — Control y diagnóstico**

| # ICMP no es TCP ni UDP: opera en capa 3 directamente  # Tipos de mensajes ICMP:  Type 0 → Echo Reply (respuesta a ping)  Type 3 → Destination Unreachable (host/puerto inalcanzable)  Type 8 → Echo Request (el ping que envías)  Type 11 → Time Exceeded (TTL=0, respuesta de traceroute)  # Herramientas que usan ICMP:  ping 8.8.8.8 # verificar conectividad  traceroute 8.8.8.8 # ver saltos hasta el destino  traceroute -I 8.8.8.8 # usando ICMP en lugar de UDP |
| --- |

| **ℹ FIREWALLS** | Muchos firewalls bloquean ICMP. Por eso nmap -Pn omite el ping y escanea directamente los puertos aunque el host no responda a pings. |
| --- | --- |

# **⑦ ARP — Resolución de direcciones**

ARP traduce direcciones IP a direcciones MAC en la red local. Opera en capa 2.

| # ¿Quién tiene 192.168.1.1? — ARP Request (broadcast)  # 192.168.1.1 está en MAC AA:BB:CC:DD:EE:FF — ARP Reply (unicast)  arp -a # ver tabla ARP local  arp -n # sin resolución de nombres  # Caché ARP: se guarda temporalmente para no preguntar siempre |
| --- |

| **🔐 ARP POISONING** | Un atacante en la misma red puede enviar ARP Replies falsos (Gratuitous ARP) para decir 'la IP del router soy yo' → Man in the Middle. Herramienta: arpspoof, ettercap. |
| --- | --- |

# **⑧ Metadatos de imagen y OSINT de red**

Los metadatos (EXIF) de imágenes pueden revelar información crítica para OSINT de personas y organizaciones.

| exiftool imagen.jpg # ver todos los metadatos  # Campos interesantes:  # GPS coordinates → geolocalización exacta  # Camera make/model  # Date/Time Original  # Software → versión de edición  # Herramientas online:  # Jeffrey's Exif Viewer, Exif.regex.info  # Fotoforensics.com (análisis de manipulaciones) |
| --- |

| **💡 OSINT** | Una foto de LinkedIn puede contener coordenadas GPS si fue tomada con móvil sin desactivar ubicación. Fundamental verificarlo antes de publicar. |
| --- | --- |
