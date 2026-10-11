# Frontend — Módulo 3 (Tracking Post-Incidente)

## Contexto importante

Este frontend es una **reconstrucción aproximada**, no una extensión de
código real. No se disponía del repositorio `frontend/` real del equipo
(`tokens.css`, `shared/ui`, `shared/layout`, `modules/cases` reales) —
solo de su documentación exhaustiva (`DESIGN_SYSTEM.md`,
`FRONTEND_MODULE_GUIDE.md`). Se reconstruyó con la máxima fidelidad
posible a esa documentación: mismos tokens (hex exactos), mismas props
de componentes, mismo patrón de módulos, mismas reglas de dependencia.

**Antes de fusionar esto con el repositorio real**, alguien con acceso a
`frontend/src/` debería:
1. Sustituir `styles/`, `shared/ui/`, `shared/layout/` por los ficheros
   reales (deberían ser casi idénticos si la documentación estaba al
   día — si difieren, el código real gana siempre).
2. Revisar `modules/cases/` de este proyecto frente al real: aquí es una
   reconstrucción mínima de referencia, no la implementación completa
   del equipo.
3. Mover `modules/tracking/` (la pieza que sí es 100% la entrega real de
   este módulo) al repositorio real tal cual — no depende de nada
   reconstruido de forma incierta, solo de los contratos documentados
   (`shared/ui`, `shared/layout`) que cualquier implementación real
   debería cumplir igual.

## Decisiones de diseño específicas de Tracking

- **`SeverityBadge`** (`modules/tracking/components/`) es un componente
  propio del módulo, no `StatusBadge` de `shared/ui`. Motivo: `StatusBadge`
  solo expone 4 tonos (`primary/tertiary/neutral/muted`), ninguno con
  semántica de "alarma" — necesario para una escala de 4 niveles de
  severidad donde el nivel crítico debe distinguirse claramente. Se
  construyó usando únicamente tokens ya existentes (`error`,
  `error-container`, `tertiary`, `hairline`), sin ningún hex nuevo.
- **`CaseSelector`** llama directamente a `GET /cases/` desde el propio
  cliente HTTP de `modules/tracking/api/`, sin importar nada de
  `modules/cases/` — respeta la regla de no-dependencia entre módulos
  (una llamada HTTP a un endpoint compartido no es lo mismo que importar
  código de otro módulo frontend).
- No se usó `TableWithDrawerLayout`: el dominio de Tracking (subir log →
  revisar preview → confirmar guardado, y por separado listar eventos
  guardados) no encaja en el patrón lista+detalle. Se optó por
  composición directa de `Card` + un selector de pestañas local (estado
  de React, no un componente `Tabs` nuevo en `shared/`).

## Arrancar en local

```bash
npm install
cp .env.example .env   # ajustar VITE_API_BASE_URL si el backend no está en :8000
npm run dev
```

Requiere el backend corriendo (ver `../backend/README.md`).

## Comprobaciones

```bash
npm run typecheck   # tsc -b
npm run build        # vite build
```

Ambas verificadas sin errores.
