---
tags:
- Auditoría web
date: '2026-09-03'
author: Carlos Gómez
---

# OWASP API Top 10

<p class="note-meta">2026-09-03 · Carlos Gómez</p>

**OWASP API TOP 10**

**La API habla de más**

Seguridad de APIs · Fundamentos, superficie de ataque y OWASP API Security Top 10

| **Dato** | **Valor** |
| --- | --- |
| Fecha de clase | 03/09/2026 |
| Profesor | Carlos Gómez |
| Sesión | OWASP API Top 10: La API habla de más |
| Material principal | Transcripción de la sesión aportada por el alumno |
| Material de apoyo | HTML de clase «Seguridad de APIs y OWASP API Top 10» |
| Práctica | Teoría de APIs; la máquina de API hacking quedó para la sesión siguiente |

| **Criterio de elaboración ·** La transcripción manda sobre el contenido de clase. El HTML se usa para ordenar, completar definiciones y conservar el material que Carlos compartió como apuntes. Las ampliaciones que no aparecen claramente en la explicación oral se identifican como «Material de apoyo de clase». |
| --- |

La sesión tuvo dos bloques diferenciados. En el primero se revisaron proyectos de alumnos para mejorar arquitectura, comunicación técnica y alcance. En el segundo, Carlos introdujo el funcionamiento de las APIs y las conectó con la auditoría web: cómo se construye una petición, cómo viaja hasta el backend, qué papel juegan los endpoints, por qué autenticación y autorización son controles diferentes y por qué una API mal protegida amplía mucho la superficie de ataque.

La idea que atraviesa toda la clase es sencilla: una API no es una “cosa aparte” de una aplicación web; es la interfaz que expone funciones y datos del backend. Si el frontend restringe una acción pero el endpoint no valida permisos en servidor, esa restricción visual no es seguridad.

| **Idea central ·** El cliente no es una fuente de confianza. La seguridad efectiva debe aplicarse en el servidor y en cada endpoint: autenticar quién llama, autorizar qué puede hacer, validar lo que envía y limitar lo que recibe. |
| --- |

- La entrega de la práctica/proyecto se fijó para el 1 de octubre de 2026.
- Carlos indicó que la evaluación tendrá en cuenta el punto de partida, progreso, participación y comprensión de cada alumno, no solo el nivel técnico absoluto del producto final.
- Los grupos que presenten el proyecto en clase partirán de una calificación mínima de 7; el resto de la nota se decidirá con valoración del profesor y votación de compañeros, según lo explicado en la sesión.
- Las presentaciones finales se plantearon con una duración mínima aproximada de 30 minutos por proyecto e incluirían documentación, GitHub, despliegue, toma de decisiones y funcionalidades.

| **Pendiente de confirmar ·** En la transcripción se menciona “el lunes 5” como inicio de las presentaciones tras la entrega del 1 de octubre. No se fija aquí un mes distinto al que implique el calendario real sin confirmarlo en el campus. |
| --- |

El primer proyecto revisado busca recibir alertas de herramientas ya existentes en los SOC de clientes, correlacionarlas y reducir duplicados y ruido. Carlos reformuló la propuesta como un «correlacionador y optimizador de tickets» y propuso integrarlo con un flujo de asignación automática, playbooks y perfiles de analistas.

- Fuentes de datos de seguridad → correlador de eventos → output/ticket.
- Integración sugerida con Jira para generar tickets automáticamente.
- Asignación de tickets según tipología, experiencia previa del analista y carga de trabajo.
- Responsable/supervisor para verificar el cierre del ticket antes de incorporar el caso al conocimiento del sistema.
- Despliegue local del modelo como argumento de seguridad y privacidad: la información no sale de la empresa.

| **Conceptos de IA usados en clase ·** Carlos insistió en utilizar correctamente «human in the loop» para la supervisión humana del aprendizaje/decisiones y «human on the loop» para la supervisión del proceso completo. También pidió explicar qué significa “aprende” en términos técnicos, evitando dejarlo como una frase vaga. |
| --- |

Se habló de Obsidian como base relacional/documental de playbooks y de Neo4j como grafo para representar relaciones y conocimiento aprendido de los casos cerrados. El grupo mencionó Llama/Ollama en local. La sesión subrayó que un sistema de este tipo necesita validación humana porque un ticket cerrado incorrectamente no debe convertirse automáticamente en conocimiento de referencia.

| **Precisión terminológica ·** En la conversación aparecen expresiones como «grafo vectorial Neo4j» y «aprendizaje por castigo». Se conservan como lenguaje de clase, pero no se convierten aquí en una afirmación sobre una arquitectura concreta de ML porque la implementación real del proyecto no quedó detallada. |
| --- |

Como mejora de validación, Carlos propuso montar un honeypot y/o fuentes reales controladas de alertas (por ejemplo Wazuh y Windows Defender) para comprobar si el correlador funciona con eventos que se parezcan más a un entorno real.

El segundo proyecto busca sustituir la formación genérica de concienciación por una experiencia adaptada a la empresa, al departamento y al nivel del usuario. La propuesta combina píldoras breves, minijuegos, evaluación adaptativa y campañas de phishing como verificación posterior.

- Onboarding de la organización mediante un formulario con sector, sistemas operativos, herramientas, procesos y normativas.
- Roles diferenciados: administración de la organización (DPO, RR. HH., sistemas u otro responsable) y empleados.
- Arquitectura multi-tenant: cada organización solo ve sus propios datos; el superadministrador de la plataforma puede gestionar varias organizaciones.
- Evaluación adaptativa tipo CAT según el rendimiento del usuario.
- Gamificación con píldoras, minijuegos y progresión por créditos para evitar que todo se complete de golpe.
- Idea de integrar Teams/Slack u otra herramienta corporativa mediante API para lanzar recordatorios o preguntas breves sobre contenidos ya vistos.
- Importación de empleados mediante Excel/tabla para evitar altas manuales una a una.

| **Principio pedagógico ·** Carlos propuso microformaciones de unos pocos minutos al día, repartidas en el tiempo, en lugar de una sesión larga que el empleado pueda “fumarse” de golpe sin retención. |
| --- |

API significa Application Programming Interface. En la explicación de Carlos, una interfaz centraliza métodos o funciones del código y define cómo otros componentes pueden llamarlos sin necesitar conocer toda la implementación interna.

Ejemplo de clase: un eCommerce puede tener funciones como ver precio, compra, catálogo o categoría. La interfaz expone la operación y los parámetros necesarios; la lógica interna puede consultar una base de datos y devolver únicamente el resultado.

**Estructura conceptual repetida en clase**

| GET /api/v1/<metodo-o-recurso> |
| --- |

El punto concreto al que se envía la petición se denomina endpoint. El endpoint representa una funcionalidad o un recurso disponible a través de la API.

Carlos explicó que las APIs web se entienden mejor con el modelo cliente-servidor. El cliente inicia la comunicación; el servidor contiene los datos y la lógica que procesa la petición y devuelve una respuesta.

| **Elemento** | **Papel en la explicación** |
| --- | --- |
| Cliente | Navegador, aplicación móvil, otro servidor, script o dispositivo IoT que inicia la petición. |
| Servidor / backend | Recibe la petición, autentica/autoriza, ejecuta lógica, consulta datos y construye la respuesta. |
| API | Interfaz que define qué operaciones/endpoints existen y qué datos deben enviarse. |
| Respuesta | Código HTTP, cabeceras y cuerpo; frecuentemente JSON, XML o texto. |

| **No confundir ·** En clase «cliente» no significa “persona que compra”, sino el componente software que realiza la petición: el navegador, la app, un script, etc. |
| --- |

La clase descompuso una llamada en varios elementos. El cliente construye una petición con un método, una URL/endpoint y cabeceras; puede incluir además parámetros o cuerpo. La petición viaja por la red hasta el servidor, donde se comprueba quién llama y qué permisos tiene. El servidor procesa y devuelve un código y una respuesta que el cliente interpreta para actualizar la pantalla.

**Ejemplo didáctico de estructura HTTP; no corresponde a una URL real de la práctica**

| GET /api/v1/catalogo/abrigos HTTP/1.1 Host: https://ejemplo.tld Authorization: Bearer <token> Content-Type: application/json |
| --- |

| **Parte** | **Qué representa** |
| --- | --- |
| Método | Acción solicitada. Carlos mostró GET y POST y mencionó otros métodos como HEAD/OPTIONS y WebSocket en la documentación consultada. |
| Endpoint | Ruta concreta de la función o recurso. |
| Host | Servidor al que va dirigida la petición. |
| Cabeceras | Metadatos/valores de contexto como Authorization, API keys, Content-Type, etc. |
| Parámetros / cuerpo | Datos que el endpoint necesita para ejecutar la operación. |
| Código de respuesta | Resultado HTTP: 200, 404, 429, etc. |
| Cuerpo de respuesta | Datos devueltos, frecuentemente JSON. |

Esta distinción fue una de las ideas más importantes de la sesión y Carlos señaló que aparece con frecuencia en entrevistas técnicas.

| **Concepto** | **Pregunta que responde** | **Ejemplo** |
| --- | --- | --- |
| Autenticación | ¿Quién eres? | Validar usuario/contraseña, token u otra credencial. |
| Autorización | ¿Qué puedes hacer? | Determinar si ese usuario puede leer, modificar o ejecutar una función/recurso concreto. |

Primero debe resolverse la identidad; después se decide qué permisos tiene. Estar correctamente autenticado no implica estar autorizado para cualquier endpoint o dato.

| **Regla de examen ·** Autenticación ≠ autorización. Un token válido puede seguir usándose de forma indebida si la API no verifica el permiso sobre el objeto o la función concreta. |
| --- |

Aunque el usuario no vea una ruta /api en pantalla, el navegador realiza peticiones de red para cargar información dinámica. Carlos abrió las herramientas de desarrollo y destacó la pestaña Network: ahí pueden observarse solicitudes, endpoints, cabeceras, payloads y respuestas.

- La página web actúa como una plantilla que se rellena con la información devuelta por el backend.
- Cambiar filtros, categorías o productos provoca nuevas peticiones; el cliente interpreta las respuestas y actualiza la interfaz.
- Una API puede ser “invisible” para el usuario normal y, aun así, ser observable por quien inspecciona el tráfico.

| **Metodología de auditoría ·** Si una aplicación usa una API, el tráfico de la aplicación es una fuente de enumeración: observar qué endpoints usa, qué parámetros envía y qué respuestas recibe. |
| --- |

La clase utilizó Polymarket como ejemplo de plataforma que documenta públicamente su API para que terceros puedan construir bots e integraciones. Carlos remarcó que la documentación de una API describe métodos, parámetros esperados y estructura de las respuestas.

También explicó que herramientas de desarrollo asistido por IA pueden trabajar a partir de la documentación oficial de una API: se les facilita la URL de documentación y se construye el software utilizando los endpoints documentados. Esto no elimina la necesidad de revisar permisos, límites y seguridad de la integración.

| **Material de apoyo de clase ·** El HTML compartido por Carlos desarrolla REST, GraphQL, SOAP, gRPC, WebSocket y webhooks, además de diferenciar APIs públicas, de socios e internas. Estos conceptos amplían la introducción oral y forman parte del material entregado. |
| --- |

| **Tipo** | **Idea básica del material de apoyo** |
| --- | --- |
| REST | Recursos por URL, métodos HTTP y respuestas normalmente JSON. |
| GraphQL | Un endpoint; el cliente declara campos que necesita. |
| SOAP | Mensajes XML y contrato formal. |
| gRPC | Comunicación binaria sobre HTTP/2, habitual entre servicios. |
| WebSocket | Canal bidireccional persistente. |
| Webhooks | El servidor llama a una URL del receptor cuando ocurre un evento. |

Para Carlos, las APIs son un vector muy relevante porque concentran funciones del backend y a menudo quedan menos protegidas que el frontend. La clase insistió en que no basta con ocultar botones o formularios: un atacante puede construir directamente la petición HTTP.

- Cada endpoint y cada método habilitado.
- Parámetros de ruta y consulta, cuerpo JSON/XML y cabeceras.
- Flujos de registro, login, recuperación y refresco de sesión.
- Versiones antiguas o entornos de prueba que sigan expuestos.
- Integraciones con terceros y webhooks.
- Errores y respuestas que revelen más información de la necesaria.

| **Material de apoyo de clase ·** El HTML resume las familias de riesgo como autorización rota, autenticación débil, exposición de datos, consumo sin límites, manipulación de objetos, configuración insegura, inyección, inventario deficiente y monitorización insuficiente. |
| --- |

Carlos conectó la auditoría de APIs con la enumeración web vista en clases anteriores. Si dirsearch/ffuf/feroxbuster prueban rutas de una web usando diccionarios, el mismo principio puede aplicarse a rutas y endpoints de una API.

La idea no es adivinar sin contexto, sino usar jerarquías y pistas visibles. Ejemplo conceptual: si observamos /api/v1/catalogo/abrigos y la aplicación tiene otras categorías, “abrigos” es una parte potencialmente iterable o sustituible por otros valores plausibles.

**Ejemplo conceptual de enumeración; no es un objetivo real**

| /api/v1/catalogo/abrigos /api/v1/catalogo/pantalones /api/v1/catalogo/<FUZZ> |
| --- |

| **Fase de auditoría ·** Esta actividad pertenece a Recogida de información / Análisis de vulnerabilidades mientras buscamos superficie y comportamientos. No es explotación por sí misma. |
| --- |

La vulnerabilidad que Carlos desarrolló con más detalle fue IDOR (Insecure Direct Object Reference), equivalente en el lenguaje de OWASP API a Broken Object Level Authorization (BOLA). Ocurre cuando un identificador que controla el cliente permite acceder a un objeto que no le corresponde porque el servidor no comprueba la relación entre el usuario autenticado y ese recurso.

**Ejemplo didáctico simplificado a partir del razonamiento de clase**

| GET /api/expediente?id=348 → cambiar 348 por 347 y observar si devuelve datos de otra persona |
| --- |

El criterio es el impacto y la autorización. Cambiar page=3 por page=4 en una paginación no es IDOR si la funcionalidad es pública; cambiar el identificador de un expediente privado y recibir los datos de otra persona sí puede constituir una vulnerabilidad grave.

| **Caso real mencionado en clase ·** Carlos relató incidentes en servicios sanitarios donde una mala autorización sobre identificadores permitió acceso a información clínica de terceros. Los detalles concretos se conservan como relato del profesor; estos apuntes no los presentan como verificación independiente. |
| --- |

La web puede mostrar únicamente funciones permitidas a un usuario, pero la API suele contener más operaciones internas. Si un endpoint administrativo existe y el backend no verifica el rol, ocultar el botón en el frontend no evita que alguien construya la petición manualmente.

Carlos puso ejemplos conceptuales de endpoints internos capaces de listar todos los pedidos o modificar roles. El punto técnico es que la API debe autorizar cada función y cada objeto de manera independiente del frontend.

| **Regla práctica ·** No confíes en la visibilidad de la interfaz. Un endpoint no queda protegido porque el usuario “no tenga botón” para llamarlo. |
| --- |

Carlos explicó que, cuando un objetivo web dispone de aplicación móvil, una auditoría autorizada puede encontrar más información estudiando la app. El ejecutable está en el dispositivo del usuario y puede analizarse mediante técnicas de ingeniería inversa; las llamadas a endpoints, rutas y determinados valores pueden aparecer en el código compilado o en recursos de la aplicación.

La clase mencionó dotPeek como herramienta de descompilación en ciertos entornos y explicó la idea general de decompilar para recuperar clases, métodos y cadenas. La herramienta concreta depende de la plataforma y del tipo de binario; la transcripción no detalla un flujo técnico completo de Android.

| **Pendiente de confirmar ·** No se fija aquí que “todas las llamadas Android deban estar hardcodeadas” ni que dotPeek sea la herramienta estándar para APK. La clase trató el principio de ingeniería inversa y exposición de cadenas/endpoints, no un procedimiento Android completo. |
| --- |

También se discutieron causas por las que el ecosistema móvil puede ampliar el riesgo: ingeniería inversa, posibilidad de sideloading, fragmentación/versiones sin parchear y dispositivos rooteados. La idea clave es que una app descargada queda físicamente disponible para el análisis, a diferencia de parte de la lógica que permanece en el servidor en una web tradicional.

La sesión enlazó la seguridad móvil con el riesgo de dependencias. Un software propio puede estar correctamente diseñado y resultar vulnerable porque incorpora una librería con una vulnerabilidad crítica.

Carlos utilizó Log4j/Log4Shell y Minecraft como ejemplo conceptual de cómo una dependencia vulnerable puede comprometer aplicaciones que la incluyen. La conclusión fue que la seguridad debe abarcar también librerías, frameworks y dependencias, no solo el código escrito por el equipo.

| **Buena práctica ·** Inventariar dependencias, mantenerlas actualizadas y vigilar vulnerabilidades conocidas forma parte de la superficie real de una aplicación. |
| --- |

El HTML de clase desarrolla el OWASP API Security Top 10 en su edición 2019 y menciona que la edición 2023 reorganiza algunos riesgos. La sesión oral se centró sobre todo en los fundamentos y en IDOR/BOLA, pero Carlos entregó este material como guía para continuar el aprendizaje.

| **Ref. del material** | **Riesgo** | **Idea principal** |
| --- | --- | --- |
| API1:2019 | Broken Object Level Authorization | Acceder a objetos de otros manipulando identificadores sin control de propiedad. |
| API2:2019 | Broken User Authentication | Login, recuperación o tokens mal implementados. |
| API3:2019 | Excessive Data Exposure | La API devuelve más datos de los que necesita el cliente. |
| API4:2019 | Lack of Resources & Rate Limiting | Faltan límites de frecuencia, tamaño o consumo. |
| API5:2019 | Broken Function Level Authorization | Usuarios alcanzan funciones administrativas sin permiso. |
| API6:2019 | Mass Assignment | El backend acepta campos que el cliente no debería poder modificar. |
| API7:2019 | Security Misconfiguration | TLS/CORS/errores/configuración/defaults inseguros. |
| API8:2019 | Injection | Entrada no fiable llega a SQL/NoSQL/comandos/LDAP/XML. |
| API9:2019 | Improper Assets Management | Versiones y entornos olvidados o sin inventario. |
| API10:2019 | Insufficient Logging & Monitoring | Ataques no registrados ni detectados a tiempo. |

| **Separación de fuentes ·** La lista API1–API10 anterior procede del HTML que Carlos compartió. No se afirma que todos esos diez puntos se desarrollasen verbalmente durante esta sesión. |
| --- |

| **Elemento** | **Uso** |
| --- | --- |
| GET | Leer/obtener información. |
| POST | Crear un recurso o ejecutar una acción. |
| PUT | Reemplazar un recurso. |
| PATCH | Modificar parcialmente. |
| DELETE | Eliminar un recurso. |
| Authorization | Transportar credenciales/tokens de acceso. |
| Content-Type | Indicar el formato del cuerpo. |
| JSON | Formato habitual de intercambio de datos en APIs web. |
| XML | Formato usado en algunos protocolos/servicios; requiere parsers seguros. |

Durante la explicación oral, Carlos mostró especialmente GET, POST, el uso de cabeceras y respuestas JSON. El HTML amplía la tabla con PUT, PATCH, DELETE y formatos adicionales.

Al final de la clase se mencionaron JWT, cookies de sesión, limpieza de cabeceras, protección de rutas, límites temporales y CORS como elementos que estaban aplicando algunos alumnos en sus propios proyectos.

Carlos remarcó que JWT no es “seguro por existir”: una implementación incorrecta puede fallar. La seguridad depende de cómo se validan firma, algoritmo, caducidad, claves y contexto de uso.

| **Pendiente de confirmar ·** La explicación final mezcla diseños concretos de alumnos y comentarios de implementación. No se convierte aquí en una arquitectura recomendada universal; debe revisarse caso por caso. |
| --- |

Carlos advirtió sobre el riesgo de desplegar rápidamente aplicaciones generadas con ayuda de IA dejando permisos demasiado amplios. Mencionó Supabase y el endpoint de registro como ejemplo de cómo una configuración por defecto o una configuración no revisada puede dejar funciones accesibles más allá de lo previsto.

| **Lección ·** La IA puede acelerar el desarrollo, pero no sustituye la revisión de autenticación, autorización, permisos y configuración. “Funciona” no significa “está securizado”. |
| --- |

| **Fase** | **Aplicación en APIs** |
| --- | --- |
| Planificación | Definir alcance: dominios, aplicaciones móviles, endpoints, versiones, cuentas/roles de prueba y acciones permitidas. |
| Recogida de información | Identificar API, observar tráfico, documentación, endpoints, versiones, parámetros y métodos. |
| Análisis de vulnerabilidades | Comparar comportamiento entre usuarios/roles, modificar identificadores, campos, métodos y revisar controles. |
| Pruebas de explotación controladas | Demostrar de forma mínima y autorizada el impacto de un vector confirmado, evitando extracción masiva o acciones innecesarias. |

| **Alcance ·** Carlos puso ejemplos de auditoría real y de aplicaciones móviles para explicar vectores. Estos apuntes mantienen el trabajo práctico dentro de laboratorios, CTF o auditorías expresamente autorizadas. |
| --- |

1. Descubrir endpoints mediante documentación, Network del navegador, tráfico de la app, JavaScript y, cuando esté autorizado, análisis del cliente móvil.
2. Identificar roles y conseguir cuentas de prueba representativas.
3. Capturar una petición legítima y conservarla como línea base.
4. Cambiar una sola variable cada vez: identificador, método, campo, tamaño, versión, token/rol o cabecera.
5. Comparar código de estado, tamaño, campos y comportamiento de la respuesta.
6. Confirmar autorización en servidor y no asumir que una diferencia visual equivale a vulnerabilidad.
7. Documentar petición, respuesta, impacto y mitigación mínima.

| **Material de apoyo de clase ·** El HTML propone Burp Suite/OWASP ZAP, Postman/Hoppscotch/Insomnia, mitmproxy, ffuf/feroxbuster, Nuclei, jwt\_tool y escáneres basados en OpenAPI como herramientas habituales. |
| --- |

- Confiar en que el frontend aplica la seguridad.
- Confundir “usuario autenticado” con “usuario autorizado”.
- Devolver objetos completos y ocultar campos solo en la interfaz.
- Aceptar del cliente roles, identificadores o campos sensibles sin validarlos en servidor.
- Mantener endpoints/versions antiguas sin inventario ni controles equivalentes.
- Usar secretos o credenciales incrustados en aplicaciones cliente.
- Dar por seguro un sistema solo porque las peticiones legítimas funcionan.
- Confiar ciegamente en código generado por IA o configuraciones por defecto.
- Denegar por defecto y autorizar explícitamente cada objeto y función.
- Validar entrada en servidor con esquemas/tipos estrictos.
- Devolver solo los campos necesarios.
- Aplicar rate limiting, límites de tamaño y tiempos de operación.
- Mantener inventario de APIs, versiones y entornos.
- Registrar autenticaciones fallidas, accesos denegados y anomalías relevantes.
- Revisar dependencias y configuración como parte del ciclo de desarrollo.
- Probar con varias cuentas/roles y automatizar tests de autorización.
- ☐ Puedo explicar qué significa API y qué problema resuelve.
- ☐ Sé distinguir cliente, servidor, frontend, backend y API.
- ☐ Entiendo qué es un endpoint y cómo se estructura una petición HTTP.
- ☐ Puedo explicar la diferencia entre autenticación y autorización.
- ☐ Sé por qué ocultar un botón no protege un endpoint.
- ☐ Entiendo qué aporta la pestaña Network para descubrir llamadas de API.
- ☐ Puedo explicar por qué una app móvil puede ampliar la superficie de exposición.
- ☐ Entiendo el concepto de ingeniería inversa y por qué no deben incrustarse secretos en el cliente.
- ☐ Sé explicar qué es IDOR/BOLA y cuándo cambiar un ID sí constituye una vulnerabilidad.
- ☐ Puedo relacionar API1 y API5 con autorización a nivel de objeto y función.
- ☐ Recuerdo las diez categorías del OWASP API Security Top 10 2019 del material de clase.
- ☐ Entiendo que rate limiting, validación, logging e inventario de versiones son controles de seguridad.
- ☐ Puedo situar enumeración de endpoints y explotación controlada en las fases correctas de auditoría.
- ☐ Sé por qué el código generado con IA necesita revisión de permisos y configuración.

| **Herramienta / tecnología** | **Objetivo** | **Fase** | **Nivel** | **Notas** |
| --- | --- | --- | --- | --- |
| DevTools / Network | Observar peticiones, endpoints, headers y respuestas | Recogida / Análisis | Practicada | Usada conceptualmente para localizar llamadas API. |
| Burp Suite | Interceptar y modificar tráfico HTTP | Análisis / Explotación controlada | Recurrente | Conectado con la metodología web anterior. |
| curl | Realizar peticiones HTTP desde terminal | Análisis | Recurrente | Carlos lo usó como ejemplo al leer documentación de APIs. |
| dirsearch / ffuf / feroxbuster | Enumerar rutas/endpoints | Recogida / Análisis | Practicada | Mencionadas como extensión natural de la enumeración web. |
| dotPeek | Descompilación/inspección de binarios compatibles | Recogida / Análisis | Mencionada | No se desarrolló un procedimiento Android concreto. |
| Neo4j | Grafo para el proyecto de SOC | Proyecto | Introducida | Arquitectura del proyecto del grupo. |
| Obsidian | Base documental/playbooks del proyecto SOC | Proyecto | Introducida | Se mostró una bóveda con MITRE/playbooks/assets. |
| Ollama / Llama | Modelo local para agente | Proyecto | Introducida | Orientado a mantener datos dentro de la empresa. |
| Wazuh | Fuente/monitorización para validar alertas | Proyecto | Mencionada | Propuesta para fase de pruebas/integración. |
| Jira | Gestión/asignación de tickets | Proyecto | Mencionada | Propuesta de integración. |
| Supabase | Backend/base de datos en desarrollo moderno | Seguridad de desarrollo | Mencionada | Usada como ejemplo de revisar permisos/endpoints. |
| JWT | Token de autenticación/autorización | Seguridad de APIs | Introducida | La seguridad depende de una validación correcta. |

| **Término** | **Definición para estudiar** |
| --- | --- |
| API | Interfaz mediante la cual componentes de software llaman funciones o recursos de otro componente. |
| Endpoint | Ruta concreta de una API que representa una operación/recurso. |
| Cliente | Componente que inicia la petición: navegador, app, script, dispositivo, etc. |
| Backend | Servidor y lógica que procesa las peticiones y accede a los datos. |
| Header | Metadato de la petición/respuesta HTTP. |
| Payload | Datos enviados en el cuerpo de una petición o recibidos en una respuesta. |
| Autenticación | Verificar quién es el actor. |
| Autorización | Verificar qué está autorizado a hacer ese actor. |
| IDOR / BOLA | Fallo de autorización sobre objetos referenciados por identificadores controlables. |
| BFLA | Fallo de autorización a nivel de función/operación. |
| Rate limiting | Límite de peticiones o consumo por cliente/tiempo. |
| JWT | Token firmado que transporta claims; debe validarse correctamente. |
| Multi-tenant | Arquitectura en la que varias organizaciones comparten plataforma manteniendo separación lógica de datos. |
| Human in the loop | Humano dentro del proceso de decisión/aprendizaje que revisa o valida resultados. |
| Playbook | Procedimiento documentado para responder a un tipo de incidente o caso de uso. |

La clase conecta directamente con el repaso del 02/09: la misma metodología de enumeración web se extiende a APIs. Interactuar con la aplicación, observar el tráfico, enumerar rutas, formular hipótesis y validar cada hallazgo sigue siendo el patrón general.

La sesión terminó indicando que el día siguiente se realizaría una máquina centrada en API hacking, con varios vectores diferentes. Por tanto, este apunte debe utilizarse como fundamento teórico antes de la práctica.

| **Categoría** | **Información nueva** | **Certeza** | **Acción futura** |
| --- | --- | --- | --- |
| Sesión | 03/09/2026 · «OWASP API Top 10: La API habla de más» · profesor Carlos Gómez. | Alta | Conectar con la práctica de API hacking de la siguiente sesión. |
| APIs | Cliente-servidor, endpoints, métodos, cabeceras, parámetros, respuestas y JSON como fundamentos. | Alta | Usar como base para laboratorios de API. |
| Seguridad | Autenticación y autorización deben diferenciarse y validarse en servidor. | Alta | Reforzar especialmente BOLA/IDOR y BFLA. |
| Metodología | Enumerar endpoints como extensión de enumeración web; validar objeto/función con varias cuentas/roles. | Alta | Aplicar en máquinas autorizadas. |
| Mobile | La app descargada puede analizarse; endpoints/secretos no deben depender de ocultación en cliente. | Alta | Profundizar en herramientas Android/iOS cuando haya práctica específica. |
| Dependencias | Una vulnerabilidad en una librería puede afectar en cascada al producto. | Alta | Mantener relación con supply chain/SCA. |
| OWASP API | HTML de clase incluye OWASP API Security Top 10 2019 y ejercicios. | Alta | Repasar API1–API10 antes del laboratorio. |
| Proyecto SOC | Correlación de alertas, playbooks, supervisión humana, IA local e integración con Jira/Wazuh. | Alta | Seguir evolución del proyecto si vuelve a aparecer. |
| Proyecto awareness | Formación adaptada, multi-tenant, CAT, gamificación y posible integración vía Teams/Slack. | Alta | Seguir evolución del proyecto si vuelve a aparecer. |
| Pendiente | Nombre exacto de la vulnerabilidad Android mencionada al inicio (“Unison Exploitation” en transcripción) no queda suficientemente claro. | Media | Confirmar solo si se necesita documentarla en detalle. |

| **Resumen final ·** Una API es una superficie de ataque directamente conectada con la lógica y los datos del backend. Para estudiarla: identifica endpoints, entiende la petición, separa autenticación de autorización, no confíes en el cliente y comprueba que cada objeto y cada función están autorizados en servidor. |
| --- |
