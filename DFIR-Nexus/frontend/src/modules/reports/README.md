# Módulo 5 — Informes (frontend)

Pantalla del Generador de Informes, construida sobre el frontend común de
NEXUS siguiendo `frontend/DESIGN_SYSTEM.md` y `frontend/FRONTEND_MODULE_GUIDE.md`.

Esta carpeta es **lo único que aporta el Módulo 5 al frontend**: el resto del
frontend (`styles/`, `shared/`, `app/`, los demás módulos) es trabajo de la
rama `modulo-casos` y no se toca ni se duplica aquí.

## Qué hace

Un informe pertenece siempre a un caso, así que la pantalla se organiza
alrededor de un caso: se elige uno, se ven todas las versiones emitidas para él
y se puede emitir una nueva.

No hay editar ni borrar, y no es un olvido: el backend no expone esas
operaciones porque un informe pericial emitido es inmutable. Corregirlo
significa emitir una versión nueva, y por eso la tabla marca cuál está
`VIGENTE` y cuáles quedan como `HISTÓRICO`.

## Estructura

```
modules/reports/
├── api/         httpClient propio + reportsApi (1:1 con routes.py) + casesLookupApi
├── types/       Report y ReportGenerateInput, calcados de schemas.py
├── components/  ReportTable · ReportDetailDrawer · ReportGenerateForm · reportFormat
└── pages/       ReportsPage
```

Endpoints reales consumidos (ninguno inventado):

| Método | Ruta | Uso |
|---|---|---|
| `POST` | `/reports/generate` | Emitir una versión nueva |
| `GET` | `/cases/{case_id}/reports` | Listar las versiones del caso |
| `GET` | `/reports/{id}/download` | Descargar el informe (`?formato=pdf\|docx\|html\|json`) |
| `GET` | `/cases` | Poblar el selector de casos (Módulo 1, solo lectura) |

## Integración en el frontend común

**El `router.tsx` no hay que tocarlo.** El Módulo 1 ya enruta `/reports` con

```ts
import { ReportsPage } from '@/modules/reports/pages/ReportsPage'
```

y este módulo exporta `ReportsPage` con ese mismo nombre desde ese mismo
fichero, así que al copiar esta carpeta sustituye al placeholder sin que nadie
edite nada. Verificado el 2026-08-29 con `tsc --noEmit` sobre el `router.tsx`
de la rama `modulo-casos` sin modificar.

> Por eso **no se renombra `pages/ReportsPage.tsx` ni su export**: son el punto
> de enganche con una rama ajena. El barril `pages/index.ts` se mantiene para
> uso interno, pero no es lo que importa el router.

Queda **un solo cambio** en ficheros compartidos, que no se incluye aquí para
no pisar la rama que los posee:

**`frontend/.env.example` y tu `.env`** — añadir la URL del backend de
informes:

```env
VITE_REPORTS_API_BASE_URL=http://127.0.0.1:8001
```

Hoy el Módulo 1 (`/cases`) y el Módulo 5 (`/reports`) son dos aplicaciones
FastAPI distintas y no pueden escuchar en el mismo puerto. **Cuando ambos
backends se fusionen, basta con borrar esa variable**: por defecto se usa
`VITE_API_BASE_URL` y todo apunta al mismo origen.

Si el backend del Módulo 1 no responde, la pantalla no se queda muerta: pide el
`case_id` a mano y el módulo sigue siendo usable por sí solo.

## Decisiones

* **Las fechas se muestran en UTC con el formato del PDF** (`2026-08-15 20:59
  UTC`). MySQL devuelve `DATETIME` sin offset, así que el navegador lo leería
  como hora local y la pantalla contradiría al informe firmado. `formatUtc()`
  interpreta explícitamente como UTC lo que llega sin zona.
* **No se importa nada de `modules/cases/`**, ni siquiera su `httpClient`
  (regla §13 del Design System). El módulo tiene el suyo, como propone §17, y
  la relación con Casos pasa por `case_id`, igual que en el backend.
* **`VIGENTE`/`HISTÓRICO` se deducen** comparando `version` con la última
  emitida; no es un estado que devuelva el backend. Usa los tonos ya existentes
  de `StatusBadge`, sin introducir ningún color nuevo.
* **La descarga navega a la URL** en vez de usar `<a download>`: el backend
  responde con `Content-Disposition: attachment` y su propio nombre de fichero,
  así que se reutiliza el `Button` compartido (que no admite `href`) y el
  nombre lo sigue decidiendo el backend.
* **El PDF conserva el botón principal** aunque haya cuatro formatos. No son
  opciones equivalentes: el PDF es el documento firmado y los otros tres son
  copias del mismo contenido emitidas en la misma generación. Presentarlos en
  igualdad daría a entender que da lo mismo cuál se aporta, y no da lo mismo.
* **El HTML se abre en otra pestaña**, no con `location.assign` como los demás.
  El backend lo sirve `inline` porque ese formato existe para leerlo, así que
  navegar a él reemplazaría la aplicación por el informe y habría que volver
  atrás. Los otros tres llegan como `attachment` y no cambian de página.

## Comprobado

`tsc -b` sin errores, `npm run build` compila y `oxlint` sin avisos.

Ejecutada contra el backend real del Módulo 5 (listado, detalle, modal de
generación y las cuatro descargas). Los tres botones nuevos se han pulsado y
devuelven `200` con el `formato` correcto; los ficheros recibidos coinciden
byte a byte con los de disco.

Sin comprobar todavía: el responsive real por debajo de `md`.
