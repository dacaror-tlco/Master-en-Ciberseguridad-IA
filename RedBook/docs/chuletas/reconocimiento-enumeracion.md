---
tags:
  - Chuletas
---
# Reconocimiento y enumeración

## Descubrimiento de red
- `sudo netdiscover -r 192.168.18.0/24`
- `sudo arp-scan <red>` (equivalente a netdiscover)
- `nmap -p- <red>` (más ruidoso que netdiscover)

## Escaneo de puertos y servicios
- `nmap -p- -sC -sV -Pn -T5 --open <ip> -oN salida`
  - `-p-` todos los puertos · `-sC` scripts por defecto · `-sV` versión · `-Pn` sin ping
- `searchsploit proftpd 1.3.5` (buscar exploit por versión)
- Scripts NSE de un servicio: `--script ftp-*`

## SMB (445/139)
- `smbclient -N -L //ip` (sesión nula)
- `netexec smb 192.168.18.113 -u '' -p '' --shares`
- `smbmap -H ip -u <user> -p <passwd>`
- `enum4linux <ip>`

## NFS
- `showmount -e <ip>`
- `mount -t nfs 192.168.15.123:/ /home/kali/Desktop/mnt`
- `rpcinfo <ip>`

## Web
- `feroxbuster -u http://<ip>`
- `mysql -h <ip> -u root --skip-ssl` (credenciales vistas en `config.inc`/`config.php`)

## Metasploit (flujo básico)
```
msfconsole
search <servicio> <versión>
use 0
show options
set RHOSTS <ip>
run
```

## Credenciales (en línea)
- `hydra -L usuarios.txt -P passwords.txt ftp://192.168.18.118`
- `hydra -l <user> -P /usr/share/wordlists/rockyou.txt ssh://<ip>`

## Diccionarios
- `/usr/share/wordlists/` (rockyou, SecLists)
- `wget https://<url>/diccionario`
