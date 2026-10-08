# Post-explotación y escalada

## GTFOBins
[:material-open-in-new: Sitio oficial](https://gtfobins.github.io/)

**Qué hace.** Catálogo de binarios Unix que pueden abusarse (sudo, SUID, capabilities) para escalar o salir de restricciones.

**Cuándo se usa.** Tras obtener acceso, para ver cómo convertir un binario permitido en escalada de privilegios.

**Aparece en.** [Sesión 2026-09-17](../otros/general/apuntes-17-09-2026-carlos-castillo.md), [Glosario Ciberseguridad](../otros/general/glosario-ciberseguridad.md), [Sesion 23 Explotacion Servicios Vulnerables II](../red-team/explotacion/sesion-23-explotacion-servicios-vulnerables-ii.md), [Facultad](../red-team/maquinas/facultad.md), [HTB Tier 1 Responder Three](../red-team/maquinas/htb-tier-1-responder-three.md), [HTB Tier 2](../red-team/maquinas/htb-tier-2.md), [Magic](../red-team/maquinas/magic.md), [Practica 1 Webos Castillo Gomez](../red-team/maquinas/practica-1-webos-castillo-gomez.md), [Repaso Semanal Vaccine Oopsie](../red-team/maquinas/repaso-semanal-vaccine-oopsie.md), [Rockstar Escalada Linux LFI](../red-team/maquinas/rockstar-escalada-linux-lfi.md) (+7)

## linPEAS
[:material-open-in-new: Sitio oficial](https://github.com/peass-ng/PEASS-ng)

**Qué hace.** Script que enumera el sistema Linux buscando vías de escalada de privilegios.

**Cuándo se usa.** Justo después de conseguir shell en Linux, para encontrar configuraciones débiles.

**Aparece en.** [Explotacion Maquinas Locales I](../red-team/explotacion/explotacion-maquinas-locales-i.md), [CMS y Curling](../red-team/maquinas/cms-y-curling.md), [Facultad](../red-team/maquinas/facultad.md), [Practica 1 Webos Castillo Gomez](../red-team/maquinas/practica-1-webos-castillo-gomez.md), [Repaso Semanal Vaccine Oopsie](../red-team/maquinas/repaso-semanal-vaccine-oopsie.md), [Rockstar Escalada Linux LFI](../red-team/maquinas/rockstar-escalada-linux-lfi.md), [Sesion 26 Mr. Robot II Evolve](../red-team/maquinas/sesion-26-mr-robot-ii-evolve.md), [Repaso General II](../red-team/repasos/repaso-general-ii.md), [Auditoria Web Desde 0](../red-team/web/auditoria-web-desde-0.md)

## LOLBAS
[:material-open-in-new: Sitio oficial](https://lolbas-project.github.io/)

**Qué hace.** Equivalente de GTFOBins para binarios y scripts legítimos de Windows.

**Cuándo se usa.** Escalada y living-off-the-land en entornos Windows.

## pspy
[:material-open-in-new: Sitio oficial](https://github.com/DominicBreuker/pspy)

**Qué hace.** Observa procesos y tareas cron en Linux sin privilegios.

**Cuándo se usa.** Detectar procesos o cron ejecutados por root como vía de escalada.

**Aparece en.** [CMS y Curling](../red-team/maquinas/cms-y-curling.md), [Rockstar Escalada Linux LFI](../red-team/maquinas/rockstar-escalada-linux-lfi.md)

## winPEAS
[:material-open-in-new: Sitio oficial](https://github.com/peass-ng/PEASS-ng)

**Qué hace.** Equivalente de linPEAS para enumeración de escalada en Windows.

**Cuándo se usa.** Tras obtener shell en Windows, para localizar vectores de escalada.

**Aparece en.** [Explotacion Maquinas Locales I](../red-team/explotacion/explotacion-maquinas-locales-i.md), [Repaso Semanal Vaccine Oopsie](../red-team/maquinas/repaso-semanal-vaccine-oopsie.md), [Repaso semanal VII - Devel](../red-team/maquinas/repaso-semanal-vii-devel.md), [Repaso General II](../red-team/repasos/repaso-general-ii.md)
