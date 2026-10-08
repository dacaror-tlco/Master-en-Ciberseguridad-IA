---
tags:
- Auditoría web
date: '2026-07-16'
author: Carlos Castillo
---

# PortSwigger Introduccion y Path Traversal

<p class="note-meta">2026-07-16 · Carlos Castillo</p>

**EVOLVE ACADEMY · MÁSTER EN CIBERSEGURIDAD OFENSIVA**

**PortSwigger Web Security Academy**

**Introducción y repaso de Path Traversal**

Instructor: Carlos Castillo · 16/07/2026 · Nivel intermedio

Alumno: Chema — José Manuel Mármol Arjona

# **1. Objetivos de aprendizaje**

- Comprender qué es **PortSwigger Web Security Academy** y cómo se organiza (artículos teóricos, *learning paths* y laboratorios).
- Diferenciar la **teoría** de los **laboratorios prácticos** y entender por qué los labs son el núcleo del aprendizaje.
- Repasar en profundidad el **Path Traversal**: qué es, por qué ocurre y cómo se relaciona la web con el sistema de archivos del servidor.
- Aprender a **identificar parámetros** que hacen referencia a archivos y a reconocer las señales de un posible Path Traversal.
- Recorrer los **6 casos** de Path Traversal de PortSwigger: básico, ruta absoluta, secuencias anidadas, URL encoding, doble URL encoding, restricción por directorio inicial y por extensión (null byte).
- Interiorizar las principales **técnicas de evasión de filtros** y sus límites (ninguna es universal).
- Construir una **checklist personal** de comprobación de Path Traversal reutilizable en máquinas de Hack The Box y auditorías reales.
- Conocer, a nivel informativo, la certificación **BSCP** de PortSwigger.

# **2. Resumen de la sesión**

Esta sesión abre el bloque de **seguridad web** apoyado en **PortSwigger Web Security Academy**, la plataforma educativa gratuita de la empresa que desarrolla **Burp Suite**. PortSwigger reúne casi todas las vulnerabilidades web (SQL Injection, XSS, CSRF, XXE, Path Traversal, etc.) organizadas en *learning paths*, con artículos teóricos y, sobre todo, **laboratorios** interactivos que se generan en la nube con su propia URL.

El profesor deja clara la filosofía del módulo: **el valor está en los laboratorios**, no en leerse toda la teoría. Los labs de una misma vulnerabilidad van *de menos a más* — no en dificultad de enumeración, sino en la cantidad de **casos y contextos** (validaciones y filtros del lado servidor). Practicar todas esas casuísticas construye un **mapa mental** que permite reconocer una vulnerabilidad y saber qué probar cuando aparece en un entorno real.

El grueso técnico es un **repaso completo de Path Traversal** a través de los laboratorios de PortSwigger, recorriendo seis casos que van desde la explotación trivial sin validación hasta bypasses con secuencias anidadas, *URL encoding* simple y doble, restricción por directorio inicial y truncado con *null byte*. Se enfatiza una idea recurrente: **casi nunca sabemos qué hace el servidor por detrás** (si bloquea, elimina o transforma la entrada) salvo que tengamos el código fuente, así que se razona por prueba y error sobre el comportamiento observado.

La sesión cierra conectando Path Traversal con **LFI** (Local File Inclusion) como paso siguiente: una vez se puede leer un archivo arbitrario, el objetivo pasa a localizar archivos de configuración, credenciales o claves privadas (id\_rsa) que permitan avanzar.

| **ℹ Idea central de la clase**  PortSwigger permite trabajar la misma vulnerabilidad en muchos contextos distintos. Esa variedad es justo lo que cuesta al principio en un entorno real: no saber si estás lanzando bien el ataque, si la app no es vulnerable o si está bien sanitizada. Los labs entrenan ese criterio. |
| --- |

# **3. PortSwigger Web Security Academy**

**PortSwigger** es la empresa creadora de **Burp Suite**, la herramienta de referencia para pentesting web. Su plataforma educativa, **Web Security Academy**, es gratuita y cubre la mayoría de vulnerabilidades web con material teórico y laboratorios prácticos.

La estructura se divide en dos grandes partes: la sección **Academy** (teoría y *learning paths*) y la sección **Labs** (laboratorios). En clase el foco se pone en los **laboratorios**, que se generan bajo demanda con conexión a Internet y una URL propia por alumno (similar a cómo se despliega una máquina en Hack The Box).

Cada laboratorio incluye la **solución oficial** y, en muchos casos, un **vídeo** resolviéndolo. La teoría está en inglés; se puede traducir, aunque la traducción automática a veces distorsiona los términos técnicos.

## **3.1 Elementos de la plataforma**

| **Elemento** | **Función** | **Utilidad para el estudiante** |
| --- | --- | --- |
| Learning paths | Rutas de aprendizaje que agrupan vulnerabilidades por temática (SQLi, XSS, API, etc.). | Orientan el orden de estudio; útiles para quien va más avanzado o quiere especializarse. |
| Artículos teóricos | Explicación conceptual de cada vulnerabilidad con ejemplos. | Refuerzo de apoyo. No se leen en clase; sirven para repasar o aclarar dudas puntuales. |
| Laboratorios (Labs) | Entornos prácticos explotables, uno por caso/contexto de la vulnerabilidad. | El núcleo. Permiten practicar muchas casuísticas de una misma vulnerabilidad. |
| Burp Suite | Herramienta con la que se interceptan y manipulan las peticiones de los labs. | Imprescindible: Proxy para interceptar, Repeater para probar variantes, Intruder para fuzzing. |
| Seguimiento de progreso | Marca los labs resueltos (estado 'Solved'). | Sirve de checklist de avance; la BSCP exige tenerlos completados. |

## **3.2 Progresión de dificultad en los labs**

Dentro de una misma vulnerabilidad, los laboratorios usan **la misma página web** (idéntica y sencilla) y solo cambia la **lógica de validación del servidor**. Así se aísla el concepto: no hay que rehacer enumeración ni fase de reconocimiento, solo entender qué filtro aplica el backend y cómo evadirlo. Esto los hace **microretos** ligeros frente a la densidad de una máquina de Hack The Box.

| **⚠ Buena práctica de estudio**  El profesor insiste: rellenar todos los labs 'por rellenar' no es aprender. El objetivo es que haga *clic* en la cabeza el porqué de cada caso. Completar labs copiando la solución no prepara para una auditoría real ni para un examen sin ayuda. |
| --- |

# **4. Vulnerabilidades web mencionadas**

Durante la sesión se citaron varias vulnerabilidades para ubicar el catálogo de PortSwigger. Solo se desarrolla **Path Traversal**; el resto se mencionan como referencia o como contenido futuro del módulo.

| **Vulnerabilidad** | **Descripción breve** | **¿Se desarrolla hoy?** |
| --- | --- | --- |
| Path Traversal | Acceso a archivos y directorios fuera del directorio previsto por la aplicación. | Sí — tema central |
| LFI | Local File Inclusion: inclusión/lectura de archivos locales del servidor. Paso natural tras Path Traversal. | Introducido |
| RFI | Remote File Inclusion: inclusión de archivos remotos. | Mencionada |
| SQL Injection | Inyección de consultas SQL. Se anticipa que se verá 'la semana que viene', incluyendo Blind SQLi. | No (futuro) |
| Cross-Site Scripting (XSS) | Inyección de scripts en el navegador de la víctima. | No (ya visto / futuro) |
| CSRF | Cross-Site Request Forgery: forzar acciones no deseadas en sesión autenticada. | No (futuro) |
| Clickjacking | Engaño visual con capas/iframes. 'Relleno de informe', se verá muy por encima. | No |
| XXE | XML External Entity. Referida como ejemplo ya trabajado en clase. | No (ya visto) |
| OS Command Injection | Ejecución de comandos del SO desde la aplicación. | No (futuro) |
| File Upload | Subida de archivos maliciosos. | No (futuro) |
| WebSockets | Vulnerabilidades sobre el protocolo WebSocket (pocos labs). | No (autoestudio) |
| Prototype Pollution | Contaminación de prototipos en JavaScript. Nivel avanzado. | No (autoestudio) |
| **ℹ NOTA**  Este punto no aparece cerrado en el material: el reparto exacto de qué vulnerabilidades se verán en clase y cuáles quedan para autoestudio se decidirá según el ritmo del grupo en las semanas restantes. |

# **5. Fundamentos de Path Traversal**

El **Path Traversal** (o *Directory Traversal*, 'recorrido de directorios') es una vulnerabilidad que permite a un atacante **leer archivos y directorios fuera del directorio previsto** por la aplicación. Ocurre cuando una aplicación web recibe, en un parámetro, un **nombre de archivo** que usa para construir una ruta en el sistema de archivos del servidor **sin validar correctamente** esa entrada.

La clave conceptual: una imagen o documento que muestra la web **no está en el aire**, está en el servidor. La aplicación hace, por detrás, una **llamada a un archivo** dentro de una ruta. Si podemos manipular esa ruta, podemos intentar salir del directorio previsto y alcanzar archivos sensibles del sistema.

## **5.1 Cómo se construye la ruta**

Supongamos una petición que carga una imagen:

| https://ejemplo.local/image?filename=218.png |
| --- |

Por detrás, el servidor concatena ese filename a una **ruta base** para construir la **ruta final**:

| /var/www/images/218.png |
| --- |

Si la entrada no se valida, un valor manipulado con secuencias ../ (directorio padre) puede **remontar** hacia directorios superiores hasta alcanzar, por ejemplo, /etc/passwd:

| ../../../etc/passwd |
| --- |
| **⚠ AVISO**  El resultado depende de cómo esté programada la aplicación, de los permisos del proceso, del sistema operativo y de las medidas de seguridad aplicadas. Que exista un parámetro con nombre de archivo NO garantiza que sea vulnerable. |

## **5.2 Por qué /etc/passwd**

/etc/passwd es el archivo de prueba habitual en Linux porque es **legible por cualquier usuario** y su presencia confirma lectura de archivos arbitrarios. Contiene la **lista de usuarios** del sistema (no las contraseñas, que están en /etc/shadow).

| **ℹ Matiz importante (de clase)**  Cuidado con la expectativa: /etc/passwd no da credenciales. Da enumeración de usuarios, shells asignadas y, según permisos, pistas del sistema. Las contraseñas hash viven en /etc/shadow, normalmente solo legible por root. |
| --- |

## **5.3 Impacto**

La lectura de archivos arbitrarios es **crítica**: permite enumerar usuarios, leer archivos de configuración con credenciales, exfiltrar claves privadas SSH (id\_rsa), etc. En una auditoría real, esta vulnerabilidad suele puntuar de **7 para arriba** (alta o crítica) según el contexto.

# **6. Rutas relativas y absolutas**

Entender la diferencia entre ruta relativa y absoluta es esencial para Path Traversal, porque algunos servidores bloquean una y no la otra.

| **Concepto** | **Linux** | **Windows** | **Ejemplo** |
| --- | --- | --- | --- |
| Ruta absoluta | Empieza en la raíz /. Es la ruta completa desde el inicio del sistema. | Empieza por letra de unidad, p. ej. C:\. | /etc/passwd |
| Ruta relativa | Se resuelve desde el directorio actual, usando ./ y ../. | Igual, con separador \. | ../../../etc/passwd |
| Directorio actual | El directorio desde el que se resuelve la ruta. | Ídem. | . |
| Directorio padre | Sube un nivel en la jerarquía. | Ídem. | .. |
| Separador habitual | Barra /. | Barra invertida \ (aunque / suele funcionar). | / vs \ |
| **ℹ NOTA**  Cuando una petición empieza con /, se le está diciendo al sistema que arranque **desde la raíz**, ignorando el directorio de trabajo. Por eso una ruta absoluta puede evadir filtros que solo vigilan las secuencias ../. |
| **ℹ Ampliación técnica**  **Ampliación técnica: normalización y canonicalización.** Antes de acceder al archivo, muchos sistemas *normalizan* la ruta (resuelven los . y .. y colapsan barras repetidas) o la *canonicalizan* (obtienen la ruta real definitiva). Un filtro que actúa **antes** de normalizar y solo elimina una vez las secuencias ../ es justamente el que se evade con las técnicas de los casos 3 a 6. |

# **7. Identificación de posibles puntos vulnerables**

El primer paso — y el que más cuesta al principio — es **saber detectar** dónde puede haber Path Traversal. La señal es un parámetro que provoca una **llamada a un archivo** que podría estar contenido en una ruta del servidor. Parámetros típicos a vigilar:

| ?filename=  ?file=  ?image=  ?document=  ?path=  ?template=  ?download=  ?page= |
| --- |

Señales que deberían **activar la hipótesis** de Path Traversal:

- La respuesta muestra una imagen o un documento.
- El parámetro contiene un nombre de archivo o una extensión (.png, .jpg, .pdf, .txt).
- El servidor devuelve errores relacionados con rutas o archivos (p. ej. *invalid product ID*, *file not found*).
- El comportamiento cambia al modificar el parámetro.
- La aplicación descarga o renderiza archivos.

## **7.1 Cuidado: parámetros que NO son Path Traversal**

En el primer laboratorio de la clase, la página tenía un parámetro productId=15 en /product?productId=15. Es **iterable** (cambiar el número muestra otro producto) pero **no accede a archivos**: es una simple selección de registro. El profesor lo contrastó así en pizarra:

| **Parámetro** | **Qué hace por detrás (nivel programación)** | **¿Path Traversal?** |
| --- | --- | --- |
| productId | Itera sobre un número, del 1 al 100. Piénsalo como un for (1..100): selecciona un registro. | No |
| filename | Accede a archivos dentro de una ruta, p. ej. /var/www/html/images/x.jpg. Es una llamada a fichero. | Sí (candidato) |

La diferencia real: uno accede a la **base de datos / lógica** (número de registro) y el otro accede al **sistema de archivos** del servidor. Solo el segundo puede permitir salir del directorio hacia /etc/passwd.

| **ℹ Lección del Lab 1**  La imagen se cargaba mediante una petición **en segundo plano** a /image?filename=9.jpg, que no era visible en la barra del navegador. Se descubrió haciendo *forward* en Burp Proxy. Muchas peticiones (imágenes, favicon, recursos) ocurren por detrás: revísalas en Burp o en la pestaña 'Red' del inspector. |
| --- |
| **⚠ AVISO**  No te fíes solo de las extensiones. A veces el backend guarda los archivos **sin extensión** (9) y añade .jpg por su cuenta al construir la ruta. Ver .jpg en el parámetro no confirma que ese sea el nombre real en disco, ni al revés. |

# **8. Casuísticas y evasión de filtros — los 6 casos**

El corazón de la clase. Todos los laboratorios usan la misma web; solo cambia la validación del servidor. Para cada caso: qué intenta bloquear la app, qué prueba el auditor, qué se observa y qué se concluye. **Metodología común de arranque** en Burp Repeater:

| **1. Localizar la petición que llama al archivo (p. ej. /image?filename=9.jpg)** |
| --- |

**↓**

| **2. Enviarla a Repeater (clic derecho → Send to Repeater)** |
| --- |

**↓**

| **3. Guardar una respuesta base (imagen que carga bien)** |
| --- |

**↓**

| **4. Modificar SOLO el parámetro filename con cada variante** |
| --- |

**↓**

| **5. Comparar código de estado, longitud y contenido de la respuesta** |
| --- |

## **8.1 Caso 1 — Básico, sin validación**

La aplicación no valida nada. Se remonta con ../ y se accede directamente al archivo objetivo.

| ../../../etc/passwd |
| --- |

**Qué observar:** la respuesta devuelve el contenido de /etc/passwd en lugar de la imagen. PortSwigger detecta la lectura en sus logs y marca el lab como *Solved*.

| **⚠ RIESGO**  En este caso funcionan **tanto** ../../../etc/passwd **como** /etc/passwd: al no haber validación, la relativa y la absoluta valen igual. Es el escenario más inseguro. |
| --- |

## **8.2 Caso 2 — Bloqueo de ../ → usar ruta absoluta**

El servidor **bloquea** las secuencias ../ (no sabemos si las elimina, las reemplaza o rechaza la petición: sin el código fuente nunca lo sabremos con certeza). Por tanto la ruta relativa falla:

| ../../../etc/passwd → bloqueado / no encuentra el archivo |
| --- |

Pero al detectar una **ruta absoluta**, el backend a veces se 'ciega' y accede directamente, saltándose la concatenación con la ruta base. Solución:

| /etc/passwd |
| --- |
| **⚠ AVISO**  Paradoja del caso 2: este laboratorio es **más seguro** que el Caso 1 (bloquea ../), pero sigue siendo vulnerable porque no sanitiza bien la ruta absoluta. Se ve poco en la práctica: si fuera común, /etc/passwd funcionaría en casi todas las webs. |

## **8.3 Caso 3 — Eliminación de secuencias → anidar ../**

El filtro **elimina** las secuencias ../ de la entrada, pero lo hace de forma **no recursiva** (una sola pasada). La idea: si intercalas las secuencias, al borrar la interior lo que queda **recompone** una ../ válida. Se prueba anidando:

| ....//....//....//etc/passwd |
| --- |

**Razonamiento (bajado a tierra, tal como lo explicó el profesor):** el filtro recibe ....//, localiza y **elimina** el ../ que reconoce en el centro, y con los caracteres que sobran a los lados se vuelve a formar ../. Lo que **realmente llega** al servidor no es lo que enviaste, sino la versión ya 'limpiada' por el filtro:

| **1. Envío ....//....//....//etc/passwd** |
| --- |

**↓**

| **2. El filtro elimina cada ../ interior (una sola pasada)** |
| --- |

**↓**

| **3. Lo que queda se recompone como ../../../etc/passwd** |
| --- |

**↓**

| **4. Esa secuencia sí es válida → acceso al archivo** |
| --- |
| **ℹ NOTA**  Nunca envías directamente algo que 'funcione en una terminal'. Envías una petición que pasa por un filtro en el backend y **luego** llega al servidor. Piensa en qué queda *después* del filtro, no en lo que escribes. |
| **⚠ AVISO**  Ojo con no confundir este caso con el Caso 2. En el Caso 2 basta la ruta absoluta /etc/passwd; aquí el filtro **sí** elimina las ../, y el truco es que las anidas para que, tras el borrado, vuelva a quedar una ../ que remonta hasta /etc/passwd. |

## **8.4 Caso 4 — URL encoding**

El filtro bloquea los caracteres ../ en texto plano, pero **no** su versión codificada. Se aprovecha que la URL interpreta igual el carácter codificado que el literal. Codificación de cada carácter:

| **Carácter** | **URL encode** | **Significado** |
| --- | --- | --- |
| . (punto) | %2e | Codificación del punto. |
| / (barra) | %2f | Codificación de la barra. |
| ../ | %2e%2e%2f | Secuencia de traversal codificada completa. |

En Burp se usa el **Decoder** (Encode as → URL) o el atajo *Ctrl+U* sobre la selección. Payload:

| %2e%2e%2f%2e%2e%2f%2e%2e%2fetc/passwd |
| --- |
| **⚠ AVISO**  URL encoding **no es cifrado**. Es solo una representación alternativa del mismo carácter que la URL entiende de forma nativa. Confundir encoding con cifrado es un error frecuente. |

## **8.5 Caso 5 — Doble URL encoding**

El backend **decodifica una vez** antes de aplicar el filtro. Si envías ../ con un solo encode, al decodificarlo el filtro lo detecta. La solución es codificar **dos veces**, de modo que tras la primera decodificación quede una secuencia codificada que el filtro ya no reconoce, y una segunda decodificación posterior la convierta en ../ cuando ya ha pasado el control.

| %252e%252e%252f%252e%252e%252fetc/passwd |
| --- |

Aquí %25 es el carácter % codificado. Es decir, %252e → (decodifica) → %2e → (decodifica) → .

| **1. Envío %252e%252e%252f (doble encode)** |
| --- |

**↓**

| **2. Backend decodifica 1 vez → %2e%2e%2f (aún codificado, el filtro NO lo detecta)** |
| --- |

**↓**

| **3. Pasa el filtro sin ser reconocido como ../** |
| --- |

**↓**

| **4. Segunda decodificación → ../ ya dentro → acceso al archivo** |
| --- |

**Escalera de decodificación (esquema del profesor).** La clave es cuántas veces decodifica el backend antes de validar. Cada envío se compara con lo que 've' el filtro:

| **Envío** | **Lo que hace el backend** | **Resultado en el filtro** |
| --- | --- | --- |
| ../ normal (sin encode) | Lo recibe tal cual. | **Detectado** (bloqueado) |
| URL x1 (%2e%2e%2f) | Decodifica 1 vez → ../ | **Detectado** (bloqueado) |
| URL x2 (%252e%252e%252f) | Decodifica 1 vez → queda %2e%2e%2f (aún codificado) | **No detectado** → pasa |
| URL x3 | Decodifica, decodifica → queda %2e%2e%2f en la fase de validación | **No detectado** → pasa |

Es decir: hay que **encodear una vez más** de las que el backend decodifica **antes** de validar. Si valida tras 1 decodificación, con doble encode basta; si decodifica dos veces antes de validar, hará falta triple.

| **ℹ NOTA**  Esta técnica solo es relevante cuando existen **varias fases de decodificación**. No sabemos cuántas hace la app: prueba 1, 2 y como mucho 3 veces. Codificar 200 veces no tiene sentido. Cada nivel de encode que hace falta delata una capa más de decodificación mal diseñada. |
| --- |

## **8.6 Caso 6a — Restricción por directorio inicial**

La aplicación exige que la ruta **comience** por un directorio concreto (p. ej. la carpeta de imágenes). Valida el **inicio** pero no el resto, así que se cumple el prefijo y luego se remonta:

| /var/www/images/../../../etc/passwd |
| --- |

**Razonamiento:** el primer ../ sale de images, el segundo de www, el tercero de var — quedando en la raíz para bajar a /etc/passwd. El truco es **conocer la ruta base inicial**, que en este lab se da fácil, pero en un caso real habría que descubrirla (por un error, otra vulnerabilidad que la filtre, etc.).

| **✓ Perspectiva defensiva**  Como planteó una alumna (perfil desarrolladora): la defensa correcta sería validar que la ruta final **permanezca dentro** del directorio autorizado tras normalizar, no solo comprobar el prefijo del inicio. |
| --- |

## **8.7 Caso 6b — Restricción por extensión → null byte**

La aplicación exige que la ruta **termine** en una extensión concreta (p. ej. .png). Se evade con un **null byte** (%00), que trunca la cadena: el filtro ve que termina en .png y lo aprueba, pero al llegar al sistema el byte nulo corta la cadena y descarta todo lo que va después.

| ../../../etc/passwd%00.png |
| --- |
| **1. Envío ../../../etc/passwd%00.png** |

**↓**

| **2. Backend valida: termina en .png → OK** |
| --- |

**↓**

| **3. Llega al servidor: el null byte (%00) trunca la cadena** |
| --- |

**↓**

| **4. Queda ../../../etc/passwd → acceso al archivo** |
| --- |
| **⚠ AVISO**  **El null byte NO es una técnica universal ni garantizada.** Su efectividad depende del lenguaje, la API y la **versión** utilizada; en la mayoría de entornos modernos ya no funciona (se corrigió hace años en PHP y otros). Se estudia por su valor conceptual e histórico y porque aún aparece en sistemas antiguos. |
| **ℹ NOTA**  Otros bypasses de extensión mencionados de pasada: ciertos **caracteres especiales** (incluidos algunos caracteres multibyte) pueden interpretarse como separadores. Se ven menos; todo depende de cuántas barreras haya puesto el desarrollador. |

## **8.8 Qué probar cuando nada funciona: diccionarios**

Si la comprobación manual de los 6 casos no da resultado, se recurre a **fuzzing** con diccionarios de Path Traversal (existen muchos en **SecLists**, dentro de Fuzzing/, y también se pueden generar con IA). Se cargan en **Burp Intruder** sobre el parámetro. Ruta de referencia en SecLists para LFI:

| /usr/share/seclists/Fuzzing/LFI/ (payloads de Path Traversal y rutas por defecto Linux/Windows) |
| --- |
| **⚠ Ruido y rate limiting**  Los labs de PortSwigger **bloquean la fuerza bruta** (rate limiting): el Intruder se corta. En un entorno real esto también importa — controla la **concurrencia**. En Burp: *Settings → Resource pool*, crea un pool con **máximo 1 request** concurrente para lanzar peticiones de una en una y hacer menos ruido. |

# **9. Funcionamiento paso a paso (modelo mental)**

Representación **simplificada** de qué ocurre entre la petición y la respuesta. No es exacta, pero sirve para razonar los bypasses: siempre hay que pensar en qué queda *después* del filtro del backend.

| **1. El usuario/atacante solicita un archivo (parámetro filename)** |
| --- |

**↓**

| **2. La aplicación recibe el parámetro** |
| --- |

**↓**

| **3. Construye o concatena la ruta (ruta base + entrada)** |
| --- |

**↓**

| **4. El BACKEND aplica filtros/validaciones (bloqueo, borrado, decodificación...)** |
| --- |

**↓**

| **5. El sistema operativo resuelve/normaliza la ruta resultante** |
| --- |

**↓**

| **6. El servidor intenta leer el archivo** |
| --- |

**↓**

| **7. La aplicación devuelve el contenido o un error** |
| --- |
| **ℹ NOTA**  La incógnita permanente es la caja del backend: no sabemos si bloquea, elimina, reemplaza o decodifica, ni cuántas veces. Solo lo sabríamos con el **código fuente**. Por eso en auditoría web se pide cada vez más el código (caja gris/blanca): permite hacer ingeniería inversa del filtro y argumentar mejor la vulnerabilidad. |

# **10. Path Traversal frente a LFI**

Se confunden con frecuencia. Path Traversal es la **puerta**: encontrar que se puede salir del directorio y **leer** un archivo. LFI es el **paso siguiente**: usar esa capacidad para incluir/leer archivos concretos del sistema y sacar provecho (configuraciones, credenciales, id\_rsa).

| **Aspecto** | **Path Traversal** | **LFI** |
| --- | --- | --- |
| Objetivo principal | Salir del directorio previsto y alcanzar rutas arbitrarias. | Incluir/leer archivos locales concretos para extraer información útil. |
| Lectura de archivos | Sí (lectura de contenido). | Sí, orientada a archivos con valor (config, claves, logs). |
| Inclusión/interpretación | Normalmente solo lectura. | Puede implicar inclusión/interpretación según el lenguaje del servidor. |
| Relación con el lenguaje servidor | Independiente del lenguaje (es acceso a fichero). | Muy ligada a cómo el servidor incluye/procesa archivos (p. ej. PHP). |
| Impacto habitual | Lectura de archivos sensibles (alto). | Desde lectura hasta acceso al sistema si se encadena (crítico). |
| **ℹ NOTA**  En la práctica se solapan y a menudo se llega de uno a otro (Path Traversal → LFI), pero **no son sinónimos**. Lo importante de Path Traversal es demostrar la salida del directorio; lo importante de LFI es **qué archivo** encuentras y para qué te sirve. |
| **⚠ De la lectura al acceso**  Encadenamiento típico visto en clases anteriores: Path Traversal/LFI para leer /etc/passwd → enumerar usuarios → leer /home/<usuario>/.ssh/id\_rsa → conectarse por SSH con la clave privada sin necesidad de contraseña. |

# **11. Prevención y buenas prácticas (lado defensivo)**

- **No usar directamente** la entrada del usuario como ruta de archivo.
- Usar **identificadores indirectos** (un índice o ID que mapea internamente al archivo real), no el nombre del fichero.
- Aplicar **listas permitidas** (*allowlist*) de archivos o valores válidos, en lugar de listas de bloqueo.
- **Normalizar y canonicalizar** la ruta y, después, **verificar que la ruta final permanece dentro** del directorio autorizado.
- **Limitar los permisos** del proceso del servidor (mínimo privilegio) y separar los archivos sensibles.
- **Evitar validaciones basadas solo en reemplazar cadenas** (replace de ../): son las que se evaden con anidado, encoding y doble encoding.
- **Registrar** accesos anómalos y realizar pruebas de seguridad periódicas.

**Pseudocódigo defensivo** (independiente del lenguaje):

| base = "/var/www/images/"  entrada = request.get("filename")  ruta\_final = canonicalizar( base + entrada ) # resuelve ../ y symlinks  if not ruta\_final.startsWith( canonicalizar(base) ):  rechazar() # la ruta se escapó del directorio permitido  else:  servir(ruta\_final) # dentro del directorio autorizado |
| --- |
| **ℹ Ampliación: Red / Blue / Purple**  En una auditoría, el equipo ofensivo (Red Team) reporta la vulnerabilidad, pero **no siempre puede indicar cómo arreglarla**: depende del framework, librerías y arquitectura, que a veces no conocemos. Hay 1000 formas de corregirlo. De ahí el valor del perfil **Purple Team**, que entiende desarrollo y ataque a la vez. |

# **12. Certificación BSCP (Burp Suite Certified Practitioner)**

Solo lo comentado en la sesión, a título informativo:

- Certificación de **PortSwigger** enfocada **exclusivamente en seguridad web**, muy ligada a los laboratorios de la Academy.
- **Orientación práctica**: el examen consiste en explotar aplicaciones web reales, no en teoría.
- Formato descrito en clase: aproximadamente **4 horas** para vulnerar varios laboratorios/aplicaciones que van **en cadena** (p. ej. conseguir usuario admin → escalar → llegar a ejecución de comando o a leer un archivo/flag objetivo).
- Requiere trabajar con **Burp Suite Professional** (hay periodo de prueba). Para practicar se recomienda tener **completados los laboratorios** de la Academy.
- Se percibe como una certificación de **muy buena relación calidad-precio** para especializarse en web, difícil pese a su bajo coste. Distinta de certificaciones más generales como eJPT (entry level) u OSCP (amplia, no solo web).

| **ℹ NOTA**  Los requisitos, precio, duración y condiciones de la certificación **pueden cambiar**. Deben comprobarse en la documentación oficial de PortSwigger. Los datos concretos mencionados en clase (importe, tiempo, formato) no se verifican aquí. |
| --- |
| **✓ CORRECTO**  Mensaje del profesor: antes que 'sacar el papel', el objetivo es **aprender web de verdad**. Completar labs copiando soluciones no prepara para una auditoría real, que es donde de verdad se aporta valor. |

# **13. Herramientas utilizadas en la sesión**

| **Herramienta** | **Objetivo** | **Fase de auditoría** | **Comando o uso visto** | **Nivel** | **Notas** |
| --- | --- | --- | --- | --- | --- |
| Burp Suite — Proxy | Interceptar peticiones y descubrir llamadas en segundo plano. | Enumeración web | Interceptar y hacer forward hasta ver /image?filename= | Recurrente | Reveló la petición vulnerable oculta. |
| Burp Suite — Repeater | Reenviar y modificar una petición para probar variantes. | Explotación web | Send to Repeater; editar solo el parámetro filename | Recurrente | Núcleo del trabajo manual de la sesión. |
| Burp Suite — Decoder | Codificar payloads en URL encode. | Explotación web | Encode as → URL (o Ctrl+U) | Introducida | Usado en casos 4 y 5. |
| Burp Suite — Intruder | Fuzzing del parámetro con diccionarios. | Enumeración/Explotación web | Send to Intruder + wordlist LFI | Introducida | Bloqueado por rate limiting en labs. |
| Burp — Resource pool | Controlar concurrencia para reducir ruido. | Explotación web | Pool con máximo 1 request concurrente | Introducida | Relevante en entornos reales. |
| SecLists | Diccionarios de Path Traversal / LFI. | Enumeración web | Fuzzing/LFI/ (rutas Linux y Windows) | Introducida | También sirve rutas por defecto para leer. |
| curl | Leer la respuesta cruda sin renderizar como imagen. | Explotación web | Petición al endpoint con el payload | Practicada | Un alumno lo usó al fallar en el navegador. |
| PortSwigger Web Security Academy | Plataforma de labs y teoría web. | Formación / práctica | Generar lab → URL propia por alumno | Introducida | Base de todo el bloque web. |
| **ℹ NOTA**  Aunque /etc/passwd es el objetivo de prueba, recuerda que en los labs es PortSwigger quien detecta la lectura en sus logs y marca el lab como resuelto — no hay que 'entregar' nada más. |

# **14. Payloads importantes (resumen de los 6 casos)**

| # Caso 1 — Sin validación (relativa o absoluta):  ../../../etc/passwd  /etc/passwd    # Caso 2 — Bloquea ../ → ruta absoluta:  /etc/passwd    # Caso 3 — Elimina ../ (no recursivo) → anidar:  ....//....//....//etc/passwd    # Caso 4 — URL encoding simple:  %2e%2e%2f%2e%2e%2f%2e%2e%2fetc/passwd    # Caso 5 — Doble URL encoding:  %252e%252e%252f%252e%252e%252fetc/passwd    # Caso 6a — Debe empezar por el directorio base:  /var/www/images/../../../etc/passwd    # Caso 6b — Debe terminar en extensión → null byte:  ../../../etc/passwd%00.png |
| --- |
| **⚠ AVISO**  Ningún payload es universal ni garantizado. Cada aplicación valida de una forma distinta y muchas no son vulnerables. Estos payloads son un punto de partida para la comprobación, no una solución mágica. |

# **15. Riesgos, errores comunes y buenas prácticas**

| **⚠ AVISO**  Pensar que **cualquier** parámetro file/filename es vulnerable, o probar payloads sin entender qué archivo carga realmente la aplicación. |
| --- |
| **⚠ AVISO**  Confundir **URL encoding con cifrado**, o suponer que el backend siempre hace varias decodificaciones. |
| **⚠ AVISO**  Creer que ../../../etc/passwd funciona **en todos los casos**, o ignorar el escenario **Windows** (rutas y separadores distintos). |
| **⚠ AVISO**  No comparar la **respuesta original** con la modificada (código de estado, longitud, contenido): es la base para saber si una variante funcionó. |
| **⚠ AVISO**  Confundir **Path Traversal con LFI**, o asumir que **leer** un archivo implica **ejecutar** código (no es lo mismo). |
| **⚠ AVISO**  Lanzar muchas pruebas **sin documentar** resultados, o hacer fuerza bruta a máxima velocidad generando ruido innecesario. |
| **✓ CORRECTO**  Buena práctica de aprendizaje: apóyate en la IA (Claude, ChatGPT) para recordar un payload o generar un diccionario, pero **no para que piense por ti** dónde atacar. El mapa mental (reconocer la vulnerabilidad y saber qué probar) tiene que ser tuyo; en un examen tipo OSCP no habrá IA. |

# **16. Conexión con sesiones anteriores**

Esta sesión enlaza directamente con el trabajo previo de **seguridad web** y **explotación en laboratorio**:

- **Burp Suite** (Proxy, Repeater, Intruder, Decoder) ya se había estudiado a fondo: aquí se aplica de forma intensiva y se añade el control de **Resource pool** para el ruido.
- **XXE** se cita como ejemplo de vulnerabilidad ya trabajada donde también se detectaba y explotaba una lectura/inyección; sirve de contraste con el flujo manual de Path Traversal.
- La cadena **Path Traversal → LFI → `id\_rsa` → SSH** conecta con las máquinas ya resueltas (Castor, Nike) donde se exfiltró la clave privada para persistencia por SSH.
- **SecLists / rockyou** y el **fuzzing** enlazan con la metodología de enumeración web vista con ffuf, Feroxbuster y diccionarios.
- Se anticipa el bloque de **SQL Injection** (incluida Blind SQLi) para las próximas semanas, y más adelante **pivoting y escalada de privilegios** (entorno de 4 máquinas encadenadas).

# **17. Resumen final**

PortSwigger Web Security Academy es la plataforma de referencia para practicar web: su valor está en los **laboratorios**, que aíslan una vulnerabilidad y la presentan en múltiples contextos. El objetivo no es completarlos por completar, sino construir un **mapa mental** que permita reconocer la vulnerabilidad y saber qué probar.

El **Path Traversal** nace de cómo el servidor **construye y resuelve rutas** a partir de la entrada del usuario. Se recorrieron 6 casos: sin validación, bloqueo de ../ (ruta absoluta), eliminación no recursiva (anidado), URL encoding, doble URL encoding, y restricción por directorio inicial y por extensión (null byte). La idea transversal: **casi nunca sabemos qué hace el backend**, así que razonamos sobre lo observable y sobre qué queda tras el filtro. Ninguna técnica de evasión es universal, y muchas apps simplemente no son vulnerables. Path Traversal es la puerta; **LFI** es el paso siguiente hacia información con valor (config, credenciales, id\_rsa).

# **18. Checklist de Path Traversal**

1. ¿Existe un parámetro que parezca cargar un archivo (filename, file, image, path, page...)?
2. ¿El parámetro incluye un nombre de archivo o una extensión?
3. ¿Hay peticiones en segundo plano (revisadas en Burp Proxy / pestaña Red)?
4. ¿La aplicación acepta ../ (caso básico)?
5. ¿Acepta una **ruta absoluta** /etc/passwd?
6. ¿Elimina secuencias de traversal? Probar anidado ....//....//.
7. ¿Procesa **URL encoding**? Probar %2e%2e%2f.
8. ¿Realiza varias decodificaciones? Probar **doble** encoding %252e%252e%252f.
9. ¿Exige un **directorio inicial**? Anteponer la ruta base y remontar.
10. ¿Añade o exige una **extensión**? Probar **null byte** %00.png.
11. ¿Existen diferencias entre **Linux y Windows** (rutas, separador \)?
12. ¿Cambia la respuesta (estado / longitud / contenido) respecto a la base?
13. ¿El archivo solicitado es realmente accesible (permisos)?
14. ¿Se ha documentado la evidencia y controlado el ruido (rate limiting)?

# **19. Preguntas de repaso**

## **19.1 Preguntas cortas**

1. ¿Qué diferencia hay entre una ruta relativa y una ruta absoluta?
2. ¿Por qué /etc/passwd es el archivo de prueba habitual y qué información contiene realmente?
3. ¿Qué representan %2e y %2f en URL encoding?
4. ¿Por qué el doble URL encoding evade un filtro que sí detecta el encoding simple?
5. ¿Qué hace un null byte (%00) y de qué depende su efectividad?
6. ¿En qué se diferencia Path Traversal de LFI?
7. ¿Por qué el Caso 2 (bloquea ../, permite ruta absoluta) se considera más seguro que el Caso 1?
8. ¿Para qué sirve crear un Resource pool con 1 request en Burp?

## **19.2 Preguntas de desarrollo**

1. Explica, con el modelo 'petición → filtro backend → servidor', por qué ....//....// puede funcionar cuando el filtro elimina ../ una sola vez.
2. Describe la cadena completa desde un Path Traversal hasta el acceso por SSH a una máquina, indicando qué archivos se leen en cada paso.
3. Argumenta por qué en auditoría web pedir el código fuente aporta valor frente a una prueba de caja negra, usando los casos de esta sesión como ejemplo.

## **19.3 Preguntas tipo test**

**1. El parámetro `productId=15` de la web del lab era vulnerable a Path Traversal.**

- a) Verdadero, porque es iterable.
- b) Falso: solo selecciona un registro, no accede a archivos.
- c) Verdadero, si se le añade .jpg.
- d) Depende del navegador.

**2. ¿Qué payload corresponde al doble URL encoding de `../`?**

- a) %2e%2e%2f
- b) ..%2f
- c) %252e%252e%252f
- d) ....//

**3. El null byte `%00` se usa para...**

- a) Cifrar la ruta.
- b) Truncar la cadena y descartar la extensión exigida.
- c) Duplicar el directorio padre.
- d) Saltarse el rate limiting.

**4. Ante un filtro que bloquea `../` pero permite rutas absolutas, el payload correcto es:**

- a) ../../../etc/passwd
- b) /etc/passwd
- c) %2e%2e%2f
- d) etc/passwd

**5. ¿Dónde reveló Burp la petición vulnerable en el Lab 1?**

- a) En la barra de direcciones del navegador.
- b) En una petición en segundo plano /image?filename= vista al hacer forward.
- c) En el parámetro productId.
- d) En el favicon.

**6. URL encoding es...**

- a) Un algoritmo de cifrado simétrico.
- b) Una representación alternativa del carácter que la URL interpreta igual.
- c) Lo mismo que base64.
- d) Una función exclusiva de Burp.

**7. Path Traversal frente a LFI:**

- a) Son exactamente sinónimos.
- b) Path Traversal es leer saliendo del directorio; LFI es el paso siguiente para incluir/leer archivos con valor.
- c) LFI siempre precede a Path Traversal.
- d) LFI solo afecta a Windows.

**8. ¿Cuál de estas es una defensa correcta contra Path Traversal?**

- a) Reemplazar una vez ../ por cadena vacía.
- b) Canonicalizar la ruta y verificar que queda dentro del directorio permitido.
- c) Confiar en la extensión enviada por el usuario.
- d) Bloquear solo la palabra passwd.

## **19.4 Ejercicios prácticos (laboratorios autorizados)**

1. En PortSwigger, completa los 6 laboratorios de Path Traversal y anota, para cada uno, qué validación aplicaba el servidor y qué payload la evadió. Documenta código de estado y longitud de respuesta base vs. exitosa.
2. En una máquina de Hack The Box con un parámetro que cargue archivos, aplica la checklist de la sección 18 en orden y, si encuentras Path Traversal, encadénalo a LFI para leer /etc/passwd y localizar un id\_rsa.

## **19.5 Soluciones**

**Cortas:** 1) Relativa se resuelve desde el directorio actual con ./ ../; absoluta parte de la raíz /. 2) Es legible por todos y confirma lectura de archivos; contiene usuarios (no contraseñas, que van en /etc/shadow). 3) %2e=., %2f=/. 4) Porque el backend decodifica una vez antes de filtrar; con doble encode tras esa decodificación queda algo aún codificado que el filtro no reconoce. 5) Trunca la cadena descartando lo posterior; depende del lenguaje, la API y la versión. 6) Path Traversal es salir del directorio y leer; LFI es incluir/leer archivos concretos con valor. 7) Porque bloquea ../ (más restrictivo), aunque siga siendo vulnerable por la ruta absoluta. 8) Para lanzar peticiones de una en una y reducir ruido / rate limiting.

**Test:** 1-b · 2-c · 3-b · 4-b · 5-b · 6-b · 7-b · 8-b.

# **20. Tarjetas de memoria**

**P:** ¿Qué es Path Traversal? **R:** Vulnerabilidad que permite leer archivos/directorios fuera del directorio previsto, manipulando un parámetro que construye una ruta en el servidor.

**P:** ¿Qué es una ruta relativa? **R:** Ruta resuelta desde el directorio actual usando ./ y ../.

**P:** ¿Qué es una ruta absoluta? **R:** Ruta completa desde la raíz / (o C:\ en Windows).

**P:** ¿Qué significa ..? **R:** El directorio padre (sube un nivel).

**P:** ¿Qué es URL encoding? **R:** Representación alternativa de un carácter (%2e=., %2f=/) que la URL interpreta igual. No es cifrado.

**P:** ¿Qué es doble URL encoding? **R:** Codificar dos veces (%252e) para superar un filtro que decodifica una sola vez antes de validar.

**P:** ¿Qué es un null byte y para qué se usa aquí? **R:** %00, un byte vacío que trunca la cadena; se usaba para evadir la exigencia de extensión (passwd%00.png).

**P:** ¿Qué es normalización de rutas? **R:** Resolver ./.. y colapsar barras repetidas para obtener la ruta efectiva.

**P:** ¿Qué es canonicalización? **R:** Obtener la ruta real y definitiva de un archivo (resolviendo enlaces), base para comprobar que sigue dentro del directorio permitido.

**P:** ¿Para qué sirve Burp Repeater? **R:** Reenviar y modificar una petición para probar variantes de payload y comparar respuestas.

**P:** ¿Qué es una allowlist (lista permitida)? **R:** Defensa que solo acepta valores/archivos explícitamente autorizados, en vez de bloquear los 'malos'.

**P:** ¿Diferencia Path Traversal vs LFI? **R:** Path Traversal = salir del directorio y leer; LFI = paso siguiente para incluir/leer archivos concretos con valor (config, id\_rsa).

**P:** Payload del Caso 3 (elimina ../ una vez). **R:** ....//....//....//etc/passwd.

**P:** ¿Qué hace Resource pool con 1 request en Burp? **R:** Envía las peticiones de una en una para reducir ruido y evitar el rate limiting.

**P:** ¿Qué contiene /etc/passwd? **R:** La lista de usuarios del sistema y sus shells; NO las contraseñas (esas están en /etc/shadow).

**P:** ¿Qué diccionario/carpeta de SecLists se usó? **R:** Fuzzing/LFI/, con payloads de Path Traversal y rutas por defecto de Linux/Windows.

# **21. Glosario**

**PortSwigger** — Empresa creadora de Burp Suite y de la Web Security Academy.

**Web Security Academy** — Plataforma educativa gratuita de PortSwigger con teoría y laboratorios web.

**Burp Suite** — Herramienta de pentesting web (Proxy, Repeater, Intruder, Decoder, etc.).

**Payload** — Entrada manipulada que se envía para explotar una vulnerabilidad.

**Path Traversal / Directory Traversal** — Acceso a archivos fuera del directorio previsto manipulando la ruta.

**Ruta absoluta** — Ruta completa desde la raíz / (o unidad en Windows).

**Ruta relativa** — Ruta resuelta desde el directorio actual con ./ y ../.

**URL encoding** — Codificación de caracteres en la URL (%2e, %2f).

**Null byte** — Byte nulo %00 que trunca cadenas; usado históricamente para bypasses de extensión.

**Normalización** — Resolución de ./.. y barras repetidas en una ruta.

**Canonicalización** — Obtención de la ruta real definitiva de un archivo.

**LFI (Local File Inclusion)** — Inclusión/lectura de archivos locales del servidor.

**RFI (Remote File Inclusion)** — Inclusión de archivos remotos.

**BSCP** — Burp Suite Certified Practitioner, certificación web práctica de PortSwigger.

**Rate limiting** — Límite de peticiones por tiempo que frena la fuerza bruta.

# **22. Actualización del registro de herramientas**

Cambios respecto al registro acumulado tras esta sesión (copiable a la base de conocimiento del proyecto):

| **Herramienta** | **Nivel** |
| --- | --- |
| Burp Suite — Proxy | Recurrente |
| Burp Suite — Repeater | Recurrente |
| Burp Suite — Decoder | Practicada (nuevo: URL encode) |
| Burp Suite — Intruder | Practicada |
| Burp Suite — Resource pool | Introducida (nuevo) |
| SecLists (Fuzzing/LFI) | Practicada |
| curl | Recurrente |
| PortSwigger Web Security Academy | Introducida (nuevo: plataforma) |

**Conceptos/técnicas nuevos consolidados:** Path Traversal (6 casos), URL encoding y doble encoding como bypass, null byte para extensión, distinción Path Traversal vs LFI, control de ruido con Resource pool.
