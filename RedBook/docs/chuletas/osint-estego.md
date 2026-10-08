---
tags:
  - Chuletas
---
# OSINT y esteganografía

## Análisis de archivos
- `file <archivo>` → tipo real
- `convert` → cambiar de formato
- `strings -n 8 <archivo>` → cadenas legibles (datos ocultos)
- `exiftool <archivo>` → metadatos (`-Artist=""`, `-Comment=""`, `-gps:all`)
- `exiftool -c "%.6f" -GPSLatitude -GPSLongitude img.jpg`
- `md5sum` → hash
- `binwalk <archivo>` / `binwalk -e <archivo>` → archivos incrustados / extraer

## Esteganografía
- `steghide info <img>`
- `steghide embed -cf <img> -ef <txt> -p "<pwd>"`
- `steghide extract -sf <img> -p "<pwd>"`
- `stegseek <img> /usr/share/wordlists/rockyou.txt` → crackear passphrase

## OSINT
- Brechas: DeHashed, LeakRadar
- Grafos: Maltego · Teléfonos: Truecaller
- Superficie/exposición: Shodan, Censys, FOFA, Google Dorks, Wayback Machine

## HUMINT (personas)
- Usuarios: Sherlock, Maigret, whatsmyname
- Imágenes: PimEyes, Yandex

## Subdominios
- subdomainfinder.c99.nl, Censys search, Sublist3r, Shodan, FOFA
- `python sublist3r.py -d <dominio>`
