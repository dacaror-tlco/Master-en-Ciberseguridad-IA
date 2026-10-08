---
tags:
- Fundamentos
---

# Manual VBox a VMware

**EVOLVE ACADEMY · MASTER EN CIBERSEGURIDAD**

**Manual de Laboratorio**

Migrar una Máquina Virtual de VirtualBox a VMware Workstation

Entorno: Windows 10/11 · VMware Workstation 25H2 · Disco VMDK

# **① Introducción y requisitos previos**

Este manual explica cómo importar una máquina virtual de VirtualBox en VMware Workstation aprovechando que VirtualBox puede guardar el disco en formato .vmdk, que VMware acepta de forma nativa. No se necesitan herramientas de conversión adicionales.

**Requisitos:**

- VMware Workstation (versión 16 o superior recomendada)
- Carpeta de la VM de VirtualBox con el archivo .vmdk y .vbox
- No es necesario tener VirtualBox instalado

| **💡 NOTA** | Este proceso no modifica el archivo .vmdk original. La VM de VirtualBox sigue siendo utilizable si se mantiene el archivo original. |
| --- | --- |

| **⚠ AVISO** | Elige 'Mantener formato existente' cuando VMware lo pregunte. El .vmdk ya es compatible de forma nativa y la conversión no mejora el rendimiento. |
| --- | --- |

# **② Flujo de trabajo completo**

| **Localizar .vmdk** | **→** | **Nueva VM VMware** | **→** | **Seleccionar disco** | **→** | **Configurar red** | **→** | **Arrancar** |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

# **③ Paso a paso: crear la VM en VMware**

**Paso 1 — Verificar los archivos de la VM**

Antes de abrir VMware, comprobar que la carpeta de la VM contiene al menos:

| **Archivo** | **Extensión** | **Descripción** |
| --- | --- | --- |
| Rickdiculously Easy.vbox | .vbox | Configuración de la VM (XML) |
| PTD.vmdk | .vmdk | Disco duro virtual — el más importante |
| Rickdiculously Easy.vbox-prev | .vbox-prev | Backup de configuración anterior |

| **✓ CLAVE** | Solo necesitas el archivo .vmdk. El resto puede ignorarse para la importación en VMware. |
| --- | --- |

**Paso 2 — Crear nueva máquina virtual**

**1. Abrir VMware Workstation** — clic en 'Create a New Virtual Machine'

**2. Seleccionar 'Custom (advanced)'** — permite elegir el disco existente

**3. Compatibilidad de hardware** — dejar 'Workstation 25H2 or later' por defecto → Siguiente

**4. Instalación del SO** — seleccionar 'Instalaré el sistema operativo después' → Siguiente

**Paso 3 — Configurar el sistema operativo**

Seleccionar Linux como sistema operativo invitado. Para RickdiculouslyEasy (Fedora 26):

| Sistema operativo: Linux |
| --- |
| Versión: Other Linux 5.x or later kernel 64-bit |
|  |
| # Si la máquina es de 32 bits usar la variante 32-bit |

**Paso 4 — Nombre y procesadores**

**1. Nombre de la VM** — por ejemplo: RickdiculouslyEasy

**2. Procesadores** — 1 procesador, 1 núcleo — suficiente para máquinas CTF

**3. Memoria RAM** — 512 MB o 1024 MB — más que suficiente para esta VM

**Paso 5 — Configuración de red (importante para CTF)**

| **Modo de red** | **Comunicación** | **Recomendado para** |
| --- | --- | --- |
| Host-only | VM ↔ Host solamente. Aislada de internet. | CTF / laboratorio (más seguro) |
| NAT | VM accede a internet a través del host. | Si la máquina necesita internet |
| Bridged | VM como equipo más en la red real. | Entornos de producción |

| **🔐 HACKING** | Para máquinas CTF como RickdiculouslyEasy usa siempre Host-only. Aisla la VM vulnerable de tu red y de internet. |
| --- | --- |

**Paso 6 — Controladores e/s**

**1. Tipo de controlador SCSI** — LSI Logic (Recomendado) → Siguiente

**2. Tipo de disco** — SCSI (Recomendado) → Siguiente

**Paso 7 — Seleccionar el disco existente**

| **⚠ CRÍTICO** | Aquí está el paso clave. NO crear un nuevo disco. |
| --- | --- |

**1. En la pantalla 'Seleccionar un disco'** — elegir 'Utilizar un disco virtual existente'

**2. Clic en Examinar** — navegar hasta la carpeta de la VM y seleccionar PTD.vmdk

| Ruta ejemplo: |
| --- |
| C:\Users\TuUsuario\Downloads\Rickdiculously Easy\PTD.vmdk |

**3. Cuando VMware pregunte si convertir el disco** — seleccionar “convertir” va mejor!!!

| **💡 INFO** | Convertir no mejora el rendimiento. El .vmdk ya es el formato nativo de VMware. Además, mantener el formato original preserva la compatibilidad con VirtualBox si fuera necesario. |
| --- | --- |

**Paso 8 — Finalizar y ajustar**

**1. Pantalla resumen** — revisar que aparece el .vmdk correcto en 'Disco duro' → clic en Finalizar

**2. Aviso del dispositivo SATA** — clic en 'No' — es normal, VirtualBox usaba un controlador SATA por lo tanto elegir como sata.

| Mensaje normal al arrancar por primera vez: |
| --- |
| 'No se puede conectar el dispositivo virtual sata0:1' |
|  |
| → Clic en 'No'. No afecta al funcionamiento de la VM. |

# **④ Primer arranque**

Al encender la VM debería aparecer el GRUB del sistema operativo. En el caso de RickdiculouslyEasy:

| Fedora (4.11.0-300.fc26.x86\_64) 26 (Server Edition) ← seleccionar esta |
| --- |
| Fedora (0-rescue-...) 26 (Server Edition) |
|  |
| # Se selecciona automáticamente en 2 segundos |
| # Pulsar Enter para arrancar inmediatamente |

| **✓ OBJETIVO** | Si ves el GRUB, la importación ha sido correcta. La VM está funcionando en VMware. |
| --- | --- |

# **⑤ Problemas comunes y soluciones**

| **Problema** | **Causa** | **Solución** |
| --- | --- | --- |
| La VM no arranca / pantalla negra | Disco no detectado correctamente | Editar configuración → comprobar que el .vmdk está enlazado |
| Error: no se puede conectar sata0:1 | VirtualBox usaba controlador SATA distinto | Clic en 'No' al aviso — ignorar |
| No se ve la VM desde Kali | Red configurada en NAT en vez de Host-only | Apagar VM → Editar configuración → Red → Host-only |
| VMware pide convertir el disco | Compatibilidad de versión | Seleccionar 'Mantener formato existente' |
| La VM va muy lenta | Poca RAM o CPU asignada | Subir a 1024 MB RAM y 2 núcleos desde configuración |

# **⑥ Cambiar la red a Host-only después de importar**

Si la VM quedó configurada con NAT y quieres aislarla para el CTF:

**1. Apagar la VM completamente**

**2. Clic derecho sobre la VM → 'Settings'**

**3. Sección 'Network Adapter'** — cambiar de NAT a 'Host-only'

**4. Clic en OK y arrancar la VM**

| # Verificar desde Kali que la VM es accesible: |
| --- |
| ip a # ver tu IP en la red host-only (vmnet1) |
|  |
| # Escanear el rango para encontrar la IP de la víctima: |
| nmap -sn 192.168.x.0/24 # sustituir x por tu subred |
|  |
| # Una vez localizada: |
| nmap -sCV <IP\_victima> # enumeración completa |

| **🔐 LAB** | En VMware la red Host-only usa el adaptador vmnet1 (192.168.56.x por defecto). Comprueba tu IP con 'ip a' en Kali antes de escanear. |
| --- | --- |

# **⑦ Resumen del proceso**

| **Localizar PTD.vmdk** | **→** | **Nueva VM Custom** | **→** | **Disco existente** | **→** | **Host-only** | **→** | **Finalizar** | **→** | **Arrancar** |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

Proceso completo en menos de 5 minutos una vez se tienen los archivos localizados. Los pasos críticos son:

- Paso 7: elegir 'Utilizar un disco virtual existente' y seleccionar el .vmdk correcto
- Mantener formato existente cuando VMware lo pregunte
- Ignorar el aviso del dispositivo SATA (clic en No)
- Usar red Host-only para máquinas CTF / laboratorio
