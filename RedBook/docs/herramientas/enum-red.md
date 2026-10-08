# Enumeración de red y servicios

## enum4linux
[:material-open-in-new: Sitio oficial](https://github.com/CiscoCXSecurity/enum4linux)

**Qué hace.** Enumera información de SMB/Windows: usuarios, grupos, shares, políticas.

**Cuándo se usa.** Tras detectar SMB (445/139) para listar recursos y cuentas.

**Aparece en.** [Sesion 25 Evolve](../otros/general/sesion-25-evolve.md)

## nmap
[:material-open-in-new: Sitio oficial](https://nmap.org/)

**Qué hace.** Escáner de red: descubre hosts, puertos abiertos, servicios y versiones.

**Cuándo se usa.** Al principio de casi toda auditoría, para saber qué hay expuesto antes de atacar.

**Aparece en.** [Wireshark](../blue-team/analisis-trafico/wireshark.md), [OWASP CVSS CWE CVE](../metodologias/estandares/owasp-cvss-cwe-cve.md), [Bash Comandos Avanzados](../otros/fundamentos/bash-comandos-avanzados.md), [Bash Scripting](../otros/fundamentos/bash-scripting.md), [Fundamentos Linux](../otros/fundamentos/fundamentos-linux.md), [Intro Redes](../otros/fundamentos/intro-redes.md), [Manual VBox a VMware](../otros/fundamentos/manual-vbox-a-vmware.md), [Redes Typos Datagramas](../otros/fundamentos/redes-typos-datagramas.md), [Sesión 2026-09-17](../otros/general/apuntes-17-09-2026-carlos-castillo.md), [Glosario Ciberseguridad](../otros/general/glosario-ciberseguridad.md) (+43)

## smbclient
[:material-open-in-new: Sitio oficial](https://www.samba.org/)

**Qué hace.** Cliente SMB para listar y acceder a recursos compartidos de red.

**Cuándo se usa.** Conectarte a shares SMB encontrados y revisar/descargar ficheros.

**Aparece en.** [Sesion 25 Evolve](../otros/general/sesion-25-evolve.md), [Explotacion Maquinas Locales I](../red-team/explotacion/explotacion-maquinas-locales-i.md), [HTB Starting Point Tier 0](../red-team/maquinas/htb-starting-point-tier-0.md), [Practica 1 Webos Castillo Gomez](../red-team/maquinas/practica-1-webos-castillo-gomez.md)
