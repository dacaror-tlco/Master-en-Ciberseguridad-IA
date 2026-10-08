---
tags:
- Fundamentos
---

# Bash Scripting

EVOLVE ACADEMY - MASTER EN CIBERSEGURIDAD

**Introduction to Bash Scripting**

Evolve Academy · Automatización y scripting

*Temas: Variables · Condicionales · Bucles · Funciones · Argumentos · Scripts de enumeración · Buenas prácticas*

# **① ¿Qué es un script de Bash?**

Un script es un fichero de texto con comandos Bash que se ejecutan secuencialmente. Permite automatizar tareas repetitivas.

| #!/bin/bash  # La primera línea es el 'shebang': indica qué intérprete usar  # Crear y ejecutar un script:  nano mi\_script.sh # crear el fichero  chmod +x mi\_script.sh # dar permiso de ejecución  ./mi\_script.sh # ejecutar  bash mi\_script.sh # ejecutar sin dar permiso x |
| --- |

| **💡 SHEBANG** | El #!/bin/bash al inicio es obligatorio para que el sistema sepa que es un script Bash. Sin él, puede interpretarse con sh (shell básica) con diferencias de sintaxis. |
| --- | --- |

# **② Variables**

| #!/bin/bash  # Asignar variables (sin espacios alrededor del =):  nombre='Kali'  ip='192.168.1.1'  contador=0  # Usar variables (con $):  echo "Hola $nombre"  echo "Escaneando: $ip"  # Variables especiales:  $0 # nombre del script  $1 # primer argumento  $2 # segundo argumento  $# # número de argumentos  $@ # todos los argumentos  $? # código de retorno del último comando (0=éxito)  $$ # PID del script actual  # Capturar salida de un comando:  fecha=$(date)  usuarios=$(cat /etc/passwd | grep bash | cut -d: -f1)  echo "Fecha: $fecha" |
| --- |

| **⚠ ESPACIOS** | nombre='valor' ← correcto. nombre = 'valor' ← error. Bash es sensible a los espacios en las asignaciones. |
| --- | --- |

# **③ Entrada de usuario y argumentos**

| #!/bin/bash  # Leer input interactivo:  echo -n 'Introduce la IP objetivo: '  read ip\_objetivo  echo "Escaneando $ip\_objetivo..."  # Leer con prompt integrado:  read -p 'Usuario: ' usuario  read -sp 'Contraseña: ' password # -s = silencioso (no muestra lo escrito)  echo  # Argumentos desde línea de comandos:  # ./script.sh 192.168.1.1 80  ip=$1  puerto=$2  # Verificar que se pasaron argumentos:  if [ $# -lt 2 ]; then  echo 'Uso: $0 <ip> <puerto>'  exit 1  fi |
| --- |

# **④ Condicionales (if/elif/else)**

| #!/bin/bash  # Sintaxis básica:  if [ condición ]; then  # comandos si es verdad  elif [ otra\_condición ]; then  # comandos si la segunda es verdad  else  # si ninguna es verdad  fi  # Comparaciones numéricas:  # -eq igual [ $a -eq $b ]  # -ne no igual [ $a -ne $b ]  # -lt menor que [ $a -lt $b ]  # -gt mayor que [ $a -gt $b ]  # -le menor o igual [ $a -le $b ]  # -ge mayor o igual [ $a -ge $b ]  # Comparaciones de strings:  # = igual [ "$a" = "$b" ]  # != no igual [ "$a" != "$b" ]  # -z vacío [ -z "$var" ]  # -n no vacío [ -n "$var" ]  # Ficheros:  # -f existe y es fichero [ -f fichero.txt ]  # -d existe y es directorio [ -d /ruta ]  # -x es ejecutable [ -x script.sh ]  # -r es legible [ -r fichero ]  # Ejemplo real:  if ping -c1 -W1 $ip &>/dev/null; then  echo "$ip está activo"  else  echo "$ip no responde"  fi |
| --- |

# **⑤ Bucles**

| # FOR — iterar sobre lista:  for ip in 192.168.1.1 192.168.1.2 192.168.1.3; do  echo "Probando $ip"  done  # FOR con rango (secuencia):  for i in $(seq 1 254); do  ping -c1 -W1 192.168.1.$i &>/dev/null && echo "192.168.1.$i activo"  done  # FOR sobre fichero:  for linea in $(cat hosts.txt); do  nmap -p 80,443 $linea  done  # WHILE — mientras condición sea verdad:  contador=1  while [ $contador -le 10 ]; do  echo "Intento $contador"  contador=$((contador + 1))  done  # WHILE para leer líneas de un fichero:  while read linea; do  echo "Procesando: $linea"  done < lista.txt |
| --- |

| **💡 AUTOMATIZACIÓN** | El bucle for con ping sobre el rango /24 es la base de un escáner de hosts casero. Mucho más lento que nmap pero útil para entender cómo funcionan. |
| --- | --- |

# **⑥ Funciones**

| #!/bin/bash  # Definir función:  función\_saludar() {  local nombre=$1 # 'local' limita la variable a la función  echo "Hola, $nombre!"  }  # Llamar función:  función\_saludar 'Chema'  función\_saludar 'Carlos'  # Función con retorno:  esta\_activo() {  ping -c1 -W1 $1 &>/dev/null  return $? # 0=éxito, 1=fallo  }  if esta\_activo '192.168.1.1'; then  echo 'Host activo'  fi  # Función de banner para scripts:  banner() {  echo '================================='  echo " $1"  echo '================================='  }  banner 'Scanner de puertos v1.0' |
| --- |

# **⑦ Script completo: mini scanner de hosts**

| #!/bin/bash  # Host scanner para red /24  # Uso: ./hostscan.sh 192.168.1  RED=$1  ACTIVOS=() # array para guardar resultados  if [ -z "$RED" ]; then  echo "Uso: $0 <prefijo\_red> (ej: 192.168.1)"  exit 1  fi  echo "[\*] Escaneando $RED.0/24..."  for i in $(seq 1 254); do  ip="$RED.$i"  if ping -c1 -W1 $ip &>/dev/null; then  echo "[+] $ip — ACTIVO"  ACTIVOS+=("$ip")  fi  done  echo ""  echo "[\*] Hosts activos encontrados: ${#ACTIVOS[@]}"  for host in "${ACTIVOS[@]}"; do  echo " → $host"  done |
| --- |

# **⑧ Limpieza de rastros y forense**

| # El historial registra todos los comandos en:  ~/.bash\_history  /var/log/auth.log # intentos de login  /var/log/syslog # log del sistema  /var/log/apache2/ # logs de Apache  # Como atacante, limpiar rastros:  history -c && history -w # borrar historial en memoria y disco  export HISTFILE=/dev/null # deshabilitar historial esta sesión  shred -u ~/.bash\_history # borrado seguro  # Como defensor (forense), buscar rastros:  cat ~/.bash\_history  last # últimos logins  lastb # intentos fallidos de login  who # usuarios conectados ahora  w # qué están haciendo |
| --- |

| **🔐 FORENSE** | Eliminar todos los rastros es más complejo de lo que parece: hay múltiples ficheros de log en diferentes rutas. Como defensor, los logs deben enviarse a un SIEM remoto para que el atacante no pueda borrarlos. |
| --- | --- |
