---
tags:
- Estándares y clasificación
---

# OWASP CVSS CWE CVE

**EVOLVE ACADEMY · MÁSTER EN CIBERSEGURIDAD**

**OWASP Top 10, CVSS, CWE y CVE**

El marco de trabajo para clasificar, identificar y puntuar vulnerabilidades

**Instructor: Evolve Academy · Miércoles 24 (preparación previa a clase)**

*Temas: OWASP Top 10:2025 · CWE · CVE · CVSS · NVD · Severidad · Vector de ataque · Marco de trabajo*

| **ℹ Sobre este documento**  Apunte de preparación técnica elaborado ANTES de la clase del miércoles 24, no a partir de una transcripción. La lista del OWASP Top 10 que se incluye es la versión 2025 (versión vigente, publicada en su forma final en enero de 2026), verificada contra la web oficial de OWASP. Si el instructor trabaja con la edición 2021, el orden y nombres cambian: anótalo en clase. |
| --- |

# **① Objetivos de la sesión**

- Entender qué es **OWASP** y por qué su Top 10 es la referencia estándar en seguridad web.
- Diferenciar con claridad los tres conceptos que se confunden: **CWE, CVE y CVSS**.
- Saber leer un **identificador CVE** y un **score CVSS** y entender qué significan.
- Conocer la lista del **OWASP Top 10:2025** y los cambios respecto a 2021.
- Comprender cómo encajan estos marcos en el día a día de una auditoría.

# **② Conceptos clave: el vocabulario que no se debe confundir**

Estos cuatro términos forman el lenguaje común de la industria. Confundirlos es uno de los errores más típicos al empezar:

| **Sigla** | **Significa** | **Qué es** | **Quién lo mantiene** |
| --- | --- | --- | --- |
| **OWASP** | Open Worldwide Application Security Project | Fundación sin ánimo de lucro; publica el Top 10 y muchos otros recursos | Comunidad OWASP |
| **CWE** | Common Weakness Enumeration | Catálogo de TIPOS de debilidad (categorías genéricas) | MITRE |
| **CVE** | Common Vulnerabilities and Exposures | Identificador único de una vulnerabilidad CONCRETA en un producto | MITRE / NVD |
| **CVSS** | Common Vulnerability Scoring System | Sistema de PUNTUACIÓN de severidad (0.0 a 10.0) | FIRST |
| **✓ La analogía que lo aclara todo**  CWE es la enfermedad genérica ('infección respiratoria'). CVE es el caso clínico concreto de un paciente concreto ('la neumonía de Juan el 3 de marzo'). CVSS es la gravedad de ese caso (de leve a crítica). OWASP Top 10 es el ranking de las enfermedades más frecuentes y peligrosas. |

# **③ CWE — Common Weakness Enumeration**

CWE es un catálogo de **tipos de debilidad** de software, mantenido por MITRE. Describe el patrón de fallo de forma genérica, sin referirse a un producto concreto. Cada entrada tiene un identificador CWE-XXX.

| **Identificador** | **Debilidad** | **Relación** |
| --- | --- | --- |
| CWE-89 | SQL Injection | Inyección (A05:2025) |
| CWE-79 | Cross-Site Scripting (XSS) | Inyección (A05:2025) |
| CWE-22 | Path Traversal (incluye LFI) | Broken Access Control (A01:2025) |
| CWE-287 | Improper Authentication | Authentication Failures (A07:2025) |
| CWE-209 | Exposición de info en mensajes de error | Mishandling of Exceptional Conditions (A10:2025) |
| **ℹ Dónde lo verás**  CWE-22 (Path Traversal) es exactamente el tipo de debilidad detrás de los ataques LFI que ya has trabajado. Cuando una herramienta o un informe dice 'CWE-89', te está diciendo el tipo de fallo de forma estandarizada. |

# **④ CVE — Common Vulnerabilities and Exposures**

Un **CVE** identifica una vulnerabilidad **concreta** en un producto y versión específicos. Es el 'DNI' de cada vulnerabilidad pública. Cuando Nmap o searchsploit te muestran un CVE, se refieren a un fallo concreto, documentado y normalmente con exploit asociado.

## **Formato de un identificador CVE**

| CVE-2021-44228  | | |  | | +--- Número secuencial dentro de ese año  | +--------- Año de asignación (no siempre el de descubrimiento)  +-------------- Prefijo fijo |
| --- |

El ejemplo CVE-2021-44228 es **Log4Shell**, ya visto en la sesión 25 al aplicar el marco mental de 4 elementos. Es un caso perfecto: un CVE concreto, de tipo CWE de inyección, con un CVSS crítico.

| **ℹ NVD — la base de datos de referencia**  La NVD (National Vulnerability Database, del NIST) es el repositorio donde cada CVE se enriquece con su CWE asociado, su puntuación CVSS y los productos afectados. Es la fuente que consultas para saber la gravedad real de un CVE. |
| --- |

# **⑤ CVSS — Common Vulnerability Scoring System**

CVSS asigna una **puntuación de 0.0 a 10.0** a una vulnerabilidad para reflejar su severidad. Lo mantiene FIRST. Permite priorizar: ante decenas de hallazgos, atiendes primero los de mayor score. Conviven la versión 3.1 (la más extendida) y la 4.0 (más reciente).

## **Rangos de severidad (CVSS v3.x)**

| **Score** | **Severidad** |
| --- | --- |
| 0.0 | None (ninguna) |
| 0.1 – 3.9 | Low (baja) |
| 4.0 – 6.9 | Medium (media) |
| 7.0 – 8.9 | High (alta) |
| 9.0 – 10.0 | Critical (crítica) |

## **De qué se compone el score (métricas base)**

El score base se calcula a partir de varias métricas. Estas son las principales para entender de dónde sale el número:

- **Attack Vector (AV)**: cómo se accede — red (Network), adyacente, local o físico. A más remoto, más grave.
- **Attack Complexity (AC)**: lo difícil que es explotarlo.
- **Privileges Required (PR)**: qué permisos necesita el atacante de partida.
- **User Interaction (UI)**: si requiere que la víctima haga algo.
- **Impacto CIA**: Confidencialidad, Integridad y Disponibilidad afectadas.

| **✓ Vector CVSS**  Verás cadenas como CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H. Se leen como una ficha: vector de red, complejidad baja, sin privilegios ni interacción, impacto alto en C/I/A → score crítico. No hay que memorizarla, sí saber interpretarla. |
| --- |

# **⑥ OWASP Top 10:2025**

El **OWASP Top 10** es el ranking de las diez categorías de riesgo más críticas en aplicaciones web. No es una lista de vulnerabilidades concretas, sino de **categorías** (cada una agrupa múltiples CWEs). Es la referencia estándar de la industria y el marco mental de cualquier auditoría web. Esta es la edición 2025, verificada contra la web oficial de OWASP:

| **#** | **Categoría 2025** | **Notas** |
| --- | --- | --- |
| A01 | Broken Access Control | Se mantiene en #1. Absorbe SSRF. Incluye IDOR, escalada de privilegios, Path Traversal/LFI |
| A02 | Security Misconfiguration | Sube del #5 al #2. Credenciales por defecto, buckets abiertos, cabeceras inseguras. Incluye XXE |
| A03 | Software Supply Chain Failures | NUEVA (amplía 'Componentes vulnerables'). Dependencias, build, distribución |
| A04 | Cryptographic Failures | Baja del #2 al #4. Cifrado débil, datos sensibles expuestos |
| A05 | Injection | Baja del #3 al #5. Incluye SQLi, XSS, command injection, LDAP |
| A06 | Insecure Design | Baja al #6. Fallos de diseño, falta de threat modeling |
| A07 | Authentication Failures | Se mantiene en #7. Antes 'Identification and Authentication Failures' |
| A08 | Software or Data Integrity Failures | Se mantiene en #8. Integridad de código y datos, deserialización insegura |
| A09 | Security Logging & Alerting Failures | Se mantiene en #9. Añade 'Alerting': loguear sin alertar no sirve |
| A10 | Mishandling of Exceptional Conditions | NUEVA. Mala gestión de errores, 'failing open', fugas en mensajes de error |
| **✗ Cambios principales frente a 2021**  Dos categorías nuevas (A03 Software Supply Chain Failures y A10 Mishandling of Exceptional Conditions), SSRF absorbido dentro de A01, y varias reordenaciones (Misconfiguration sube fuerte, Injection y Cryptographic Failures bajan). Si encuentras material que pone Injection en el #3, es de la edición 2021. |
| **ℹ Por qué OWASP no es CVSS ni CVE**  OWASP clasifica riesgos por categorías; cada categoría agrupa muchos CWEs; cada CWE puede materializarse en múltiples CVEs; y cada CVE tiene su CVSS. Los cuatro marcos encajan en cascada: OWASP → CWE → CVE → CVSS. |

# **⑦ Cómo encaja todo en una auditoría**

| **1. OWASP Top 10** |
| --- |
| **↓** |
| **2. CWE** |
| **↓** |
| **3. CVE** |
| **↓** |
| **4. CVSS** |
| **↓** |
| **5. Priorización** |

Flujo mental de izquierda a derecha: el **OWASP Top 10** te dice qué categorías de riesgo buscar; al encontrar un fallo lo clasificas con su **CWE**; si corresponde a un fallo público conocido tiene un **CVE**; ese CVE trae un **CVSS** que te permite **priorizar** qué reportar y remediar primero. Es el hilo que conecta el reconocimiento con el informe final.

# **⑧ Herramientas y recursos de la sesión**

| **Recurso** | **Objetivo** | **Fase de auditoría** | **Uso visto** | **Nivel** | **Notas** |
| --- | --- | --- | --- | --- | --- |
| OWASP Top 10 | Marco de categorías de riesgo | Transversal | owasp.org/Top10 | Introducida | Edición 2025 vigente |
| NVD | Consultar CVE/CVSS/CWE | Análisis vuln. | nvd.nist.gov | Mencionada | Base de datos del NIST |
| MITRE CWE | Catálogo de debilidades | Clasificación | cwe.mitre.org | Mencionada | Tipos genéricos de fallo |
| searchsploit | Buscar exploits por CVE/producto | Explotación | searchsploit producto | Practicada | Ya usado (sesión 25, FTP) |
| CVSS Calculator | Calcular/leer vectores CVSS | Análisis vuln. | first.org/cvss/calculator | Mencionada | Interpretar el vector |

# **⑨ Riesgos, errores comunes y buenas prácticas**

- **Confundir CWE con CVE**: CWE es el tipo, CVE es el caso concreto. El error más frecuente al empezar.
- **Tratar el CVSS como verdad absoluta**: es una guía de priorización, no mide el riesgo en TU contexto (un crítico en un servicio aislado puede importar menos que un medio en algo expuesto).
- **Usar la edición OWASP equivocada**: confirma siempre si trabajas con 2021 o 2025; el orden cambió.
- **Reportar sin clasificar**: un buen informe mapea cada hallazgo a su CWE y, si aplica, CVE+CVSS.

| **✓ Buena práctica**  En tus informes de laboratorio, acostúmbrate desde ya a etiquetar cada hallazgo con su categoría OWASP y su CWE. Es exactamente lo que se espera en una auditoría web junior, el perfil más demandado según la sesión 25. |
| --- |

# **⑩ Conexión con sesiones anteriores**

- **Marco mental de 4 elementos (sesión 25)**: Log4Shell (CVE-2021-44228) ya lo analizaste con FUENTE/PROCESO/PRIVILEGIOS/DESTINO. Ahora le pones nombre formal: su CWE, su CVSS y su categoría OWASP.
- **LFI / Path Traversal**: el tipo de fallo que trabajaste es CWE-22, dentro de A01 Broken Access Control.
- **searchsploit (sesión 25, FTP)**: buscabas exploits por versión; muchos están indexados por CVE.
- **Enumeración y fuzzing web (lunes y martes)**: sirven para DETECTAR fallos que luego clasificas con estos marcos.

# **⑪ Resumen final**

Cuatro marcos forman el lenguaje común de la seguridad de aplicaciones y encajan en cascada. **OWASP Top 10** clasifica los riesgos web en diez categorías (edición vigente 2025, con dos categorías nuevas y SSRF absorbido en Broken Access Control). **CWE** cataloga los tipos genéricos de debilidad. **CVE** identifica vulnerabilidades concretas en productos concretos. **CVSS** las puntúa de 0.0 a 10.0 para priorizar. Dominar este vocabulario es lo que permite pasar de 'he encontrado un fallo' a un informe profesional que lo clasifica, lo identifica y justifica su gravedad.

# **⑫ Checklist de repaso**

- Distingo sin dudar CWE (tipo), CVE (caso concreto) y CVSS (puntuación).
- Sé leer un identificador CVE y para qué sirve la NVD.
- Conozco los rangos de severidad CVSS y sé interpretar un vector base.
- Puedo nombrar las categorías del OWASP Top 10:2025 y los cambios frente a 2021.
- Entiendo la cascada OWASP → CWE → CVE → CVSS.
- Sé mapear un hallazgo de laboratorio a su categoría OWASP y su CWE.
- Relaciono Log4Shell, LFI/Path Traversal y SQLi con sus CWE y categorías OWASP.

# **⑬ Actualización del registro de herramientas**

| **Recurso** | **Nivel propuesto** | **Cambio** |
| --- | --- | --- |
| OWASP Top 10 | Introducida | NUEVO marco — edición 2025 |
| NVD (nvd.nist.gov) | Mencionada | NUEVO recurso de consulta CVE/CVSS |
| MITRE CWE | Mencionada | NUEVO catálogo de debilidades |
| CVSS Calculator | Mencionada | NUEVO — interpretar vectores |
| searchsploit | Practicada | Se mantiene; conexión con CVEs |
