# Credenciales y hashes

## CrackMapExec / NetExec
[:material-open-in-new: Sitio oficial](https://github.com/Pennyw0rth/NetExec)

**Qué hace.** Navaja suiza para redes Windows/AD: valida credenciales, enumera y ejecuta sobre SMB/WinRM.

**Cuándo se usa.** Movimiento y validación de credenciales en entornos Windows.

**Aparece en.** [Sesion 25 Evolve](../otros/general/sesion-25-evolve.md), [HTB Starting Point Tier 0](../red-team/maquinas/htb-starting-point-tier-0.md), [Practica 1 Webos Castillo Gomez](../red-team/maquinas/practica-1-webos-castillo-gomez.md), [Rockstar Escalada Linux LFI](../red-team/maquinas/rockstar-escalada-linux-lfi.md), [Repaso Enumeracion Web](../red-team/web/repaso-enumeracion-web.md)

## hashcat
[:material-open-in-new: Sitio oficial](https://hashcat.net/hashcat/)

**Qué hace.** Crackeador de hashes acelerado por GPU.

**Cuándo se usa.** Romper hashes offline a gran velocidad con grandes diccionarios o fuerza bruta.

**Aparece en.** [Explotacion Servicios III](../red-team/explotacion/explotacion-servicios-iii.md), [Sesion 23 Explotacion Servicios Vulnerables II](../red-team/explotacion/sesion-23-explotacion-servicios-vulnerables-ii.md), [HTB Tier 1 Responder Three](../red-team/maquinas/htb-tier-1-responder-three.md), [HTB Tier 2](../red-team/maquinas/htb-tier-2.md), [Rockstar Escalada Linux LFI](../red-team/maquinas/rockstar-escalada-linux-lfi.md), [Sesion 26 Mr. Robot II Evolve](../red-team/maquinas/sesion-26-mr-robot-ii-evolve.md), [Sesion Reactor HTB](../red-team/maquinas/sesion-reactor-htb.md), [Vaccine Repaso](../red-team/maquinas/vaccine-repaso.md), [Vaccine](../red-team/maquinas/vaccine.md)

## hashid
[:material-open-in-new: Sitio oficial](https://github.com/psypanda/hashID)

**Qué hace.** Identifica el tipo de un hash.

**Cuándo se usa.** Antes de crackear, para saber qué algoritmo y modo usar en john/hashcat.

**Aparece en.** [Explotacion Servicios III](../red-team/explotacion/explotacion-servicios-iii.md), [Sesion 23 Explotacion Servicios Vulnerables II](../red-team/explotacion/sesion-23-explotacion-servicios-vulnerables-ii.md), [Vaccine Repaso](../red-team/maquinas/vaccine-repaso.md)

## Hydra
[:material-open-in-new: Sitio oficial](https://github.com/vanhauser-thc/thc-hydra)

**Qué hace.** Fuerza bruta de credenciales contra muchos protocolos (SSH, FTP, HTTP, etc.).

**Cuándo se usa.** Ataque de credenciales en línea cuando hay un servicio de login expuesto.

**Aparece en.** [Sesión 2026-09-17](../otros/general/apuntes-17-09-2026-carlos-castillo.md), [Sesion 25 Evolve](../otros/general/sesion-25-evolve.md), [Report (2026-09-21)](../otros/informes/report-2026-09-21.md), [Sesion 23 Explotacion Servicios Vulnerables II](../red-team/explotacion/sesion-23-explotacion-servicios-vulnerables-ii.md), [Auditoria WordPress Academy](../red-team/maquinas/auditoria-wordpress-academy.md), [Facultad](../red-team/maquinas/facultad.md), [HTB Starting Point Tier 1](../red-team/maquinas/htb-starting-point-tier-1.md), [Repaso Metodologia Web SSTI CasaPaco](../red-team/maquinas/repaso-metodologia-web-ssti-casapaco.md), [Rockstar Escalada Linux LFI](../red-team/maquinas/rockstar-escalada-linux-lfi.md), [Sesion 26 Mr. Robot II Evolve](../red-team/maquinas/sesion-26-mr-robot-ii-evolve.md) (+7)

## Impacket
[:material-open-in-new: Sitio oficial](https://github.com/fortra/impacket)

**Qué hace.** Colección de scripts Python para protocolos de red (SMB, Kerberos, etc.).

**Cuándo se usa.** Operaciones sobre servicios Windows: psexec, secretsdump, relays, tickets.

**Aparece en.** [Explotacion Maquinas Locales I](../red-team/explotacion/explotacion-maquinas-locales-i.md)

## John the Ripper
[:material-open-in-new: Sitio oficial](https://www.openwall.com/john/)

**Qué hace.** Crackeador de contraseñas y hashes offline.

**Cuándo se usa.** Romper hashes obtenidos (shadow, zip, etc.) usando diccionario o reglas.

**Aparece en.** [IA Introduccion y Vibe Coding](../otros/ia/ia-introduccion-y-vibe-coding.md), [Explotacion Servicios III](../red-team/explotacion/explotacion-servicios-iii.md), [Sesion 23 Explotacion Servicios Vulnerables II](../red-team/explotacion/sesion-23-explotacion-servicios-vulnerables-ii.md), [HTB Starting Point Tier 1](../red-team/maquinas/htb-starting-point-tier-1.md), [HTB Tier 1 Responder Three](../red-team/maquinas/htb-tier-1-responder-three.md), [HTB Tier 2](../red-team/maquinas/htb-tier-2.md), [Practica 1 Webos Castillo Gomez](../red-team/maquinas/practica-1-webos-castillo-gomez.md), [Repaso Semanal Vaccine Oopsie](../red-team/maquinas/repaso-semanal-vaccine-oopsie.md), [Rockstar Escalada Linux LFI](../red-team/maquinas/rockstar-escalada-linux-lfi.md), [Sesion 26 Mr. Robot II Evolve](../red-team/maquinas/sesion-26-mr-robot-ii-evolve.md) (+8)

## Responder
[:material-open-in-new: Sitio oficial](https://github.com/lgandx/Responder)

**Qué hace.** Envenena LLMNR/NBT-NS/mDNS para capturar hashes de autenticación en red local.

**Cuándo se usa.** Dentro de una red Windows, para capturar credenciales NTLM.

**Aparece en.** [Glosario Ciberseguridad](../otros/general/glosario-ciberseguridad.md), [IA De los cimientos a la cima](../otros/ia/ia-de-los-cimientos-a-la-cima.md), [IA Practica 1 Grafos Subagentes Infraestructura](../otros/ia/ia-practica-1-grafos-subagentes-infraestructura.md), [IA Redes Neuronales](../otros/ia/ia-redes-neuronales.md), [Report](../otros/informes/report.md), [Auditoria WordPress Academy](../red-team/maquinas/auditoria-wordpress-academy.md), [Facultad](../red-team/maquinas/facultad.md), [HTB Starting Point Tier 0](../red-team/maquinas/htb-starting-point-tier-0.md), [HTB Starting Point Tier 1](../red-team/maquinas/htb-starting-point-tier-1.md), [HTB Tier 1 Responder Three](../red-team/maquinas/htb-tier-1-responder-three.md) (+14)
