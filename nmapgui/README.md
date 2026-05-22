# NmapGUI — Interfaz gráfica para nmap

GUI profesional para nmap desarrollada en Python + PyQt6.  
Proyecto para el Máster en Ciberseguridad e IA.

## Características

- **Panel de configuración** con todos los parámetros de nmap
  - Tipo de escaneo (SYN, TCP, UDP, Null, FIN, Xmas, ACK, Ping…)
  - Selección de puertos (top 1000, todos, top 100, personalizado)
  - Timing T0–T5
  - Detección de SO y versión de servicios
  - Scripts NSE por categoría o personalizados
  - Opciones de exportación automática
- **Preview del comando en tiempo real** — editable manualmente
- **Streaming de salida** — la consola se actualiza línea a línea
- **Visualización por pestañas**:
  - 🖥 Hosts — IP, hostname, estado, SO, puertos abiertos
  - 🔌 Puertos — estado coloreado (open/closed/filtered)
  - ⚙ Servicios — producto, versión, extrainfo
  - 🛡 OS / CPE — detección de sistema operativo
  - 📜 Scripts — resultados NSE por puerto y host
  - 📋 Consola — salida raw en tiempo real
- **Exportar a JSON** con un clic
- **Dark theme** completo (Catppuccin Mocha)

## Estructura del proyecto

```
nmapgui/
├── main.py                 # Punto de entrada + estilos globales
├── gui/
│   ├── main_window.py      # Ventana principal + hilo de escaneo
│   ├── config_panel.py     # Panel izquierdo: parámetros nmap
│   ├── command_bar.py      # Barra del comando generado
│   └── results_panel.py    # Panel derecho: pestañas de resultados
├── core/
│   ├── runner.py           # subprocess + streaming + cancelación
│   └── parser.py           # Parser XML de nmap
├── exports/                # Ficheros XML/TXT/grepable generados
└── README.md
```

## Instalación en Kali Linux

```bash
# 1. Clonar / copiar el proyecto
cd ~/tools/nmapgui

# 2. Instalar PyQt6
pip install PyQt6 --break-system-packages
# o con entorno virtual:
python3 -m venv venv && source venv/bin/activate && pip install PyQt6

# 3. Asegurarse de tener nmap
sudo apt install nmap -y

# 4. Ejecutar
python3 main.py
```

## Uso

1. Introduce el **target** (IP, rango CIDR, dominio)
2. Selecciona el **tipo de escaneo** y opciones en el panel izquierdo
3. El **comando nmap** se genera automáticamente en la barra superior
4. Pulsa **▶ Escanear** (o edita el comando manualmente y lanza)
5. Observa la **consola raw** en tiempo real
6. Al terminar, explora los resultados en las pestañas

## Notas de seguridad

- Los escaneos SYN (-sS) y de OS (-O) requieren privilegios root → marca "Ejecutar con sudo"
- Usa siempre en redes y sistemas de tu propiedad o con permiso explícito
- Los resultados se guardan automáticamente en `exports/`

## Dependencias

| Paquete | Versión mínima | Uso |
|---------|----------------|-----|
| Python  | 3.10+          | f-strings con tipos, match |
| PyQt6   | 6.4+           | GUI |
| nmap    | 7.80+          | Herramienta de red |
