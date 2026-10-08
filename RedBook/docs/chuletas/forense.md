---
tags:
  - Chuletas
---
# Forense y Wireshark

## Servir archivos / recibir
- `python3 server.py` · `python3 server.py https`

## Crear certificados (HTTPS de laboratorio)
```
openssl req -x509 -newkey rsa:2048 -nodes \
  -keyout key.pem -out cert.pem -days 365 \
  -subj "/CN=localhost"
```

## Notas
- `.aspx` → `.net` → pensado para servidor Windows
- Wireshark / tcpdump para capturar y seguir flujos de tráfico (más Blue Team: ver
  [Análisis de tráfico](../blue-team/analisis-trafico/index.md)).
