---
tags:
- Auditoría web
---

# Sesion 29 OWASP Web Burp

**Apuntes — Máster de Ciberseguridad Ofensiva (Evolve Academy)**

**Vulnerabilidades Web: OWASP Top 10, CVSS y Reconocimiento Web**

| **Campo** | **Detalle** |
| --- | --- |
| Sesión | Vulnerabilidades Web — OWASP Top 10 2025 + Introducción a Burp Suite |
| Instructor | Carlos (Castillo) |
| Fecha | 29/06/2026 |
| Bloque | Inicio del módulo de Hacking Web (Red Team) |
| Tipo de clase | Mayoritariamente teórica + primera práctica con Burp Suite |

|  |
| --- |
| **INFO**  Esta sesión abre el bloque de **hacking web**, que se extenderá aproximadamente **dos meses**. El instructor avisa de que fue una clase con mucha teoría (metodología) y poca práctica, sentando las bases antes de empezar a explotar máquinas web. |

# **1. Objetivos de la sesión**

- Entender qué es el **OWASP Top 10 (versión 2025)** y para qué sirve realmente en una auditoría.
- Conocer de forma general las 10 categorías de vulnerabilidades web y saber ubicar ejemplos en ellas.
- Introducir **CVSS** como sistema de puntuación de criticidad de las vulnerabilidades.
- Diferenciar la **metodología de informe / cliente** de la **metodología técnica del hacker**.
- Comprender la **metodología de auditoría web** y dónde encaja el análisis de vulnerabilidades.
- Dar los primeros pasos con **Burp Suite**: qué es un proxy, interceptar peticiones y usar el Repeater.

# **2. OWASP Top 10 (2025)**

El **OWASP Top 10** es un estándar que agrupa las **10 categorías de vulnerabilidades web más frecuentes**. Se construye analizando todos los **CVE** publicados durante los últimos años y clasificándolos por tipo (inyección, criptografía, etc.).

|  |
| --- |
| **INFO**  Según lo comentado en clase, la versión de **2025** se publicó en **enero de 2026** y sustituye a la de **2021**, con la que se trabajaba anteriormente. Antes de esa, la referencia conocida era la de **2017** (época del «boom» de SQL Injection, XSS y XXE). |

**¿Para qué sirve realmente?** Para tener un enfoque global y una base metodológica común, sobre todo de cara al **informe** y a la parte burocrática frente al cliente. Demuestra al CISO/CEO que se han revisado las vulnerabilidades más típicas de los últimos años.

|  |
| --- |
| **AVISO**  **No hay que aprenderse el Top 10 de memoria ni obsesionarse con clasificar.** El instructor insiste: en una auditoría real, una vulnerabilidad encadenada puede tocar varias categorías a la vez y es difícil encasillarla. Hoy en día una IA puede asignar la categoría (A06, A07...) al instante. El valor humano está en **entender** la vulnerabilidad y **defender el informe**, no en memorizar etiquetas. |

## **2.1. Las 10 categorías (resumen de clase)**

| **Código** | **Categoría** | **Descripción vista en clase** |
| --- | --- | --- |
| A01 | Control de acceso defectuoso (Broken Access Control) | Acceder a datos de otros usuarios. Caso típico: IDOR (cambiar id=4 → id=5 en la URL sin control de sesión). Muy frecuente en auditoría diaria. |
| A02 | Configuración de seguridad incorrecta (Security Misconfiguration) | Credenciales por defecto, paneles expuestos, cabeceras inseguras, mensajes de error que filtran rutas del sistema. Suele deberse al error humano. |
| A03 | Fallos en la cadena de suministro de software | Categoría nueva. Librerías y dependencias vulnerables o comprometidas (backdoors). Gran preocupación actual de los CISO por el desarrollo masivo con IA. |
| A04 | Fallos criptográficos | Cifrados débiles, claves mal gestionadas, TLS mal configurado. |
| A05 | Diseño inseguro | Lógica de negocio, subidas de archivos sin validación (p. ej. permitir subir un PHP cuando solo se debería poder subir un PDF), falta de límites. |
| A06 | Inyección | SQL Injection, XSS, inyección de comandos, LDAP, NoSQL. Sigue muy alto en el ranking. |
| A07 | Fallos de autenticación | Enumeración de usuarios, contraseñas débiles, ausencia de bloqueo / rate limit. Permite fuerza bruta cuando no hay protección. |
| A08 | Fallos en la integridad del software o de los datos | Pipelines (CI/CD) sin verificación de integridad. Relacionado con el desarrollo masivo de software y la gestión de datos. |
| A09 | Fallos de registro y monitorización (logging) | Falta de logs y alertas. Impide hacer un forense posterior (analogía: pedir a la policía que investigue cuando no había cámaras instaladas). |
| A10 | Mala gestión de situaciones excepcionales | Manejo de errores que filtra información de más. Muy ligado a A02. |

|  |
| --- |
| **RIESGO / LAB**  **Ejercicio mental de la sesión:** si una aplicación permite **fuerza bruta porque no bloquea** las peticiones, ¿en qué categoría cae? No es A01 (control de acceso) → es **A07, fallo de autenticación**. La ausencia de firewall/bloqueo es lo que lo habilita, pero la vulnerabilidad reportada es la enumeración de usuarios / fuerza bruta. |

|  |
| --- |
| **INFO**  **Nota:** la máquina que se usará en prácticas próximas es una máquina de **WordPress**, donde plugins y dependencias inseguras (relacionado con A03/A05) son especialmente relevantes. |

# **3. CVSS, CVE y categorización**

El **CVSS (Common Vulnerability Scoring System)** es la **nota** que se asigna a cada vulnerabilidad. Se calcula con el **CVSS Calculator**, donde se rellenan métricas (por ejemplo, impacto en confidencialidad: High, etc.). En el ejemplo de clase, con cierto contexto, una vulnerabilidad daba una puntuación de **6,8**.

| **Concepto** | **Qué es** |
| --- | --- |
| CVE | Identificador único de una vulnerabilidad concreta y pública. |
| CVSS | Sistema de puntuación que asigna una nota (criticidad) a la vulnerabilidad. |
| Niveles | Crítico / Alto / Medio / Bajo según la puntuación. |
| Informativa | Apartado SIN puntuación. Se usa cuando hay indicios de algo vulnerable pero no se ha explotado. |

|  |
| --- |
| **INFO**  **Nota:** el CWE (clasificación de tipos de debilidad) y el detalle del cálculo CVSS se trabajarán más adelante, junto con un mini-informe y un informe real anonimizado. El instructor no entró en profundidad porque es más "parte de informe". |

|  |
| --- |
| **RIESGO / LAB**  **Principio clave:** "Si yo no exploto esa vulnerabilidad, no hay vulnerabilidad." Solo se categoriza como crítico/alto/medio/bajo lo que se ha **explotado**. Si solo hay indicios → se reporta como informativa. |

# **4. Dos metodologías que NO hay que confundir**

El instructor remarca con fuerza que conviene separar mentalmente dos cosas:

| **Metodología de informe / cliente** | **Metodología técnica del hacker** |
| --- | --- |
| Es lo que paga y espera el cliente. | Es lo que el auditor hace realmente por detrás. |
| Se basa en el OWASP Top 10 y la categorización. | Enumeración → análisis → explotación encadenada. |
| Reporta solo el QUÉ (la vulnerabilidad concreta). | Prueba muchas cosas, encadena fallos, descarta caminos. |
| No es un write-up paso a paso. | Sí puede ser exploratoria y desordenada. |

|  |
| --- |
| **AVISO**  Una auditoría real **no es un write-up** del estilo "hice nmap, luego curl, luego tal". En el informe se reporta la **vulnerabilidad concreta** (por ejemplo: enumeración de usuario → A07), no toda la cadena de comandos. |

## **4.1. Pruebas realizadas**

Apartado del informe donde se documenta **lo que se ha probado aunque no haya dado resultado** (p. ej. "probé un SQLi en el buscador X, metí la comilla y estaba sanitizado"). Da valor al cliente y demuestra el trabajo realizado.

|  |
| --- |
| **RIESGO / LAB**  **Cuidado con SQLMAP:** si el cliente pide no hacer muchas peticiones y se adjunta una captura de **SQLMAP** (que lanza muchísimas peticiones) como prueba realizada, queda muy mal. Hay que saber controlar el ruido y respetar el alcance acordado. |

# **5. Metodología de auditoría web**

La metodología es la de siempre, pero con un paso intermedio importante: el **análisis de vulnerabilidades**, donde se mapea el stack tecnológico contra posibles CVE / exploits antes de explotar.

|  |
| --- |
| Reconocimiento y enumeración |
| **↓** |
| Análisis de vulnerabilidades (mapeo del stack → CVE / exploits) |
| **↓** |
| Explotación |
| **↓** |
| Post-explotación y escalada (poco peso en web) |
| **↓** |
| Documentación e informe |

Durante el **análisis de vulnerabilidades** el auditor se hace su propio mapa mental: ¿hay control de acceso? ¿puedo inyectar en alguna parte? ¿los componentes están desactualizados? Si no hay login, quizá no interesa centrarse en autenticación; el contexto manda.

## **5.1. Web real vs máquina de HTB**

Una aplicación web real **no es como una máquina de Hack The Box**. Aparecen subdominios, scope/alcance, entornos de producción vs preproducción y muchísima información y ruido que en HTB no existe.

| **Aspecto** | **Máquina HTB / VulnHub** | **Auditoría web real** |
| --- | --- | --- |
| Información expuesta | La justa y necesaria. | Muchísima: subdominios, datos, configuraciones. |
| Permiso | Todo está habilitado para hackear. | Hay un scope y reglas que respetar. |
| Impacto de un IDOR | Suele dar igual (datos ficticios). | Crítico: ver datos, tarjetas, info de clientes reales. |
| Denegación de servicio | Te reinician el lab. | Puede tirar un servicio real → problema grave con el cliente. |

|  |
| --- |
| **RIESGO / LAB**  **Scope y ruido importan.** Aunque un servicio bloquee la fuerza bruta, con Burp Suite se puede **simular la secuencia más lenta** (tardando horas en vez de minutos) imitando a una persona haciendo clic. Pero hay que valorar siempre si la denegación de servicio entra o no en el alcance: cada cliente es un mundo. |

|  |
| --- |
| **INFO**  El puesto al que más probablemente se accede empezando es **auditoría web** (equipos pool). Por eso este bloque recibirá mucha caña. Saber **reflejar el trabajo en el informe** vale tanto como saber hackear. |

# **6. Introducción a Burp Suite**

**Burp Suite es un proxy.** Actúa como **man in the middle** entre el navegador y el servidor: intercepta las peticiones antes de que lleguen al servidor, permite **verlas, modificarlas y decidir si pasan o no**. Funciona con cualquier método (GET, POST, PUT...).

|  |
| --- |
| Navegador (tú) |
| **↓** |
| Proxy de Burp — 127.0.0.1:8080 (intercepta / modifica) |
| **↓** |
| Servidor web |

|  |
| --- |
| **INFO**  Analogía de clase: el proxy es una "calle" por la que debe viajar el tráfico (puerto **8080**). Si el navegador no va por esa calle, Burp no captura nada. El navegador tiene que apuntar al proxy de Burp para que la interceptación funcione. |

## **6.1. Pestañas principales**

| **Pestaña** | **Para qué** |
| --- | --- |
| Proxy | Núcleo de Burp. Intercepta el tráfico HTTP/HTTPS (Intercept ON/OFF, Forward). |
| Repeater | Repite y modifica una petición concreta tantas veces como se quiera para analizarla. |
| Intruder | Automatiza/itera valores de una petición (p. ej. fuerza bruta de credenciales en un login). |
| Target / Dashboard | Vista general del objetivo y la actividad. |
| Sequencer / Collaborator | Funciones avanzadas (se verán más adelante). |

|  |
| --- |
| **INFO**  Para esta sesión basta con dominar **Proxy** y entender un poco el **Repeater**. Son las dos que más se usan. |

## **6.2. Flujo básico de trabajo**

1. Activar **Intercept ON** en la pestaña Proxy.
2. Navegar en la web y dejar que Burp capture las peticiones.
3. Ir haciendo **Forward** para dejar pasar las que no interesan.
4. Cuando aparece una petición interesante (un login, una API interna...), **clic derecho → Send to Repeater**.
5. En el **Repeater**, pulsar **Send** y analizar/modificar parámetros, cabeceras y respuestas las veces que haga falta.

En el ejemplo de clase, al interceptar el inicio de sesión de una web se veían **muchas peticiones** (login, una internal API, recursos de terceros como Circle/Clarity). Enviando la petición de login al Repeater se podía inspeccionar información como un Android Story ID o una public key, descubriendo así la tecnología usada por detrás.

## **6.3. Dos formas de enrutar el tráfico hacia Burp**

| **Opción** | **Descripción** | **Ventaja / inconveniente** |
| --- | --- | --- |
| Open Browser (navegador interno de Burp) | Navegador que ya viene preconfigurado para pasar por el proxy. Solo hay que preocuparse de Intercept ON/OFF. | Recomendado al empezar: menos ruido, sin líos de configuración. |
| FoxyProxy (Firefox/Chrome propio) | Extensión que mete tu navegador en el proxy de Burp (127.0.0.1:8080). | Más rápido para gente experta, pero mucho ruido (pestañas, recursos de terceros) y requiere activarlo manualmente. |

|  |
| --- |
| **AVISO**  **Ruido:** trabajar en el navegador habitual con muchas pestañas abiertas genera muchísimo tráfico irrelevante (analytics, redes sociales, etc.). Por eso al empezar conviene el **Open Browser** o un navegador limpio dedicado. |

## **6.4. Configuración de FoxyProxy (visto en clase)**

Si se usa FoxyProxy en lugar del Open Browser, la configuración del proxy es:

|  |
| --- |
| Título : Burp  Tipo : HTTP  Host / IP : 127.0.0.1  Puerto : 8080 |

Con FoxyProxy activado, todo el navegador pasa por Burp. Para desactivarlo se selecciona **Disable** y se vuelve a navegar normal.

## **6.5. Certificado de Burp**

Al navegar con un navegador propio (no el Open Browser), el navegador **no detecta el proxy de Burp como seguro**. Hay que instalar el **certificado de Burp (PortSwigger)** como certificado de confianza.

Con Burp y el proxy **encendidos**, se accede desde el navegador a:

|  |
| --- |
| http://burpsuite/  (también vale poner simplemente: burpsuite/ ) |

Desde ahí se descarga el **CA Certificate** y se importa en la gestión de certificados del navegador (Chrome: Administrar certificados → instalados por ti → importar como certificado de confianza). Aparecerá como **PortSwigger**, indicando al navegador que el proxy es seguro.

|  |
| --- |
| **INFO**  **Nota sobre entornos HTB:** al trabajar con máquinas de HTB se está conectado por VPN dentro de Kali, en una red interna **sin acceso a internet**, por lo que el ruido de terceros desaparece. Recordatorio de clase: la VPN debe usarse desde Kali, no desde Windows. |

# **7. Herramientas utilizadas en la sesión**

| **Herramienta** | **Objetivo** | **Fase de auditoría** | **Comando o uso visto** | **Nivel** | **Notas** |
| --- | --- | --- | --- | --- | --- |
| Burp Suite (Proxy/Repeater/Intruder) | Interceptar y modificar tráfico HTTP/HTTPS | Reconocimiento, análisis y explotación web | Intercept ON/OFF, Forward, Send to Repeater | Introducida | Proxy man-in-the-middle en 127.0.0.1:8080. Foco en Proxy y Repeater. |
| FoxyProxy | Enrutar el navegador hacia el proxy de Burp | Configuración previa | HTTP · 127.0.0.1 · 8080 | Introducida | Alternativa al Open Browser interno de Burp. |
| CVSS Calculator | Puntuar la criticidad de una vulnerabilidad | Análisis / informe | Selección de métricas → nota (ej. 6,8) | Mencionada | Se profundizará junto al informe. |
| Nmap | Detectar puertos y servicios | Enumeración | Repaso anunciado para próxima clase | Recurrente | Se aplicará ahora al contexto web. |
| Curl | Interacción manual con servicios web | Enumeración web | Mencionado para próxima clase | Mencionada | Se verá con Nmap en el repaso web. |
| SQLMAP | Automatizar SQL Injection | Explotación | Mencionado como ejemplo de ruido | Mencionada | Cuidado: genera muchas peticiones; respetar el scope. |
| Hydra | Fuerza bruta de credenciales | Explotación / autenticación | Citado como alternativa al Intruder | Practicada | Comparado con el Intruder de Burp. |

|  |
| --- |
| **INFO**  **Nota:** Nmap, Curl y SQLMAP solo se **mencionan** en esta sesión (se repasarán o aplicarán en la siguiente clase). No se desarrollan en profundidad en el material proporcionado. |

# **8. Riesgos, errores comunes y buenas prácticas**

|  |
| --- |
| **RIESGO / LAB**  Lanzar fuerza bruta a lo loco contra un servicio (como pasó en el examen final tipo eJPT) puede **tirar el laboratorio o el servicio del cliente**. En real esto significa llamadas a medianoche y problemas serios. |

|  |
| --- |
| **AVISO**  Adjuntar capturas de **SQLMAP** como "prueba realizada" cuando el cliente pidió pocas peticiones delata que no se hizo el SQLi manual y rompe el acuerdo de ruido. |

|  |
| --- |
| **AVISO**  Trabajar en el navegador personal con muchas pestañas mete **ruido** que dificulta identificar la petición relevante en Burp. |

|  |
| --- |
| **BUENA PRÁCTICA**  Usar el **Open Browser** de Burp (o un navegador limpio dedicado) al empezar, mantener **Intercept** controlado y enviar al **Repeater** solo lo que interesa. |

|  |
| --- |
| **BUENA PRÁCTICA**  Separar siempre la **metodología de informe** (lo que ve el cliente) de la **metodología técnica**, y documentar bien: "lo que no se documenta, no existe". |

|  |
| --- |
| **BUENA PRÁCTICA**  Antes de atacar, hacer **análisis de vulnerabilidades**: mapear el stack y decidir qué tiene sentido probar según el contexto (no probar autenticación si no hay login, etc.). |

# **9. Conexión con sesiones anteriores**

Esta sesión retoma el enfoque **Red Team** tras un paréntesis de Blue Team y conecta directamente con lo ya trabajado:

- **Nmap** y **fuzzing**, vistos en sesiones previas, ahora se aplicarán al contexto **web** (se anuncia un repaso de Nmap + Curl).
- La **fuerza bruta** ya practicada con **Hydra** se relaciona ahora con el **Intruder** de Burp: misma idea (iterar credenciales) desde un proxy web.
- La metodología **enumeración → explotación → escalada** practicada en HTB (Starting Point, Mr. Robot...) se reordena para web añadiendo el paso de **análisis de vulnerabilidades**.
- La **SQL Injection** introducida en Metasploitable 2 (DVWA) reaparece como categoría OWASP (A06) y como ejemplo de "prueba realizada" en el informe.
- Los **plugins de WordPress** (relevantes en la cadena de suministro, A03) enlazan con la próxima máquina de prácticas, que será de WordPress.

# **10. Resumen final**

Sesión de apertura del módulo de **hacking web**, centrada en la **metodología**. El **OWASP Top 10 2025** sirve como marco común para el informe, pero lo importante es **entender** las vulnerabilidades, no memorizar categorías. El **CVSS** puntúa la criticidad y solo se categoriza lo que se **explota** (lo demás, informativa).

Hay que distinguir la **metodología de informe** (lo que paga el cliente) de la **metodología del hacker**, y recordar que una web real no es una máquina de HTB: hay scope, ruido y riesgo de denegación de servicio. La metodología web añade el paso de **análisis de vulnerabilidades** antes de explotar.

En la parte práctica se introdujo **Burp Suite** como **proxy man-in-the-middle**: interceptar con el **Proxy**, dejar pasar con **Forward**, enviar al **Repeater** lo interesante e iterar con el **Intruder**. Dos formas de enrutar el tráfico (**Open Browser** vs **FoxyProxy**) y la instalación del **certificado de PortSwigger** para navegadores propios.

# **11. Checklist de repaso**

- ¿Sé explicar qué es el OWASP Top 10 y para qué sirve realmente?
- ¿Puedo poner un ejemplo de A01 (IDOR), A02 (misconfiguration) y A07 (autenticación)?
- ¿Entiendo qué es CVSS y la diferencia entre crítico/alto/medio/bajo e informativa?
- ¿Distingo la metodología de informe de la metodología técnica del hacker?
- ¿Sé por qué una web real no es como una máquina de HTB (scope, ruido, DoS)?
- ¿Sé qué es Burp Suite y por qué es un proxy / man in the middle?
- ¿Sé interceptar, hacer Forward y enviar una petición al Repeater?
- ¿Entiendo la diferencia entre Open Browser y FoxyProxy y sé configurar el proxy (127.0.0.1:8080)?
- ¿Sé instalar el certificado de PortSwigger desde http://burpsuite/?

# **12. Actualización del registro de herramientas**

Cambios y novedades tras esta sesión (para copiar a la base de conocimiento del proyecto):

| **Herramienta** | **Nivel anterior** | **Nivel tras la sesión** | **Motivo** |
| --- | --- | --- | --- |
| Burp Suite (Proxy/Repeater) | Practicada (Intruder) | Practicada | Se explica de cero el concepto de proxy, Intercept/Forward y Repeater. El Intruder ya se había usado en Mr. Robot. |
| FoxyProxy | — | Introducida | Nueva: configuración HTTP 127.0.0.1:8080 para enrutar el navegador hacia Burp. |
| CVSS Calculator | — | Mencionada | Nueva referencia: puntuación de criticidad; se profundizará con el informe. |
| Curl | — | Mencionada | Anunciada para el repaso web junto a Nmap. |
| SQLMAP | — | Mencionada | Citada como ejemplo de herramienta ruidosa a usar con criterio. |

|  |
| --- |
| **INFO**  **Próximos temas anunciados:** repaso de **Nmap + Curl** aplicados a web, práctica con una **máquina de WordPress**, y desarrollo progresivo de la metodología web (interpretación de peticiones, tipos de vulnerabilidades, mini-informe e informe real anonimizado). |
