---
tags:
- Fundamentos
---

# Bash Comandos Avanzados

EVOLVE ACADEMY - MASTER EN CIBERSEGURIDAD

**Bash y PowerShell: Comandos Personalizados y Diversión**

Instructor: Carlos · Bash avanzado

*Temas: Redirección avanzada · Operadores lógicos · Pipes · grep/find · Ejercicios prácticos · Plataforma ejercicios*

# **① Repaso: operadores de redirección**

La redirección controla a dónde van la entrada y salida de los comandos. Fundamental para guardar resultados y encadenar herramientas.

| **Operador** | **Función** | **Ejemplo** |
| --- | --- | --- |
| > | Redirigir stdout a fichero (sobreescribe) | nmap -sV IP > resultados.txt |
| >> | Redirigir stdout añadiendo al final | echo 'nuevo' >> fichero.txt |
| < | Usar fichero como stdin | sort < lista.txt |
| 2> | Redirigir stderr (errores) | find / -name x 2> /dev/null |
| 2>&1 | Mezclar stderr con stdout | cmd > todo.txt 2>&1 |
| | | Pipe: stdout → stdin del siguiente | cat /etc/passwd | grep bash |
| || | OR lógico: ejecutar si el anterior falla | cmd1 || cmd2 |
| && | AND lógico: ejecutar si el anterior tuvo éxito | apt update && apt upgrade |
| ; | Ejecutar en secuencia independiente | cmd1; cmd2; cmd3 |

| **💡 /dev/null** | /dev/null es un 'agujero negro': todo lo que se redirija aquí desaparece. Útil para suprimir mensajes de error que no interesan. |
| --- | --- |

# **② Operadores lógicos en la práctica**

| # AND (&&) — ejecutar solo si el anterior tiene éxito:  mkdir proyecto && cd proyecto && touch README.md  nmap -sV 192.168.1.1 && echo 'Scan completado'  # OR (||) — ejecutar solo si el anterior falla:  ping -c1 8.8.8.8 || echo 'Sin conectividad'  cat fichero.txt || echo 'Fichero no existe'  # Punto y coma (;) — siempre ejecuta ambos:  echo 'inicio'; whoami; id; uname -a  # Encadenamiento típico en pentesting:  nmap -p- IP 2>/dev/null | grep open | tee puertos.txt && echo 'Done' |
| --- |

# **③ grep — Búsqueda de patrones**

| grep 'patrón' fichero.txt # búsqueda básica  grep -i 'patrón' fichero.txt # ignorar mayúsculas  grep -r 'patrón' /directorio/ # recursivo  grep -v 'patrón' fichero.txt # líneas que NO contienen  grep -n 'patrón' fichero.txt # mostrar número de línea  grep -c 'patrón' fichero.txt # contar coincidencias  grep -o 'patrón' fichero.txt # mostrar solo la parte que coincide  grep -E 'pat1|pat2' fichero.txt # regex extendida (OR)  grep -A3 'patrón' fichero.txt # 3 líneas después de la coincidencia  grep -B3 'patrón' fichero.txt # 3 líneas antes  # Ejemplos en pentesting:  grep 'open' nmap\_result.txt # filtrar puertos abiertos  grep -r 'password' /var/www/ # buscar passwords en código fuente  cat /etc/passwd | grep '/bin/bash' # usuarios con bash |
| --- |

# **④ find — Búsqueda de ficheros**

| find / -name 'fichero.txt' # buscar por nombre  find / -name '\*.conf' # todos los .conf  find / -name '\*.conf' -type f # solo ficheros (no dirs)  find /home -user kali # ficheros de un usuario  find / -perm -4000 2>/dev/null # ficheros con SUID ← escalada de privs  find / -perm -2000 2>/dev/null # ficheros con SGID  find / -writable -type f 2>/dev/null# ficheros escribibles  find / -mtime -7 # modificados en los últimos 7 días  find . -size +10M # ficheros mayores de 10 MB  # Con acción:  find /tmp -name '\*.tmp' -delete # borrar temporales  find . -name '\*.py' -exec cat {} \; # ejecutar cat en cada .py |
| --- |

| **🔐 SUID** | find / -perm -4000 2>/dev/null es uno de los primeros comandos tras comprometer un equipo. Los ficheros SUID con propietario root son vectores clásicos de escalada. |
| --- | --- |

# **⑤ Comandos de texto y procesamiento**

| # sort — ordenar líneas:  sort fichero.txt # orden alfabético  sort -n fichero.txt # orden numérico  sort -r fichero.txt # orden inverso  sort -k2 fichero.txt # ordenar por columna 2  sort -u fichero.txt # eliminar duplicados al ordenar  # uniq — eliminar duplicados (requiere input ordenado):  sort passwords.txt | uniq  sort passwords.txt | uniq -c # contar repeticiones  # cut — extraer columnas:  cut -d: -f1 /etc/passwd # primer campo del /etc/passwd  cut -d',' -f2,4 datos.csv # columnas 2 y 4 de CSV  # awk — procesado más potente:  awk '{print $1}' fichero.txt # primera columna  awk -F: '{print $1,$3}' /etc/passwd# usuario y UID  # wc — contar:  wc -l fichero.txt # contar líneas  wc -w fichero.txt # contar palabras |
| --- |

# **⑥ echo y creación de ficheros**

| # echo — imprimir texto:  echo 'Hola Mundo'  echo $USER # variable de entorno  echo -e 'línea1\nlínea2' # interpretar \n  # Crear ficheros con echo:  echo 'contenido' > fichero.txt # crear/sobreescribir  echo 'más contenido' >> fichero.txt# añadir al final  # Simular chat (demostración):  echo 'Hola' > chat.txt  echo 'Adiós' >> chat.txt # añade sin borrar lo anterior  cat chat.txt # muestra ambas líneas  # Heredoc — texto multilínea:  cat << EOF > script.sh  #!/bin/bash  echo 'Mi script'  EOF |
| --- |

# **⑦ Plataforma de ejercicios: flujo de trabajo**

El máster utiliza una plataforma de ejercicios (**ejercicios.academy**) donde se practican los comandos vistos. Flujo recomendado:

| **Leer el enunciado** | -> | **Probar en terminal Kali** | -> | **Verificar solución** | -> | **Anotar en apuntes** |
| --- | --- | --- | --- | --- | --- | --- |

| # Consejos para los ejercicios:  # 1. La 'ls' básica vs 'ls -la':  ls # lista simple (solo nombres)  ls -l # lista larga (permisos, tamaño, fecha)  ls -la # incluye ficheros ocultos (empiezan por .)  ls -lh # tamaños legibles (KB, MB, GB)  # 2. El flag -e en rm es peligroso:  rm -rf directorio/ # borra recursivamente sin confirmación  # NUNCA: rm -rf / o rm -rf /\* |
| --- |

| **💡 CONSEJO** | La práctica supera a la memorización. Usa la plataforma de ejercicios todos los días aunque sean 15 minutos. Los comandos se interiorizan con el uso, no leyendo. |
| --- | --- |

# **⑧ Comandos de red en Bash**

| ip a # ver interfaces de red (moderno)  ifconfig # ver interfaces (legacy, aún disponible en Kali)  ip route # tabla de rutas  ss -tulnp # puertos abiertos y procesos (moderno)  netstat -tulnp # igual pero legacy  ping -c4 8.8.8.8 # test de conectividad  curl ifconfig.me # ver IP pública  wget URL # descargar fichero  curl -s URL # petición HTTP silenciosa  # Netcat — navaja suiza de red:  nc -lvnp 4444 # escuchar en puerto 4444  nc IP 4444 # conectar a IP:4444  nc -z IP 80 # comprobar si puerto está abierto |
| --- |
