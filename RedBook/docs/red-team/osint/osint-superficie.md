---
tags:
- OSINT e ingeniería social
---

# OSINT Superficie

EVOLVE ACADEMY - MASTER EN CIBERSEGURIDAD

**OSINT: Mapeando la Superficie de una Organización**

Evolve Academy · Reconocimiento ofensivo

*Temas: OSINT metodología · Sherlock · Maigret · Maltego · Google Dorks · Shodan · HIBP · Marco legal*

# **① ¿Qué es OSINT y marco legal?**

OSINT (Open Source Intelligence) es la recopilación de información **desde fuentes públicas** sin necesitar credenciales ni exploits. Es el primer paso de cualquier auditoría.

| **⚖ LEGAL** | El OSINT en sí mismo es legal: uses información pública. El límite está en cómo se usa: un escaneo de puertos a una empresa sin contrato es ilegal. La autorización explícita del cliente es la clave. |
| --- | --- |

| **Estado** | **Descripción** |
| --- | --- |
| Legal | Consultar redes sociales, WHOIS, LinkedIn, registros DNS, Shodan sobre IPs públicas con contrato. |
| Zona gris | Usar bases de datos de contraseñas filtradas para auditoría interna (consultar ≠ usar contra terceros). |
| Ilegal | Escanear sin autorización, usar credenciales filtradas para acceder, comprar bases robadas. |

# **② Metodología OSINT — El ciclo de inteligencia**

| **1. Definir objetivo** | -> | **2. Recolección** | -> | **3. Procesamiento** | -> | **4. Análisis** | -> | **5. Informe** |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

**Antes de abrir cualquier herramienta:** define exactamente qué información necesitas. ¿Empleados? ¿Infraestructura expuesta? ¿Credenciales filtradas? Objetivo concreto = menos ruido.

| **💡 PRIMER PASO** | Cuando un cliente te contrata para una auditoría externa, lo primero que le preguntas es: ¿qué activos son tuyos? Dominio principal, filiales, rangos de IP. Eso es el 'scope'. |
| --- | --- |

# **③ Google Dorks — Búsqueda avanzada**

| # Operadores de búsqueda avanzada en Google:  site:empresa.com # solo resultados de ese dominio  site:empresa.com filetype:pdf # PDFs de ese dominio  site:empresa.com inurl:admin # URLs con 'admin'  site:empresa.com intitle:login # páginas con 'login' en el título  intext:'contraseña' site:emp.com # texto específico en la página  # Dorks útiles en auditorías:  site:empresa.com filetype:xlsx # hojas Excel expuestas  site:empresa.com filetype:sql # dumps de BD expuestos  inurl:/wp-content/uploads site:emp # uploads de WordPress  site:pastebin.com empresa.com # menciones en Pastebin  site:github.com empresa.com # código en GitHub  # Encontrar subdominios:  site:\*.empresa.com  # Recursos:  # exploit-db.com/google-hacking-database (GHDB) |
| --- |

| **🔐 EXPOSICIÓN** | Muchas empresas tienen documentos internos, copias de seguridad (.bak, .old) o paneles de administración indexados en Google por error. Los Google Dorks los encuentran en segundos. |
| --- | --- |

# **④ Sherlock y Maigret — Búsqueda por username**

| # Sherlock: busca un username en cientos de redes sociales  # Instalación:  pip install sherlock-project  # o desde GitHub:  git clone https://github.com/sherlock-project/sherlock  cd sherlock && pip install -r requirements.txt  # Uso básico:  sherlock usuario\_objetivo  # Guardar resultados en fichero:  sherlock usuario\_objetivo --output resultados.txt  # Con Tor (más anónimo):  sherlock usuario\_objetivo --tor  # Maigret: más completo, análisis de perfiles  pip install maigret  maigret usuario\_objetivo  maigret usuario\_objetivo --report html # informe HTML |
| --- |

| **⚠ FALSOS POSITIVOS** | Sherlock y Maigret solo verifican el código HTTP de respuesta (200 vs 404). Algunas webs devuelven 200 aunque el usuario no exista → hay que verificar manualmente los resultados clave. |
| --- | --- |

# **⑤ WHOIS y DNS — Infraestructura del objetivo**

| # WHOIS — información de registro de dominios:  whois empresa.com  # Información que puede revelar:  # Registrant (propietario), correos, teléfonos, fechas  # Muchos usan privacy protection — datos ocultos  # DNS — enumeración de subdominios:  dig empresa.com ANY # todos los registros DNS  dig empresa.com MX # servidores de correo  dig empresa.com NS # servidores de nombre  # Transferencia de zona (si está mal configurada):  dig axfr empresa.com @ns1.empresa.com  # Si funciona: ORO. Revela todos los subdominios.  # Herramientas de enumeración de subdominios:  subfinder -d empresa.com  amass enum -d empresa.com  dnsrecon -d empresa.com  # Certificate Transparency (sin herramientas):  # crt.sh/?q=%.empresa.com ← en el navegador  curl -s 'https://crt.sh/?q=%.empresa.com&output=json' | jq '.[].name\_value' |
| --- |

# **⑥ Shodan — El buscador de dispositivos**

| # Shodan indexa servicios expuestos en Internet  # Web: shodan.io | CLI: pip install shodan  # Búsquedas en Shodan web:  org:'Nombre Empresa' # todos los activos de una empresa  net:185.12.34.0/24 # rango de IPs  hostname:empresa.com # por hostname  # Filtros útiles:  port:22 org:'empresa' # SSH expuesto  port:3389 country:ES # RDP en España  product:Apache version:2.2 # versiones vulnerables  vuln:CVE-2021-44228 # Log4Shell expuesto  # CLI de Shodan:  export SHODAN\_API\_KEY='tu\_api\_key'  shodan init $SHODAN\_API\_KEY  shodan search 'org:empresa port:22'  shodan host 1.2.3.4 |
| --- |

| **💡 SHODAN** | Shodan no solo encuentra cámaras IP y routers: también servidores con versiones vulnerables, bases de datos abiertas, paneles de administración sin autenticación. Fundamental en auditorías externas. |
| --- | --- |

# **⑦ HIBP y bases de datos filtradas**

| # Have I Been Pwned (HIBP) — haveibeenpwned.com  # Consultar si un email o dominio tiene credenciales filtradas.  # API (requiere key gratuita para dominios):  curl 'https://haveibeenpwned.com/api/v3/breachedaccount/correo@empresa.com'  # Herramientas similares:  # dehashed.com (requiere suscripción)  # intelx.io  # hunter.io → correos corporativos por dominio  # ⚠ IMPORTANTE:  # Consultar HIBP = LEGAL (datos ya públicos)  # Descargar/usar bases de datos robadas = ILEGAL  # Usar credenciales filtradas contra sistemas = ILEGAL |
| --- |

| **⚖ LEGALIDAD** | Consultar si un email está en HIBP es legal. Comprar o descargar bases de datos de contraseñas es ilegal. Usarlas para acceder a sistemas ajenos es delito penal en todos los países de la UE. |
| --- | --- |

# **⑧ LinkedIn y OSINT de personas**

| # LinkedIn como fuente de OSINT organizacional:  # Empleados → tecnologías usadas (Java developer, Azure admin...)  # Organigramas → estructura de la empresa  # Ofertas de trabajo → tecnologías y herramientas usadas internamente  # Formato de email corporativo:  # La mayoría sigue patrones: nombre.apellido@empresa.com  # hunter.io puede verificar el formato de una empresa  # Herramientas para LinkedIn:  # linkedin2username → genera listas de usuarios  # InSpy → enumera empleados por empresa  # Construcción de perfil de un objetivo (persona):  # 1. Nombre completo → variaciones (con/sin tilde)  # 2. Username en redes → sherlock/maigret  # 3. Correos → hunter.io, HIBP  # 4. Foto → búsqueda inversa (Google Lens, pimeyes.com)  # 5. Número de teléfono → truecaller, eyecon  # 6. Documentos online → Google Dorks site:linkedin.com nombre |
| --- |

| **🔐 SPEAR PHISHING** | Toda la información recopilada sobre una persona o empresa se usa para construir ataques de spear phishing altamente personalizados. Un email que menciona el nombre de tu jefe, tu cargo y tu proyecto actual tiene altísima tasa de éxito. |
| --- | --- |
