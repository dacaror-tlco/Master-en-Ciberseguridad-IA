# Instalación como servicio de sistema

El agente se ejecuta siempre a través del mismo punto de entrada
(`python -m agent.main --config <ruta.yaml>`); lo único que cambia por
plataforma es quién lo arranca, lo reinicia si muere, y le manda la señal
de parada. `agent/main.py` ya sabe responder a `SIGTERM`/`SIGINT` con un
apagado ordenado (para el sync engine, hace un último flush, y cierra el
store), así que las tres integraciones son wrappers finos.

## Linux (systemd)

```bash
sudo mkdir -p /opt/evidence-agent /etc/evidence-agent /var/lib/evidence-agent
sudo cp -r agent /opt/evidence-agent/
sudo cp config/agent.example.yaml /etc/evidence-agent/agent.yaml   # ajustar antes de arrancar
cd /opt/evidence-agent && sudo python3 -m venv venv && sudo ./venv/bin/pip install -r requirements.txt

sudo cp agent/service/evidence-agent.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now evidence-agent

# ver logs:
journalctl -u evidence-agent -f
```

## Windows (pywin32)

```powershell
pip install pywin32
$env:EVIDENCE_AGENT_CONFIG = "C:\ProgramData\evidence-agent\agent.yaml"
python agent\service\windows_service.py install
python agent\service\windows_service.py start
```

La variable de entorno `EVIDENCE_AGENT_CONFIG` debe quedar definida a
nivel de sistema (no solo de sesión) para que el servicio la vea al
arrancar automáticamente tras un reinicio — se configura en Variables de
entorno del Sistema, o dejándola fijada en el propio registro del
servicio.

## macOS (launchd)

```bash
sudo mkdir -p /opt/evidence-agent /var/log/evidence-agent
sudo cp -r agent config /opt/evidence-agent/
cd /opt/evidence-agent && sudo python3 -m venv venv && sudo ./venv/bin/pip install -r requirements.txt

sudo cp agent/service/com.empresa.evidence-agent.plist /Library/LaunchDaemons/
sudo chown root:wheel /Library/LaunchDaemons/com.empresa.evidence-agent.plist
sudo launchctl load /Library/LaunchDaemons/com.empresa.evidence-agent.plist
```

## Notas comunes

- **Permisos**: en las 3 plataformas el agente corre como root/administrador,
  porque necesita monitorizar rutas y procesos de todos los usuarios. Es
  candidato a hardening posterior (capacidades específicas en Linux en vez
  de root completo).
- **`db_path`** en la config debe apuntar a una ruta que sobreviva
  reinicios y con permisos de escritura para el usuario del servicio.
- **Actualizar `rules.yaml`** en caliente no requiere reiniciar el
  servicio si en el futuro se añade un watcher sobre el propio fichero de
  reglas; hoy sí requiere reinicio (`systemctl restart evidence-agent`,
  etc.) porque se carga una sola vez al construir el `Orchestrator`.
