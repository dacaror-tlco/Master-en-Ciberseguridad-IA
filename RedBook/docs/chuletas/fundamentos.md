---
tags:
  - Chuletas
---
# Fundamentos (Linux / Windows)

## Bash — navegación y ficheros
- `pwd`, `ls`, `cd`, `mkdir`, `mkdir -p` (jerarquía), `touch`
- `rm` / `rm -rf` (recursivo), `cp <origen> <destino>`, `mv <origen> <destino>` (también renombra)
- `grep <patrón>` / `grep -r <patrón> <ruta>`
- Config permanente: `~/.bashrc`

## Búsqueda y procesado
- `find . -name "*.txt"` (dónde / filtro / archivo); `-mtime -7` (días); `-perm /u+x`; `-delete`
- `head -n` / `tail -n` / `tail -f` (seguimiento en tiempo real)
- `wc` (líneas/palabras/caracteres), `sort` / `sort -rh` (por tamaño), `uniq`
- Pipe `|` encadena: `history | head -10`
- Operadores: `&&` (2º si el 1º va bien), `||` (2º si el 1º falla), `;` (secuencia)
- `kill <pid>`; `$!` = último proceso

## Info del sistema
- `uname -a`, `df -h` (disco), `free -h` (RAM), `whoami`, `hostname`
- `gunzip` (descomprimir), `history` (historial), `setxkbmap es` (teclado)

## Permisos
- `ls -l`: primer carácter `d` = directorio; luego `owner` / `group` / `others` (`rwx`)
- `chmod` octal: `r=4 w=2 x=1` → `7=rwx`, `777`, `421=r+x`...
- Comandos propios en `$PATH`; `#!/bin/bash` + permiso de ejecución

## Windows — cmd ↔ Linux
| cmd | Linux / PowerShell |
|---|---|
| `dir` | `ls` |
| `cd` / `cd /d D:\` | `cd` |
| `cls` | `clear` |
| `del` / `rmdir` | `rm` / `rmdir` |
| `ipconfig` | `ifconfig` |
| `copy` / `move` | `cp` / `mv` |
| `whoami /all` | `whoami` |
| `net user <u>` / `net share` / `net accounts` | — |
| `dir /b /s *.txt` | `find . -name "*.txt"` |
| `doskey /history` | `history` |

## Funciones PowerShell
- `Set-Location -Path "..."`, `Get-Location`, `Clear-Host`, `Get-NetIPConfiguration`
