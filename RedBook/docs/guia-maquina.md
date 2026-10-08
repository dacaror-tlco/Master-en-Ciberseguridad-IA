---
tags:
  - Guía
hide:
  - tags
---
# Guía de máquina — ¿por dónde tiro?

Flujo operativo para una máquina de CTF o laboratorio. Úsalo como mapa: **enumera siempre antes
de explotar** y, en cada paso, salta a la [chuleta](chuletas/index.md) con los comandos y a una
máquina de ejemplo en los [walkthroughs](red-team/walkthroughs/index.md).

!!! tip "Regla de oro"
    Si te atascas, vuelve a enumerar. El 90% de lo que falta es enumeración que te saltaste.

## 0 · Preparación y reconocimiento de red
- [ ] `netdiscover -r <red>` / `arp-scan` para localizar la IP
- [ ] `nmap -p- -sCV -Pn -T5 --open <ip> -oN nmap.txt`
- [ ] Añadir el host a `/etc/hosts` si usa dominio (`.htb`, `.thl`)
- [ ] Anotar **puertos y versiones** → salta al servicio correspondiente

→ [Chuleta: Reconocimiento y enumeración](chuletas/reconocimiento-enumeracion.md)

## 1 · ¿Qué puerto veo? → por dónde seguir

| Puerto / servicio | A dónde ir |
|---|---|
| 21 FTP | [FTP](#ftp-21) |
| 22 SSH | [SSH](#ssh-22) |
| 80 / 443 HTTP(S) | [Web](#web-80-443) |
| 139 / 445 SMB | [SMB](#smb-139-445) |
| 3306 MySQL · 5432 Postgres | [Bases de datos](#bases-de-datos) |
| 2049 NFS | [NFS](#nfs-2049) |
| Otro / desconocido | [Servicios poco comunes](#servicios-poco-comunes) |

---

## FTP (21)
- [ ] Probar acceso anónimo: `ftp anonymous@<ip>` → `get`/`put`, `ls -la`
- [ ] ¿La escritura se refleja en la web (IIS/Apache)? → subir webshell → RCE
- [ ] Buscar exploit por versión: `searchsploit <servicio> <versión>`
- [ ] Si pide credenciales: `hydra -L users -P rockyou ftp://<ip>`

**Ejemplo:** [Devel](red-team/walkthroughs/windows.md#devel-htb-21-ftp-80-iis) (FTP que sirve la raíz de IIS).

## SSH (22)
- [ ] Rara vez es la entrada; sirve para consolidar acceso con credenciales ya obtenidas
- [ ] Fuerza bruta solo con usuario conocido: `hydra -l <user> -P rockyou ssh://<ip>`
- [ ] ¿Clave `id_rsa` encontrada? → `chmod 600`, y si tiene passphrase: `ssh2john` → `john`
- [ ] rbash restringido → `ssh user@ip bash`

→ [Chuleta: claves SSH](chuletas/explotacion.md#claves-ssh)

## Web (80 / 443)
**Enumerar primero:**
- [ ] Fingerprint: `whatweb`, Wappalyzer; mirar código fuente y cabeceras
- [ ] Directorios: `dirsearch -u http://<ip>` / `feroxbuster` / `ffuf`
- [ ] Vhosts/subdominios si hay dominio: `ffuf -u http://FUZZ.<dom>/ ...`
- [ ] `robots.txt`, `/.git`, backups, paneles de login

**¿Es un CMS?**
- [ ] WordPress → `wpscan --url ... -e u,ap`; plugins con CVE (File Manager, etc.)
- [ ] Joomla → `joomscan`; editar plantilla para webshell
- [ ] Drupal/otros → `searchsploit`

**¿Qué vulnerabilidad probar?** (según lo que haga la app)

| Señal en la app | Técnica | Chuleta | Ejemplo |
|---|---|---|---|
| Formulario / parámetro con comillas rompe | SQLi | [SQLi](chuletas/sqli-union.md) | [GoodGames](red-team/walkthroughs/web.md#goodgames-htb) |
| Carga/incluye ficheros por nombre | LFI / Path Traversal | [Path Traversal](chuletas/path-traversal.md) | [Report](red-team/walkthroughs/web.md#report-thl-22-80-3306) |
| Refleja texto en plantillas | SSTI | [SSTI](chuletas/ssti.md) | [GoodGames](red-team/walkthroughs/web.md#goodgames-htb) |
| La app pide/visita una URL | SSRF | [SSRF](chuletas/ssrf.md) | — |
| Sube XML / procesa XML | XXE | — | [Castor](red-team/walkthroughs/linux.md#castor-thl) |
| Permite subir archivos | File upload | [SQLi/upload](chuletas/sqli-union.md) | [Magic](red-team/walkthroughs/web.md#magic-htb) |
| Campo que ejecuta (ping, trace) | Command injection | — | [Rick](red-team/walkthroughs/linux.md#rick-thm-21-22-80-9090-13337-22222-60000) |
| Parámetros ocultos | Fuzzing params (x8) | [Explotación](chuletas/explotacion.md) | [Rockstars](red-team/walkthroughs/web.md#rockstars-thl-22-80) |

!!! tip "¿El login te bloquea por intentos?"
    Muchos paneles limitan los intentos **por IP**. Se suele evitar mandando una IP distinta en
    cada petición con una cabecera: `X-Forwarded-For: 9.9.9.9` (también `X-Real-IP`,
    `X-Client-IP`). En Burp Intruder se itera esa cabecera junto al diccionario de contraseñas.
    Visto en [Nibbles](red-team/walkthroughs/web.md#nibbles-htb).

→ Objetivo: **webshell o reverse shell**. Recordatorio de reverse en [Explotación](chuletas/explotacion.md#reverse-shell-recordatorio).

## SMB (139 / 445)
- [ ] Sesión nula: `smbclient -N -L //<ip>`; `netexec smb <ip> -u '' -p '' --shares`
- [ ] Enumerar: `enum4linux <ip>`
- [ ] Con credenciales: `smbmap -H <ip> -u <user> -p <pass>` (buscar recursos READ/WRITE)
- [ ] Credenciales válidas + WinRM → `evil-winrm`

→ [Chuleta: SMB](chuletas/reconocimiento-enumeracion.md#smb-445139)

## Bases de datos
- [ ] MySQL: `mysql -h <ip> -u root -p --skip-ssl` (credenciales vistas en `config.php`/`wp-config.php`)
- [ ] Puerto interno no expuesto → túnel con `chisel` (`R:3307:127.0.0.1:3306`)
- [ ] Volcar usuarios/hashes → crackear ([Explotación](chuletas/explotacion.md#cracking-de-hashes-offline))

**Ejemplo:** [Magic](red-team/walkthroughs/web.md#magic-htb) (chisel → MySQL interno).

## NFS (2049)
- [ ] `showmount -e <ip>`
- [ ] `mount -t nfs <ip>:/ /mnt/...` → buscar ficheros, claves, `no_root_squash`

## Servicios poco comunes
- [ ] Banner: `nc <ip> <puerto>`; `searchsploit <servicio>`
- [ ] Puertos altos con servicios propios (ver [Rick](red-team/walkthroughs/linux.md#rick-thm-21-22-80-9090-13337-22222-60000))
- [ ] Software con CVE conocido (p. ej. Log4Shell en [Unified](red-team/walkthroughs/windows.md#unified-htb-8080-22-6789-8443-8843))

---

## Ya tengo shell de usuario → escalada
- [ ] **Estabilizar** la shell (pty, `stty raw -echo`, `TERM`)
- [ ] `sudo -l` (lo primero siempre)
- [ ] SUID: `find / -perm -4000 -type f 2>/dev/null`
- [ ] Cron / procesos: `cat /etc/crontab`, `pspy64`
- [ ] Secuestro de `$PATH` o de módulo Python
- [ ] Credenciales reutilizables en ficheros de config, mail, `.bash_history`
- [ ] Binario permitido → **GTFOBins**
- [ ] Windows: `whoami /priv` → `SeImpersonatePrivilege` → **Potato**

→ [Chuleta: Escalada de privilegios](chuletas/escalada.md) · [Fases: Post-explotación](metodologias/fases/post-explotacion.md)

## Documentar
- [ ] Capturar evidencias y cadena de ataque
- [ ] Redactar hallazgos e impacto → [Fases: Informe](metodologias/fases/informe.md)
