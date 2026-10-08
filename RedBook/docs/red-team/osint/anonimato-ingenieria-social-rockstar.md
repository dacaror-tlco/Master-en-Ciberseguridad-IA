---
tags:
- OSINT e ingeniería social
date: '2026-07-06'
---

# Anonimato Ingenieria Social Rockstar

<p class="note-meta">2026-07-06</p>

**EVOLVE ACADEMY · MÁSTER EN CIBERSEGURIDAD OFENSIVA**

**Anonimato, Ingeniería Social y Enumeración Web**

Instructor: Carlos Gómez Pintado

| **Campo** | **Detalle** |
| --- | --- |
| Instructor | Carlos Gómez Pintado |
| Módulo | Ingeniería social / Enumeración web ofensiva |
| Fecha | No indicada explícitamente en el material (sesión previa a la clase de phishing con GoPhish de Carlos Castillo) |
| Entorno de laboratorio | Kali Linux · Máquina Rockstar de HackerLabs (autorizada) |
| Contexto | Cómo opera la infraestructura del cibercrimen para saber detectarla y protegerse, más una máquina de enumeración web |

| **ℹ Cómo leer estos apuntes**  La sesión mezcla dos bloques. El bloque de infraestructura anónima (Monero, VPS, dominios, QRishing, IP logger) se documenta con enfoque **defensivo y de atribución**: entender cómo se construye para reconocerla, no para replicarla. El bloque de laboratorio (máquina Rockstar) sí es práctica ofensiva en entorno autorizado. Se distingue en todo momento lo dicho en clase de las explicaciones complementarias añadidas para el estudio. |
| --- |

# **1. Objetivos de la sesión**

- Entender cómo el cibercrimen construye una **infraestructura anónima** (VPN sin logs, Monero, VPS y dominios pagados con cripto) para saber **detectarla, atribuirla y protegerse**.
- Aprender a hacer **seguimiento de un posible estafador** con un IP logger (uso defensivo/atribución).
- Conocer técnicas de **ingeniería social** actuales, en especial el **QRishing** como evolución del phishing y el smishing.
- Comprender el modelo **as-a-Service** del cibercrimen (SaaS / RaaS) y por qué se detiene a los operadores.
- Resolver la máquina **Rockstar (HackerLabs)**: descubrimiento de host, enumeración web y **fuzzing de parámetros** hasta obtener acceso por SSH.

# **2. Conceptos clave**

| **Concepto** | **Definición breve** |
| --- | --- |
| Anonimato | Cualidad de operar sin identidad atribuible. En la práctica se rompe por comodidad (reutilizar nick, IP o contraseñas). |
| VPN | Virtual Private Network. Túnel cifrado hacia servidores alquilados en un CPD; actúa como proxy con IP cambiante. No garantiza anonimato si el proveedor guarda logs. |
| Tabla de enrutado del proveedor | Registro que correlaciona la IP real del usuario con la IP de VPN asignada en cada instante. Es lo que permite desanonimizar bajo orden judicial. |
| Monero (XMR) | Criptomoneda orientada a privacidad; sus wallets no dejan trazabilidad pública en su blockchain. |
| VPS | Virtual Private Server. Servidor virtual donde se aloja contenido (por ejemplo, un sitio web). |
| Calentar un dominio | Enviar correos progresivamente durante ~1 mes para subir la reputación (domain authority) y que no lo marquen como nuevo/sospechoso. |
| Phishing / Smishing / QRishing | Ingeniería social por web falsa / por SMS / mediante códigos QR maliciosos. |
| IP logger | Servicio que, tras un clic, registra IP y (si el usuario lo permite) geolocalización aproximada o por GPS. |
| SaaS / RaaS | Software-as-a-Service / Ransomware-as-a-Service: modelo donde uno desarrolla/vende la herramienta y otro (el cliente) asume el riesgo de usarla. |
| Ciberresponsabilidad bancaria | Cobertura ligada a un ciberseguro por la que el banco puede tener que reintegrar el dinero de una estafa si se aporta denuncia + movimientos. |
| Fuzzing de parámetros | Probar automáticamente muchos nombres/valores de parámetros contra un endpoint para descubrir cuáles cambian la respuesta. |

# **3. Anonimato: cómo se construye y cómo se rompe**

| **⚠ Enfoque de la sección**  Se describe la arquitectura que usan los ciberdelincuentes para que sepas **identificarla, atribuirla y protegerte**. No es una guía para replicarla. |
| --- |

## **3.1 La comodidad rompe el anonimato**

Idea central del instructor: el anonimato hace que la gente se atreva a decir y hacer cosas que no haría a cara descubierta. Pero la mayoría de personas rompen su propio anonimato **por comodidad**: reutilizan el mismo nick, la misma IP o las mismas contraseñas, y eso permite correlacionar identidades.

| **ℹ Regla mental de la clase**  Para una acción que se quiera desligar de la identidad: **cuenta nueva + IP nueva** (*new account, new IP*). No reutilizar alias ni patrones. |
| --- |

## **3.2 Cómo funciona realmente una VPN**

Una VPN mete tu tráfico en una red privada de servidores alquilados en un CPD y sale a Internet por ellos, funcionando como un **proxy**. Cambia tu IP de salida, pero el proveedor sigue sabiendo quién eres.

| **ℹ Complemento técnico**  Para poder devolverte las respuestas, el proveedor mantiene una **tabla de enrutado** que asocia tu IP real con la IP de VPN que te asignó. Esa tabla es exactamente lo que permite desanonimizar. |
| --- |
| **1. Usuario (IP real)** |

**↓**

| **2. Servidor VPN / proxy en CPD (IP de salida)** |
| --- |

**↓**

| **3. Servidor destino en Internet** |
| --- |

**↓**

| **4. Respuesta enrutada de vuelta usando la tabla IP real ↔ IP VPN** |
| --- |

**Por qué la mayoría de VPN no da anonimato real:** el proveedor guarda la tabla de enrutado (según la clase, del orden de ~5 años). Con orden judicial (FBI, Interpol, Hacienda/CNI, etc.) puede entregarla y desanonimizar al usuario. El instructor cita como ejemplos de VPN que colaboran: NordVPN, PureVPN/similares, Surfshark, ProtonVPN, Sophos, Check Point, entre otras.

| **⚠ El caso Mullvad (según la clase)**  Se presenta **Mullvad** como VPN que, según el instructor, habría rechazado múltiples solicitudes de colaboración y no es nominal (no pide registro con datos personales). La afirmación concreta sobre el número de solicitudes rechazadas es del instructor y no está verificada en el material. |
| --- |
| **ℹ Idea legal que repite el instructor**  Una VPN es una **herramienta legal**; lo que puede ser ilegal es el uso. El símil del instructor: comprar una espada es legal; atravesar a alguien con ella, no. |

## **3.3 La cadena de anonimización del cibercrimen**

El instructor encadena varias piezas para lograr una infraestructura difícil de atribuir. Se resume a alto nivel para **reconocerla**, no como receta:

| **1. VPN sin logs / no nominal (p. ej. Mullvad)** |
| --- |

**↓**

| **2. Criptomoneda no trazable (Monero / XMR)** |
| --- |

**↓**

| **3. VPS pagado con Monero + acceso por clave SSH (sin usuario/contraseña)** |
| --- |

**↓**

| **4. Dominio pagado con cripto en registrador que admite pago anónimo** |
| --- |

**↓**

| **5. Dominio 'calentado' ~1 mes para ganar reputación** |
| --- |

| **ℹ Nota de estudio / seguridad**  Documentamos el concepto (por qué Monero se asocia a operaciones ilícitas y por qué es relevante para un analista) **sin detalle operativo** para romper trazabilidad. El objetivo es reconocer el patrón en una investigación, no reproducirlo. |
| --- |

**Acceso al VPS por clave SSH** (concepto técnico correcto y reutilizable en laboratorio): conviene inyectar una clave SSH al aprovisionar el servidor y acceder sin usuario/contraseña. Forma general del comando:

| ssh -i /ruta/a/clave root@IP |
| --- |

## **3.4 Alojamiento del sitio malicioso y calentamiento de dominio**

Un phishing es, en el fondo, **una web**: una carpeta con ficheros relacionados, con permisos, expuesta a Internet. Por eso necesita un servidor (VPS) y un dominio. El **calentamiento** consiste en enviar correos de forma progresiva durante ~1 mes para que el dominio gane reputación y no lo marquen como spam.

| **ℹ Continuidad**  La próxima clase (Carlos Castillo) cubrirá el montaje de un servidor de phishing real con **GoPhish**, plantillas y captura de credenciales — desde la perspectiva de red team autorizado y concienciación. |
| --- |

## **3.5 Tor y la 'red cebolla'**

Tor enruta la conexión saltando por varios nodos (como capas de cebolla) hasta un **nodo de salida** que alcanza el exterior; para devolver la respuesta se recorre el camino inverso.

| **⚠ Matiz del instructor sobre nodos de salida**  El instructor afirma que hoy una gran parte de los nodos de salida estarían controlados por autoridades, lo que reduciría el anonimato frente a los inicios de Tor. Su conclusión práctica: con VPS privados baratos pagados con Monero, para muchos casos ya no compensa depender solo de Tor. |
| --- |

# **4. Ingeniería social: IP logger y QRishing**

## **4.1 IP logger (geolocalización tras un clic)**

Un IP logger genera un enlace que, al abrirse, registra la IP del visitante y puede pedirle la ubicación. El uso que enseña el instructor es de **atribución**: darle un enlace verosímil a un estafador que te ha timado para obtener su IP y timestamp.

| **✓ Uso legítimo mostrado en clase**  El objetivo del ejercicio es **atribución de un atacante que te ha estafado**, no espiar a terceros al azar. Con una IP + timestamp, la policía puede pedir a la operadora qué persona tenía esa IP en ese momento (igual que con las VPN). |
| --- |
| **⚠ Vector adicional mencionado (no demostrado)**  El instructor comenta que un IP logger no se autoejecuta en una imagen, pero sí podría dispararse desde **documentos con macros** (formatos ofimáticos). Se menciona como vector, no se demuestra en clase. |

## **4.2 QRishing (la evolución de la ingeniería social)**

Como el phishing por enlace y el smishing están muy 'quemados', la ingeniería social evoluciona hacia el **QRishing**: incrustar el enlace malicioso en un código QR. El diseño cuidado del QR reduce la desconfianza de la víctima. Ejemplos que menciona el instructor en contexto de red team autorizado / concienciación: pegatinas sobre QR legítimos, cartas o carteles manipulados, cartas de restaurante.

| **⚠ Lección defensiva del QRishing**  No escanees QR de origen desconocido (pegatinas en la calle, carteles, cartas de restaurante manipuladas). Un QR llamativo y 'profesional' NO es garantía de confianza. Desconfía de cualquier QR que lleve a un **login** o pida **permisos de ubicación**; verifica el dominio destino antes de introducir credenciales. |
| --- |
| **ℹ Herramientas de clonado de UI mencionadas**  Para el front de un phishing se citan asistentes de IA / plataformas tipo **Lovable, Emergent**, etc., capaces de replicar visualmente una web a partir de su URL o capturas. Se documenta como parte del panorama; solo replican el front, en contexto autorizado. |

# **5. Modelo 'as-a-Service' del cibercrimen (SaaS / RaaS)**

El cibercrimen ya no lo mueven solo los técnicos: el que **desarrolla y vende** la herramienta asume poco riesgo y hace negocio recurrente; el **cliente/operador** que la ejecuta asume el riesgo.

| **1. Desarrollador: crea el ransomware / panel y lo vende (cuota fija)** |
| --- |

**↓**

| **2. Broker de acceso inicial: vende credenciales / RCE de una víctima** |
| --- |

**↓**

| **3. Cliente/operador: compra ambos, ejecuta el ataque y asume el riesgo** |
| --- |

**↓**

| **4. El desarrollador cobra además un % del rescate** |
| --- |

**RaaS (Ransomware-as-a-Service):** en lugar de atacar uno mismo a una gran empresa, se vende el ransomware a muchos operadores.

| **ℹ Por qué se pilla a los operadores**  Los operadores suelen tener **cero conocimiento técnico** y cometen fallos graves: paneles con credenciales por defecto (p. ej. cPanel admin sin contraseña), reutilización de alias, mala gestión de su propio anonimato. Por eso se detiene al operador antes que al desarrollador. |
| --- |

# **6. Si eres víctima de una ciberestafa**

**Ciberresponsabilidad bancaria:** los bancos suelen tener un ciberseguro con ciberresponsabilidad asociada. Si aportas la **denuncia policial + los movimientos bancarios sellados**, el banco puede tener que reintegrar el dinero. Aplica a casos como pagos falsos de la 'DGT', reservas de piso falsas o compras fraudulentas.

| **⚠ AVISO**  Son pautas generales de la clase, **no asesoramiento legal**. Los procedimientos y la confidencialidad varían según el caso y la entidad; ante una estafa real, denuncia y consulta con profesionales. |
| --- |

# **7. Laboratorio: máquina Rockstar (HackerLabs)**

| **ℹ Contexto**  Máquina de HackerLabs resuelta en directo (inicialmente se confundió con la máquina 'Academy'). Objetivo del tramo: **enumeración web y descubrimiento de un parámetro oculto** hasta obtener credenciales SSH. La escalada de privilegios queda para la siguiente sesión. |
| --- |

## **7.1 Descubrimiento de host y sistema operativo**

Primero se identifica la interfaz local y el rango de red; luego se descubre la IP víctima.

| # Ver nuestra IP e interfaz (eth0)  ip a  # Descubrir hosts en el rango de red /24  sudo netdiscover -r 10.0.2.0/24 |
| --- |

La interfaz de trabajo era **eth0** con IP **10.0.2.3**. Se descartan 127.0.0.1 (localhost) y las interfaces Docker. Por norma, la .1 y la .2 suelen ser gateway/router de VirtualBox; se buscó un host más alto y la víctima resultó ser **10.0.2.9**.

| **ℹ Repaso de redes aplicado**  **Rango /24:** los 3 primeros octetos son fijos y el último varía de 0 a 255 (10.0.2.0/24). /16 fija 2 octetos, /8 fija 1, y /0 abarca todas las direcciones (equivale a 0.0.0.0 en un listener: escuchar en todos los orígenes). |
| --- |

**ICMP y detección de SO por TTL:**

| # Comprobar si el host está vivo (ICMP = ping)  ping 10.0.2.9 |
| --- |
| **TTL aprox. observado** | **Sistema operativo probable** |
| 64 | Linux / Unix |
| 128 | Windows |
| 192 | Solaris (según la clase) |
| 254 | macOS / otros (según la clase) |

| **ℹ Detalle de curiosidad (AWS)**  Amazon (AWS) no trae ICMP habilitado por defecto en su red, para dificultar el *ping sweep* (barrido de pings para descubrimiento de activos). En la máquina, el TTL apuntaba a Linux. Recuerda también que los **3 primeros dígitos de la MAC** identifican al fabricante. |
| --- |

## **7.2 Escaneo de puertos y servicios (Nmap)**

| # Escaneo de versiones sobre puertos abiertos, agilizando con min-rate  nmap -sVC --open --min-rate 1500 10.0.2.9 |
| --- |

Se encontraron **2 puertos: 22 (SSH) y 80 (HTTP)**. Con esta combinación en un CTF se ataca primero el 80: al 22 no se entra sin credenciales (salvo un CVE de la versión, poco habitual en CTF), así que la vía es la web.

## **7.3 Enumeración web**

**Metodología del instructor (símil del coche):** ir de más a menos. El servidor (Apache) sería el chasis; primero se comprueba si la versión tiene vulnerabilidades conocidas, y luego se baja al detalle (rutas, ficheros, parámetros). En paralelo, descubrimiento de directorios y ficheros con wordlists:

| # Directorios con Gobuster  gobuster dir -u http://10.0.2.9 -w /usr/share/wordlists/dirb/common.txt  # Directorios + ficheros por extensión con Feroxbuster  feroxbuster -u http://10.0.2.9 -w /usr/share/wordlists/dirb/common.txt -x php,py,txt,html |
| --- |
| **ℹ Directorios vs. ficheros y códigos de estado**  Una web es una carpeta con ficheros y subcarpetas. La diferencia clave: el **fichero tiene extensión** (y por tanto puede ejecutar/mostrar contenido). Por eso se añade -x con las extensiones a probar. Los **códigos de estado** orientan: 200 (existe y responde), 500 (error interno), etc. |

**Hallazgos:** index.php y db.php. db.php devuelve 0 words (página en blanco): un PHP que se ejecuta pero no imprime nada (sin echo/print) resulta en 0 bytes. index.php reacciona pero tampoco muestra nada útil de entrada.

| **⚠ Diccionarios: no confundir usos**  **rockyou** es de contraseñas (no sirve para directorios); listas tipo *directory-list* / *common.txt* son de directorios. Gobuster, Feroxbuster y Dirsearch son equivalentes para descubrir rutas; usa el que prefieras. |
| --- |

## **7.4 Fuzzing de parámetros: descubrir el parámetro oculto**

Como index.php reacciona pero no se ve nada útil, se busca un **parámetro que cambie su comportamiento**. La herramienta idónea es **x8** (fuzzing de parámetros), pero su instalación por Docker falló.

| **⚠ x8 con Docker falló**  Instalación prevista (repositorio de x8): git clone del repo, cd x8, y docker build -t x8 .. Al fallar Docker, la alternativa recomendada por un compañero fue compilar con Cargo (Rust): cargo build --release. En clase se optó por **escribir un fuzzer propio en Python** (curl + diccionario). |
| --- |

**Comprobación manual previa con curl** (verbo POST y cuerpo con --data):

| # Enviar un parámetro por POST y ver cómo responde el index.php  curl -X POST http://10.0.2.9/index.php --data "parametro=valor" |
| --- |

**Idea del fuzzing de parámetros:** se lanza contra index.php un diccionario de posibles nombres de parámetro (p. ej. /usr/share/wordlists/dirb/common.txt) y se observa qué respuesta devuelve cada uno. El parámetro correcto hace que la respuesta **cambie de un 500 a un 200**. En la máquina, el parámetro válido resultó ser backdoor.

## **7.5 Los dos scripts propios: descubrir NOMBRE y descubrir VALOR**

El fuzzing de Rockstar tiene **dos incógnitas distintas**, y por eso se resuelve con dos herramientas complementarias. Primero hay que averiguar **qué parámetro** acepta index.php (su nombre); una vez conocido (backdoor), hay que averiguar **qué valor** hace que devuelva las credenciales. Como x8 no arrancó por Docker, en clase se montaron dos scripts propios en Python que cubren cada fase.

| **Script** | **Qué incógnita resuelve** | **Diccionario que consume** | **Analogía** |
| --- | --- | --- | --- |
| x8\_lite.py | El **nombre** del parámetro oculto | Nombres de parámetro (admin, id, backdoor…) | Reimplementa el motor de x8 |
| valfuzz.py | El **valor** de un parámetro ya conocido | Valores (p. ej. rockyou.txt) | Estilo ffuf/wfuzz con marcador FUZZ |

**`x8\_lite.py` — descubrimiento de nombres (motor tipo x8).** No prueba un parámetro por petición como un fuzzer clásico: aprende primero un *baseline* de la respuesta normal, luego mete **muchos parámetros por petición** (hasta 128) con valores aleatorios, compara contra el baseline (cambio de código, líneas que aparecen/desaparecen, reflexiones) y, si un lote provoca cambios, lo parte por la mitad de forma recursiva (**búsqueda binaria**) hasta aislar el parámetro responsable. Además prueba nombres típicos con valores no aleatorios (admin=true, debug=1…) y reconfirma cada hallazgo.

| # Descubrir nombres de parámetro por POST (body urlencoded) contra index.php  python3 x8\_lite.py -u http://10.0.2.9/index.php -X POST -w /usr/share/wordlists/dirb/common.txt --verify |
| --- |
| **ℹ Cómo trabaja x8\_lite por dentro**  Fases internas de x8\_lite.py: **LEARN** (aprende el baseline y descarta líneas dinámicas tipo CSRF/timestamp) → **BATCH** (muchos parámetros a la vez) → **COMPARE** (diff contra baseline) → **BISECT** (búsqueda binaria para aislar el parámetro) → **CUSTOM** (admin=true, debug=1…) → **VERIFY** (reconfirma uno a uno). Este enfoque por lotes es mucho más rápido que un parámetro por petición. |

**`valfuzz.py` — fuzzing de valores (estilo ffuf/wfuzz).** Aquí el **nombre del parámetro es fijo** (backdoor) y lo que varía es el valor: por cada palabra del diccionario manda una petición y detecta cuál provoca una respuesta distinta al resto. Marca el punto de inyección con FUZZ y detecta la anomalía por tres criterios: código de estado distinto de la mayoría, tamaño (bytes) fuera del patrón, o una palabra clave que solo aparece en esa respuesta (--match-keyword).

| # Fuzzear el VALOR del parámetro backdoor (nombre fijo, valor = FUZZ)  python3 valfuzz.py -u http://10.0.2.9/index.php -X POST -d "backdoor=FUZZ" -w /usr/share/wordlists/rockyou.txt  # Afinar marcando como HIT solo si la respuesta contiene 'uid='  python3 valfuzz.py -u http://10.0.2.9/index.php -X POST -d "backdoor=FUZZ" -w rockyou.txt --match-keyword "uid=" |
| --- |
| **ℹ Cómo detecta el hit valfuzz**  valfuzz.py calcula la respuesta **baseline** (la combinación código+tamaño más frecuente) y marca como *hit* todo lo que se desvía de ella. Igual que en ffuf, se pueden ocultar respuestas por código (--filter-code 403) o por tamaño (--filter-size), o exigir un código concreto (--match-code 200,302). |
| **⚠ No confundir uno con otro**  **Diferencia clave entre los dos:** x8\_lite.py consume un diccionario de **nombres** de parámetro (la incógnita es *qué parámetro existe*); valfuzz.py usa un nombre **fijo** y un diccionario de **valores** (la incógnita es *qué valor lo activa*). Son fases consecutivas, no alternativas. |

**Flujo completo del tramo, con los dos scripts:**

| **1. index.php responde pero no muestra nada útil (500)** |
| --- |

**↓**

| **2. x8\_lite.py → descubre el NOMBRE del parámetro: 'backdoor'** |
| --- |

**↓**

| **3. valfuzz.py → fuzzea el VALOR de 'backdoor' (500 → 200)** |
| --- |

**↓**

| **4. La respuesta revela usuario y contraseña** |
| --- |

**↓**

| **5. Acceso por SSH con esas credenciales** |
| --- |

| **✓ Resultado del tramo**  El valor 'anómalo' del parámetro backdoor devolvió un **usuario y una contraseña válidos**, con los que se logró acceso por SSH (puerto 22). Los valores concretos no se documentan aquí por ser específicos del CTF. |
| --- |
| **ℹ Buena práctica de la clase**  El instructor insiste en **entender cuándo usar cada herramienta** más que en memorizar cómo se programa: x8\_lite.py descubre parámetros aceptados por un endpoint y valfuzz.py descubre el valor que los activa; sabiendo eso, la implementación concreta es secundaria. |
| **✓ Scripts adjuntos**  Ambos scripts (x8\_lite.py y valfuzz.py) se entregan junto a estos apuntes. Requieren la librería requests (pip install requests) y funcionan en Kali sin Docker, que es justo el problema que bloqueó a x8 en clase. |

# **8. Herramientas utilizadas en la sesión**

| **Herramienta** | **Objetivo** | **Fase** | **Comando o uso visto** | **Nivel** | **Notas** |
| --- | --- | --- | --- | --- | --- |
| netdiscover | Descubrir hosts del rango | Reconocimiento | sudo netdiscover -r 10.0.2.0/24 | Practicada | .1/.2 suelen ser gateway |
| ping / ICMP | Host vivo y SO por TTL | Reconocimiento | ping 10.0.2.9 | Recurrente | TTL 64→Linux, 128→Windows |
| Nmap | Puertos y versiones | Enumeración | nmap -sVC --open --min-rate 1500 IP | Recurrente | Primer paso habitual |
| Gobuster | Descubrir directorios | Enum. web | gobuster dir -u URL -w common.txt | Practicada | Equivalente a Dirb/Dirsearch |
| Feroxbuster | Directorios + ficheros | Enum. web | feroxbuster -u URL -w lista -x php,py,txt,html | Practicada | -x para extensiones |
| curl | Peticiones POST manuales | Enum./pruebas | curl -X POST URL/index.php --data "p=v" | Practicada | Verbo con -X, cuerpo con --data |
| x8 | Fuzzing de parámetros | Enum. web | docker build -t x8 . (falló); alt. cargo build --release | Introducida | Falló por Docker; se sustituyó por scripts propios |
| x8\_lite.py (propio) | Descubrir NOMBRE de parámetro | Enum. web | python3 x8\_lite.py -u URL -X POST -w nombres.txt --verify | Practicada | Motor tipo x8: learn/batch/bisect/verify |
| valfuzz.py (propio) | Descubrir VALOR de un parámetro | Enum. web | python3 valfuzz.py -u URL -X POST -d "backdoor=FUZZ" -w rockyou.txt | Practicada | Estilo ffuf/wfuzz; detectó el valor de backdoor |
| SSH | Acceso remoto | Acceso inicial | ssh -i clave root@IP / ssh user@IP | Practicada | Vía de entrada final |
| IP Logger | IP + geolocalización tras clic | Ing. social / atribución | Enlace verosímil + redirect | Introducida | Uso defensivo: atribuir estafador |
| GoPhish | Campañas de phishing | Ing. social | Se verá con Castillo la próxima clase | Mencionada | Plantillas + captura de credenciales |
| SmartLead (warmup) | Calentar dominios | Infraestructura | Envío progresivo ~1 mes | Mencionada | Sube domain authority |
| Mullvad VPN | VPN no nominal (según clase) | Anonimato | Cuenta por número, pago poco vinculable | Mencionada | Afirmaciones no verificadas |
| Monero (XMR) | Cripto de privacidad | Anonimato / pagos | Pago de VPS y dominio | Mencionada | Concepto; sin detalle operativo |
| Lovable / Emergent (IA) | Clonar UI de webs | Ing. social | URL/capturas → réplica del login | Mencionada | Solo front; contexto autorizado |

| **ℹ NOTA**  Varias herramientas (GoPhish, SmartLead, Mullvad, Monero, clonadores de UI) se nombran pero no se desarrollan a fondo en el material. GoPhish y el montaje de phishing se profundizarán con Carlos Castillo en la próxima clase. |
| --- |

# **9. Conexión con sesiones anteriores**

- **Netdiscover, ping/TTL y Nmap** enlazan con el flujo de reconocimiento y enumeración ya visto en máquinas previas: primero descubrir el host, luego el SO, luego los servicios.
- **Gobuster y Feroxbuster** consolidan la fase de enumeración web ya practicada: mientras Nmap descubre puertos y servicios, estas herramientas encuentran rutas, directorios y ficheros ocultos dentro de la aplicación web.
- El **fuzzing de parámetros con x8/curl** amplía el concepto de fuzzing (antes de directorios) hacia los parámetros de un endpoint: mismo principio, distinto objetivo.
- El repaso de **redes (/24, /16, /8, /0, 0.0.0.0)** refuerza los fundamentos de subnetting vistos en las sesiones de redes.

# **10. Resumen final para repasar**

La sesión tiene dos mitades. En la primera, Carlos Gómez Pintado explica cómo el cibercrimen construye anonimato (VPN sin logs, Monero, VPS y dominio pagados con cripto, calentamiento de dominio, Tor) y cómo se rompe ese anonimato por comodidad o por la tabla de enrutado del proveedor; introduce el IP logger para atribución, el QRishing como evolución de la ingeniería social, y el modelo as-a-Service (RaaS) del cibercrimen.

En la segunda mitad se resuelve la máquina **Rockstar** de HackerLabs: descubrimiento con netdiscover, host vivo por ping (Linux por TTL), Nmap revela 22 y 80, enumeración web con Gobuster/Feroxbuster (index.php y db.php), y fuzzing de parámetros en dos fases: **`x8\_lite.py`** descubre el **nombre** del parámetro oculto (backdoor) y **`valfuzz.py`** descubre el **valor** que lo activa (respuesta 500 → 200), revelando credenciales para entrar por SSH. Ambos scripts sustituyeron a x8, que no arrancó por Docker. **La escalada de privilegios (cron) queda pendiente para la próxima sesión.**

# **11. Checklist de repaso**

1. Explicar qué es la tabla de enrutado de una VPN y por qué rompe el anonimato.
2. Recitar la cadena de anonimización del cibercrimen y para qué sirve cada pieza.
3. Diferenciar phishing, smishing y QRishing, y dar la lección defensiva de cada uno.
4. Explicar el modelo RaaS y por qué se detiene antes al operador que al desarrollador.
5. Descubrir el host víctima con netdiscover e inferir el SO por TTL.
6. Enumerar la web con Gobuster/Feroxbuster e interpretar los códigos de estado.
7. Explicar el fuzzing de parámetros (nombre y valor) y por qué el cambio 500→200 es la señal.
8. Distinguir cuándo usar x8\_lite.py (descubre el NOMBRE) y cuándo valfuzz.py (descubre el VALOR).
9. Describir las fases internas de x8\_lite.py (learn, batch, bisect, verify) y por qué van por lotes.
10. Reproducir el comando curl -X POST --data para probar un parámetro manualmente.

# **12. Próxima sesión (anticipo)**

| **⚠ Pendiente**  Este contenido **aún no se ha impartido**; se anticipa a partir de lo dicho al final de la clase para orientar el estudio. Se documentará en detalle cuando se dé. |
| --- |

- **Escalada de privilegios de Rockstar** mediante **cron** (tarea programada) y demás vectores. En esta sesión solo se llegó al acceso inicial por SSH.
- **Repaso** de lo hecho hasta ahora antes de continuar.
- Nueva máquina de **HackerLabs** (mencionada como 'Banco').
- Inicio del bloque de **phishing con GoPhish** a cargo de **Carlos Castillo**: montaje de servidor de phishing, plantillas y captura de credenciales.

# **13. Notas de fidelidad al material**

- El **instructor de esta sesión es Carlos Gómez Pintado**. La clase de phishing con GoPhish la impartirá Carlos Castillo en la sesión siguiente.
- El bloque de infraestructura anónima se documenta con **enfoque defensivo/atribución**, sin detalle operativo para replicar la técnica.
- Las afirmaciones sobre Mullvad (solicitudes rechazadas) y sobre los TTL de Solaris/macOS se atribuyen a la clase y no se verifican de forma independiente en el material.
- Los valores concretos de credenciales de Rockstar no se transcriben por ser específicos del CTF; se documenta el método.
- La **fecha** exacta de la sesión no aparece en el material.

# **14. Actualización del registro de herramientas**

Para copiar a tu base de conocimiento. Altas y cambios de nivel de esta sesión:

| **Herramienta** | **Cambio** | **Nivel resultante** |
| --- | --- | --- |
| x8 | Alta (fuzzing de parámetros; build Docker/Cargo) | Introducida |
| x8\_lite.py (propio) | Alta (descubrimiento de NOMBRES de parámetro, motor tipo x8) | Practicada |
| valfuzz.py (propio) | Alta (fuzzing de VALORES estilo ffuf, marcador FUZZ) | Practicada |
| curl | Uso explícito con -X POST --data para fuzzing manual | Practicada |
| Feroxbuster | Uso con -x para ficheros por extensión | Practicada |
| Gobuster | Uso dir con diccionario | Practicada |
| netdiscover | Descubrimiento con -r sobre /24 | Practicada |
| SSH | Acceso con credenciales / clave id\_rsa | Practicada |
| IP Logger | Alta (atribución de estafadores, uso defensivo) | Introducida |
| GoPhish | Alta (se profundizará con Castillo) | Mencionada |
| SmartLead (warmup) | Alta (calentamiento de dominios) | Mencionada |
| Mullvad VPN | Alta (VPN no nominal, según la clase) | Mencionada |
| Monero (XMR) | Alta (cripto de privacidad; concepto) | Mencionada |
| Tor | Alta/repaso (red cebolla, nodos de salida) | Mencionada |
| Lovable / Emergent (IA) | Alta (clonado de UI para front de phishing) | Mencionada |
