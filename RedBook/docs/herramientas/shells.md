# Shells, acceso y transferencia

## curl
[:material-open-in-new: Sitio oficial](https://curl.se/)

**Qué hace.** Cliente HTTP de línea de comandos.

**Cuándo se usa.** Lanzar y afinar peticiones web manualmente, probar endpoints y payloads.

**Aparece en.** [Bash Comandos Avanzados](../otros/fundamentos/bash-comandos-avanzados.md), [Sesión 2026-09-17](../otros/general/apuntes-17-09-2026-carlos-castillo.md), [CMS y Curling](../red-team/maquinas/cms-y-curling.md), [HTB Tier 1 Responder Three](../red-team/maquinas/htb-tier-1-responder-three.md), [HTB Tier 2](../red-team/maquinas/htb-tier-2.md), [Nibbles - Apuntes](../red-team/maquinas/nibbles-apuntes.md), [Nibbles HTB](../red-team/maquinas/nibbles-htb.md), [Practica 1 Webos Castillo Gomez](../red-team/maquinas/practica-1-webos-castillo-gomez.md), [Repaso Semanal Vaccine Oopsie](../red-team/maquinas/repaso-semanal-vaccine-oopsie.md), [Rockstar Escalada Linux LFI](../red-team/maquinas/rockstar-escalada-linux-lfi.md) (+13)

## evil-winrm
[:material-open-in-new: Sitio oficial](https://github.com/Hackplayers/evil-winrm)

**Qué hace.** Cliente WinRM pensado para pentesting en Windows.

**Cuándo se usa.** Obtener shell remota en Windows cuando tienes credenciales y WinRM (5985).

**Aparece en.** [Glosario Ciberseguridad](../otros/general/glosario-ciberseguridad.md), [Explotacion Maquinas Locales I](../red-team/explotacion/explotacion-maquinas-locales-i.md), [HTB Starting Point Tier 1](../red-team/maquinas/htb-starting-point-tier-1.md), [HTB Tier 1 Responder Three](../red-team/maquinas/htb-tier-1-responder-three.md), [HTB Tier 2](../red-team/maquinas/htb-tier-2.md)

## git-dumper
[:material-open-in-new: Sitio oficial](https://github.com/arthaud/git-dumper)

**Qué hace.** Descarga un repositorio Git expuesto en un sitio web.

**Cuándo se usa.** Cuando encuentras /.git accesible, para recuperar código y secretos.

**Aparece en.** [Report (2026-09-21)](../otros/informes/report-2026-09-21.md), [Report](../otros/informes/report.md)

## Netcat
[:material-open-in-new: Sitio oficial](https://linux.die.net/man/1/nc)

**Qué hace.** Utilidad de red para leer/escribir por TCP/UDP; sirve de listener de shells.

**Cuándo se usa.** Recibir reverse shells y transferencias puntuales.

**Aparece en.** [Bash Comandos Avanzados](../otros/fundamentos/bash-comandos-avanzados.md), [Report](../otros/informes/report.md), [Explotacion Maquinas Locales I](../red-team/explotacion/explotacion-maquinas-locales-i.md), [Auditoria WordPress Academy](../red-team/maquinas/auditoria-wordpress-academy.md), [Facultad](../red-team/maquinas/facultad.md), [HTB Tier 2](../red-team/maquinas/htb-tier-2.md), [Magic](../red-team/maquinas/magic.md), [Nibbles - Apuntes](../red-team/maquinas/nibbles-apuntes.md), [Nibbles HTB](../red-team/maquinas/nibbles-htb.md), [Practica 1 Webos Castillo Gomez](../red-team/maquinas/practica-1-webos-castillo-gomez.md) (+15)

## python http.server
[:material-open-in-new: Sitio oficial](https://docs.python.org/3/library/http.server.html)

**Qué hace.** Servidor HTTP improvisado de una línea.

**Cuándo se usa.** Servir archivos para transferirlos a la máquina víctima.

**Aparece en.** [Explotacion Maquinas Locales I](../red-team/explotacion/explotacion-maquinas-locales-i.md), [Nibbles - Apuntes](../red-team/maquinas/nibbles-apuntes.md), [Repaso Semanal Vaccine Oopsie](../red-team/maquinas/repaso-semanal-vaccine-oopsie.md), [Rockstar Escalada Linux LFI](../red-team/maquinas/rockstar-escalada-linux-lfi.md), [Sesion 27 XXE LFI Nike](../red-team/maquinas/sesion-27-xxe-lfi-nike.md), [Repaso General II](../red-team/repasos/repaso-general-ii.md), [Auditoria Web LFI Escalada Linux](../red-team/web/auditoria-web-lfi-escalada-linux.md), [Repaso Enumeracion Web](../red-team/web/repaso-enumeracion-web.md), [SQLi y fundamentos de SQL](../red-team/web/sqli-y-fundamentos-de-sql.md)

## revshells.com
[:material-open-in-new: Sitio oficial](https://www.revshells.com/)

**Qué hace.** Generador web de comandos de reverse shell en muchos lenguajes.

**Cuándo se usa.** Para obtener rápido el comando de shell inversa adaptado al entorno destino.

**Aparece en.** [HTB Tier 2](../red-team/maquinas/htb-tier-2.md), [Nibbles - Apuntes](../red-team/maquinas/nibbles-apuntes.md), [Practica 1 Webos Castillo Gomez](../red-team/maquinas/practica-1-webos-castillo-gomez.md), [Repaso Semanal Vaccine Oopsie](../red-team/maquinas/repaso-semanal-vaccine-oopsie.md), [Sesion 27 XXE LFI Nike](../red-team/maquinas/sesion-27-xxe-lfi-nike.md), [Vaccine Repaso](../red-team/maquinas/vaccine-repaso.md), [Repaso Enumeracion Web](../red-team/web/repaso-enumeracion-web.md)

## socat
[:material-open-in-new: Sitio oficial](http://www.dest-unreach.org/socat/)

**Qué hace.** Relé de datos entre puntos; crea shells más estables que netcat.

**Cuándo se usa.** Shells totalmente interactivas (TTY) y túneles.

**Aparece en.** [Magic](../red-team/maquinas/magic.md), [Repaso Semanal Vaccine Oopsie](../red-team/maquinas/repaso-semanal-vaccine-oopsie.md), [Vaccine Repaso](../red-team/maquinas/vaccine-repaso.md)

## ssh
[:material-open-in-new: Sitio oficial](https://www.openssh.com/)

**Qué hace.** Cliente de acceso remoto seguro; también hace túneles y port-forwarding.

**Cuándo se usa.** Acceso con credenciales/clave y pivoting entre redes.

**Aparece en.** [Wireshark](../blue-team/analisis-trafico/wireshark.md), [Intro Redes](../otros/fundamentos/intro-redes.md), [Sesión 2026-09-17](../otros/general/apuntes-17-09-2026-carlos-castillo.md), [Glosario Ciberseguridad](../otros/general/glosario-ciberseguridad.md), [Sesion 25 Evolve](../otros/general/sesion-25-evolve.md), [IA De los cimientos a la cima](../otros/ia/ia-de-los-cimientos-a-la-cima.md), [IA hibrida, agentes y SQL Injection](../otros/ia/ia-hibrida-agentes-y-sql-injection.md), [IA Practica 1 Grafos Subagentes Infraestructura](../otros/ia/ia-practica-1-grafos-subagentes-infraestructura.md), [Report (2026-09-21)](../otros/informes/report-2026-09-21.md), [Report](../otros/informes/report.md) (+37)

## wget
[:material-open-in-new: Sitio oficial](https://www.gnu.org/software/wget/)

**Qué hace.** Descargador de archivos por HTTP/FTP.

**Cuándo se usa.** Traer herramientas o ficheros al objetivo desde la terminal.

**Aparece en.** [Bash Comandos Avanzados](../otros/fundamentos/bash-comandos-avanzados.md), [Explotacion Maquinas Locales I](../red-team/explotacion/explotacion-maquinas-locales-i.md), [Explotacion Servicios III](../red-team/explotacion/explotacion-servicios-iii.md), [Facultad](../red-team/maquinas/facultad.md), [HTB Tier 2](../red-team/maquinas/htb-tier-2.md), [Nibbles - Apuntes](../red-team/maquinas/nibbles-apuntes.md), [Practica 1 Webos Castillo Gomez](../red-team/maquinas/practica-1-webos-castillo-gomez.md), [Repaso Semanal Vaccine Oopsie](../red-team/maquinas/repaso-semanal-vaccine-oopsie.md), [Repaso semanal VII - Devel](../red-team/maquinas/repaso-semanal-vii-devel.md), [Rockstar Escalada Linux LFI](../red-team/maquinas/rockstar-escalada-linux-lfi.md) (+4)
