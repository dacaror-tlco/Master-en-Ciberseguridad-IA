---
tags:
- Auditoría web
date: '2026-09-09'
author: Carlos Gómez
---

# SQL despliegue seguro y consultas

<p class="note-meta">2026-09-09 · Carlos Gómez</p>

![Portada original proporcionada por Chema para la sesión del 09/09/2026.](../../assets/img/sql-despliegue-seguro-y-consultas/img001.png)

# Sesión 09/09/2026 — SQL, despliegue seguro y arquitectura de base de datos

**Profesor:** Carlos Gómez

**Fecha de clase:** 09/09/2026

**Título:** descriptivo, construido a partir del contenido de la sesión; no consta un título oficial en la transcripción.

|  |
| --- |
| **INFO — Documento complementario:** Se ha creado un manual específico de SQL con todas las consultas vistas, sintaxis corregida y ampliaciones para estudio. |

**Abrir manual SQL en Drive:** [Manual SQL específico — 09/09/2026](https://docs.google.com/document/d/10w7jBc_BC9nxtm87wFu2S7uQJN3jgswE/edit?usp=drivesdk)

# 1. Objetivos de la sesión

- Debatir sobre los riesgos, límites y evolución reciente de la inteligencia artificial y el papel del human-in-the-loop.
- Diseñar una arquitectura web segmentada con un servidor público y un servidor de base de datos aislado en red privada.
- Desplegar servidores Ubuntu en Hetzner y trabajar con red privada, claves SSH, API tokens y firewalls.
- Instalar MySQL, crear una base de datos de práctica de un taller mecánico y exponer un panel web de consultas.
- Practicar consultas SQL esenciales como SHOW DATABASES, SHOW TABLES, SELECT, WHERE, AND, BETWEEN, ORDER BY, LIMIT, operaciones y alias.
- Relacionar estas consultas con la comprensión posterior de SQL Injection.

# 2. Resumen de la sesión

La clase tuvo dos bloques claramente diferenciados. El primero fue un debate de actualidad sobre la aceleración de los modelos de IA, el riesgo de sistemas auto-mejorables, el impacto laboral y la necesidad de mantener supervisión humana. El segundo fue técnico: se diseñó y desplegó una pequeña arquitectura segura en Hetzner con un web server expuesto y un servidor MySQL en red privada, se restringió el tráfico con firewalls y se creó una base de datos de taller mecánico para practicar SQL.

El bloque final se centró en consultas SQL de lectura y filtrado. El profesor buscó que el alumnado entienda qué consulta hay detrás de una aplicación antes de pasar a laboratorios de SQL Injection manual.

# 3. Actualidad de IA comentada en clase

## 3.1 Hecho de actualidad verificado

Se comentó la dimisión de Jacob Coxon, investigador que había trabajado en preentrenamiento en OpenAI y Anthropic, y sus advertencias sobre una carrera hacia sistemas auto-mejorables. También se mencionó la respuesta de Evan Hubinger, responsable de Alignment Science en Anthropic, quien expresó públicamente una estimación personal superior al 10 % de riesgo existencial en la próxima década.

|  |
| --- |
| **ADVERTENCIA — Separación entre hecho y opinión:** La existencia de esas declaraciones está verificada. Las conclusiones sobre si la superinteligencia llegará, cuándo lo hará o qué consecuencias tendrá son escenarios debatidos y no hechos demostrados. |

## 3.2 Ideas del debate

- La IA se trató como herramienta que aumenta productividad, no como sustituto automático del conocimiento técnico.
- Se insistió en que una persona que conoce arquitectura, APIs, webhooks, repositorios y despliegue puede pedir mejores soluciones a un agente.
- Se debatió sobre productividad, salarios, reorganización de puestos y aparición de perfiles de IA, datos y ciberseguridad.
- Se habló del coste de los tokens y del posible crecimiento de modelos locales como alternativa futura.
- Varios nombres/versiones de modelos aparecen distorsionados en la transcripción; no se fijan como información técnica confirmada.

|  |
| --- |
| **BUENA PRÁCTICA — Concepto clave:** Human-in-the-loop: incluso cuando un agente genera código o ejecuta tareas, la arquitectura, los permisos, la seguridad, las pruebas y la revisión final siguen necesitando supervisión humana. |

# 4. Arquitectura desplegada

|  |
| --- |
| Internet / usuario  ↓ HTTPS 443 [ Web Server / DMZ ]  ↕ red privada [ Firewall / reglas ]  ↕ TCP 3306 [ MySQL / BBDD Server ]  (sin IP pública) |

La idea central fue reducir la superficie de exposición. El servidor web tiene una interfaz pública y otra privada. El servidor de base de datos se mantiene en la red interna y se accede a él a través del web server, no directamente desde Internet.

|  |
| --- |
| **BUENA PRÁCTICA — Principio de seguridad:** Segmentación + mínimo privilegio + deny-by-default: bloquear por defecto y habilitar únicamente los flujos necesarios. |

# 5. Relación con las fases de auditoría

| **Fase** | **Aplicación en la sesión** |
| --- | --- |
| Planificación | Definición de la arquitectura, separación DMZ/red interna, roles de web server y BBDD server y puertos necesarios. |
| Recogida de información | Comprobación de conectividad, ping/traceroute, observación del TTL y revisión de recursos, interfaces y puertos. |
| Análisis de vulnerabilidades | Identificación de riesgos: BBDD expuesta a Internet, puertos innecesarios, salida irrestricta, API tokens y claves privadas. |
| Pruebas de explotación controladas | No se ejecutó una explotación real en esta sesión. Las reverse shells y SQL Injection se usaron como escenarios para justificar controles y preparar prácticas posteriores. |

# 6. Hetzner: proyecto, servidores y red privada

- Se creó un proyecto específico para agrupar recursos relacionados.
- Se desplegaron dos servidores Ubuntu: web server y BBDD server.
- Se creó una private network en el rango 10.10.10.0/24 como red interna de práctica.
- El web server mantiene conectividad pública y privada; al BBDD server se le retiró la red pública para aislarlo.
- Se recalcó activar 2FA para servicios críticos y cuentas de infraestructura.

|  |
| --- |
| **INFO — No inventar IPs:** La transcripción contiene una IP pública mostrada como ejemplo durante la explicación. No se conserva en estos apuntes porque no aporta al aprendizaje y podría corresponder a un recurso efímero real. |

# 7. SSH y gestión de claves

Se repasó el uso de autenticación por clave pública para acceder a los servidores. La transcripción distorsiona “SSH” como “SCH/CCH” en varios puntos; se corrige por contexto técnico.

**Generar un par de claves SSH**

|  |
| --- |
| ssh-keygen |

**Forma general de conexión usada como referencia**

|  |
| --- |
| ssh -i <ruta\_clave\_privada> root@<IP\_SERVIDOR> |

|  |
| --- |
| **RIESGO — Clave pública vs privada:** La clave pública se instala en el servidor. La clave privada permanece en el equipo del usuario y no debe compartirse ni mostrarse. Durante la clase el profesor corrigió explícitamente una confusión inicial entre ambas. |

# 8. API tokens para automatización

Se generó un API token del proyecto de Hetzner para que un agente pudiera automatizar tareas como creación/configuración de firewalls y gestión de recursos. El token estaba limitado al proyecto, lo que reduce el alcance respecto a una credencial global.

|  |
| --- |
| **RIESGO — Riesgo:** Dar un API token a un agente o mostrarlo en una clase es una decisión de seguridad relevante. Debe aplicarse mínimo privilegio, alcance limitado, almacenamiento seguro, rotación y revocación posterior. No se incluye ningún valor de token en estos apuntes. |

# 9. Firewalls: inbound, outbound y zero trust

- Inbound: tráfico que entra al servidor. Se trabajó con reglas para permitir solo servicios necesarios.
- Outbound: tráfico que sale del servidor. Se planteó restringirlo para dificultar reverse shells y exfiltración.
- Web server: se discutieron 22/SSH, 80/HTTP y 443/HTTPS como puertos necesarios durante el despliegue.
- BBDD server: el flujo esencial desde el web server hacia MySQL fue TCP/3306.
- La estrategia explicada fue “bloqueo todo y habilito lo que sí permito”.

|  |
| --- |
| **ADVERTENCIA — Matiz técnico:** Bloquear todo el tráfico saliente puede romper DNS, NTP, actualizaciones, repositorios y otros servicios. La política correcta es permitir explícitamente las salidas necesarias y revisar dependencias. |

El profesor también comentó que una reverse shell puede encapsularse mediante protocolos permitidos y que HTTPS/WebSocket puede complicar el filtrado. La conclusión práctica es que un firewall reduce superficie, pero no sustituye el hardening, el control de aplicaciones, la monitorización ni la gestión de vulnerabilidades.

# 10. TTL, ping y traceroute

Se observó un TTL de respuesta inferior al valor inicial típico de Linux y se relacionó con los saltos de red. Esto se utilizó como recordatorio de que el TTL se decrementa al atravesar routers.

|  |
| --- |
| **INFO — Inferencia técnica:** Usar TTL para identificar el sistema operativo es una heurística, no una prueba concluyente: el valor puede verse alterado por la red, configuración del host, túneles o dispositivos intermedios. |

**Clase — visualizar saltos de red**

|  |
| --- |
| traceroute <IP\_SERVIDOR> |

# 11. NTP y Kerberos

Tras el descanso se revisó una regla de firewall para NTP (UDP/123). El profesor conectó esta sincronización con Kerberos: los tickets incluyen marcas de tiempo y una diferencia de reloj excesiva puede provocar errores de autenticación.

|  |
| --- |
| **ADVERTENCIA — Corrección técnica verificada:** La transcripción habla de diferencias de “milésimas de segundo”. En Windows/Kerberos la tolerancia predeterminada habitual es de 5 minutos. Aun así, sincronizar correctamente el tiempo sigue siendo esencial, especialmente en laboratorios de Active Directory. |

# 12. MySQL y base de datos del taller

- Se instaló MySQL en el BBDD server.
- Se habilitó la comunicación interna por TCP/3306.
- Se generó mediante scripts una base de datos de taller mecánico con aproximadamente 40 000 filas, unas 10 tablas y distintos usuarios/roles según la explicación del profesor.
- La base de datos se utilizó como dataset de práctica para consultas y para una web sencilla de consulta.

|  |
| --- |
| **INFO — Evidencia:** La transcripción indica una generación cercana a 39 990 filas y menciona ejemplos como 3 000 clientes y 4 200 vehículos. Se conserva el orden de magnitud, sin convertir esos valores en inventario exacto del script porque el script no se adjuntó a esta conversación. |

# 13. Front, back y consulta SQL desde una web

Se creó una web sencilla en el web server para ejecutar consultas y visualizar resultados. El objetivo pedagógico era mostrar cómo el front envía una entrada, el back construye o ejecuta una query y la base de datos devuelve filas.

**Modelo conceptual explicado en clase**

|  |
| --- |
| SELECT <columnas> FROM <tabla> WHERE <campo> = <entrada>; |

|  |
| --- |
| **BUENA PRÁCTICA — Conexión con SQLi:** Comprender la query legítima permite entender después cómo una entrada controlada por el usuario puede modificar la lógica de una consulta vulnerable. En una aplicación real deben usarse prepared statements y validación adecuada. |

# 14. Consultas SQL vistas en clase

|  |
| --- |
| SHOW DATABASES; USE taller\_mecanico; SHOW TABLES; |

|  |
| --- |
| SELECT \* FROM empleados; SELECT nombre FROM empleados; |

|  |
| --- |
| SELECT \* FROM empleados WHERE tarifa\_hora = 45.30; |

|  |
| --- |
| SELECT \* FROM empleados WHERE tarifa\_hora > 40  AND tarifa\_hora < 70 ORDER BY tarifa\_hora ASC; |

|  |
| --- |
| SELECT \* FROM empleados WHERE tarifa\_hora BETWEEN 40 AND 70 ORDER BY tarifa\_hora ASC; |

|  |
| --- |
| SELECT \* FROM clientes LIMIT 5; |

|  |
| --- |
| SELECT salario\_bruto\_anual \* 1.33 AS coste\_empresa FROM empleados; |

|  |
| --- |
| **ADVERTENCIA — Anidamiento:** Se intentó explicar una consulta anidada, pero el ejemplo oral quedó sintácticamente incompleto en la transcripción. No se presenta como comando válido; el manual SQL complementario incluye una subconsulta correcta. |

# 15. Puntos de SQL que conviene memorizar

| **Elemento** | **Idea** |
| --- | --- |
| SELECT | qué columnas o expresiones devolver |
| FROM | de qué tabla(s) salen los datos |
| WHERE | filtrar filas |
| AND / OR | combinar condiciones |
| BETWEEN | rango inclusivo |
| ORDER BY | ordenar por columna/expresión |
| ASC / DESC | dirección del orden |
| LIMIT | limitar filas en MySQL |
| AS | alias para columnas/tablas |
| SUM / COUNT / AVG | agregaciones |
| JOIN | relacionar tablas |
| Subconsulta | usar el resultado de un SELECT dentro de otra consulta |

# 16. Riesgos, errores y buenas prácticas

| **Situación** | **Conclusión** |
| --- | --- |
| BBDD con IP pública | Reducir exposición; preferir red privada cuando el caso lo permita. |
| SSH abierto a Internet | Restringir origen, usar claves y considerar bastion/VPN según arquitectura. |
| Token de API compartido | Limitar alcance, almacenar de forma segura y revocar al terminar. |
| Egress abierto | Aplicar listas de salidas necesarias; ayuda contra C2/exfiltración pero requiere diseño. |
| SELECT \* en aplicación | Evitar por defecto; solicitar solo columnas necesarias. |
| SQL construido por concatenación | Usar consultas parametrizadas/prepared statements. |
| Confiar en IA sin revisar | Verificar comandos, permisos, arquitectura, costes y efectos antes de aplicar. |

# 17. Herramientas y tecnologías de la sesión

| **Herramienta / tecnología** | **Objetivo** | **Fase de auditoría** | **Uso visto** | **Nivel** | **Notas** |
| --- | --- | --- | --- | --- | --- |
| Hetzner Cloud | Desplegar infraestructura | Planificación | Proyecto, servidores, red privada, firewalls, API token | Practicada | Infraestructura temporal de clase. |
| Ubuntu Server | Sistema de los servidores | Planificación | Web server y BBDD server | Practicada | Despliegue cloud. |
| SSH / ssh-keygen | Administración remota | Recogida de información | Par de claves y acceso remoto | Practicada | Diferenciar pública/privada. |
| traceroute | Ver saltos de red | Recogida de información | Análisis de ruta y TTL | Introducida | Heurística de red. |
| Firewall Hetzner | Reducir exposición | Análisis de vulnerabilidades | Reglas inbound/outbound | Practicada | Deny-by-default. |
| MySQL | SGBD relacional | Análisis de vulnerabilidades | Instalación, 3306 y consultas | Practicada | Base del bloque SQLi. |
| Claude / agente | Automatizar despliegue | Planificación | Configuración de servidores/firewalls/scripts | Practicada | Requiere supervisión humana. |
| WebGoat | Recurso extra SQLi | Pruebas de explotación controladas | Recomendado para practicar | Mencionada | No se ejecutó en clase. |
| PortSwigger Web Security Academy | Labs SQLi | Pruebas de explotación controladas | Previsto para siguientes sesiones | Recurrente | Práctica posterior. |
| Hack The Box | Máquinas SQLi | Pruebas de explotación controladas | Previsto para siguientes sesiones | Recurrente | No se resolvió una máquina en esta sesión. |

# 18. Conexión con sesiones anteriores y siguientes

- La sesión anterior con Carlos Castillo repasó SQLMap y preparó el paso hacia SQL Injection manual.
- Esta sesión aportó los fundamentos de SQL necesarios para comprender la consulta que existe detrás de una vulnerabilidad.
- Las siguientes clases se orientan a laboratorios de PortSwigger y máquinas donde se aplicará SQLi de forma práctica.

# 19. Pendientes y tareas

- Practicar consultas SQL sobre el script de taller mecánico.
- El profesor sugirió generar aproximadamente 50 ejercicios de dificultad progresiva con pistas y explicaciones.
- Revisar el manual SQL complementario creado junto a estos apuntes.
- Continuar con laboratorios de SQL Injection manual en próximas sesiones.
- Práctica 1: en la sesión se recordó como fecha límite el 1 de octubre; conviene contrastarlo con el campus si cambia.

# 20. Checklist de repaso

- Puedo explicar por qué el servidor de BBDD no debería estar expuesto directamente.
- Distingo interfaz pública, red privada y segmentación.
- Sé para qué sirven los puertos 22, 80, 443, 3306 y 123 en el contexto de la sesión.
- Diferencio clave pública y privada SSH.
- Entiendo el riesgo de un API token y el principio de mínimo privilegio.
- Sé distinguir inbound y outbound y explicar por qué se restringe egress.
- Entiendo por qué NTP importa para Kerberos.
- Sé usar SHOW DATABASES, USE y SHOW TABLES.
- Sé construir SELECT con WHERE, AND, BETWEEN, ORDER BY y LIMIT.
- Sé usar AS para alias y hacer un cálculo sin modificar la base de datos.
- Sé relacionar estos fundamentos con SQL Injection sin confundir enumeración con explotación.

# 21. Glosario

| **Término** | **Definición** |
| --- | --- |
| DMZ | Zona de red intermedia destinada a sistemas expuestos o semiexpuestos, separada de redes internas. |
| Segmentación | Separación de redes/recursos para limitar visibilidad y movimiento lateral. |
| Inbound | Tráfico entrante hacia un sistema. |
| Outbound | Tráfico saliente desde un sistema. |
| Egress filtering | Control del tráfico de salida. |
| SSH | Protocolo de administración remota segura. |
| API token | Credencial que autoriza llamadas a una API con un alcance determinado. |
| MySQL | SGBD relacional utilizado en la práctica. |
| NTP | Network Time Protocol, usado para sincronización horaria. |
| Kerberos | Protocolo de autenticación basado en tickets y marcas de tiempo. |
| SQL | Lenguaje declarativo para trabajar con bases de datos relacionales. |
| SQL Injection | Vulnerabilidad donde una entrada altera una consulta SQL por construcción insegura. |
| Prepared statement | Consulta parametrizada que separa estructura SQL y datos. |

# 22. Fuentes y verificación

Fuente principal: transcripción de la sesión proporcionada por Chema. Se han corregido errores evidentes de reconocimiento de voz (por ejemplo SSH, Hetzner, NTP, MySQL) sin inventar salidas, IPs, credenciales ni scripts ausentes.

- **Jorge Sánchez — Manual de SQL:** [abrir fuente](https://jorgesanchez.net/manuales/sql/intro-sql-sql2016.html) — Ampliación SQL; orientado a Oracle.
- **MySQL 8.4 — SELECT:** [abrir fuente](https://dev.mysql.com/doc/refman/8.4/en/select.html)
- **MySQL 8.4 — SHOW DATABASES:** [abrir fuente](https://dev.mysql.com/doc/refman/8.4/en/show-databases.html)
- **MySQL 8.4 — SHOW TABLES:** [abrir fuente](https://dev.mysql.com/doc/refman/8.4/en/show-tables.html)
- **Microsoft Learn — Kerberos y sincronización de reloj:** [abrir fuente](https://learn.microsoft.com/es-es/troubleshoot/windows-server/windows-security/kerberos-authentication-troubleshooting-guidance)
- **AP — dimisión y advertencias de Jacob Coxon:** [abrir fuente](https://apnews.com/article/2ed549e07f2f941600a135070487d83d)

# 23. Actualización de memoria del proyecto

| **Categoría** | **Información nueva** | **Nivel de certeza** | **Acción futura** |
| --- | --- | --- | --- |
| Sesión | 09/09/2026 — profesor Carlos Gómez. | Alta | Conectar con labs SQLi posteriores. |
| Arquitectura | Web server público + BBDD server aislado en red privada /24 con firewalls. | Alta | Reutilizar como patrón de arquitectura segura. |
| Herramientas | Hetzner, SSH, API token, firewall, MySQL, traceroute. | Alta | Actualizar registro de herramientas. |
| SQL | SHOW DATABASES, USE, SHOW TABLES, SELECT, WHERE, AND, BETWEEN, ORDER BY, LIMIT, cálculos y alias. | Alta | Practicar con ejercicios y SQLi manual. |
| Kerberos | NTP/UDP 123 ligado a sincronización; corrección: tolerancia típica de Windows 5 min, no milésimas. | Alta | Recordar antes de labs de AD/Kerberos. |
| Pendiente | El script exacto de taller y sus nombres de columnas completos no se adjuntaron. | Alta | No inventar esquema; usar el script cuando esté disponible. |
| Continuidad | Próximas sesiones: PortSwigger/HTB orientados a SQLi manual. | Media | Confirmar material exacto al recibir la siguiente transcripción. |
