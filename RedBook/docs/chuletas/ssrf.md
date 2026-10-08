---
tags:
  - Chuletas
---
# SSRF (Server-Side Request Forgery)

Basado en los labs tipo PortSwigger.

## Acceso a servicios internos
- Probar botones "Check stock" / "my account" que piden una URL
- Cambiar la URL interna por `http://localhost/admin`
- Acción sobre el panel interno: `http://localhost/admin/delete?username=carlos`

## Barrido de IPs internas
- `http://192.168.0.1:8080/admin`
- Burp Intruder, payload numérico `1-255`, mirar códigos de respuesta
- Al dar con la IP, lanzar `admin/delete?username=carlos`

## Bypass de filtros
- Encodear `admin` varias veces
- IP alternativa: `127.1` en lugar de `127.0.0.1`
- Si fuerza un host permitido, usar userinfo + fragmento:
  `http://localhost#@stock.weliketoshop.net` (encodear el `#`)
- Si solo admite una ruta concreta (`/product/stock`), reutilizar la URL que aparece en el
  redirect de "next product" y meter el `admin` en el path (encodeado).
