---
tags:
  - Walkthroughs
---
# Walkthroughs (apuntes manuscritos)

Resolución paso a paso de las máquinas practicadas, a partir de los apuntes de mano
(con comandos normalizados y algún añadido para que se entiendan).

!!! warning "Fiabilidad"
    Las máquinas **HTB/THM** (Nibbles, Devel, Bounty, Unified, Curling, Magic, GoodGames,
    Oopsie, Mr Robot, Rick) están contrastadas con su resolución conocida y llevan nota cuando
    algo del apunte no cuadra. Las de **TheHackerLabs** se transcriben tal cual: no las he
    verificado de forma independiente, así que trátalas como tus notas y confirma los `[?]`.

| Máquina | Técnicas clave | Página |
|---|---|---|
| Webos | SMB, crack SSH, SUID python | [Web y CMS](web.md) |
| Nibbles | Nibbleblog CVE, upload | [Web y CMS](web.md) |
| Facultad | WordPress, GTFOBins php | [Web y CMS](web.md) |
| Bounty | IIS web.config, JuicyPotato | [Windows](windows.md) |
| Devel | FTP+IIS, meterpreter, Potato | [Windows](windows.md) |
| Unified | Log4Shell, MongoDB | [Windows](windows.md) |
| Curling | Joomla, cron | [Web y CMS](web.md) |
| Magic | upload bypass, chisel, MySQL | [Web y CMS](web.md) |
| GoodGames | SQLi, SSTI | [Web y CMS](web.md) |
| Report | upload, LFI | [Web y CMS](web.md) |
| Torrijas | WordPress CVE, bpftrace | [Web y CMS](web.md) |
| Fruits | LFI, find SUID | [Linux y servicios](linux.md) |
| Nike / Castor / El Banco | XXE, cadenas de escalada | [Linux y servicios](linux.md) |
| Rockstars / Academy | fuzzing, WordPress | [Web y CMS](web.md) |
| Oopsie / Mr Robot / Rick | IDOR, WP, multi-puerto | [Linux y servicios](linux.md) |
| Inject Crew / Pylon | crack, logrotate | [Linux y servicios](linux.md) |

Para la referencia por técnica, mira las [Chuletas](../../chuletas/index.md); para decidir el enfoque,
el [Selector de metodología](../../metodologias/selector.md).
