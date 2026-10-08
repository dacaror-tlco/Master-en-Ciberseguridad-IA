---
tags:
- Auditoría web
---

# Fuzzing Web

**EVOLVE ACADEMY · MÁSTER EN CIBERSEGURIDAD**

**Introducción al Fuzzing Web**

Automatizar el descubrimiento enviando entradas masivas a una aplicación web

**Instructor: Evolve Academy · Martes 23 (preparación previa a clase)**

*Temas: Fuzzing · ffuf · wfuzz · Wordlists · Keyword FUZZ · Filtrado de respuestas · Directorios · Vhosts · Parámetros · Login*

| **ℹ Sobre este documento**  Apunte de preparación técnica elaborado ANTES de la clase del martes 23, no a partir de una transcripción. Continúa de forma natural el apunte de Metodologías de Enumeración Web (lunes 22). Todo orientado a laboratorios autorizados y auditorías con contrato. Contrasta y amplía con lo que explique el instructor. |
| --- |

# **① Objetivos de la sesión**

- Entender qué es el **fuzzing** y en qué se diferencia de la enumeración manual.
- Dominar la mecánica del **keyword `FUZZ`** y de las **wordlists**.
- Usar **ffuf** para los cuatro casos principales: directorios, ficheros, vhosts y parámetros.
- Saber **filtrar respuestas** (por código, tamaño, palabras, líneas) para separar señal de ruido.
- Aplicar fuzzing a un **formulario de login** y entender sus límites éticos y legales.

# **② Conceptos clave**

**Fuzzing** es el envío automatizado de un gran número de entradas a una aplicación para observar cómo responde y descubrir comportamientos no documentados: rutas ocultas, parámetros válidos, valores aceptados o errores reveladores. En el contexto web, sustituyes una parte de la petición HTTP por cada palabra de una **wordlist** y analizas las respuestas.

| **ℹ Fuzzing vs enumeración**  La enumeración (lunes 22) es la estrategia: QUÉ buscar y en qué orden. El fuzzing es la TÉCNICA activa que lo ejecuta a gran escala. Enumerar directorios a mano es inviable; un fuzzer prueba miles de candidatos en segundos. |
| --- |

## **El keyword FUZZ y las wordlists**

La pieza central de ffuf es la palabra clave FUZZ: marcas en la petición el punto donde quieres inyectar, y la herramienta lo reemplaza por cada línea del diccionario.

| # FUZZ marca el punto de inyección; -w indica la wordlist  ffuf -u http://OBJETIVO/FUZZ -w /usr/share/seclists/Discovery/Web-Content/common.txt |
| --- |
| **Dónde pones FUZZ** | **Qué descubres** |
| En la ruta (/FUZZ) | Directorios y ficheros |
| En la cabecera Host (Host: FUZZ.x.com) | Virtual hosts / subdominios |
| En la query (?FUZZ=valor) | Nombres de parámetros ocultos |
| En el valor (?id=FUZZ) | Valores válidos de un parámetro |
| En el cuerpo POST (user=FUZZ) | Usuarios, credenciales, tokens |
| **✓ Wordlists en tu entorno**  En Parrot/Kali tienes SecLists en /usr/share/seclists/. Las más usadas en web: Discovery/Web-Content/ (rutas), Discovery/DNS/ (subdominios), Usernames/ y Passwords/ (login). Elegir la wordlist adecuada al contexto importa más que su tamaño. |

# **③ Flujo de un fuzzing efectivo**

| **1. Elegir punto FUZZ** |
| --- |
| **↓** |
| **2. Elegir wordlist** |
| **↓** |
| **3. Lanzar baseline** |
| **↓** |
| **4. Filtrar respuestas** |
| **↓** |
| **5. Analizar hits** |

El paso crítico es el cuarto: sin filtrado, la salida es una lista interminable de respuestas idénticas. La clave del fuzzing no es lanzar peticiones, es **distinguir la respuesta anómala** del ruido de fondo.

# **④ Filtrado de respuestas — el núcleo del fuzzing**

ffuf permite **filtrar** (ocultar) o **emparejar** (mostrar solo) respuestas según varios criterios. Primero observas la respuesta 'normal' (baseline) y luego filtras todo lo que se le parezca.

| **Flag** | **Filtra/empareja por** | **Ejemplo de uso** |
| --- | --- | --- |
| -fc | Código de estado | -fc 404 oculta los 404 |
| -fs | Tamaño en bytes | -fs 1234 oculta el tamaño de baseline |
| -fw | Nº de palabras | -fw 56 oculta respuestas con 56 palabras |
| -fl | Nº de líneas | -fl 10 oculta respuestas de 10 líneas |
| -mc | Empareja por código | -mc 200,301,302 solo muestra esos |
| **✗ El problema del baseline**  Muchas apps devuelven 200 OK para CUALQUIER ruta (página de error 'bonita'). Si filtras solo por -fc 404 no verás nada útil. Solución: lanza una petición a una ruta inexistente, mira su tamaño/palabras y filtra por -fs o -fw. |

# **⑤ Casos prácticos con ffuf**

## **Caso 1 — Directorios y ficheros**

| # Directorios; -mc para quedarte solo con códigos interesantes  ffuf -u http://OBJETIVO/FUZZ -w /usr/share/seclists/Discovery/Web-Content/raft-medium-directories.txt -mc 200,301,302,403  # Ficheros con extensiones según el stack (-e)  ffuf -u http://OBJETIVO/FUZZ -w /usr/share/seclists/Discovery/Web-Content/common.txt -e .php,.txt,.bak |
| --- |

## **Caso 2 — Virtual hosts**

| # Fuzzing de vhosts por cabecera Host; filtra el tamaño de baseline con -fs  ffuf -u http://OBJETIVO -H 'Host: FUZZ.OBJETIVO.com' -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt -fs 0 |
| --- |
| **ℹ Vhosts en HTB**  Caso muy frecuente en Hack The Box: una IP sirve varias webs según Host. Recuerda añadir el vhost descubierto a /etc/hosts para poder navegarlo. |

## **Caso 3 — Parámetros ocultos**

| # Nombres de parámetros GET; filtra por tamaño para detectar el que cambia la respuesta  ffuf -u 'http://OBJETIVO/page.php?FUZZ=1' -w /usr/share/seclists/Discovery/Web-Content/burp-parameter-names.txt -fs 1234 |
| --- |

## **Caso 4 — Login (fuerza bruta sobre formulario)**

| # POST con dos puntos de inyección no es el caso base: aquí fuzzeamos la password de un user conocido  ffuf -u http://OBJETIVO/login -X POST -d 'username=admin&password=FUZZ' -H 'Content-Type: application/x-www-form-urlencoded' -w /usr/share/seclists/Passwords/probable-v2-top1575.txt -fc 200 |
| --- |
| **⚠ Ataque en laboratorio — solo con autorización**  La fuerza bruta de credenciales solo es legítima en máquinas propias o entornos autorizados (HTB, labs). Contra sistemas reales sin contrato es un delito. Además bloquea cuentas y deja rastro evidente en logs. Hydra es la herramienta especializada para esto; ffuf sirve para casos web puntuales. |

# **⑥ Herramientas utilizadas en la sesión**

| **Herramienta** | **Objetivo** | **Fase de auditoría** | **Comando o uso visto** | **Nivel** | **Notas** |
| --- | --- | --- | --- | --- | --- |
| ffuf | Fuzzing web flexible | Enum. / explotación web | ffuf -u URL/FUZZ -w wl -fs N | Practicada | Herramienta central de la sesión |
| wfuzz | Fuzzing web (clásico) | Enum. web | wfuzz -w wl URL/FUZZ | Mencionada | Alternativa histórica a ffuf |
| SecLists | Colección de wordlists | Transversal | /usr/share/seclists/ | Practicada | Fuente de diccionarios |
| Hydra | Fuerza bruta de login | Acceso / credenciales | hydra -l user -P wl ... | Practicada | Especializada para auth |
| Feroxbuster | Rutas web recursivas | Enum. web | feroxbuster -u URL -w wl | Practicada | Complementa a ffuf |
| **✗ Nota sobre wfuzz**  wfuzz aparece como herramienta nueva a anotar (Mencionada). Cumple la misma función que ffuf pero es más antigua y lenta; ffuf es el estándar actual. Confirma en clase cuál prioriza el instructor. |

# **⑦ Riesgos, errores comunes y buenas prácticas**

- **No establecer baseline**: filtrar mal y no ver hits o ahogarte en falsos positivos.
- **Wordlist desproporcionada**: lanzar diccionarios enormes cuando uno pequeño y dirigido basta.
- **Demasiada concurrencia** (-t alto): tumbar el servicio en un lab compartido o ser detectado al instante.
- **Fuzzear fuera de scope**: cualquier petición a un host no autorizado es ilegal.

| **✓ Buena práctica**  Itera el filtrado: lanza, observa el baseline, ajusta -fs/-fw, vuelve a lanzar. Ajusta la velocidad (-t) y el rate (-rate) en entornos sensibles. Guarda los hits para reusarlos en la fase de explotación. |
| --- |

# **⑧ Conexión con sesiones anteriores**

- **Enumeración web (lunes 22)**: el fuzzing es la herramienta activa que ejecuta la metodología de enumeración. Misma teoría, ahora a escala y automatizada.
- **Hydra**: ya la conocías para fuerza bruta de servicios; aquí ves su equivalente web puntual con ffuf y dónde encaja cada una.
- **Marco mental de 4 elementos (sesión 25)**: fuzzear parámetros es localizar FUENTES que el servidor PROCESA — el paso previo a inyecciones (LFI, SQLi) que verás en el módulo de SQLi manual en unas semanas.

# **⑨ Resumen final**

El fuzzing web automatiza el descubrimiento sustituyendo una parte de la petición HTTP (marcada con FUZZ) por cada línea de una wordlist. Sirve para directorios, ficheros, virtual hosts, parámetros y valores, e incluso para fuerza bruta puntual de login. La herramienta de referencia es **ffuf**; wfuzz es la alternativa clásica. La habilidad real no está en lanzar peticiones, sino en **filtrar respuestas** (-fc, -fs, -fw, -fl, -mc) a partir de un baseline para distinguir el hallazgo del ruido. Y todo, siempre, dentro de un entorno autorizado.

# **⑩ Checklist de repaso**

- Sé explicar qué es el fuzzing y cómo se relaciona con la enumeración del lunes.
- Entiendo el keyword FUZZ y dónde colocarlo (ruta, Host, query, body).
- Sé elegir la wordlist adecuada de SecLists según el caso.
- Domino el filtrado: -fc, -fs, -fw, -fl y -mc, y sé establecer un baseline.
- Puedo fuzzear directorios, vhosts y parámetros con ffuf.
- Entiendo el caso de login y sus límites éticos/legales (solo labs autorizados).
- Sé cuándo usar ffuf y cuándo Hydra para credenciales.

# **⑪ Actualización del registro de herramientas**

| **Herramienta** | **Nivel propuesto** | **Cambio** |
| --- | --- | --- |
| ffuf | Practicada | Refuerzo como herramienta central de fuzzing |
| wfuzz | Mencionada | NUEVA — alternativa clásica a ffuf |
| SecLists | Practicada | Consolidar ubicación y categorías clave |
| Hydra | Practicada | Se mantiene; contraste con ffuf para login |
