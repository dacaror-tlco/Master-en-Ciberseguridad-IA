---
tags:
- Auditoría web
---

# Enumeracion Web

**EVOLVE ACADEMY · MÁSTER EN CIBERSEGURIDAD**

**Metodologías de Enumeración Web**

Reconocimiento y mapeo de aplicaciones web antes de la explotación

**Instructor: Evolve Academy · Lunes 22 (preparación previa a clase)**

*Temas: Enumeración web · Fingerprinting · Subdominios · Directorios y ficheros · Tecnologías · Endpoints · Metodología ordenada*

| **ℹ Sobre este documento**  Apunte de preparación técnica elaborado ANTES de la clase del lunes 22, no a partir de una transcripción. Sirve para llegar con la base montada. Todos los conceptos y comandos están orientados a laboratorios autorizados (Hack The Box, máquinas propias) y auditorías con contrato. Tras la clase conviene contrastar y ampliar con lo que explique el instructor. |
| --- |

# **① Objetivos de la sesión**

- Entender qué es la **enumeración web** y por qué es la fase que más determina el éxito de una auditoría web.
- Conocer una **metodología ordenada**: de lo pasivo a lo activo, de lo general a lo concreto.
- Saber identificar el **stack tecnológico** de una web (servidor, framework, CMS, lenguaje).
- Enumerar **subdominios, directorios, ficheros y parámetros** ocultos.
- Diferenciar enumeración de **fuzzing** (que se ve el martes 23) y entender cómo encajan.

# **② Conceptos clave**

La **enumeración web** es el proceso de descubrir toda la superficie de una aplicación web: qué tecnologías usa, qué rutas existen, qué ficheros están expuestos, qué subdominios hay y qué puntos de entrada (inputs) acepta. Es **reconocimiento dirigido**: no se explota nada todavía, se construye el mapa.

| **ℹ Idea central**  Cuanto más completo es el mapa, más superficie de ataque tienes. La mayoría de los hallazgos críticos (paneles de admin, backups .bak/.old, ficheros de configuración, endpoints de API) aparecen en esta fase, no explotando un 0-day. |
| --- |

## **Enumeración pasiva vs activa**

| **Tipo** | **Qué hace** | **Toca el objetivo** | **Ejemplos** |
| --- | --- | --- | --- |
| **Pasiva** | Recopila info sin enviar tráfico directo al objetivo | No (o mínimo) | WHOIS, DNS público, crt.sh, Google Dorks, Wayback Machine |
| **Activa** | Interactúa directamente con el servidor | Sí | Escaneo de directorios, fingerprinting, fuzzing de parámetros |
| **✗ Ruido y autorización**  La enumeración activa genera tráfico y queda en logs. En auditoría real puede disparar WAFs/IDS. Empieza siempre por lo pasivo y confirma el alcance (scope) antes de lanzar herramientas activas. |

# **③ Metodología de enumeración web (flujo recomendado)**

| **1. Recon pasivo** |
| --- |
| **↓** |
| **2. Fingerprint stack** |
| **↓** |
| **3. Subdominios** |
| **↓** |
| **4. Directorios/ficheros** |
| **↓** |
| **5. Endpoints/parámetros** |

El orden importa: cada fase alimenta a la siguiente. Identificar el CMS (fase 2) te dice qué wordlists usar al buscar directorios (fase 4); los subdominios encontrados (fase 3) se convierten en nuevos objetivos que vuelves a fingerprintear.

## **Fase 1 — Reconocimiento pasivo**

Antes de tocar el servidor, recopila lo que ya es público:

- **Certificados TLS** (crt.sh): revelan subdominios incluidos en el certificado.
- **Wayback Machine**: rutas y ficheros antiguos que quizá sigan accesibles.
- **Google Dorks**: site:objetivo.com filetype:pdf, inurl:admin, etc. (visto en la sesión de OSINT de Superficie).

| **ℹ Conexión con OSINT**  Esta fase es directamente la metodología OSINT de superficie que ya trabajaste: Google Dorks, Shodan y consultas DNS. La enumeración web es OSINT aplicado a un dominio concreto, ya dentro del scope. |
| --- |

## **Fase 2 — Fingerprinting del stack tecnológico**

Identifica servidor web, lenguaje, framework y CMS. Esto condiciona toda la estrategia posterior.

| # WhatWeb: identifica tecnologías de una web  whatweb -a 3 http://OBJETIVO  # Cabeceras HTTP a mano con curl (Server, X-Powered-By, Set-Cookie)  curl -sI http://OBJETIVO |
| --- |

- **Wappalyzer** (extensión de navegador): equivalente visual, muy rápido para una primera ojeada.
- Pistas útiles: cabecera Server, X-Powered-By, nombre de las cookies (PHPSESSID, JSESSIONID, laravel\_session), extensiones de fichero (.php, .aspx, .jsp).

| **✓ Por qué importa el CMS**  Si detectas WordPress, el siguiente paso natural es WPScan (auditoría web dinámica, perfil junior más demandado). Cada CMS tiene rutas y vulnerabilidades típicas conocidas. |
| --- |

## **Fase 3 — Enumeración de subdominios**

Cada subdominio es una web potencialmente distinta y un nuevo objetivo. Combina fuentes pasivas con resolución activa.

| # Subfinder: subdominios desde fuentes pasivas  subfinder -d OBJETIVO.com -o subdominios.txt  # ffuf por fuzzing de subdominios vía cabecera Host (vhosts)  ffuf -u http://OBJETIVO -H 'Host: FUZZ.OBJETIVO.com' -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt |
| --- |
| **ℹ Virtual hosts en laboratorio**  En HTB es muy habitual que la IP sirva varias webs según la cabecera Host. Si una web responde igual ante cualquier Host, filtra por tamaño de respuesta (-fs) para descartar el falso positivo. El fuzzing de vhosts se profundiza el martes 23. |

## **Fase 4 — Enumeración de directorios y ficheros**

Descubre rutas no enlazadas: paneles, backups, ficheros de configuración, directorios de subida.

| # Feroxbuster: descubrimiento recursivo de rutas  feroxbuster -u http://OBJETIVO -w /usr/share/seclists/Discovery/Web-Content/raft-medium-directories.txt  # Gobuster: con extensiones concretas según el stack detectado  gobuster dir -u http://OBJETIVO -w /usr/share/seclists/Discovery/Web-Content/common.txt -x php,txt,bak,old |
| --- |
| **Herramienta** | **Punto fuerte** |
| **Feroxbuster** | Recursividad automática, muy rápido, ideal para mapear toda la estructura |
| **Gobuster** | Sencillo y directo, control fino de extensiones con -x |
| **ffuf** | El más flexible: directorios, ficheros, vhosts y parámetros con el keyword FUZZ |
| **Dirsearch** | Trae diccionarios y extensiones por defecto bien pensados |
| **✗ Errores comunes**  Lanzar el diccionario equivocado (rutas de IIS contra un servidor Apache/PHP), no filtrar códigos de respuesta y ahogarte en 404, u olvidar las extensiones (-x) acordes al lenguaje detectado en la fase 2. |

## **Fase 5 — Endpoints y parámetros**

El último nivel: descubrir parámetros GET/POST ocultos y endpoints de API que reciben entrada de usuario. Son los futuros puntos de inyección (LFI, SQLi, etc.).

| # Descubrir parámetros GET ocultos con ffuf  ffuf -u 'http://OBJETIVO/index.php?FUZZ=test' -w /usr/share/seclists/Discovery/Web-Content/burp-parameter-names.txt -fs 0 |
| --- |
| **ℹ Marco mental de 4 elementos**  Cada parámetro descubierto es una FUENTE (sesión 25): una entrada que el servidor PROCESA. Identificarlos aquí es localizar dónde podrás atacar después. |

# **④ Herramientas utilizadas en la sesión**

| **Herramienta** | **Objetivo** | **Fase de auditoría** | **Comando o uso visto** | **Nivel** | **Notas** |
| --- | --- | --- | --- | --- | --- |
| WhatWeb | Fingerprint de tecnologías | Enum. web | whatweb -a 3 URL | Introducida | Ya aparecía en sesiones previas |
| Wappalyzer | Fingerprint visual | Enum. web | Extensión navegador | Introducida | Complemento rápido de WhatWeb |
| Subfinder | Subdominios pasivos | Enum. web | subfinder -d dominio | Mencionada | Herramienta NUEVA en esta sesión |
| Feroxbuster | Rutas web recursivas | Enum. web | feroxbuster -u URL -w wl | Practicada | Recursividad automática |
| Gobuster | Directorios/ficheros | Enum. web | gobuster dir -u URL -x php | Practicada | Control de extensiones |
| ffuf | Fuzzing flexible | Enum. web | ffuf -u URL/FUZZ -w wl | Practicada | Vhosts y parámetros |
| Dirsearch | Directorios con dicc. propio | Enum. web | dirsearch -u URL | Mencionada | Diccionarios por defecto |
| curl | Cabeceras HTTP | Enum. web | curl -sI URL | Practicada | Fingerprint manual |
| **✗ Nota sobre Subfinder**  Subfinder no estaba en tu registro previo: es una herramienta nueva a anotar. Mencionada en este material de preparación; confirma en clase los flags y fuentes que recomienda el instructor antes de marcarla como Practicada. |

# **⑤ Riesgos, errores comunes y buenas prácticas**

- **Saltarse el recon pasivo** y atacar a ciegas: pierdes subdominios y contexto.
- **No respetar el scope**: enumerar subdominios o IPs fuera de contrato es ilegal.
- **Ignorar el fingerprint**: usar wordlists genéricas en vez de las del stack real reduce muchísimo los hallazgos.
- **No filtrar respuestas** (-fs, -fc): el ruido de 404/redirecciones esconde lo importante.

| **✓ Buena práctica**  Guarda la salida de cada fase en ficheros (estructura recon/ vista en la sesión 25). La enumeración es iterativa: cada subdominio nuevo reinicia el ciclo fingerprint → directorios → parámetros. |
| --- |

# **⑥ Conexión con sesiones anteriores**

Esta sesión enlaza directamente con varias anteriores:

- **OSINT de Superficie**: la fase pasiva (Dorks, DNS, crt.sh) es OSINT aplicado dentro del scope.
- **Nmap (sesión 25 y otras)**: Nmap descubre el puerto/servicio web; la enumeración web empieza justo donde Nmap termina (puerto 80/443 abierto).
- **Marco mental de 4 elementos**: cada parámetro/endpoint enumerado es una FUENTE que el servidor PROCESA.
- **Fuzzing (martes 23)**: la enumeración define dónde fuzzear; el fuzzing es la técnica activa para hacerlo a fondo.

# **⑦ Resumen final**

La enumeración web es el mapa previo a cualquier ataque: de lo **pasivo a lo activo** y de lo **general a lo concreto**. Cinco fases encadenadas — recon pasivo, fingerprint del stack, subdominios, directorios/ficheros y endpoints/parámetros — que se retroalimentan. El stack detectado decide las wordlists; los subdominios generan nuevos objetivos; los parámetros descubiertos son los futuros puntos de inyección. Hacerla bien y de forma ordenada (guardando salidas) es lo que separa una auditoría web productiva de un ataque a ciegas.

# **⑧ Checklist de repaso**

- Sé explicar la diferencia entre enumeración pasiva y activa, y por qué empezar por la pasiva.
- Puedo hacer fingerprint de un stack con WhatWeb y leer cabeceras con curl -sI.
- Sé enumerar subdominios con Subfinder y por fuzzing de vhosts con ffuf.
- Domino Feroxbuster/Gobuster/ffuf para directorios y sé ajustar extensiones según el stack.
- Entiendo cómo descubrir parámetros ocultos y por qué son puntos de inyección.
- Sé filtrar respuestas (-fs/-fc) para reducir ruido.
- Tengo claro cómo encadena la enumeración con el fuzzing del martes 23.

# **⑨ Actualización del registro de herramientas**

Para copiar a tu base de conocimiento tras validar en clase:

| **Herramienta** | **Nivel propuesto** | **Cambio** |
| --- | --- | --- |
| Subfinder | Mencionada | NUEVA — enumeración de subdominios pasiva |
| WhatWeb | Introducida | Se mantiene |
| Wappalyzer | Introducida | Se mantiene |
| Feroxbuster | Practicada | Refuerzo en contexto de metodología |
| ffuf | Practicada | Refuerzo (vhosts y parámetros) |
| Dirsearch | Mencionada | Se mantiene hasta uso práctico |
