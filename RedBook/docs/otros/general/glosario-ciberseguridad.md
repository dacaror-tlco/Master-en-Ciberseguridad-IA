---
tags:
- General
date: '2026-07-28'
---

# Glosario Ciberseguridad

<p class="note-meta">2026-07-28</p>

**EVOLVE ACADEMY · MÁSTER EN CIBERSEGURIDAD OFENSIVA**

**Glosario del Máster de Ciberseguridad**

Referencia acumulativa de la colección de apuntes · Actualizado 28/07/2026

| **ℹ Cómo usar este glosario**  Documento de referencia del proyecto. Reúne los términos que han aparecido en TODAS las sesiones del máster: redes, Linux, OSINT, análisis de tráfico, explotación web y de servicios, Windows/Active Directory, cloud, ingeniería social, defensa y normativa, y el bloque de Inteligencia Artificial. Cada apunte incluye además su propio glosario con los términos de esa clase. Se amplía con cada sesión nueva. |
| --- |

# **Redes y protocolos**

| **Término** | **Significado** | **Definición** |
| --- | --- | --- |
| Modelo OSI | Open Systems Interconnection | Modelo teórico de 7 capas (física, enlace, red, transporte, sesión, presentación, aplicación) que estructura la comunicación y ayuda a diagnosticar dónde falla. |
| TCP/IP | Transmission Control Protocol / Internet Protocol | Pila de protocolos real de Internet; versión práctica y simplificada del modelo OSI. |
| TCP | Transmission Control Protocol | Transporte fiable y orientado a conexión: garantiza entrega y orden mediante el handshake SYN/SYN-ACK/ACK. |
| UDP | User Datagram Protocol | Transporte sin conexión: rápido pero sin garantía de entrega ni orden (streaming, DNS, VoIP). |
| IP | Internet Protocol | Protocolo de red que direcciona y enruta paquetes entre redes mediante direcciones IP. |
| ICMP | Internet Control Message Protocol | Protocolo de control y diagnóstico de red (lo usan ping y traceroute). |
| ARP | Address Resolution Protocol | Resuelve una dirección IP a su dirección MAC dentro de la red local. |
| DNS | Domain Name System | Traduce nombres de dominio a direcciones IP. |
| HTTP / HTTPS | HyperText Transfer Protocol (Secure) | Protocolo de la web; HTTPS lo cifra con TLS/SSL. |
| FTP | File Transfer Protocol | Transferencia de ficheros; en claro salvo variantes seguras. |
| SMTP | Simple Mail Transfer Protocol | Protocolo de envío de correo electrónico. |
| SSH | Secure Shell | Acceso remoto cifrado a la consola de un sistema (puerto 22). |
| RDP | Remote Desktop Protocol | Escritorio remoto de Windows (puerto 3389). |
| VNC | Virtual Network Computing | Control remoto gráfico multiplataforma de un equipo. |
| SMB | Server Message Block | Compartición de ficheros/impresoras en redes Windows. |
| NFS | Network File System | Sistema de ficheros compartido en red típico de Unix/Linux. |
| NIS | Network Information Service | Servicio de directorio/credenciales centralizado en entornos Unix. |
| LDAP | Lightweight Directory Access Protocol | Acceso a servicios de directorio (usuarios, equipos); base de Active Directory. |
| LAN / WAN | Local / Wide Area Network | Red de área local frente a red de área amplia. |
| NAT | Network Address Translation | Traduce direcciones privadas a públicas para salir a Internet compartiendo una IP. |
| MAC | Media Access Control | Dirección física única de una tarjeta de red (capa 2). |
| Puerto | Port | Número que identifica un servicio dentro de una IP (80 HTTP, 443 HTTPS, 22 SSH). |
| Three-Way Handshake | — | Establecimiento de una conexión TCP en tres pasos: SYN → SYN-ACK → ACK. |
| TTL | Time To Live | Saltos que puede dar un paquete antes de descartarse; ayuda a estimar el SO de origen. |
| TLS / SSL | Transport Layer Security / Secure Sockets Layer | Cifrado del tráfico en tránsito; TLS es el sucesor moderno de SSL. |
| VPN | Virtual Private Network | Túnel cifrado que conecta redes o equipos a través de Internet. |
| Tor | The Onion Router | Red de anonimato que enruta el tráfico por varios nodos cifrados. |
| WPA2 | Wi-Fi Protected Access 2 | Cifrado WiFi; vulnerable a captura del four-way handshake para cracking offline. |
| IoT | Internet of Things | Dispositivos conectados (cámaras, sensores), a menudo mal securizados; objetivo frecuente en Shodan. |
| Encapsulación / Datagrama | PDU — Protocol Data Unit | Cada capa envuelve los datos con su cabecera; la unidad resultante (trama, paquete, datagrama, segmento). |

# **Vulnerabilidades web**

| **Término** | **Significado** | **Definición** |
| --- | --- | --- |
| SSTI | Server-Side Template Injection (inyección de plantillas en servidor) | El servidor evalúa como código un input que debería ser texto, abusando del motor de plantillas. Escala a lectura de ficheros, fuga de datos y RCE. |
| SSRF | Server-Side Request Forgery (falsificación de petición en servidor) | Se fuerza al servidor a hacer peticiones a destinos elegidos por el atacante, abusando de un parámetro que acepta una URL. |
| SQLi | SQL Injection (inyección SQL) | Inyección de sintaxis SQL en una consulta para leer, modificar o eludir la lógica de la BBDD (p. ej. ' OR 1=1 --). |
| LFI | Local File Inclusion (inclusión local de ficheros) | La aplicación lee/incluye ficheros locales del servidor a partir de una entrada del usuario. |
| RFI | Remote File Inclusion (inclusión remota de ficheros) | Variante de LFI en la que el fichero se carga desde una URL remota controlada por el atacante. |
| XXE | XML External Entity (entidad externa XML) | Abuso de entidades externas en XML para leer ficheros, hacer SSRF o provocar DoS. |
| IDOR | Insecure Direct Object Reference (referencia directa insegura a objeto) | Acceso a recursos de otros usuarios manipulando un identificador sin control de autorización. |
| Path Traversal | Directory Traversal (salto de directorio) | Uso de ../ para salir del directorio previsto y acceder a ficheros fuera del alcance. |
| CSRF | Cross-Site Request Forgery (falsificación de petición entre sitios) | Petición no deseada enviada en nombre de una víctima autenticada; se mitiga con tokens anti-CSRF. |
| XSS | Cross-Site Scripting (secuencias de comandos entre sitios) | Inyección de JavaScript que se ejecuta en el navegador de otros usuarios. |

# **Ataques de red y análisis de tráfico**

| **Término** | **Significado** | **Definición** |
| --- | --- | --- |
| DoS / DDoS | (Distributed) Denial of Service | Ataque que satura un servicio para dejarlo inoperativo; distribuido si procede de muchas fuentes. |
| SYN Flood | — | DoS de capa 4 que inunda con paquetes SYN dejando conexiones medio abiertas. |
| ARP Poisoning / Spoofing | — | Envenenamiento de la tabla ARP para interceptar tráfico de la red local (MITM). |
| MAC Spoofing / Flooding | — | Suplantar una MAC o saturar la tabla del switch para forzar el reenvío de tráfico. |
| Port Scan | Escaneo de puertos | Sondeo de puertos abiertos y servicios de un objetivo (p. ej. con Nmap). |
| Sniffer | — | Herramienta que captura y analiza el tráfico de red (p. ej. Wireshark). |
| BPF | Berkeley Packet Filter | Sintaxis de filtros de captura de bajo nivel usada en Wireshark/tcpdump. |
| MITM | Man-in-the-Middle | El atacante se sitúa entre dos partes para interceptar o alterar la comunicación. |

# **Ejecución, escalada y post-explotación**

| **Término** | **Significado** | **Definición** |
| --- | --- | --- |
| RCE | Remote Code Execution (ejecución remota de código) | Ejecutar comandos o código arbitrario en el sistema objetivo. Objetivo final de muchas vulnerabilidades. |
| Reverse shell | — | Conexión iniciada desde la víctima hacia el atacante, que le devuelve una shell interactiva. |
| Webshell | — | Script (p. ej. .php) subido al servidor que permite ejecutar comandos vía peticiones web. |
| SUID | Set User ID | Bit que ejecuta un binario con los privilegios de su propietario; vector clásico de escalada (find / -perm -4000). |
| SGID | Set Group ID | Como SUID pero con los permisos del grupo propietario. |
| Escalada de privilegios | Privilege Escalation | Pasar de un usuario limitado a uno con más permisos (root/administrador). |
| Pivoting | Movimiento lateral | Usar una máquina comprometida como salto para alcanzar otros sistemas internos. |
| Sandbox | — | Entorno aislado y restringido donde se ejecuta código para limitar el impacto (p. ej. Docker). |
| SECRET\_KEY | Clave secreta del framework | Clave con la que el framework firma sesiones/tokens; si se filtra, permite falsificarlos. |

# **Pentest, técnicas y conceptos ofensivos**

| **Término** | **Significado** | **Definición** |
| --- | --- | --- |
| CVE | Common Vulnerabilities and Exposures | Identificador público y único de una vulnerabilidad conocida (p. ej. CVE-2021-44228, Log4Shell). |
| Exploit | — | Código o técnica que aprovecha una vulnerabilidad concreta para comprometer un sistema. |
| Payload | Carga útil | Parte del ataque que produce el efecto buscado (la reverse shell, el comando ejecutado). |
| Fuzzing | — | Envío masivo y automatizado de entradas (diccionarios) para descubrir rutas, parámetros o fallos (ffuf, Sublist3r). |
| Fuerza bruta | Brute force | Probar sistemáticamente muchas combinaciones (contraseñas, valores) hasta acertar. |
| Diccionario / Wordlist | — | Lista de palabras/valores para fuzzing o fuerza bruta (SecLists, rockyou.txt). |
| Enumeración | Enumeration | Fase de recolección activa de servicios, usuarios, rutas y versiones del objetivo. |
| Footprinting | Huella | Reconocimiento inicial de la superficie e infraestructura del objetivo (OSINT, Shodan, WHOIS). |
| Fingerprinting | Huella tecnológica | Identificación de tecnologías y versiones (Wappalyzer/WhatWeb o por mensajes de error). |
| Polyglot | — | Cadena interpretable por varios motores a la vez; en SSTI fuerza un error que identifica el motor. |
| Motor de plantillas | Template engine | Combina plantilla (texto fijo + variables) y datos para generar la salida. Ejemplos: ERB, Jinja2, Tornado, FreeMarker, Twig. |
| CTF | Capture The Flag | Reto de ciberseguridad en el que se busca una 'flag' explotando vulnerabilidades. |
| Caja negra / gris / blanca | Black / Grey / White box | Nivel de información previa: negra = solo la URL; gris = credenciales/datos parciales; blanca = código y documentación. |

# **OSINT**

| **Término** | **Significado** | **Definición** |
| --- | --- | --- |
| OSINT | Open-Source Intelligence | Inteligencia obtenida de fuentes abiertas y públicas (webs, redes, registros). |
| Google Dorks | — | Operadores de búsqueda avanzada de Google (site:, filetype:, intitle:) para hallar información expuesta. |
| WHOIS | — | Consulta de datos de registro de un dominio (titular, fechas, servidores). |
| Shodan | — | Buscador de dispositivos conectados a Internet (servidores, cámaras, IoT) y sus servicios/vulnerabilidades. |
| HIBP | Have I Been Pwned | Servicio que indica si un correo/credencial aparece en filtraciones de datos conocidas. |
| EXIF | Exchangeable Image File Format | Metadatos incrustados en imágenes (cámara, fecha, a veces GPS); se extraen con exiftool. |
| Metadatos | Metadata | Datos 'sobre los datos' de un fichero (autor, software, coordenadas) útiles en OSINT. |
| Esteganografía | Steganography | Ocultar información dentro de otro fichero (p. ej. datos en una imagen con steghide). |

# **Sistema, Linux y shell**

| **Término** | **Significado** | **Definición** |
| --- | --- | --- |
| Shell | — | Intérprete de comandos (Bash en Linux, PowerShell en Windows). |
| CLI / GUI | Command-Line / Graphical User Interface | Interfaz por línea de comandos frente a interfaz gráfica. |
| Pipe / Redirección | — | Encadenar la salida de un comando como entrada de otro, o redirigir hacia/desde ficheros (stdin/stdout/stderr). |
| Permisos (rwx) | — | Permisos de lectura/escritura/ejecución sobre ficheros y directorios en Linux. |
| PATH | — | Variable de entorno con los directorios donde el shell busca los ejecutables. |
| Cron | — | Planificador de tareas periódicas en Linux; posible vector de persistencia/escalada. |

# **Defensa, roles y gobernanza**

| **Término** | **Significado** | **Definición** |
| --- | --- | --- |
| Red / Blue / Purple Team | — | Ofensiva (Red), defensa (Blue) y combinación/coordinación de ambas (Purple). |
| SOC | Security Operations Center | Equipo/centro que monitoriza y responde a incidentes de seguridad 24/7. |
| SIEM | Security Information and Event Management | Plataforma que centraliza y correla logs para detectar incidentes. |
| EDR | Endpoint Detection and Response | Solución que detecta y responde a amenazas en los equipos finales. |
| IDS / IPS | Intrusion Detection / Prevention System | Sistemas que detectan (IDS) o bloquean (IPS) actividad maliciosa. |
| WAF | Web Application Firewall | Firewall específico para filtrar ataques web (SQLi, XSS...). |
| MFA | Multi-Factor Authentication | Autenticación con más de un factor (contraseña + código/dispositivo). |
| IAM | Identity and Access Management | Gestión de identidades y permisos de acceso. |
| OWASP | Open Worldwide Application Security Project | Comunidad que publica estándares y el 'Top 10' de riesgos web. |
| OSCP / eJPT | Offensive Security Certified Professional / eLearnSecurity Junior Penetration Tester | Certificaciones de pentesting: eJPT (junior) y OSCP (referencia práctica avanzada). |

# **Normativa y cumplimiento**

| **Término** | **Significado** | **Definición** |
| --- | --- | --- |
| ISO/IEC 27001 | — | Estándar internacional para un Sistema de Gestión de la Seguridad de la Información (SGSI). |
| SGSI | Sistema de Gestión de la Seguridad de la Información | Marco de políticas y controles para gestionar la seguridad de forma continua. |
| ENS | Esquema Nacional de Seguridad | Normativa española de seguridad para el sector público y sus proveedores. |
| RGPD / GDPR | Reglamento General de Protección de Datos | Normativa europea de protección de datos personales. |
| PCI DSS | Payment Card Industry Data Security Standard | Estándar de seguridad para el tratamiento de datos de tarjetas de pago. |
| DORA | Digital Operational Resilience Act | Reglamento europeo de resiliencia operativa digital para el sector financiero. |
| NIS 2 | Network and Information Security Directive 2 | Directiva europea (2024) de ciberseguridad para sectores esenciales; actualiza la NIS 1. |
| TIBER-EU | Threat Intelligence-Based Ethical Red Teaming | Marco europeo de ejercicios de Red Team basados en inteligencia de amenazas (banca/seguros). |

# **Marcos de clasificación y puntuación (OWASP · CWE · CVE · CVSS)**

| **Término** | **Significado** | **Definición** |
| --- | --- | --- |
| OWASP Top 10 | Open Worldwide Application Security Project — Top 10 | Ranking de las diez categorías de riesgo más críticas en apps web; cada categoría agrupa varios CWE. Referencia estándar de auditoría (edición vigente 2025). |
| CWE | Common Weakness Enumeration | Catálogo de TIPOS genéricos de debilidad de software (MITRE): CWE-89 SQLi, CWE-22 Path Traversal, CWE-79 XSS. |
| CVE | Common Vulnerabilities and Exposures | Identificador público y único de una vulnerabilidad concreta en un producto (p. ej. CVE-2021-44228, Log4Shell). |
| CVSS | Common Vulnerability Scoring System | Puntuación de severidad de 0.0 a 10.0 (None/Low/Medium/High/Critical), mantenida por FIRST; sirve para priorizar. |
| NVD | National Vulnerability Database | Base de datos del NIST que enriquece cada CVE con su CWE, su CVSS y los productos afectados. |
| Tríada CIA | Confidentiality, Integrity, Availability | Los tres pilares de la seguridad: Confidencialidad, Integridad y Disponibilidad; base del impacto en CVSS. |
| searchsploit | — | Buscador local de exploits (Exploit-DB) por producto, versión o CVE. |
| Deserialización insegura | Insecure Deserialization | Procesar datos serializados no confiables, permitiendo ejecución de código o manipulación de objetos. |
| Supply chain | Cadena de suministro de software | Riesgos por dependencias, librerías o procesos de build/distribución comprometidos (OWASP A03:2025). |

# **Windows, Active Directory y credenciales**

| **Término** | **Significado** | **Definición** |
| --- | --- | --- |
| LLMNR / NBT-NS Poisoning | Link-Local Multicast Name Resolution / NetBIOS Name Service | Cuando Windows no resuelve por DNS hace broadcast; el atacante responde 'soy yo' y captura el hash de la víctima. |
| Responder | — | Herramienta que envenena LLMNR/NBT-NS/mDNS y captura hashes NTLMv2 en la red local. |
| NTLM / NTLMv1 / NTLMv2 | New Technology LAN Manager | Protocolos de autenticación de Windows; NTLMv2 es el reto-respuesta actual, crackeable por diccionario. |
| LM hash | LAN Manager hash | Hash heredado y muy débil de Windows antiguo (trivial de romper). |
| Kerberos / Kerberoasting | — | Autenticación de Active Directory; el Kerberoasting extrae tickets de servicio (TGS) para crackearlos offline. |
| WinRM / evil-winrm | Windows Remote Management | Servicio de administración remota de Windows (5985/5986); evil-winrm da una shell PowerShell con credenciales válidas. |
| /etc/hosts | — | Fichero de resolución de nombres local en Linux, con prioridad sobre el DNS; mapea dominios de CTF a su IP. |
| vhost fuzzing | Virtual host fuzzing | Descubrir subdominios enviando distintas cabeceras HTTP 'Host:' a la misma IP (no por DNS). |
| mDNS | Multicast DNS | Resolución de nombres en red local (Bonjour/Avahi), también abusable por Responder. |

# **Cloud, AWS y post-explotación en Linux**

| **Término** | **Significado** | **Definición** |
| --- | --- | --- |
| AWS S3 / Bucket | Amazon Simple Storage Service | Almacenamiento de objetos de AWS; un bucket mal configurado (público/escribible) es un vector frecuente. |
| LocalStack / MinIO | — | Emuladores de servicios AWS/S3 usados en laboratorios y desarrollo. |
| www-data | — | Cuenta de servicio con la que corre Apache en Linux; usuario limitado tras un RCE web, punto de partida para escalar. |
| GTFOBins | — | Catálogo de binarios Unix legítimos que pueden abusarse para escalar privilegios o evadir restricciones. |
| Kernel exploit | — | Exploit que aprovecha una vulnerabilidad del núcleo del SO para lograr privilegios de root. |
| sudo -l | — | Lista qué puede ejecutar un usuario con sudo; primer paso habitual de escalada en Linux. |

# **Ingeniería social, anonimato y cibercrimen**

| **Término** | **Significado** | **Definición** |
| --- | --- | --- |
| Ingeniería social | Social Engineering | Manipular a personas para que revelen información o realicen acciones inseguras. |
| Phishing / Smishing / QRishing | — | Ingeniería social por web/correo falso (phishing), SMS (smishing) o códigos QR maliciosos (QRishing). |
| GoPhish | — | Framework de campañas de phishing (plantillas, envío, captura de credenciales) para red team/concienciación. |
| IP logger | — | Servicio que, tras un clic, registra la IP y a veces la geolocalización; uso legítimo: atribución de un estafador. |
| VPS | Virtual Private Server | Servidor virtual alquilado donde se aloja contenido (p. ej. un sitio web). |
| Monero (XMR) | — | Criptomoneda orientada a la privacidad, sin trazabilidad pública en su blockchain. |
| RaaS / SaaS | Ransomware- / Software-as-a-Service | Modelo en el que uno desarrolla/vende la herramienta y otro (el operador) la usa y asume el riesgo. |
| Broker de acceso inicial | Initial Access Broker | Actor que vende accesos ya conseguidos (credenciales, RCE) a una víctima. |
| Calentamiento de dominio | Domain warming | Enviar correo progresivamente durante semanas para ganar reputación y evitar el marcado como spam. |
| ping sweep | Barrido de pings | Enviar ICMP a un rango para descubrir hosts vivos (netdiscover/nmap). |
| CIDR / Subnetting | Classless Inter-Domain Routing | Notación /24, /16, /8 que fija cuántos bits de la IP son de red; /0 abarca todas las direcciones. |

# **Inteligencia Artificial (bloque IA del máster)**

| **Término** | **Significado** | **Definición** |
| --- | --- | --- |
| IA / ML / DL | Inteligencia Artificial / Machine Learning / Deep Learning | IA es el campo general; ML aprende de datos; DL es ML con redes neuronales profundas. |
| Red neuronal | Neural network | Capas de neuronas conectadas por pesos numéricos que se ajustan durante el entrenamiento. |
| Neurona artificial | — | Multiplica entradas por pesos, suma, añade sesgo y aplica una función de activación. Inspirada en la biológica, no equivalente. |
| Peso / Sesgo | Weight / Bias | El peso gradúa la influencia entre neuronas; el sesgo se suma antes de la activación. Ambos se ajustan al entrenar. |
| Función de activación / pérdida | Activation / Loss | La activación decide la salida no lineal de una neurona; la pérdida mide cuánto se equivoca el modelo. |
| Backpropagation | Retropropagación | Propaga el error hacia atrás capa por capa para ajustar cada peso. |
| Descenso del gradiente | Gradient descent | Ajusta los pesos en la dirección que reduce el error. |
| Entrenamiento vs. Inferencia | Training vs. Inference | Entrenar ajusta pesos (costoso, una vez); inferir usa pesos ya fijos para predecir. |
| Aprendizaje supervisado / por refuerzo | Supervised / Reinforcement | Supervisado: ejemplos ya etiquetados. Por refuerzo: aprende por recompensa tras muchos intentos. |
| Dataset / Etiquetado | — | Conjunto de datos de entrenamiento; etiquetar es asignar a cada dato la respuesta correcta. |
| Train / Validation / Test | — | Partición del dataset para ajustar pesos, afinar diseño y medir el acierto final honesto. |
| Sobreajuste | Overfitting | El modelo memoriza el entrenamiento y falla con datos nuevos. |
| Modelo / Agente / Herramienta | — | El modelo predice; el agente persigue un objetivo usando herramientas en bucle; la herramienta es algo que el modelo invoca. |
| Token / Ventana de contexto | Token / Context window | El token es la unidad mínima de texto (mide el coste); la ventana de contexto es lo que el modelo tiene presente, no memoria permanente. |
| Embeddings | — | Representación vectorial de texto que captura significado para comparar/buscar. |
| Transformer / LLM | Large Language Model | El transformer es la arquitectura basada en atención; el LLM predice el siguiente token para generar texto. |
| Prompt | — | Instrucción/entrada al modelo; distinguir prompt de usuario y prompt de sistema. |
| Alucinación | Hallucination | Salida plausible pero falsa generada por un modelo. |
| RAG / Fine-tuning | Retrieval-Augmented Generation / Ajuste fino | RAG inyecta documentos en el contexto en inferencia (no cambia pesos); el fine-tuning reentrena y sí ajusta pesos. |
| GraphRAG / Grafo de conocimiento | Knowledge graph | Grafo de nodos y relaciones con significado explícito (Neo4j); GraphRAG lo usa como contexto para el modelo. |
| Envenenamiento de datos | Training data poisoning | Inyectar datos falsos/mal etiquetados en el dataset para que el modelo aprenda mal; eficaz si la muestra es representativa. |
| Correlación espuria | Shortcut learning | El modelo acierta por un patrón equivocado (caso lobo/husky: aprendió a detectar nieve). |
| Colapso del modelo | Model collapse | Degradación por entrenar recursivamente con contenido generado por modelos (datos sintéticos sin curar). |
| Human in the loop / XAI | — | Supervisión humana obligatoria en el ciclo; XAI (IA explicable): no basta con acertar, hay que saber por qué. |
| MCP / Vibe coding | Model Context Protocol | MCP conecta modelos con herramientas y datos externos; vibe coding es programar describiendo la intención y dejando que la IA genere el código. |
| Anonimización vs. Seudonimización | — | Anonimizar hace el dato irreversiblemente no reidentificable (fuera del RGPD); seudonimizar lo codifica de forma reversible (sigue siendo dato personal). |
| **✓ Documento vivo**  Este glosario crece con cada sesión. Cuando un apunte introduzca un término nuevo, se añade también aquí para mantener una referencia única del proyecto. |
