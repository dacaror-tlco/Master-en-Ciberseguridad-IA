# Contrato de datos — scam-shield → resto de módulos de Nexus

Cómo consumen **tracking**, **informes**, **timeline** y cualquier otro
módulo de DFIR-Nexus lo que genera scam-shield (Módulo 2 — OSINT y Fraude).

La base de datos de Nexus es **compartida** (un solo esquema MySQL). Este
documento define qué parte de ese esquema es "pública" para otros módulos
y qué garantías tiene.

---

## 1. La regla

> Los demás módulos leen **solo** de `osint_findings` (+ `cases` de Nexus).
> **Nunca** de las tablas internas de scam-shield (`osint_domain_cases`,
> `email_cases`, `wallet_cases`, `ip_cases`, …).

Motivo: las tablas internas cambian de forma cuando evoluciona un módulo
de análisis (columnas nuevas, scoring distinto). `osint_findings` es una
capa estable y desnormalizada pensada para consumo externo. Si lees las
tablas internas, cada cambio interno te rompe.

---

## 2. `osint_findings`

Una fila por **análisis terminado** de cualquier submódulo OSINT. Append-only:
un re-análisis del mismo sujeto crea una fila nueva (no actualiza la vieja),
igual que las tablas de casos internas.

| Columna | Tipo | Significado |
|---|---|---|
| `id` | int PK | — |
| `case_type` | varchar(32) | Tipo de análisis. Vocabulario cerrado (ver §3). |
| `source_table` | varchar(64) | Tabla interna real de la que sale (`ip_cases`, `osint_domain_cases`…). Informativo; no la consultes. |
| `source_id` | int | PK de la fila en esa tabla interna. |
| `case_id` | int, **nullable** | Expediente de Nexus (`cases.id`) al que está atado el análisis. `NULL` mientras no se haya atado (ver §5). |
| `subject_type` | varchar(32) | Qué clase de cosa se analizó, normalizado (ver §3). |
| `subject_value` | varchar(255) | El identificador: dominio, dirección de email, wallet, IP, teléfono E.164, nombre de entidad, nombre de fichero de imagen. |
| `risk_score` | int (0–100) | Puntuación de riesgo del análisis. |
| `risk_level` | varchar(16) | `low` (<30) · `medium` (30–59) · `high` (≥60). Mismos cortes que el frontend y la monitorización (`app/modules/osint/shared/risk_levels.py`). |
| `headline` | varchar(255) | Resumen de una línea listo para pintar. Ej: `IP 45.83.122.14 — RIESGO BAJO (0)`. |
| `flag_count` | int | Nº total de señales de riesgo detectadas. |
| `top_flags` | JSON | Hasta 5 señales, las más graves primero: `[{code, severity, description}]`. |
| `details` | JSON | Payload completo del caso (el mismo que sella la cadena de integridad). Para consumidores que quieren todo sin tocar la tabla interna. Su forma depende del `case_type` y **no** forma parte del contrato estable — trátalo como opaco / "best effort". |
| `analyzed_at` | datetime(tz) | Cuándo se ejecutó el análisis. Úsalo para "desde X". |
| `created_at` | datetime(tz) | Cuándo se escribió esta fila de proyección. |

Restricción única: `(case_type, source_id)` → `uq_osint_finding_source`.

Índices pensados para consumo: `case_type`, `case_id`, `subject_type`,
`subject_value`, `risk_score`, `risk_level`, `analyzed_at`.

### Consultas típicas

```sql
-- Todo lo de riesgo alto de un expediente
SELECT * FROM osint_findings WHERE case_id = :case_id AND risk_level = 'high'
ORDER BY analyzed_at DESC;

-- Última foto de cada sujeto analizado esta semana
SELECT f.* FROM osint_findings f
JOIN (SELECT case_type, subject_value, MAX(analyzed_at) mx
      FROM osint_findings GROUP BY case_type, subject_value) last
  ON f.case_type = last.case_type AND f.subject_value = last.subject_value
 AND f.analyzed_at = last.mx
WHERE f.analyzed_at >= :inicio_semana;

-- ¿Aparece esta IP en algún análisis?
SELECT * FROM osint_findings WHERE subject_type = 'ip_address' AND subject_value = :ip;
```

---

## 3. Vocabularios

**`case_type`** (mismo que `integrity_ledger` y `monitored_subjects`):

`domain` · `email` · `wallet` · `typosquatting` · `phone` · `cnmv` ·
`ip` · `image` · `image_reverse_search` · `image_facial_search`

**`subject_type`**:

| valor | de qué `case_type` viene | `subject_value` es |
|---|---|---|
| `domain` | `domain`, `typosquatting` | el dominio |
| `email_address` | `email` | dirección `From:` |
| `crypto_wallet` | `wallet` | dirección de la wallet |
| `ip_address` | `ip` | IPv4/IPv6 |
| `phone_number` | `phone` | teléfono normalizado (E.164) |
| `entity_name` | `cnmv` | texto consultado (nombre de entidad/empresa) |
| `image_file` | `image`, `image_reverse_search`, `image_facial_search` | nombre de fichero o SHA-256 de la imagen |

**`risk_level`**: `low` · `medium` · `high` (rangos en la tabla de §2).

---

## 4. Garantías de estabilidad

- **Solo se añaden columnas** a `osint_findings`, nunca se quitan ni se
  renombran. Escribe tus `SELECT` con columnas explícitas, no `SELECT *`
  si te molesta que aparezcan columnas nuevas.
- **`case_type` y `subject_type` solo crecen**: pueden aparecer valores
  nuevos (submódulos nuevos). No asumas una lista fija; ignora los que no
  conozcas.
- `details` (JSON) **no** es estable — su forma sigue a la tabla interna.
- Si algún día hay que romper el contrato de verdad, se crea
  `osint_findings_v2` y se mantienen los dos un tiempo.

---

## 5. Cómo se rellena `case_id`

Hoy scam-shield analiza sujetos de forma suelta (no crea expedientes), así
que `case_id` nace `NULL`. El flujo "atar un análisis a un expediente de
Nexus" es trabajo del Módulo 1 (casos) + una acción futura en scam-shield;
cuando exista, escribirá `case_id` en la fila de `osint_findings` (y,
llegado el momento, un evento en `timeline_events` con
`origen_modulo='osint'` y `origen_id = osint_findings.id`).

Mientras tanto, para correlacionar sin `case_id`: usa
`(subject_type, subject_value)`.

---

## 6. Acceso: usuario de solo lectura

Los módulos consumidores deben conectarse con un usuario **read-only** —
no deben poder escribir en el esquema de scam-shield. `osint_findings` lo
escribe únicamente scam-shield, al terminar cada análisis.

SQL para crear ese usuario (ejecutar con `avnadmin`; ajusta host/nombre):

```sql
CREATE USER 'nexus_reader'@'%' IDENTIFIED BY '<pon-una-password>';
GRANT SELECT ON defaultdb.osint_findings TO 'nexus_reader'@'%';
GRANT SELECT ON defaultdb.cases          TO 'nexus_reader'@'%';
-- opcional, si un consumidor necesita el detalle bruto de un submódulo
-- concreto (desaconsejado, rompe el punto 1):
-- GRANT SELECT ON defaultdb.integrity_ledger TO 'nexus_reader'@'%';
FLUSH PRIVILEGES;
```

> Aiven permite gestionar usuarios/roles también desde su consola; si se
> crea ahí, aplícale el mismo `GRANT SELECT` acotado a estas tablas.

---

## 7. API HTTP (alternativa a leer la tabla)

Para consumidores que prefieran no tocar la BD directamente, scam-shield
expone lo mismo en solo lectura:

- `GET /osint-findings` — filtros: `case_type`, `subject_type`,
  `subject_value`, `case_id`, `risk_level`, `min_risk_score`, `since`
  (ISO 8601), `skip`, `limit` (máx. 200). Orden: `analyzed_at` desc.
- `GET /osint-findings/{id}` — incluye `top_flags` y `details`.

Para agregaciones grandes (informes que cruzan muchos análisis) es mejor
el `SELECT` directo; la API es para lecturas puntuales.
