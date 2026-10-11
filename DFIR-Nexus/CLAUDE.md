# Nexus - Contexto del Proyecto

## Descripción General

Nexus es una plataforma web orientada a la asistencia de peritos informáticos y analistas forenses.

El objetivo es automatizar tareas repetitivas relacionadas con investigaciones de ciberseguridad, análisis forense y generación de informes.

La plataforma se desarrolla como práctica de un Máster de Ciberseguridad e Inteligencia Artificial.

---

## Arquitectura Tecnológica

Frontend:

* React
* TailwindCSS

Backend:

* FastAPI

Base de datos:

* MySQL

ORM:

* SQLAlchemy
* Alembic (migraciones versionadas desde el inicio del proyecto, incluido el Módulo 1)

Validación:

* Pydantic

Control de versiones:

* Git

APIs externas previstas:

* VirusTotal
* AbuseIPDB

Contenedorización:

* Docker (fase final del proyecto)

---

## Módulos del Proyecto

### Módulo 1 - Gestión de Casos

Responsabilidad:

* Crear casos.
* Editar casos.
* Eliminar casos.
* Gestionar evidencias.

Tablas:

* cases
* evidences

---

### Módulo 2 - OSINT y Fraude

Responsabilidad:

* Consultar APIs externas.
* Analizar IPs.
* Analizar dominios.
* Analizar URLs.
* Analizar correos electrónicos.

APIs previstas:

* VirusTotal
* AbuseIPDB

Tabla:

* osint_results

---

### Módulo 3 - Tracking Post-Incidente

Responsabilidad:

* Analizar logs.
* Analizar comandos ejecutados.
* Detectar actividad sospechosa.

Tabla:

* tracking_events

---

### Módulo 4 - Timeline

Responsabilidad:

* Correlacionar eventos.
* Construir una línea temporal de la investigación.
* Generar cronología automática.

Tabla:

* timeline_events

---

### Módulo 5 - Informes

Responsabilidad:

* Generar informes automáticos mediante IA.
* Resumir hallazgos técnicos.
* Generar conclusiones.

Tabla:

* reports

---

## Relación entre módulos

Todos los módulos dependen de un caso.

Flujo:

Caso
→ Evidencias
→ OSINT
→ Tracking
→ Timeline
→ Informe

El identificador principal para relacionar información será:

case_id

---

## Arquitectura Backend

modules/

* cases
* osint
* tracking
* timeline
* reports

Cada módulo debe contener:

* models.py
* schemas.py
* repository.py
* service.py
* routes.py

---

## Objetivos de diseño

* Código modular.
* Escalable.
* Fácil mantenimiento.
* Bajo acoplamiento entre módulos.
* Cada módulo debe poder desarrollarse por una persona distinta.
* Todas las relaciones entre módulos deben realizarse mediante case_id.
* Arquitectura preparada para futuras ampliaciones.

---

## Organización Git

Ramas principales:

* main (en el repositorio real, la rama de producción se llama `main`, no `production`)
* development

Ramas por módulo:

* modulo-casos
* modulo-osint
* modulo-tracking
* modulo-timeline
* modulo-informes

Flujo de trabajo:

1. Desarrollo en la rama del módulo.
2. Merge hacia development.
3. Pruebas de integración.
4. Merge final hacia production.

---

## Modelo de datos oficial

Lee la siguiente especificación de base de datos y utilízala como fuente de verdad para todo el desarrollo del backend.

No modifiques nombres de tablas, nombres de columnas ni relaciones salvo que exista un problema técnico que debas justificar.

## Contexto

Proyecto: Nexus

Nexus es una plataforma modular de asistencia para peritos informáticos.

La aplicación está compuesta por cinco módulos:

1. Gestión de Casos
2. OSINT y Fraude
3. Tracking Post-Incidente
4. Línea Temporal
5. Generador de Informes

Todos los módulos se relacionan mediante la entidad principal:

cases

Cada registro de las demás tablas debe pertenecer a un caso mediante la clave:

case_id

---

# Modelo de Datos

## cases

Entidad principal del sistema.

Campos:

* id (PK)
* nombre VARCHAR(150)
* estado ENUM (abierto, en_progreso, cerrado, archivado)
* fecha_creacion TIMESTAMP
* fecha_actualizacion TIMESTAMP (updated_at administrativo; añadido en el endurecimiento de Cases/Evidence, migración 0002)
* descripcion TEXT
* responsable VARCHAR(100)
* eliminado BOOLEAN, default false (borrado lógico; añadido en 0002)
* fecha_eliminacion TIMESTAMP, nullable (añadido en 0002)

Nota:
`estado` se implementa como Enum (Python Enum + SQLAlchemy Enum), no como VARCHAR libre, para evitar inconsistencias de datos (mayúsculas, sinónimos, typos). Los valores propuestos pueden ajustarse antes de implementar el Módulo 1.

Nota (borrado lógico, justificación técnica): `DELETE /cases/{id}` nunca borra la fila físicamente. Un caso es referenciado por FKs desde `tracking_events` y `reports`, backends independientes sobre la misma base compartida, sin `ondelete=CASCADE`; un DELETE físico con esos dependientes violaba integridad referencial (500 sin controlar). En su lugar, `eliminado`/`fecha_eliminacion` marcan el caso como inactivo — el registro y su historial de auditoría (ver `case_audit_log` más abajo) se conservan siempre. La transición de estados está además validada explícitamente (ver `backend/app/modules/cases/state_machine.py`): `archivado` es terminal e inmutable.

Relaciones:

* 1:N con evidences
* 1:N con osint_results
* 1:N con tracking_events
* 1:N con timeline_events
* 1:N con reports

---

## evidences

Evidencias asociadas a una investigación.

Campos:

* id (PK)
* case_id (FK → cases.id, indexado)
* tipo VARCHAR(50) (inmutable tras crear la evidencia)
* valor TEXT (inmutable tras crear la evidencia: es el contenido probatorio, ver hash_valor)
* fecha_subida TIMESTAMP (alta administrativa del registro)
* fecha_adquisicion TIMESTAMP, nullable (cuándo ocurrió/se adquirió el hecho forense; distinto de fecha_subida — añadido en 0003)
* fecha_actualizacion TIMESTAMP (updated_at administrativo — añadido en 0002)
* hash_valor VARCHAR(64) (SHA-256 de `valor`, calculado una única vez al crear; ver `backend/app/modules/cases/integrity.py` — añadido en 0003)
* observaciones TEXT
* eliminado BOOLEAN, default false (borrado lógico — añadido en 0002)
* fecha_eliminacion TIMESTAMP, nullable (añadido en 0002)

Nota (integridad, justificación técnica): `tipo`/`valor` son el contenido probatorio y pasan a ser inmutables tras la creación — `EvidenceUpdate` solo permite `observaciones`/`fecha_adquisicion`. Si se pudieran editar y `hash_valor` se recalculara en cada cambio, el hash dejaría de servir para detectar una modificación. Para corregir un dato erróneo, el flujo es eliminar (lógicamente) esa evidencia y registrar una nueva — ambas operaciones quedan en `case_audit_log`.

---

## case_audit_log

Rastro de auditoría único para `cases` y `evidences` (no dos tablas paralelas): toda fila referencia siempre un `case_id`, y `evidence_id` solo cuando la operación fue sobre una evidencia concreta de ese caso. Añadida en el endurecimiento de Cases/Evidence (migración 0004), propiedad exclusiva del Módulo 1.

Campos:

* id (PK)
* case_id (FK → cases.id, indexado)
* evidence_id (FK → evidences.id, indexado, nullable)
* accion ENUM (case_creado, case_actualizado, case_estado_cambiado, case_eliminado, evidence_creada, evidence_actualizada, evidence_eliminada)
* actor VARCHAR(100), default "api" (identificador de mejor esfuerzo: sigue sin representar una identidad verificada en las operaciones normales de Cases/Evidence, aunque el proyecto ya tenga autenticación desde la Fase 4 — los eventos de identidad sí identifican a la persona, y viven en `auth_audit_log`)
* detalle JSON, nullable
* creado_en TIMESTAMP

No sustituye ni duplica la cadena de integridad de Tracking (`chain_integrity.py`, hash-chain de eventos de log) ni el `integrity_ledger` de OSINT: son dominios de datos distintos, cada uno auditado donde vive.

---

## osint_results

Resultados de análisis OSINT.

Campos:

* id (PK)
* case_id (FK → cases.id, indexado)
* tipo_indicador VARCHAR(30)
* valor VARCHAR(255)
* reputacion VARCHAR(30)
* pais VARCHAR(80)
* detecciones INTEGER
* fuente VARCHAR(50)
* fecha_consulta TIMESTAMP
* raw_response JSON

Nota:
Si la base de datos utilizada es PostgreSQL usar JSONB.
Si la base de datos utilizada es MySQL usar JSON.

---

## tracking_events

Eventos detectados durante análisis post-incidente.

Campos:

* id (PK)
* case_id (FK → cases.id, indexado)
* hora TIMESTAMP
* evento TEXT
* severidad ENUM (baja, media, alta, critica)
* fuente_log VARCHAR(100)
* usuario_detectado VARCHAR(100)

---

## timeline_events

Cronología consolidada del caso.

Campos:

* id (PK)
* case_id (FK → cases.id, indexado)
* fecha_hora TIMESTAMP
* descripcion TEXT
* origen_modulo VARCHAR(30)
* origen_id INTEGER
* orden INTEGER

Importante:

origen_id NO es una clave foránea física.

Es una referencia lógica que apunta a:

* evidences
* osint_results
* tracking_events

según el valor de origen_modulo.

Implementar esta lógica a nivel de aplicación o mediante relaciones polimórficas.

Índice compuesto recomendado sobre (origen_modulo, origen_id) cuando se implemente este módulo.

---

## reports

Informes generados.

Campos:

* id (PK)
* case_id (FK → cases.id, indexado)
* fecha_generacion TIMESTAMP
* resumen_ia TEXT
* archivo_pdf VARCHAR(255)
* generado_por VARCHAR(100)
* version INTEGER

---

# Relaciones

cases → evidences (1:N)

cases → osint_results (1:N)

cases → tracking_events (1:N)

cases → timeline_events (1:N)

cases → reports (1:N)

---

# Requisitos ORM

Utilizar SQLAlchemy.

Crear:

* models.py
* schemas.py
* repository.py
* service.py
* routes.py

Definir relaciones bidireccionales donde corresponda.

Utilizar tipado completo.

Preparar la arquitectura para FastAPI.

No generar SQL manual salvo que sea estrictamente necesario.

Utilizar Alembic para gestionar cambios de esquema desde el primer commit del Módulo 1. Ninguna modificación al modelo de datos se aplica sin su migración correspondiente.

---

## Índices

Todos los campos `case_id` de las tablas hijas (`evidences`, `osint_results`, `tracking_events`, `timeline_events`, `reports`) deben estar indexados, dado que `case_id` es el eje principal de consulta y relación entre módulos.

`timeline_events` requiere además un índice compuesto sobre `(origen_modulo, origen_id)` cuando se implemente ese módulo.

Estos índices se definen en el modelo aunque el módulo correspondiente todavía no esté implementado, para mantener la arquitectura preparada.

---

## Prioridad Actual

> **Actualización (septiembre de 2026): los cinco módulos están implementados e integrados en
> `development`** (Casos, OSINT, Tracking, Timeline, Informes), más autenticación/identidad
> centralizada en Casos y dos pantallas transversales sin tabla propia (panel de inicio, asistente
> conversacional). Ver el estado real, módulo a módulo, en el README de la raíz. Esta sección se
> conserva porque documenta la prioridad de arranque del proyecto (Módulo 1 primero, arquitectura
> preparada para el resto antes de construirlo), no porque siga siendo la prioridad hoy.

Desarrollar únicamente el Módulo 1 (Gestión de Casos).

No implementar todavía:

* OSINT
* Tracking
* Timeline
* Informes

Pero dejar preparada la arquitectura para futuras integraciones.

Decisiones de arquitectura ya aceptadas para el Módulo 1:

* `estado` de `cases` como Enum controlado.
* Índices en todos los campos `case_id`.
* Alembic desde el inicio para gestionar migraciones.

## Fuera de alcance (por decisión explícita, no por omisión)

> **Actualización (Fase 4, septiembre de 2026): los cuatro puntos de esta lista se implementaron.**
> La lista se conserva porque documenta el orden en que se construyó el proyecto —primero el
> dominio forense, después la identidad y la integridad— y porque explica por qué buena parte del
> código anterior no asume un usuario. Lo que sigue vigente es la regla: **no anticiparse**. Nada
> de lo que quede fuera de alcance hoy debe aparecer en el código antes de decidirse.
>
> | Punto | Dónde está hoy |
> |---|---|
> | Sistema de usuarios y autenticación | JWT HS256 emitido por Casos (`backend/app/modules/auth/`), verificado por los otros cuatro backends con una copia mínima del verificador. Contraseñas con Argon2id. Todos los endpoints lo exigen salvo las excepciones listadas en el README |
> | Gestión de permisos y roles | Roles `analyst` y `admin`; la gestión de usuarios es lo único reservado a `admin` |
> | Cadena de custodia avanzada | Borrado lógico y `case_audit_log` (migraciones 0002 y 0004), más `auth_audit_log` para los eventos de identidad |
> | Hashes de integridad de evidencia | `hash_valor` SHA-256 calculado una sola vez al crear, con `tipo`/`valor` inmutables (migración 0003) |
>
> Lo que **sigue** fuera de alcance, y ahora de forma más precisa: revocación inmediata de JWT,
> refresh tokens, RS256, OAuth/OIDC, MFA, recuperación de contraseña por email, y **autorización
> por caso** (hoy cualquier analista autenticado ve cualquier expediente: haría falta un modelo de
> asignación de casos a usuarios que el proyecto no tiene).

Los siguientes puntos fueron identificados como mejoras deseables pero se descartan deliberadamente por ahora. No implementar salvo instrucción explícita en contrario:

* Sistema de usuarios y autenticación.
* Gestión de permisos y roles.
* Cadena de custodia avanzada (auditoría de borrados, soft-delete, versionado de evidencia).
* Hashes de integridad de evidencia (SHA256/MD5).

Estos puntos quedan documentados para retomarse en una fase posterior del proyecto, pero no deben aparecer en el Módulo 1 ni anticiparse en el código actual.

# REGLAS DEL PROYECTO

Este documento es la especificación oficial del proyecto.

Antes de modificar código:

1. Revisar este documento.
2. Mantener coherencia con la arquitectura definida.
3. No crear nuevos módulos sin aprobación.
4. No modificar el modelo de datos sin justificarlo.
5. Priorizar simplicidad y mantenibilidad.

Sobre el punto 3, por si genera dudas al leer el código: **los módulos siguen siendo cinco**. Ni el
asistente conversacional ni el panel de inicio son un sexto módulo, y la prueba es que ninguno de
los dos posee una tabla: el asistente es una lectura de las seis tablas del contrato servida por el
Módulo 5 (que ya tenía el cliente de IA y esa misma lectura), y el panel solo cuenta lo que los
Módulos 1 y 2 ya publican. La identidad tampoco: es una capa transversal cuya autoridad es el
Módulo 1.

## Frontend Design System

La única fuente de verdad visual del frontend es:

design/Casos/code.html

Todos los componentes globales deben derivarse de sus tokens y patrones visuales.

No se deben utilizar como referencia visual:
- Dashboard
- Tracking
- Informes
- Línea Temporal
- OSINT
- Configuración
- Evidencias

Los diseños de estos módulos únicamente sirven como referencia funcional para futuras implementaciones.

DESIGN.md complementa las reglas del sistema visual, pero en caso de conflicto visual Casos/code.html tiene prioridad.

Los nuevos módulos deben reutilizar shared/ui y shared/layout y no deben crear sistemas visuales independientes.

Los componentes de modules/* pueden importar shared/*.
shared/* nunca puede importar modules/*.
Un módulo nunca debe importar otro módulo.
