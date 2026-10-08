---
tags:
- Auditoría web
date: '2026-09-22'
---

# PortSwigger SQLi I

<p class="note-meta">2026-09-22</p>

![PortSwigger: SQLi I. IA, práctica 1 y Validation. Carlos Gómez Pintado. 22/09/2026. Portada ilustrada creada para esta sesión a partir de su referencia visual; no es una fotografía ni evidencia del laboratorio. Dedicatoria personal ficticia en las pantallas: Usuario Noe; Fecha 22/09/2014; Gracias por estos 12 años. Laboratorio simulado. Phishing e ingeniería social: representación ilustrada de la anécdota de los QR del restaurante y gimnasio, con motivos gráficos de QR ficticios y señales de advertencia.](../../assets/img/portswigger-sqli-i/img001.png)

# Esquema de la sesión

La sesión combina seguimiento de proyectos de IA, phishing e ingeniería social y análisis de SQLi. Una aplicación útil necesita información fiable y controles sobre las entradas, las cuentas y las acciones de sus usuarios.

| **Bloque** | **Ideas y relaciones** |
| --- | --- |
| IA y práctica 1 | Obsidian y respuestas revisadas → recuperación o caché → menos consultas repetidas → medir coste, calidad y límites. |
| Proyectos y phishing | Logs y PCAP · QR/URL · coches · SIEM. Ingeniería social → phishing y QR → verificación del destino y MFA. |
| Entrega | Classroom → documento explicativo + GitHub → acceso al profesor si es privado. Aplicación accesible si se dispone de ella. |
| SQLi y Validation | Entrada no confiable → consulta SQL insegura. El compromiso descrito requiere además permisos excesivos y exposición o reutilización de secretos. |
| Interpretación de evidencias | HTTP, PHP, shell y base de datos son capas distintas. Error, hipótesis y resultado observado deben distinguirse. |
| Prevención | Parametrización → autorización → mínimo privilegio → aislamiento de ficheros y secretos → pruebas de regresión. |

## Mapa temporal

00:00–01:51: incidencias de sala. 01:54–01:13:16: seguimiento de proyectos y debate. 01:13:16–01:36:04: pausa sin contenido transcrito. 01:36:04–02:19:29: continuación y análisis de Validation. 02:19:42–02:23:30: entrega de la práctica y cierre.

Contenido de clase: lo respaldado por la transcripción F001. Ampliación técnica: aclaraciones contrastadas. Inferencia técnica: interpretación razonada. Pendiente de confirmar: dato ambiguo o sin evidencia suficiente.

# IA y práctica 1

## El proyecto de apuntes y tutor

Contenido de clase · 01:54–05:32. Se comenta el uso de un cliente de terminal y de una API para atender peticiones desde un servidor y consultar información de Obsidian. La transcripción de los nombres y de la invocación es defectuosa: no permite recuperar un comando exacto fiable. La afirmación de que una modalidad resulta más barata se conserva como opinión de la conversación, sin convertirla en una comparación actual de precios.

Aparece una propuesta concreta: un panel de administración para aprobar respuestas y almacenarlas. Si una pregunta ya tiene una respuesta adecuada, se puede reutilizar. Otro participante explica un ejemplo de chatbot con preguntas frecuentes preparadas desde información local y derivación a WhatsApp cuando no resuelve la consulta. Son alternativas discutidas; no se demuestra que todas estén implementadas en vuestro proyecto.

Carlos valora positivamente que el grupo de Chema trabaje con IA local y generación de apuntes, y pregunta cuánto del alcance previsto podrá entregarse. La transcripción menciona a Mariana, Chema y otros compañeros, pero no permite cerrar una lista fiable de integrantes.

## Cómo interpretar estas propuestas

Ampliación técnica · referencias locales GLOS-158 y GLOS-152. Una caché conserva una respuesta para reutilizarla; RAG recupera documentos relevantes y los incorpora al contexto de una respuesta nueva. Ninguno de esos mecanismos implica por sí mismo entrenar el modelo. El ajuste fino sí modifica sus parámetros. Obsidian organiza el conocimiento; el sistema que lo consulta decide qué fragmentos usar y con qué permisos.

Propuesta para la documentación de la práctica, no requisito anunciado por Carlos: describir qué contenido puede responder el tutor, cómo cita las fuentes, quién aprueba una respuesta y cuándo caduca. Una respuesta almacenada debe revisarse si cambian la fuente, los permisos o la pregunta. Conviene medir consultas resueltas localmente, errores y consumo antes de afirmar que se ahorran tokens.

## Un resultado local no acredita toda la arquitectura

En la demostración del SIEM se plantea mantener datos en la empresa mediante un modelo local. Eso expresa el objetivo del grupo. Para acreditar que los datos no salen habría que revisar también conectores, APIs, telemetría y registros; la clase no aporta esa comprobación completa. Tampoco se demuestra que se haya entrenado un modelo propio.

# Recomendaciones para los proyectos

| **Proyecto y tiempo** | **Qué se presenta o propone** |
| --- | --- |
| Forense · 09:27–16:25 | Se presenta análisis de logs o PCAP, correlación, cronología, eventos, severidad y PDF. Carlos pide trazabilidad y un resumen ejecutivo que identifique el activo afectado. Para esta entrega sugiere centrarse en redes; memoria y discos quedan como posible ampliación. |
| QR y URL · 16:42–24:27 | El grupo presenta una web y un MCP que analizan destinos y redirecciones. Carlos propone escanear con cámara y mostrar el resultado antes de abrir la URL. Correo y mayor integración móvil se discuten como ampliaciones. |
| Coches · 48:44–01:03:28 | Se presenta un configurador con modelos 3D, presupuestos y suscripciones simuladas. Carlos valora el alcance acotado, pide enlaces a proveedores y advierte que un indicador visual de carga puede confundir. La API de pago todavía no está disponible según el grupo. |
| SIEM · 01:03:43–01:13:16 | El grupo describe Wazuh, un frontal propio y un asistente con Ollama. Se mencionan pruebas controladas con Atomic Red Team. Carlos prioriza la funcionalidad y la utilidad del asistente antes que el acabado visual. |

## Práctica actual y ampliaciones futuras

Contenido de clase · 11:05–11:25 y 15:40–16:14. Carlos sitúa la reconstrucción de una práctica de laboratorio a partir de su captura de tráfico como idea para la práctica 3. No debe presentarse como requisito general de la práctica 1. En el proyecto de coches también se admite explorar un proyecto diferente más adelante; el calendario completo necesita el enunciado oficial.

## Precisiones de seguridad y licencia

Ampliación técnica · GNU [S3]. La GPL permite modificar software bajo sus condiciones. La frase de la conversación «no se puede tocar Wazuh» no debe aprenderse como una prohibición general. Una conexión por API tampoco resuelve automáticamente todas las obligaciones: hay que revisar componentes, distribución y licencia aplicable.

El debate de 24:29–48:38 se desarrolla en los apartados Phishing e ingeniería social y Cómo reconocer y prevenir el phishing, con ejemplos de clase, precisiones y prevención.

# Phishing e ingeniería social

Contenido de clase · F001, 24:29–48:38. El debate surge del proyecto de análisis de QR y URL. Carlos comenta ejemplos de engaño y de confianza en servicios conocidos; no se aporta una práctica ejecutada por el grupo ni evidencia independiente de los incidentes relatados.

## Conceptos para distinguir

Ampliación técnica · Obsidian, GLOS-129 y GLOS-130. Ingeniería social es la manipulación de personas para que revelen información o realicen una acción insegura. Puede ocurrir por Internet, teléfono o en persona. «Hacking social» es una expresión informal; aquí usamos ingeniería social.

El phishing recurre a la suplantación para obtener información o inducir acciones perjudiciales. Smishing designa el engaño mediante SMS; quishing o QRishing, el que utiliza un QR como vía de entrada. Un QR no es malicioso por su formato: importa su contenido, el destino y lo que se pide después. En cambio, la SQLi afecta a la interpretación de datos dentro de una consulta; no es sinónimo de phishing.

## Ejemplos comentados en la sesión

24:29–25:57 · Se relata un formulario falso de acceso presentado dentro de contenido alojado en un servicio conocido. No se aporta URL ni captura verificable. Aprendizaje defensivo: confiar en la plataforma que aloja una página no basta para confiar en cada formulario publicado por sus usuarios.

28:21–35:12 · Se narran engaños vinculados a QR en contextos cotidianos y a supuestas promociones. La petición inesperada de una cuenta social para consultar información sencilla es una señal de alerta. El porcentaje de cuentas mencionado es parte de una anécdota, no una medida demostrada de eficacia.

35:27–37:42 · Un relato de Red Team ilustra la confianza en la imagen corporativa y en una supuesta autorización interna. Se debate también la resistencia a activar el doble factor y a aceptar restricciones de seguridad. Las simulaciones educativas requieren autorización, alcance acordado y datos de prueba.

39:58–40:44 y 43:30–46:28 · Se contraponen mensajes masivos y engaños dirigidos, y se comenta la confianza que pueden transmitir promociones o publicaciones. No se verifican las cifras de alcance, precios ni la noticia citada. La conclusión útil es verificar la solicitud aunque parezca familiar.

# Cómo reconocer y prevenir el phishing

Ampliación técnica y síntesis defensiva. Las siguientes medidas desarrollan lo debatido; no son pruebas realizadas en la máquina Validation ni nuevos requisitos de la práctica 1.

## Señales de alerta y comprobaciones

Desconfía de accesos o pagos que no encajan con la tarea, premios desproporcionados y peticiones inesperadas de códigos de verificación. Comprueba quién solicita la acción y accede al servicio desde su aplicación o dirección habitual. HTTPS y un logotipo conocido no acreditan por sí solos la legitimidad del contenido. Una URL larga tampoco demuestra fraude.

Antes de abrir un QR, revisa la dirección que muestra el lector y el contexto del soporte. Si dudas de un QR físico, consulta al establecimiento por otro canal. Un analizador de enlaces ayuda a detectar indicios, pero no garantiza que una página sea segura; el destino puede cambiar y una solicitud aparentemente normal puede ser engañosa.

## Protección de las cuentas

Usa contraseñas diferentes y activa MFA. No apruebes solicitudes que no has iniciado ni compartas códigos. Precisión respecto a 36:14–36:25 y 39:27: el doble factor reduce el riesgo, pero no todas sus modalidades resisten igual el phishing. CISA recomienda FIDO/WebAuthn como opción resistente a phishing; eso no convierte la cuenta en inmune a cualquier compromiso. [S8]

## Si has introducido datos

Desde el canal oficial, cambia la contraseña afectada y cualquier reutilizada, revisa las sesiones y los métodos de recuperación, y comunica el incidente al soporte o al equipo de seguridad. Conserva el mensaje y la dirección como evidencia sin volver a interactuar con ellos. Si facilitaste datos bancarios, contacta con tu entidad. Pedir ayuda pronto es más útil que ocultarlo por vergüenza. [S7]

## Precisiones y conexión con la práctica

F001, 41:01–43:27: «offset» parece referirse a OPSEC, seguridad operacional. Las afirmaciones de anonimato absoluto no quedan acreditadas; una VPN o un medio de pago no prueban que una actividad sea imposible de atribuir. F001, 47:38–48:38: tampoco se identifica una norma concreta que permita concluir que toda integración con IA esté prohibida.

Propuesta documental para el analizador QR/URL: mostrar destino y advertencias antes de abrirlo, explicar los límites del resultado y probar con enlaces y cuentas ficticios autorizados. Evitar enviar a servicios externos URL privadas o con tokens. Es una recomendación de diseño, no una funcionalidad ya demostrada.

## Fuentes de esta ampliación

F001: marcas temporales indicadas. Consulta local previa: Referencias\_ChatCiberseguridad, GLOS-129 y GLOS-130. Fuentes oficiales consultadas el 22/09/2026:

S7 · INCIBE · Respuesta ante phishing, smishing y vishing  
https://www.incibe.es/sites/default/files/Cuidadan%C3%ADa/Infograf%C3%ADas/infografia\_nofiarnos\_psv.pdf

S8 · CISA · Implementing Phishing-Resistant MFA  
https://www.cisa.gov/sites/default/files/2023-01/fact-sheet-implementing-phishing-resistant-mfa-508c.pdf

# Entrega de la práctica 1

Contenido de clase · 02:19:42–02:22:54. Estas indicaciones proceden del cierre de la sesión. El PDF oficial que se menciona no está entre los adjuntos recibidos; por tanto, estos apuntes no sustituyen el enunciado ni establecen una rúbrica nueva.

| **Elemento** | **Indicación recogida** |
| --- | --- |
| Canal | La entrega se realiza en Classroom. Carlos aclara que consulta el enlace allí; no pide un envío adicional por otro canal. |
| Documento explicativo | Incluir descripción, funcionalidades, para qué se ha creado la aplicación y qué hace. |
| GitHub | Pegar el enlace del repositorio en la descripción de la entrega. Sirve para que el profesor pueda consultar código cuando lo necesite. |
| Repositorio privado | Compartir acceso con Carlos Gómez. Anuncia que facilitará su usuario; la transcripción no contiene un identificador fiable. |
| Aplicación accesible | Carlos agradece disponer de una aplicación en producción si ya está accesible. La frase no acredita una obligación general de desplegarla públicamente. |
| Fecha | A las 02:20:20 corrige «31» por «30 de este mes». Con la fecha de sesión aportada, apunta al 30/09/2026. Confirmar día y hora en Classroom. |
| Instrucciones oficiales | Al final se confirma que hay un PDF de instrucciones en Classroom y compartido por el grupo. Su contenido no puede reconstruirse a partir de esa mención. |

## Checklist de trabajo para Chema

1. Consultar el PDF y la fecha exacta en Classroom. 2. Explicar el problema que resuelve el tutor y sus funciones realmente disponibles. 3. Diferenciar lo terminado de las mejoras previstas. 4. Añadir el enlace de GitHub y comprobar el acceso del profesor. 5. Describir fuentes, modelo local o API, revisión de respuestas y límites conocidos. Los puntos 2 y 4 reflejan la entrega comentada; el resto concreta una preparación editorial útil.

Carlos dice que, si necesita consultar un repositorio y falta el acceso, contactará con el grupo. No convertir esa explicación de comodidad en permiso para omitir materiales exigidos por el enunciado.

# SQLi y la máquina de la sesión

Contenido de clase · 01:03:38 y 01:36:04–02:19:29. Se retoma la máquina llamada Validation en la transcripción, dentro de Hack The Box. El título de los apuntes conserva el nombre confirmado por Chema, PortSwigger: SQLi I. No se identifica en el adjunto un laboratorio concreto de PortSwigger completado durante esta grabación.

## Qué fallo se analiza

En la revisión del código narrada hacia 02:01:08–02:01:58, Carlos contrapone dos entradas: username y country. Explica que la primera tenía un tratamiento de limpieza y que la segunda se incorporaba inseguramente a una consulta. El hecho de que country aparezca como desplegable no garantiza que la petición recibida por el servidor contenga uno de sus valores previstos.

Ampliación técnica · VUL-001 y OWASP [S1]. Una SQLi aparece cuando datos no confiables pueden alterar la estructura de una consulta. La defensa principal es parametrizar los valores. La validación de tipos y valores permitidos complementa esa separación. La interfaz del navegador no constituye un control de seguridad del servidor.

## Resultados narrados y límites de la evidencia

| **Tramo** | **Resultado o explicación en la transcripción** |
| --- | --- |
| 01:36–01:49 | Se corrige la interpretación de una cadena por la shell y se anuncia que la conexión del laboratorio vuelve a funcionar. Se distingue la petición web del proceso que la atiende. |
| 01:49–01:54 | Se identifica una cuenta de servicio y se contrastan indicios sobre cuentas y directorios. Se anuncia el hallazgo de la primera bandera. |
| 01:55–02:06 | La demostración atribuye el aumento de privilegios a reutilización de una credencial expuesta en configuración y anuncia la segunda bandera. No hay valores de credenciales o flags verificables en el adjunto. |
| 02:06–02:19 | Carlos atribuye interrupciones a una limpieza periódica del laboratorio y cierra con permisos mínimos, protección de entradas y separación de credenciales. |

El adjunto es texto de la conversación: no contiene las capturas ni las salidas completas mostradas en pantalla. Estos resultados se atribuyen a lo narrado en clase. La ausencia de comandos íntegros impide presentar una reproducción exacta o afirmar que se ha verificado experimentalmente el laboratorio.

# Aclaraciones técnicas para estudiar

| **Punto de clase** | **Interpretación precisa** |
| --- | --- |
| HTTP y shell | HTTP describe la comunicación web; PHP se interpreta en el servidor; Bash es un intérprete del sistema. PHP no es el lenguaje del front del navegador. No todos los procesos usan Bash por defecto. |
| Opción de Bash | Ampliación [S4]: la opción -c recibe una cadena de comandos como argumento; las comillas afectan a cómo se agrupan y expanden los argumentos. No equivalen a seguridad de entrada. |
| Codificación | URL encoding representa caracteres para su transporte. No cifra el contenido ni garantiza evitar un WAF. La normalización y el contexto de interpretación importan. |
| Respuesta 404 | Ampliación [S5]: indica que el servidor no encontró una representación del recurso o no desea revelar su existencia. No demuestra un error concreto de Bash; se necesitan registros y contexto de la aplicación. |
| PowerShell en Linux | Ampliación [S6]: el ejecutable habitual es pwsh si está instalado. La transcripción dice «PS»; no debe copiarse como una instrucción fiable de arranque. |
| Identificar Linux | TTL, software web y otros indicios ayudan a formular hipótesis. Un TTL observado por sí solo no identifica de forma concluyente el sistema operativo. |
| Cuentas y directorios | Una carpeta en /home no prueba que siga existiendo una cuenta. Una shell nologin suele restringir el inicio interactivo; las cuentas de servicio también son cuentas del sistema. Deben cotejarse fuentes. |
| Escritura y LFI | Carlos se corrige hacia 02:07:31: describe escritura de un fichero, no inclusión local de ficheros. SQLi, escritura y ejecución son capacidades distintas y no se implican automáticamente. |

La ausencia de Python o de una terminal cómoda no prueba que una escalada sea fácil. Del mismo modo, una cuenta del servicio MySQL, una cuenta autenticada dentro de la base de datos y root del sistema operativo son identidades distintas; compartir nombre o instalar un servicio no demuestra que compartan contraseña.

# Prevención y revisión del laboratorio

## Permisos de cada componente

Ampliación técnica · MySQL [S2]. La escritura de archivos desde MySQL depende de los privilegios de base de datos, las restricciones de secure\_file\_priv y los permisos del proceso del servidor MySQL. No se atribuye automáticamente al usuario de Apache. La ejecución posterior por el servicio web es una operación diferente. Esta distinción corrige la simplificación que aparece hacia 02:11:46–02:13:31.

Contenido de clase · 02:10–02:18. Carlos propone que una aplicación que no necesita subir archivos no pueda escribir en su código desplegado. También insiste en limitar permisos y evitar la reutilización de contraseñas. Son medidas para reducir el impacto; la corrección de la consulta vulnerable sigue siendo necesaria.

| **Control** | **Qué debe comprobarse** |
| --- | --- |
| Consultas | Parametrización en todos los valores, incluido country, y validación del dominio esperado. Una lista negra o la apariencia del formulario no bastan. [S1] |
| Cuenta de base de datos | Permisos ajustados a las operaciones de negocio. Evitar privilegios de administración o de acceso a archivos que no necesite la aplicación. [S1, S2] |
| Código y archivos | Identificar quién escribe y quién interpreta cada archivo. Código desplegado protegido; directorios de datos separados. Impedir el procesamiento de scripts donde se admitan cargas. |
| Secretos | Credenciales diferentes por servicio, rotación tras exposición y acceso limitado al componente que las necesita. Quitar toda lectura de configuración a la aplicación podría romperla. |
| Aislamiento | Una base de datos puede estar en otro servidor y seguir comunicándose con la aplicación mediante acceso restringido. Separarla no elimina por sí solo una SQLi. |
| Detección y retest | Comprobar errores de base de datos, cambios inesperados en código, accesos a secretos y procesos anómalos. Verificar que el registro legítimo sigue funcionando tras corregirlo. |

Precisión: quitar únicamente el bit de ejecución de un archivo PHP no impide necesariamente que el intérprete web lo procese. Hay que controlar la configuración del servicio y la ubicación. Mínimo privilegio y defensa en profundidad contribuyen a la seguridad; Zero Trust abarca además decisiones explícitas de acceso, identidad y contexto.

# Metodología y herramientas

| **Fase de auditoría** | **Aplicación a esta sesión** |
| --- | --- |
| Planificación | Laboratorio educativo referido por el profesor. El adjunto no documenta un alcance de auditoría sobre sistemas reales. |
| Recogida de información | Se recapitulan tecnologías y exploración anterior. Parte de los datos se comenta como trabajo del otro día; no se inventan sus salidas. |
| Análisis de vulnerabilidades | Se relacionan entrada insegura, consulta, permisos y secretos. Se corrigen confusiones entre indicio, hipótesis y hecho demostrado. |
| Pruebas de explotación controladas | La clase narra pruebas en la máquina y resultados. Los apuntes registran impacto y aprendizaje defensivo, sin instrucciones operativas de compromiso. |

## Registro de herramientas

| **Herramienta** | **Objetivo y uso visto** | **Fase y nivel** |
| --- | --- | --- |
| Burp Suite | Inspección de peticiones y discusión de Decoder. | Pruebas controladas · Practicada en la demostración |
| curl y Netcat | Comunicación en el laboratorio, descrita verbalmente. | Pruebas controladas · Practicadas; sintaxis completa no aportada |
| Bash y utilidades Linux | Interpretación de cadenas, identidad y permisos. | Análisis · Practicadas; resultados narrados |
| Obsidian y cliente de IA | Conocimiento local, respuestas y consumo. | Planificación · Mencionadas en seguimiento |
| MCP para QR y URL | Integración presentada por el grupo. | Análisis · Introducida mediante demo |
| Wazuh y Ollama | Eventos y asistente local del proyecto SIEM. | Análisis · Introducidas mediante demo |
| Atomic Red Team | El grupo dice emplearlo en pruebas propias. | Pruebas controladas · Mencionada |
| Hydra | Se propone y se descarta su uso en ese momento. | Análisis · Mencionada, no ejecutada según el relato |

Los niveles describen lo respaldado por la conversación, no el dominio del alumno. No se reconstruyen cargas ni comandos de acceso remoto ausentes o incompletos.

# Glosario y fuentes

| **Término** | **Significado en estos apuntes** |
| --- | --- |
| SQLi | Alteración de una consulta por no separar correctamente datos y código SQL. |
| Consulta parametrizada | Consulta cuya estructura se define separadamente de sus valores. |
| Caché y RAG | Reutilizar una respuesta frente a recuperar información para generar una respuesta fundamentada. |
| Modelo y agente | Modelo que produce respuestas; sistema agente que coordina decisiones y herramientas. |
| PCAP | Archivo de captura de paquetes utilizado como evidencia de tráfico. |
| SIEM y SOC | Plataforma de gestión y correlación de eventos frente a la función o equipo que opera la seguridad. |
| Mínimo privilegio | Conceder a cada identidad solo las operaciones y recursos necesarios. |

## Referencias de esta entrega

F001: transcripción adjunta de Chema, 00:00–02:23:30. Fecha, profesor y título confirmados por Chema. Las marcas temporales de cada apartado permiten localizar su evidencia. La ilustración procede de la ficha Carlos\_Gomez.png del proyecto.

Consulta local previa: Referencias\_ChatCiberseguridad, fichas VUL-001, GLOS-158 y GLOS-152. Se usan como referencias conceptuales internas, sin atribuir su contenido a esta clase. No se incorporan relatos de otras sesiones.

S1 · OWASP · Prevención de SQLi  
https://cheatsheetseries.owasp.org/cheatsheets/SQL\_Injection\_Prevention\_Cheat\_Sheet.html

S2 · MySQL 8.0 · SELECT INTO  
https://dev.mysql.com/doc/refman/8.0/en/select-into.html

S3 · GNU · Preguntas sobre licencias  
https://www.gnu.org/licenses/gpl-faq.html.en

S4 · GNU · Invocación de Bash  
https://www.gnu.org/software/bash/manual/html\_node/Invoking-Bash.html

S5 · IETF · RFC 9110  
https://www.rfc-editor.org/rfc/rfc9110.html

S6 · Microsoft · about Pwsh  
https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about\_pwsh?view=powershell-7.5

Fuentes web consultadas el 22/09/2026 para precisiones concretas. La referencia MySQL 8.0 explica el comportamiento documentado; no acredita la versión de la máquina de clase.

# Resumen y memoria de la sesión

Para la práctica 1, lo más útil de la sesión es fijar el alcance real de la aplicación, explicar sus funcionalidades y facilitar la revisión desde Classroom y GitHub. El bloque de IA propone aprovechar conocimiento local y respuestas revisadas; las mejoras sugeridas a otros grupos no se convierten automáticamente en obligaciones del grupo de Chema.

Para SQLi, la lección es que proteger un único campo no protege toda la aplicación. El servidor debe controlar todas sus entradas, separar los valores de la consulta y limitar las capacidades de cada servicio. El relato de Validation muestra cómo varios fallos pueden acumular impacto; no identifica una versión afectada ni un CVE concreto.

## Pendientes de confirmar

Obtener el PDF oficial de la práctica 1; comprobar fecha y hora límite en Classroom; localizar el usuario de GitHub del profesor; aportar capturas si se desea acreditar salidas concretas. La transcripción incluye nombres y términos mal reconocidos y un salto correspondiente al descanso. El análisis mantiene esas limitaciones sin rellenarlas con datos de otras clases.

## Actualización de memoria del proyecto

| **Categoría** | **Información nueva** | **Certeza** | **Acción futura** |
| --- | --- | --- | --- |
| Sesión | PortSwigger: SQLi I; Carlos Gómez Pintado; 22/09/2026. | Alta | Conservar esta identidad. |
| Práctica 1 | Entrega en Classroom con explicación y enlace de GitHub. | Alta | Contrastar con el PDF oficial. |
| Plazo | Corrección verbal al día 30 de este mes. | Media | Confirmar en Classroom. |
| IA | Panel de aprobación y reutilización de respuestas propuestos. | Alta | Distinguir propuesta de función implementada. |
| Máquina | Validation en HTB; resultados narrados sin capturas adjuntas. | Media | Añadir evidencia visual si se aporta. |
| Seguridad | Parametrización, permisos por servicio y secretos separados. | Alta | Aplicar revisión defensiva al desarrollo. |

Esta memoria pertenece a la sesión. Sus hechos no modifican por sí solos las reglas generales ni los apuntes de otras clases.
