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

* production
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
* descripcion TEXT
* responsable VARCHAR(100)

Nota:
`estado` se implementa como Enum (Python Enum + SQLAlchemy Enum), no como VARCHAR libre, para evitar inconsistencias de datos (mayúsculas, sinónimos, typos). Los valores propuestos pueden ajustarse antes de implementar el Módulo 1.

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
* tipo VARCHAR(50)
* valor TEXT
* fecha_subida TIMESTAMP
* observaciones TEXT

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
