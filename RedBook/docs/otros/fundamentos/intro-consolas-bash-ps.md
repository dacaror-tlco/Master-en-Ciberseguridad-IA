---
tags:
- Fundamentos
---

# Intro Consolas Bash PS

EVOLVE ACADEMY - MASTER EN CIBERSEGURIDAD

**Introducción a Consolas: Bash y PowerShell**

Instructor: Carlos · Terminal y entorno de trabajo

*Temas: Terminal vs GUI · Bash básico · PowerShell · Virtualización · PATH · Comandos de navegación*

# **① Terminal vs GUI — ¿Por qué la línea de comandos?**

La terminal (CLI) es más potente, reproducible y automatizable que la interfaz gráfica (GUI). En auditorías, la mayoría de herramientas son de consola.

| **Terminal (CLI)**   - Automatizable con scripts - Herramientas de hacking son CLI - Menor consumo de recursos - Control total del sistema - Más rápida para operaciones repetitivas | **GUI (Interfaz Gráfica)**   - Más intuitiva para principiantes - Mejor para edición visual - No automatizable directamente - Mayor consumo de recursos - Depende del entorno gráfico |
| --- | --- |

# **② Configuración del entorno: Virtualización**

El entorno de trabajo estándar en el máster es Kali Linux sobre VirtualBox o VMware. Kali incluye todas las herramientas preinstaladas.

| # Opciones de virtualización:  VirtualBox → Gratuito. Descargar imagen Kali (.ova) e importar.  VMware → Más rendimiento. Preferido por el instructor.  WSL2 → Bash en Windows (no recomendado para el máster).  Nativo → Instalación directa en hardware (máximo rendimiento).  # Recursos recomendados por VM:  RAM: mínimo 2 GB (recomendado 4 GB)  CPU: 2 cores mínimo  Disco: 30 GB mínimo  # Red en VMs:  NAT → VM con internet, sin acceso desde el exterior  Host-Only → VM aislada, solo comunica con host  Bridged → VM en la misma red que el host (como un equipo más) |
| --- |

| **💡 RECOMENDACIÓN** | Para laboratorios con varias VMs (atacante + víctima): usar red Host-Only o una red NAT interna para que estén aisladas de Internet. |
| --- | --- |

# **③ Anatomía de la terminal Bash**

| kali@kali:~$  # └─ usuario@hostname:directorio\_actual$  # ~ = home del usuario (/home/kali)  # $ = usuario normal (# = root)  # Atajos de teclado útiles:  Ctrl+C → cancelar proceso actual  Ctrl+Z → suspender proceso (bg para reanudar en background)  Ctrl+L → limpiar pantalla (equivale a 'clear')  Ctrl+A → ir al inicio de la línea  Ctrl+E → ir al final de la línea  Ctrl+R → búsqueda en historial  Tab → autocompletar comando/ruta  Tab Tab → mostrar todas las opciones posibles  ↑ / ↓ → navegar por el historial de comandos |
| --- |

# **④ Comandos esenciales de Bash**

| # Navegación:  pwd # directorio actual  ls -la # listar con detalles y ocultos  cd /ruta # cambiar directorio  cd .. # subir al padre  # Ficheros:  cat fichero.txt # ver contenido  nano fichero.txt # editor simple en terminal  cp src dst # copiar  mv src dst # mover/renombrar  rm fichero # borrar  mkdir -p dir/subdir # crear árbol de directorios  # Información del sistema:  whoami # usuario actual  id # UID, GID y grupos  uname -a # información del kernel  hostname # nombre del equipo  ifconfig / ip a # interfaces de red  df -h # espacio en disco  free -h # memoria RAM |
| --- |

# **⑤ Rutas: absoluta vs relativa**

El concepto de **path** (ruta) es uno de los más importantes del máster. Aparece constantemente en escalada de privilegios.

| **Ruta absoluta**  Empieza siempre por /  /home/kali/documentos/fichero.txt  Funciona desde cualquier directorio | **Ruta relativa**  Parte desde el directorio actual  documentos/fichero.txt  Depende de dónde estés ahora |
| --- | --- |

| **🔐 ESCALADA** | En escalada de privilegios, la diferencia entre ruta absoluta y relativa en scripts SUID puede ser la vulnerabilidad. Si un script llama 'python' (relativo) podemos poner nuestro propio 'python' en el PATH. |
| --- | --- |

# **⑥ Introducción a PowerShell**

PowerShell es la shell de Windows, también disponible en Linux/macOS. En pentesting Windows es fundamental para post-explotación.

| # Comparativa rápida Bash → PowerShell:  ls / dir → Get-ChildItem (gci, ls, dir — todos funcionan)  cd → Set-Location (cd funciona también)  cat → Get-Content  echo → Write-Host / Write-Output  rm → Remove-Item  cp → Copy-Item  mv → Move-Item  grep → Select-String  find → Get-ChildItem -Recurse  # Obtener ayuda:  Get-Help Get-ChildItem # ayuda de un comando  Get-Help Get-ChildItem -Examples  # Información del sistema:  whoami  Get-LocalUser # listar usuarios locales  Get-Process # procesos (equivale a ps aux)  ipconfig /all # interfaces de red |
| --- |

| **💡 PENTEST** | PowerShell permite ejecutar código en memoria, descargar payloads, y moverse lateralmente. Herramientas como PowerView o PowerSploit lo aprovechan. Por eso muchas empresas restringen su ejecución. |
| --- | --- |

# **⑦ Gestión de paquetes en Kali Linux**

| # APT — gestor de paquetes de Debian/Kali  sudo apt update # actualizar lista de paquetes  sudo apt upgrade -y # actualizar paquetes instalados  sudo apt install nombre-paquete # instalar herramienta  sudo apt remove nombre-paquete # desinstalar  sudo apt search herramienta # buscar paquete  apt-cache show nombre-paquete # info del paquete  # También disponible en Kali:  pip install herramienta # paquetes Python  gem install herramienta # paquetes Ruby  go install ... # paquetes Go |
| --- |
