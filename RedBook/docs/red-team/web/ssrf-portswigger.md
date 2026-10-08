---
tags:
- Auditoría web
---

# SSRF PortSwigger

**EVOLVE ACADEMY · MÁSTER EN CIBERSEGURIDAD**

**SSRF — Server Side Request Forgery**

Instructor: Carlos Castillo · 20/07/2026

Entorno: laboratorios web PortSwigger (Burp Suite) · Kali Linux

# **Objetivos de la sesión**

- Entender qué es un **SSRF** y por qué es peligroso: el atacante usa el propio servidor como intermediario para alcanzar recursos internos.
- Diferenciar SSRF de **Path Traversal / LFI** vistos en la sesión anterior.
- Detectar el indicio de SSRF: un parámetro que contiene o construye una **URL** que el servidor consulta por nosotros.
- Explotar SSRF contra **localhost** y contra la **red interna** de la empresa.
- Usar **Burp Intruder** para descubrir por fuerza bruta qué IP interna aloja el panel de administración.
- Evadir defensas de tipo **blacklist** (bypass de localhost, IPs alternativas, doble URL-encode).
- Conocer las contramedidas del lado defensivo: **whitelist**, validación de destino, control de redirecciones.

# **Conceptos clave**

## **¿Qué es un SSRF?**

**SSRF (Server Side Request Forgery)** es una vulnerabilidad web en la que el atacante consigue que **el servidor** realice una petición HTTP a un destino elegido por el atacante. El atacante no accede directamente a los recursos internos —no tiene visibilidad de la red interna—, sino que **abusa de una funcionalidad legítima** de la aplicación que ya hace peticiones a otras URLs.

| **ℹ La analogía del mensajero**  La idea central de Carlos: el servidor actúa como *mensajero* o *cabeza de turco*. Tú, como atacante externo, no puedes entrar a la red interna, pero el servidor sí. Le pasas una URL interna y el servidor la consulta por ti, devolviéndote el resultado en la respuesta de la petición web. |
| --- |

Ejemplo mental del profesor: si a ti no te dejan entrar en las oficinas de Evolve, le das una nota a un alumno que sí tiene acceso y él la introduce por ti. El alumno es el servidor: goza de la confianza interna que tú no tienes.

## **¿Qué se puede alcanzar con un SSRF?**

- Paneles de **administración internos** (p. ej. http://localhost/admin).
- **Servicios internos** levantados en la red (backends, APIs de logística/stock, etc.).
- **APIs de metadatos** de nube (AWS/Google/Amazon Web Services) accesibles desde el propio servidor.
- Recursos web internos: XML, JSON, archivos de configuración expuestos vía HTTP (p. ej. un .conf, configuración de WordPress).

| **⚠ SSRF ≠ LFI**  Límite importante señalado en clase: el SSRF trabaja **a nivel de peticiones HTTP**. NO permite leer archivos locales arbitrarios del sistema como hacía el LFI (p. ej. /etc/passwd o un id\_rsa). El destino debe ser un recurso alcanzable por HTTP/HTTPS. Si en una IP interna hay servicios pero no hay web, el SSRF no llega hasta ahí. |
| --- |

## **Diferencia con Path Traversal / LFI**

| **Aspecto** | **Path Traversal / LFI** | **SSRF** |
| --- | --- | --- |
| Indicio típico | Parámetro que carga un **archivo** (imagen, PDF, HTML…) | Parámetro que contiene o construye una **URL** |
| Qué se obtiene | Archivos locales del servidor (/etc/passwd, id\_rsa, .conf) | Respuestas de recursos **web** internos (paneles, APIs, metadatos) |
| Vector | Escapar del directorio con ../../ | Sustituir la URL destino por una interna (localhost, IP interna) |
| Nivel de acceso | Sistema de ficheros | Red interna vía HTTP |

## **SSRF a ciegas (Blind SSRF)**

Existe una variante **Blind SSRF** en la que no hay salida (*output*) visible de la vulnerabilidad en la respuesta. Para confirmarla hay que observar la interacción por otra vía —típicamente un enlace generado por **Burp Collaborator** (edición Pro), de forma análoga a levantar un servidor HTTP local y ver quién hace la llamada—. En clase **no se practicó** por requerir Collaborator/Burp Pro.

# **Desarrollo técnico**

Todos los laboratorios parten de la misma tienda web (estilo PortSwigger) con una funcionalidad de **comprobación de stock** (*Check stock*). Esa funcionalidad, por detrás, hace una petición HTTP a un servicio de almacén mediante un parámetro stockApi con una URL. Ese parámetro es el punto vulnerable.

| **ℹ Metodología antes de explotar**  Metodología del profesor: **primero entender la web** (enumerar funcionalidades), luego identificar dónde puede estar la vulnerabilidad, y solo entonces explotar. En esta tienda las piezas de valor eran: el login (My account), el parámetro productId de la URL, y sobre todo la función **Check stock**. |
| --- |

Detalle observado de paso: cambiar el productId en la URL sin permisos podría constituir un **IDOR** (*Insecure Direct Object Reference*), acceder a un recurso que no debería. En la tienda pública no tenía impacto, pero es un patrón a comprobar.

## **Laboratorio 1 — SSRF básico contra el localhost**

**Objetivo:** cambiar la URL de comprobación de stock por http://localhost/admin, acceder a la interfaz de administración y **eliminar al usuario `carlos`**.

1. Añadir un producto al carrito o abrirlo, pulsar **Check stock** e interceptar la petición con Burp Proxy.
2. La petición es un **POST** a /product/stock con un parámetro stockApi que apunta a una URL de almacén (algo como http://stock.weliketoshop.net:8080/product/stock/...).
3. Con la petición en el Repeater, decodificar el cuerpo (Ctrl+Shift+U) para editarlo cómodo, sustituir el valor de stockApi por http://localhost/admin y volver a codificar (Ctrl+U) antes de enviar.
4. La respuesta muestra el **panel de administración interno**: aparece el listado de usuarios (wiener, carlos) con botones *Delete*.
5. Para borrar a carlos, apuntar stockApi a la ruta de borrado que revela el propio panel: http://localhost/admin/delete?username=carlos.

| POST /product/stock HTTP/1.1  Host: LAB-ID.web-security-academy.net  Content-Type: application/x-www-form-urlencoded    stockApi=http://localhost/admin/delete?username=carlos |
| --- |
| **⚠ El borrado también lo hace el servidor**  Punto clave que confundió al grupo: **verlo** en la respuesta (el panel) lo hace el servidor por ti, pero si intentas hacer *clic* en el botón Delete del panel renderizado, ese clic lo lanzas **tú** desde fuera y NO funciona (no tienes acceso interno). La acción de borrado también debe ejecutarla el servidor: hay que meter la URL /admin/delete?username=carlos en stockApi. Todo pasa siempre por el servidor. |

Observación sobre el flujo del Proxy: se puede resolver dejando la petición modificada e ir dando **Forward** hasta que el servidor la procesa; al recargar la web el laboratorio aparece como resuelto (*Congratulations, you solved the lab*).

## **Laboratorio 2 — SSRF contra otro back-end de la red interna**

**Objetivo:** ya no está en localhost. El panel de administración vive en **otra IP dentro de la red interna** 192.168.0.X, en el puerto **8080**. Hay que descubrir cuál y borrar a carlos.

Al interceptar el Check stock se ve que stockApi llama a un servicio interno, p. ej. http://192.168.0.1:8080/... (el almacén). El panel de admin está en otra IP del rango, desconocida.

| **ℹ Descubrimiento de red vía SSRF**  ¿Cómo descubrir la IP interna sin acceso a terminal ni a netdiscover? Solo tenemos peticiones web a través del servidor. Solución: **fuerza bruta del último octeto** de la IP con **Burp Intruder**. Es, en la práctica, un escaneo de red interna hecho a través del SSRF. |
| --- |

1. Enviar la petición Check stock a **Intruder**.
2. En **Positions**, marcar como posición (Add §) únicamente el último octeto de la IP interna, dejando fija la parte 192.168.0. y el puerto :8080. Objetivo: http://192.168.0.§1§:8080/admin.
3. En **Payloads**, tipo **Numbers**, rango de 1 a 255, paso 1.
4. (Opcional/recomendado) En **Resource pool**, limitar a **1 petición por segundo** para no hacer ruido ni tumbar el servicio; a más peticiones/seg, más riesgo de alertas o de romper el servidor.
5. Lanzar el ataque y ordenar por **Status code** / **Length**: la IP del almacén (.1) devuelve 400/500 con *missing parameter*; la IP del panel de admin devuelve un **`200`** con longitud distinta.
6. Con la IP encontrada (en el ejemplo de clase, la .120), repetir el borrado: http://192.168.0.120:8080/admin/delete?username=carlos.

| stockApi=http://192.168.0.120:8080/admin/delete?username=carlos |
| --- |
| **⚠ Todo es dinámico por instancia**  Cada instancia de laboratorio es dinámica: la URL del lab, el productId que ves y la **IP interna del panel** cambian por alumno. No copies la IP del compañero: descúbrela con Intruder en tu propia instancia. Muchas veces la ruta de borrado te la da el panel al pasar el ratón por encima del botón Delete. |

Sigilo: para reducir ruido se puede trocear el barrido por sesiones (hoy del 1 al 50, mañana del 50 al 100…) además de limitar peticiones/segundo. Y para mapear puertos en vez de IPs, se puede iterar el puerto: es, en efecto, un mini *port scan* HTTP a través del SSRF (recordando que solo alcanza servicios que hablen HTTP).

## **Laboratorio 3 — Blind SSRF (no realizado)**

| **ℹ Pendiente / autoestudio**  No se practicó en clase por requerir Burp Collaborator (Burp Pro). Se deja como investigación personal. En Blind SSRF no hay salida visible: la confirmación se hace observando la interacción externa que provoca el servidor. |
| --- |

## **Laboratorio 4 — SSRF con filtro de entrada basado en blacklist**

**Objetivo:** mismo fin (http://localhost/admin → borrar carlos), pero ahora hay un **anti-SSRF** que bloquea ciertas cadenas. Al enviar http://localhost/... responde bloqueado por seguridad.

Una **blacklist** bloquea cadenas concretas (p. ej. la palabra localhost, o admin). Frente a ella se prueban representaciones equivalentes del mismo destino hasta encontrar una que el filtro no contemple:

## **Técnicas de bypass de blacklist vistas**

- **IP en vez de nombre:** sustituir localhost por 127.0.0.1.
- **Formas cortas/alternativas de la IP loopback:** 127.1 es equivalente a 127.0.0.1 (se pueden omitir octetos y ceros). El sistema las resuelve igual.
- **Doble (o múltiple) URL-encoding de caracteres bloqueados:** si admin está en la lista, codificar en URL alguna de sus letras. Normalmente el backend valida la cadena tras **un** URL-decode, pero **no** vuelve a decodificar; codificando **dos veces** el filtro no la reconoce y sí llega al recurso.

| stockApi=http://127.1/admin/delete?username=carlos  stockApi=http://127.1/%2561dmin/delete?username=carlos |
| --- |
| **ℹ Ampliación — por qué funciona el doble encode**  %2561 es el doble URL-encode de la letra a (a → %61 → %2561). El razonamiento es idéntico al de Path Traversal cuando el servidor filtra ../: se busca una codificación que el parser no contemple. Con una sola capa muchos filtros sí lo detectan; a partir de la segunda capa, a menudo no. |
| **⚠ Incidencias del entorno**  Detalle práctico de clase (VMware): si al arrastrar en Kali se pierde el copiar/pegar entre invitado y anfitrión, reiniciar la máquina lo restablece. Si Burp Browser no abre, revisar Settings → Tools → Burp's browser → Allow Burp's browser to run without a sandbox. |

# **Herramientas utilizadas en la sesión**

| **Herramienta** | **Objetivo** | **Fase** | **Uso visto** | **Nivel** | **Notas** |
| --- | --- | --- | --- | --- | --- |
| Burp Proxy | Interceptar y modificar la petición | Explotación web | Interceptar POST /product/stock | Recurrente | Base de todo el flujo SSRF |
| Burp Repeater | Reenviar y ajustar payloads | Explotación web | Editar stockApi y reenviar | Recurrente | Ctrl+Shift+U / Ctrl+U para (de)codificar |
| Burp Intruder | Fuerza bruta del octeto de IP | Descubrimiento interno | Payload Numbers 1–255 | Practicada | Escaneo de red vía SSRF; ordenar por status/length |
| Burp Decoder | Codificar/decodificar URL | Bypass de filtros | Doble URL-encode de 'a' | Practicada | Clave para evadir blacklist |
| Burp Resource pool | Limitar peticiones concurrentes | Sigilo | 1 req/seg | Introducida | Reduce ruido y evita alertas |
| Burp Collaborator | Detectar Blind SSRF | Detección | No usado (requiere Pro) | Mencionada | Necesario para el lab 3 |

# **Riesgos, errores comunes y buenas prácticas**

| **⚠ RIESGO**  Error frecuente: intentar pulsar los botones del panel renderizado en la respuesta. Ese clic lo lanzas tú desde fuera y falla. La acción destructiva debe viajar dentro de stockApi para que la ejecute el servidor. |
| --- |
| **⚠ AVISO**  No copies la IP interna ni el productId del compañero: cada instancia es distinta. Descubre siempre en tu propia sesión. |
| **⚠ AVISO**  Con un solo URL-encode muchos filtros detectan la cadena; prueba doble o múltiple encode antes de rendirte. |
| **✓ Contramedidas**  Defensa recomendada (lado desarrollo): **whitelist** de destinos permitidos + validación estricta del destino final, control de **redirecciones** (los redirect esconden URLs), atención a userinfo (usuario@host) y a los **fragmentos** (#) en la URL, uso de librerías/parsers robustos y bloqueo a nivel de red. La blacklist casi siempre se acaba evadiendo; la whitelist es más sólida. |
| **ℹ NOTA**  Recordatorio ético y de alcance: todo esto se practica en laboratorios autorizados (PortSwigger) y entornos propios. SSRF sí aparece en auditorías reales. |

# **Conexión con sesiones anteriores**

Esta sesión encadena directamente con la anterior de **Path Traversal / LFI**. La metodología es la misma: identificar el indicio (allí un parámetro que carga un archivo; aquí un parámetro que construye una URL), probar el caso simple y, si se bloquea, iterar variantes (duplicar ../, doble encode…). El razonamiento de bypass de filtros es transversal a ambas vulnerabilidades.

También se enlaza con el trabajo previo en **Burp Suite** (Proxy, Repeater, Intruder, Decoder) y con la lógica de enumeración: aquí Intruder cumple, vía SSRF, un papel parecido al de netdiscover/Nmap en la fase de descubrimiento, pero limitado a HTTP y a través del servidor. Se mencionó también el patrón **IDOR** y el robo de cookies vía **XSS** como caminos alternativos no desarrollados.

# **Resumen final**

El **SSRF** convierte al servidor en intermediario para alcanzar recursos internos por HTTP que el atacante no ve directamente. El indicio es un parámetro con una **URL** que el servidor consulta (aquí, stockApi del Check stock). Se explotó primero contra **localhost**, luego contra la **red interna** descubriendo la IP del panel con **Burp Intruder** (fuerza bruta de octeto, 1–255), y por último se evadió una **blacklist** con IPs alternativas (127.1) y **doble URL-encode**. La acción final siempre la ejecuta el servidor, no el atacante. Del lado defensivo, la **whitelist** y la validación del destino son más robustas que cualquier lista negra. Queda pendiente el **Blind SSRF** (requiere Burp Collaborator).

# **Checklist de repaso**

1. ¿Sé explicar la analogía del servidor como *mensajero* y por qué es peligrosa?
2. ¿Distingo el indicio de SSRF (URL) del de LFI (archivo)?
3. ¿Sé interceptar el Check stock y localizar el parámetro stockApi?
4. ¿Sé apuntar stockApi a http://localhost/admin y a la ruta /admin/delete?username=carlos?
5. ¿Entiendo por qué el clic en el panel renderizado no funciona y sí la URL en stockApi?
6. ¿Sé montar el ataque con Intruder (Positions en el octeto, Payload Numbers 1–255) y leer status/length?
7. ¿Conozco bypasses de blacklist: 127.0.0.1, 127.1, doble URL-encode?
8. ¿Sé qué contramedidas recomendar (whitelist, validación de destino, control de redirects/userinfo/fragmentos)?

# **Actualización del registro de herramientas**

Cambios de nivel y nuevas entradas respecto al registro acumulado (copiable a la base de conocimiento):

| **Herramienta** | **Nivel** |
| --- | --- |
| Burp Suite — Proxy | Recurrente |
| Burp Suite — Repeater | Recurrente |
| Burp Suite — Intruder | Practicada (fuerza bruta de IP interna vía SSRF) |
| Burp Suite — Decoder | Practicada (doble URL-encode para bypass) |
| Burp Resource pool | Introducida (control de peticiones/seg) |
| Burp Collaborator | Mencionada (necesario para Blind SSRF) |
| **ℹ Para la base de conocimiento**  Concepto/vulnerabilidad nuevo de la sesión: **SSRF** (Server Side Request Forgery), con variante **Blind SSRF** pendiente. Patrones mencionados de pasada: **IDOR** y robo de cookies vía **XSS**. |
