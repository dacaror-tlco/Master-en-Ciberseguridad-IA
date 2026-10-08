---
tags:
- Fundamentos
---

# Fundamentos Linux

EVOLVE ACADEMY - MASTER EN CIBERSEGURIDAD

**Fundamentos de Linux**

Instructor: Carlos · Kali Linux

*Temas: Sistema de ficheros · Permisos · Comandos esenciales · Procesos · Redirección · Pipes · Alias · Variables de entorno*

# **① Sistema de ficheros Linux**

Linux organiza todo en una jerarquía de directorios que parte de la raíz (/). Cada fichero y dispositivo es un nodo de ese árbol.

| **Directorio** | **Contenido** |
| --- | --- |
| / | Raíz del sistema. Todo cuelga de aquí. |
| /home | Directorios personales de cada usuario (p.ej. /home/kali) |
| /etc | Ficheros de configuración del sistema |
| /var | Datos variables: logs, bases de datos, colas |
| /tmp | Ficheros temporales (se borran en cada reinicio) |
| /bin, /usr/bin | Ejecutables del sistema y de usuario |
| /root | Directorio home del usuario root |

| **💡 CLAVE** | /todo/es/un/fichero en Linux: discos, impresoras, procesos... esto permite manipularlo todo con los mismos comandos. |
| --- | --- |

# **② Comandos de navegación esenciales**

| pwd # dónde estoy ahora (Print Working Directory)  ls # listar ficheros del directorio actual  ls -la # listar con permisos, ocultos y tamaños  cd /ruta/absoluta # ir a ruta absoluta (desde /)  cd ruta/relativa # ir a ruta relativa (desde donde estoy)  cd .. # subir un nivel (directorio padre)  cd ~ # ir al home del usuario  cd - # volver al directorio anterior |
| --- |

| **ℹ RUTAS** | Ruta absoluta: empieza por / y lleva la ruta completa. Ruta relativa: parte desde donde estás ahora. Esto es crítico en escalada de privilegios. |
| --- | --- |

# **③ Gestión de ficheros y directorios**

| mkdir clase # crear directorio  mkdir -p a/b/c # crear árbol de directorios de una vez  touch fichero.txt # crear fichero vacío (o actualizar timestamp)  cp origen destino # copiar fichero  mv origen destino # mover o renombrar  rm fichero # borrar fichero  rm -rf directorio/ # ⚠ borrar directorio recursivamente SIN confirmación  cat fichero.txt # mostrar contenido de un fichero  less fichero.txt # ver fichero paginado (q para salir)  head -n 20 fichero.txt # primeras 20 líneas  tail -n 20 fichero.txt # últimas 20 líneas |
| --- |

| **⚠ PELIGRO** | rm -rf / o rm -rf /\* con permisos de root borra TODO el sistema sin confirmación. Nunca ejecutar contra la raíz /. |
| --- | --- |

# **④ Permisos en Linux**

Cada fichero tiene tres grupos de permisos: propietario (u), grupo (g) y otros (o).

| # Formato de ls -la:  # -rwxr-xr-- 1 kali kali 1234 jun 1 fichero.sh  # ^^^ = permisos propietario (rwx = leer, escribir, ejecutar)  # ^^^ = permisos grupo (r-x = leer y ejecutar)  # ^^^ = permisos otros (r-- = solo leer)  chmod 755 fichero.sh # rwxr-xr-x (octal)  chmod +x fichero.sh # añadir permiso de ejecución  chmod u-w fichero.txt # quitar escritura al propietario  chown usuario:grupo fichero # cambiar propietario |
| --- |

| **Permiso** | **Significado** |
| --- | --- |
| r (4) | Leer el contenido del fichero / listar el directorio |
| w (2) | Modificar el fichero / crear o borrar ficheros en el directorio |
| x (1) | Ejecutar el fichero / entrar al directorio (cd) |
| SUID (s) | El fichero se ejecuta con los permisos de su propietario |
| SGID (s) | El fichero se ejecuta con los permisos del grupo |
| Sticky (t) | Solo el propietario puede borrar ficheros en el directorio |

| **🔐 HACKING** | Los ficheros con SUID de root (find / -perm -4000) son vectores clásicos de escalada de privilegios. |
| --- | --- |

# **⑤ Redirección y pipes**

| comando > fichero.txt # redirigir stdout a fichero (sobreescribe)  comando >> fichero.txt # redirigir stdout añadiendo al final  comando 2> errores.txt # redirigir stderr  comando 2>/dev/null # descartar errores  comando < entrada.txt # usar fichero como stdin  cmd1 | cmd2 # pipe: stdout de cmd1 → stdin de cmd2  # Ejemplos prácticos:  nmap -sV 192.168.1.1 | grep open > puertos\_abiertos.txt  cat /etc/passwd | grep bash  ls -la | sort -k5 -n # ordenar por tamaño |
| --- |

| **💡 PIPE** | El pipe | es la herramienta más potente de la terminal. Encadena comandos sin ficheros intermedios. Fundamental en bash scripting. |
| --- | --- |

# **⑥ Búsqueda: grep, find y which**

| grep 'patrón' fichero.txt # buscar patrón en fichero  grep -r 'patrón' directorio/ # buscar recursivamente  grep -i 'patrón' fichero.txt # sin distinguir mayúsculas  grep -v 'patrón' fichero.txt # líneas que NO contienen el patrón  find / -name 'fichero.txt' # buscar por nombre desde la raíz  find / -perm -4000 2>/dev/null # buscar ficheros con SUID  find /home -user kali # ficheros de un usuario concreto  find . -mtime -7 # modificados en los últimos 7 días  which python3 # ruta del ejecutable  locate fichero.txt # búsqueda rápida en base de datos |
| --- |

# **⑦ Procesos**

| ps aux # listar todos los procesos  ps aux | grep nginx # buscar proceso concreto  top # monitor de procesos en tiempo real  htop # monitor visual (más cómodo)  kill -9 PID # matar proceso por ID  killall nombre # matar todos los procesos con ese nombre  jobs # listar procesos en background de esta sesión  comando & # lanzar proceso en background  fg # traer último proceso background al frente |
| --- |

| **ℹ SEÑALES** | kill -9 (SIGKILL) fuerza la terminación sin que el proceso pueda limpiarse. kill -15 (SIGTERM) es más educado: pide al proceso que termine. |
| --- | --- |

# **⑧ Alias y variables de entorno**

| # Alias (atajos para comandos)  alias ll='ls -la'  alias update='sudo apt update && sudo apt upgrade -y'  unalias ll # eliminar alias  alias # listar todos los alias activos  # Para que persistan: añadir al fichero ~/.bashrc o ~/.zshrc  # Variables de entorno  export MI\_VAR='valor' # crear variable de entorno  echo $MI\_VAR # usar variable  env # listar todas las variables de entorno  PATH=$PATH:/nueva/ruta # añadir ruta al PATH  echo $PATH # ver rutas de búsqueda de ejecutables  # Variables importantes:  # $HOME → directorio home del usuario  # $USER → nombre del usuario actual  # $SHELL → shell en uso  # $PWD → directorio actual |
| --- |

# **⑨ Historial y limpieza de rastros**

| history # ver historial de comandos  history | grep nmap # buscar en el historial  !42 # re-ejecutar el comando número 42  !! # re-ejecutar el último comando  Ctrl+R # búsqueda reversa en el historial  # Limpiar rastros:  history -c # limpiar historial en memoria  cat /dev/null > ~/.bash\_history # vaciar fichero de historial  export HISTFILE=/dev/null # deshabilitar historial en esta sesión |
| --- |

| **⚠ FORENSE** | En una auditoría real, el historial se guarda en varios sitios (~/.bash\_history, /var/log/auth.log...). Conocer dónde se almacena es clave tanto para atacar como para defender. |
| --- | --- |
