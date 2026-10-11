# E2E Ejecutada — Módulo 4 (Línea Temporal)

**Fecha:** 2026-09-27
**Ejecutor:** JDaveGRamirez
**Caso usado:** case_id = 8
**Estado:** ✅ Hito conseguido

## 1. Objetivo
Verificar el flujo completo: Caso → Evidencias → OSINT → Tracking → Timeline → Informe PDF.

## 2. Preparación
- Stack: 5 backends (8000, 8001, 8002, 8003, 8124) + frontend (5173).
- Healthcheck: 200 en todos.
- Migración Timeline: 0003 (head).

## 3. Pasos ejecutados

### 3.1 Login
curl POST /auth/login → JWT con JWT_SECRET compartido.

### 3.2 GET /timeline/cases/8
Devuelve 9 eventos ordenados (3 evidence + 3 tracking + 3 osint).
IDs persistidos: 412-420 (≠ origen_id 4-69).

### 3.3 POST /timeline/cases/8/refresh
Recalcula. En rama pre-PR#3 devuelve id==origen_id (esperado, H-02).
Tras merge de PR #3 devolverá IDs persistidos 421-429.

### 3.4 Frontend /timeline con caso 8
- Tabla: 9 filas ordenadas.
- Gráfico: 3 carriles (evidence/tracking/osint).
- Compresión de hueco 18 días visible.
- Toggle Tabla/Gráfico OK.

### 3.5 Informe PDF (M5)
2 informes con hash SHA-256 y firma en reports.huellas.

## 4. Resultados
- 9 eventos correctos, orden 1..9.
- Refresh idempotente.
- Sin duplicados.
- Frontend OK.
- Tests timeline: 15/15.

## 5. Tests cruzados
timeline 16/16 · track-inc 304/304 · backend 127/127 · scam-shield 419/419 · sharingan 219/219 → TOTAL 1085/1085.

## 6. Correcciones verificadas (PR #3)
H-01, H-02, H-03, H-04, H-05, H-07, H-13, H-14, H-21.

## 7. Conclusión
Módulo 4 integrado, verificado y listo para producción en su scope actual.

## Anexo — Comandos reproducibles
Ver docs/AUDITORIA_TIMELINE.md § Anexo A.
