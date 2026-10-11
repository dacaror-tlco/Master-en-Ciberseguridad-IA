# DFIR Nexus — Design System (frontend)

> Este documento describe el sistema de diseño **realmente implementado** en `frontend/src` a fecha de redacción. Todo lo que aparece aquí existe en el código; nada se ha inventado ni extrapolado sin dejarlo dicho explícitamente. Cuando un valor está declarado pero no se usa todavía en ningún componente, se indica como tal.

Stack real (`package.json`): React 19, React Router 7 (`createBrowserRouter`), TypeScript, Vite 8, Tailwind CSS v4 vía `@tailwindcss/vite` (configuración CSS-first, **no existe** `tailwind.config.*`).

---

## 1. Propósito del Design System

Nexus es una plataforma modular: `cases` existe hoy, y `osint`, `tracking`, `timeline`, `reports` se irán añadiendo como módulos independientes, cada uno desarrollado potencialmente por una persona distinta (ver `CLAUDE.md`). Sin una fuente de verdad visual única, cada módulo nuevo tendería a reinventar su propia paleta, tipografía y componentes — exactamente lo que pasó en los mockups de Stitch (`design/*/code.html`), donde cada pantalla trae su propio `tailwind.config` embebido y, en el caso de `design/Evidencias/code.html`, una identidad visual completamente distinta (gama de grises genérica, sin sidebar).

El Design System resuelve esto centralizando en tres capas (`styles/`, `shared/ui/`, `shared/layout/`) todo lo que un módulo nuevo necesita para verse como parte de Nexus sin tener que definir un solo color, fuente o efecto por su cuenta.

---

## 2. Fuente de verdad visual

Relación real entre las piezas, de mayor a menor autoridad:

1. **`design/Casos/code.html`** — origen histórico del sistema visual. Sigue existiendo en el repositorio. Es la referencia de *por qué* los tokens tienen los valores que tienen, pero **no es lo que el código consume en tiempo de ejecución**.
2. **`frontend/src/styles/tokens.css` y `effects.css`** — la traducción real de esos valores a variables CSS (`@theme` de Tailwind v4) y clases de efecto. Esta es la fuente de verdad **operativa**: si quieres saber qué color existe, se mira aquí, no en el HTML de Stitch.
3. **`frontend/src/shared/ui/*` y `shared/layout/*`** — consumen los tokens anteriores vía clases de Tailwind (`bg-primary`, `text-on-surface-variant`, `rounded-lg`, `font-label-caps`...). No declaran valores propios.
4. **`frontend/src/modules/*`** — consumen los componentes de `shared/`. No deberían declarar estilos nuevos salvo composición de utilidades ya existentes.

**Prioridad en caso de discrepancia**: `tokens.css`/`effects.css` (lo implementado) siempre gana sobre `Casos/code.html` (el origen) y sobre cualquier otro `design/*/code.html`. Ver §17 del historial del proyecto y la sección 16 de este documento para las discrepancias ya detectadas y resueltas deliberadamente.

---

## 3. Design Tokens

Todos definidos en `src/styles/tokens.css` mediante `@theme` (Tailwind v4 CSS-first: cada variable genera automáticamente utilidades, p. ej. `--color-primary` → `bg-primary`, `text-primary`, `border-primary`).

### 3.1 Color — escala base (idéntica a la escala Material del `tailwind.config` embebido en Casos/code.html)

| Token | Valor | Token | Valor |
|---|---|---|---|
| `primary` | `#94d69d` | `on-primary` | `#003917` |
| `primary-container` | `#6faf7a` | `on-primary-container` | `#00411b` |
| `primary-fixed` | `#aff2b8` | `on-primary-fixed` | `#00210a` |
| `primary-fixed-dim` | `#94d69d` | `on-primary-fixed-variant` | `#0f5227` |
| `secondary` | `#90d6a1` | `on-secondary` | `#00391a` |
| `secondary-container` | `#08552c` | `on-secondary-container` | `#82c894` |
| `secondary-fixed` | `#abf3bb` | `on-secondary-fixed` | `#00210d` |
| `secondary-fixed-dim` | `#90d6a1` | `on-secondary-fixed-variant` | `#03522a` |
| `tertiary` | `#9fcede` | `on-tertiary` | `#003642` |
| `tertiary-container` | `#7aa8b8` | `on-tertiary-container` | `#033d4b` |
| `tertiary-fixed` | `#baeafb` | `on-tertiary-fixed` | `#001f27` |
| `tertiary-fixed-dim` | `#9fcede` | `on-tertiary-fixed-variant` | `#1b4d5b` |
| `error` | `#ffb4ab` | `on-error` | `#690005` |
| `error-container` | `#93000a` | `on-error-container` | `#ffdad6` |
| `inverse-primary` | `#2c6a3c` | `inverse-surface` | `#dae5dd` |
| `inverse-on-surface` | `#28332d` | `surface-tint` | `#94d69d` |

| Superficies | Valor |
|---|---|
| `background` / `surface` / `surface-dim` | `#0c1511` |
| `on-background` / `on-surface` | `#dae5dd` |
| `on-surface-variant` | `#c0c9bd` |
| `surface-variant` | `#2d3732` |
| `surface-container-lowest` | `#07100c` |
| `surface-container-low` | `#141e19` |
| `surface-container` | `#18221d` |
| `surface-container-high` | `#222c27` |
| `surface-container-highest` | `#2d3732` |
| `surface-bright` | `#313b36` |
| `outline` | `#8a9389` |
| `outline-variant` | `#404940` |

### 3.2 Color — tokens literales adicionales (no forman parte de la escala Material, están nombrados para no repetirlos como valores hex sueltos)

| Token | Valor | Uso real |
|---|---|---|
| `canvas` | `#0b0f0d` | Fondo real de página (`body`/`AppShell`), fondo de inputs, track de scrollbar |
| `panel` | `#131a17` | Fondo de `.nexus-glass-panel` (Card, Modal, drawer) |
| `hairline` | `#1b2520` | Borde por defecto (`* { border-color }`), hover de filas/tarjetas, fondo de `StatusBadge` neutral |

**No existen** tokens de color fuera de esta lista (ni ámbar, ni grises adicionales, ni ningún hex "de un solo uso" en los componentes revisados).

### 3.3 Radios

| Token | Valor | Utilidad Tailwind |
|---|---|---|
| `--radius` | `0.125rem` | `rounded` (bare) |
| `--radius-lg` | `0.25rem` | `rounded-lg` |
| `--radius-xl` | `0.5rem` | `rounded-xl` — **declarado, sin uso actual en ningún componente** |
| `--radius-full` | *(no sobreescrito)* | `rounded-full` mantiene el valor por defecto de Tailwind (`9999px`, círculo real) |

Decisión documentada en el propio `tokens.css`: Casos/code.html declaraba `full: 0.75rem` en su config embebido, pero su propio marcado solo usa `rounded-full` en el avatar circular del header. Adoptar `0.75rem` de forma literal habría roto la circularidad de cualquier avatar/punto futuro, así que `--radius-full` se dejó sin tocar. Es la única desviación deliberada de la literalidad en todo el sistema de tokens.

### 3.4 Espaciado

| Token | Valor | Uso real detectado |
|---|---|---|
| `--spacing-gutter` | `24px` | `SideNav`, `TopBar`, `TableWithDrawerLayout`, las 4 páginas placeholder |
| `--spacing-margin-safe` | `32px` | `SideNav` (`py-margin-safe`) |
| `--spacing-panel-gap` | `16px` | `TableWithDrawerLayout` (`gap-panel-gap`) |
| `--spacing-unit` | `4px` | **declarado, sin uso actual** |

### 3.5 Otros

`--container-max: 1440px` está declarado en `tokens.css` pero **no pertenece a ningún namespace de Tailwind v4 reconocido** (no es `--spacing-*`, `--width-*` ni `--container-*`), por lo que no genera ninguna clase de utilidad. Hoy es una variable CSS sin consumidores en el código — no debe asumirse que existe una clase `max-w-container-max` o similar.

---

## 4. Tipografía

Tres familias, cargadas en `index.html` vía Google Fonts, cada una con un rol fijo:

| Familia | Token(s) que la usan | Peso(s) cargado(s) en `index.html` | Rol |
|---|---|---|---|
| **Space Grotesk** | `font-headline-lg`, `font-headline-lg-mobile`, `font-headline-md` | 500, 600, 700 | Titulares (`<h1>`/`<h2>`/`<h3>` en `globals.css`, y explícitamente en `Card`, `Modal`, `SideNav`, `TopBar`, `CaseDetailDrawer`) |
| **JetBrains Mono** | `font-body-lg`, `font-body-md`, `font-mono-data` | 400, 500, 700 | Cuerpo de texto y todo dato/tabular (`font-body-md` es la fuente por defecto del `body`) |
| **Geist** | `font-label-caps` | 700 (única variante cargada) | Etiquetas de UI: botones, nav, headers de tabla, badges |

Escala tipográfica completa (`tokens.css`), con su peso y line-height emparejados como exige Tailwind v4:

| Token | Tamaño | Line-height | Letter-spacing | Peso | ¿Usado hoy? |
|---|---|---|---|---|---|
| `headline-lg` | 42px | 1.2 | -0.02em | 600 | No (declarado, sin consumidores) |
| `headline-lg-mobile` | 32px | 1.2 | — | 600 | No (declarado, sin consumidores) |
| `headline-md` | 28px | 1.3 | — | 500 | Sí (Card, Modal, SideNav, TopBar, CaseDetailDrawer) |
| `body-lg` | 18px | 1.6 | — | 400 | No (declarado, sin consumidores) |
| `body-md` | 14px | 1.5 | — | 400 | Sí (fuente base del `body`, Alert, EvidenceListItem, párrafo de confirmación de borrado) |
| `mono-data` | 13px | 1.4 | — | 500 | Sí (muy extendido: tablas, inputs, badges, drawer) |
| `label-caps` | 12px | 1 | 0.1em | 700 | Sí (botones, nav, headers de tabla, labels de formulario, badges) |

No existe una escala de pesos (`font-weight-*`) independiente: cada tamaño lleva su propio peso fijo emparejado (`--text-*--font-weight`), no se combinan tamaños con pesos arbitrarios.

---

## 5. Fondos y efectos

Todos definidos en `src/styles/effects.css` como clases con prefijo `nexus-`, y **montados una única vez en `AppShell`** (`src/shared/layout/AppShell/AppShell.tsx`):

| Clase | Efecto | Dónde se monta |
|---|---|---|
| `.nexus-canvas` | Fondo base (`canvas`) + grid punteado de 32px (rejilla "investigation grid") | Contenedor raíz de `AppShell` |
| `.nexus-noise-overlay` | Grano SVG fijo, opacidad 2%, `position: fixed; z-index: 50` | Hijo directo de `AppShell` |
| `.nexus-mist-gradient` | Niebla radial en `primary` al 5% | `div absolute inset-0` dentro de `AppShell` |
| `.nexus-scanline` | Línea animada de 2px que recorre la pantalla verticalmente (8s) | Hijo directo de `AppShell` |
| `.nexus-glass-panel` | Fondo `panel` + borde bicolor (relieve simulado, sin `box-shadow`) | Usado por `Card` y `Modal` (vía clase), y directamente en `CaseDetailDrawer` |
| `.nexus-glow-tertiary` / `.nexus-glow-error` | `box-shadow` de color al hacer hover | `Button` variantes `ghost` y `danger` respectivamente |
| `.nexus-glow-primary` | Mismo patrón en tono `primary` | **Declarada, sin ningún consumidor actual** (ninguna variante de `Button` ni otro componente la usa hoy) |
| `.nexus-scrollbars` | Scrollbar de webkit personalizada (pista `canvas`, thumb `hairline`) | Contenedor raíz de `AppShell` |

**Regla de una sola instancia**: `AppShell` es el único lugar del código que referencia `nexus-canvas`, `nexus-noise-overlay`, `nexus-mist-gradient`, `nexus-scanline` y `nexus-scrollbars`. Ninguna página de módulo (`CasesPage`, `OSINTPage`, etc.) vuelve a declararlos. Un módulo nuevo **nunca** debe añadir su propio `nexus-noise-overlay` ni fondo alternativo: al montarse dentro de `<Outlet />` hereda automáticamente los cuatro efectos.

---

## 6. Layout global

### `AppShell` (`shared/layout/AppShell/AppShell.tsx`)
Estructura raíz montada por el router (ver §12): `div.nexus-canvas.nexus-scrollbars` (`h-screen overflow-hidden flex`) → `nexus-scanline` + `nexus-mist-gradient` + `nexus-noise-overlay` (decorativos, `position: fixed/absolute`) → `<SideNav />` → columna derecha (`flex-1 flex flex-col`) con `<TopBar />` arriba y `<main className="flex-1 overflow-hidden"><Outlet /></main>` debajo. El `<main>` no lleva padding propio: cada layout de contenido (p. ej. `TableWithDrawerLayout`) decide su propio `p-gutter`.

### `SideNav` (`shared/layout/SideNav/SideNav.tsx`)
- Ancho fijo `w-64` (256px), alto completo, `bg-surface-container-low`, `border-r border-hairline`.
- **Oculto por debajo de `md`** (`hidden md:flex`) — en mobile no hay sidebar.
- Contiene: logo + wordmark "NEXUS" + subtítulo, botón CTA "NUEVA INVESTIGACIÓN" (enlace a `/cases`), lista de navegación, y pie con "Ayuda"/"Cerrar Sesión" (ambos decorativos, sin `onClick`, ya que no hay sistema de autenticación implementado).
- 8 ítems de navegación con orden fijo (`NAV_ITEMS`): Dashboard, Casos, Evidencias, OSINT y Fraude, Tracking Post-Incidente, Línea Temporal, Informes, Configuración. Solo los que tienen `path` no nulo son clicables (`Casos`, `OSINT y Fraude`, `Tracking Post-Incidente`, `Línea Temporal`, `Informes`); `Dashboard` y `Configuración` se muestran deshabilitados (`opacity-40 cursor-not-allowed`) porque no existen como rutas en esta fase; `Evidencias` navega a `/cases` (no tiene ruta propia).
- Solo un ítem puede estar activo a la vez (`activeLabel` se calcula con `.find()`, el primer match gana), evitando que dos entradas que comparten ruta (`Casos` y `Evidencias`) aparezcan resaltadas simultáneamente.

### `TopBar` (`shared/layout/TopBar/TopBar.tsx`)
- Altura fija `h-16`, `bg-surface-container-low/80` con `backdrop-blur-md`, `border-b border-hairline`.
- Wordmark "NEXUS" visible **solo en mobile** (`md:hidden`); el buscador ocupa su lugar en desktop (`hidden md:block`).
- Buscador, botón de notificaciones y botón de huella (`fingerprint`) llevan el atributo `disabled` — son decorativos, no hay backend de búsqueda global ni notificaciones. Los dos botones de icono añaden además `disabled:opacity-60 disabled:cursor-not-allowed`; el buscador **no** lleva ninguna clase `disabled:*` propia, solo el atributo nativo.
- El botón de huella se oculta también por debajo de `md` (`hidden md:block`).
- Avatar: círculo con icono `person` genérico (no hay imagen de usuario real, no hay sistema de usuarios).
- **Discrepancia conocida — duplicación de `Input`**: el buscador de `TopBar` está implementado como un `<input>` nativo con clases propias (`w-full bg-canvas border border-hairline rounded px-9 py-2 ...`) que reproducen parcialmente el lenguaje visual del componente compartido `shared/ui/Input`, pero `TopBar.tsx` **no importa ni utiliza** ese componente (su único import de `shared/ui` es `Icon`). Es una duplicación de estilo conocida y no intencionada como patrón a seguir, no una integración real del componente. Según la arquitectura prevista del Design System (§13–§16), esta duplicación debería evitarse en futuras implementaciones: si `TopBar` se refactoriza más adelante, el buscador debería reutilizar el componente compartido `Input` cuando sea técnicamente adecuado. Esta nota es únicamente documental: no implica ni requiere ningún cambio de código en esta fase.

### `TableWithDrawerLayout` (`shared/layout/TableWithDrawerLayout/TableWithDrawerLayout.tsx`)
- `div h-full overflow-hidden p-gutter flex gap-panel-gap` con dos zonas: `main` (`flex-1`, ancho variable) y `drawer` opcional (`aside w-96`).
- El `aside` **solo se renderiza si se pasa la prop `drawer`**, y aun así queda oculto por debajo de `xl` (`hidden xl:flex`) — no hay ningún mecanismo de "drawer deslizante" para mobile/tablet; simplemente no es visible hasta 1280px de ancho. Este es el comportamiento explícito heredado de Casos/code.html, no una limitación añadida.
- Es el único layout de contenido implementado hasta la fecha; lo usa `CasesPage` como único consumidor actual.

### Scroll
`AppShell` fija `overflow-hidden` en el contenedor raíz y en `<main>`: el scroll ocurre dentro de cada panel (`Card` usa `overflow-auto` en su cuerpo, `DataTable` hereda ese scroll, `CaseDetailDrawer` tiene su propio `overflow-y-auto` en el cuerpo). No hay scroll de página completa en ningún punto de la aplicación.

---

## 7. Componentes UI (`shared/ui/`)

### Button (`shared/ui/Button/Button.tsx`)
- **Propósito**: único botón del sistema; toda acción clicable pasa por aquí.
- **Variantes** (`variant`): `primary` (default, fondo `primary`/texto `on-primary`, usado para acciones principales — crear, guardar), `ghost` (borde `tertiary-container`, texto `tertiary`, glow al hover — acciones secundarias como cancelar o editar), `danger` (borde/texto `error`, glow rojo — eliminar).
- **Tamaños** (`size`): `md` (default, `py-3 px-4`) y `sm` (`py-1.5 px-3`, usado en acciones dentro de paneles ya densos como la cabecera de la tabla o el pie del drawer).
- **Props**: extiende todos los atributos nativos de `<button>`, más `icon?: string` (nombre de icono opcional a la izquierda del texto), `loading?: boolean`.
- **Estados**: `disabled` nativo (`disabled:opacity-50 disabled:cursor-not-allowed`); `loading` sustituye el icono por un spinner (`progress_activity` con `animate-spin`) y fuerza `disabled`.
- **Cuándo usarlo**: cualquier acción del usuario.
- **Cuándo NO usarlo**: para navegación pura usa un `<Link>` de React Router (así lo hace el propio `SideNav` para "NUEVA INVESTIGACIÓN", que no usa `Button` sino un `Link` con clases equivalentes) — `Button` no soporta `href`.

### Input (`shared/ui/Input/Input.tsx`)
- **Propósito**: campo de texto de una línea.
- **Props**: todos los atributos nativos de `<input>`, más `icon?: string` (icono a la izquierda), `label?: string`, `error?: string`.
- **Comportamiento**: genera un `id` automático con `useId()` si no se pasa uno explícito, para que `label`/`input` queden siempre correctamente asociados.
- **Estados**: `focus` (borde `primary` + `ring-primary/50`), `error` (borde `error` + mensaje en rojo debajo). El componente **no define ningún estilo `disabled:*` propio**, y a día de hoy **no existe ningún uso real de `Input` con la prop `disabled`** en el código (verificado por búsqueda en el proyecto). Si se pasara `disabled`, el campo heredaría únicamente el comportamiento por defecto del navegador, sin ningún estilo adicional definido ni probado. El buscador de `TopBar` **no** es una instancia de este componente — ver la discrepancia documentada en §6 (`TopBar`).
- **Cuándo NO usarlo**: para texto multilínea no existe un componente `Textarea` en `shared/ui`; `CaseForm` resuelve la descripción con un `<textarea>` nativo estilizado a mano, replicando las mismas clases de `Input`.

### Select (`shared/ui/Select/Select.tsx`)
- **Propósito**: selección de una opción entre una lista cerrada.
- **Props**: atributos nativos de `<select>` (vía `Omit<..., 'children'>`), más `label?`, `options: {value, label}[]`, `error?`.
- **Comportamiento visual**: mismo contenedor que `Input` (fondo `canvas`, borde `hairline`, foco `primary`), con `appearance-none` y un icono `expand_more` posicionado a la derecha en vez de un icono a la izquierda.
- **Único consumidor actual**: `CaseForm`, para el campo `estado`.
- **Nota de origen**: Casos/code.html no incluye ningún select; este componente es una extrapolación deliberada del mismo lenguaje visual de `Input` (documentado así en el propio archivo).

### Card (`shared/ui/Card/Card.tsx`)
- **Propósito**: panel "glass" genérico con cabecera/cuerpo/pie opcionales.
- **Props**: `title?`, `subtitle?`, `actions?` (nodo a la derecha de la cabecera), `footer?`, `children`, `className?`.
- **Comportamiento**: la cabecera (`bg-surface-container-highest/30`, borde inferior) solo se renderiza si hay `title` o `actions`; el pie (`bg-surface-container-highest/50`, borde superior) solo si hay `footer`. El cuerpo (`children`) siempre está envuelto en `overflow-auto`.
- **No tiene `flex-1` propio**: si se usa dentro de un contenedor flex-column que debe ocupar toda la altura disponible (como el panel principal de `CasesPage`), hay que pasarle explícitamente `className="flex-1"` — así lo hace `CasesPage`.
- **Cuándo NO usarlo**: para overlays/diálogos modales usa `Modal`, no `Card` (aunque comparten el mismo `.nexus-glass-panel`).

### DataTable (`shared/ui/DataTable/DataTable.tsx`)
Documentado en detalle en §10.

### StatusBadge (`shared/ui/StatusBadge/StatusBadge.tsx`)
- **Propósito**: representar visualmente un estado con una etiqueta y un tono, sin conocer el dominio (no sabe qué es un "Case").
- **Props**: `label: string`, `tone: 'primary' | 'tertiary' | 'neutral' | 'muted'`.
- **Tonos reales**:
  - `primary` → `bg-secondary-container text-on-secondary-container`.
  - `tertiary` → transparente, borde y texto `tertiary`/`tertiary-container`.
  - `neutral` → fondo `hairline`, texto `on-surface-variant`, borde `outline-variant`.
  - `muted` → igual que `neutral` + `opacity-60`.
- **Quién decide el tono**: el módulo consumidor. En `cases`, `CaseStatusMap.ts` mapea el enum real del backend (`abierto|en_progreso|cerrado|archivado`) a `{label, tone}`. Un módulo nuevo con sus propios estados debe crear su propio mapeo equivalente y seguir pasando solo `label`/`tone` a `StatusBadge`.

### Modal (`shared/ui/Modal/Modal.tsx`)
- **Propósito**: diálogo superpuesto (crear/editar/confirmar).
- **Props**: `open: boolean`, `onClose: () => void`, `title: string`, `children`, `footer?`.
- **Comportamiento**: overlay `fixed inset-0` con `bg-canvas/80 backdrop-blur-sm`; el panel usa `.nexus-glass-panel` + `backdrop-blur-md` (nivel de elevación más alto que `Card`, que no lleva blur); cierra con clic en el overlay, con el botón `close` de la cabecera, o con la tecla `Escape` (listener en `useEffect`); el clic dentro del panel hace `stopPropagation` para no cerrar accidentalmente.
- **Origen**: no existe en Casos/code.html; extrapolado del nivel de elevación 2 ("Modals/Popovers") de `design/evidence_narrative/DESIGN.md`, reutilizando únicamente tokens ya existentes.
- **Consumidores actuales**: `CasesPage` lo usa dos veces (formulario crear/editar, confirmación de borrado).

### Alert (`shared/ui/Alert/Alert.tsx`)
- **Propósito**: mensaje contextual en línea (no es un toast/notificación flotante — no existe ese patrón en el código).
- **Props**: `variant?: 'info' | 'success' | 'error'` (default `'info'`), `children`.
- **Tonos**: `info` (borde/icono `tertiary`, icono `info`), `success` (borde `primary`, icono `check_circle`), `error` (borde/icono `error`, icono `warning`).
- **No existe variante `warning` separada de `error`**: solo hay tres variantes, deliberadamente limitadas a los tres colores semánticos presentes en Casos/code.html, sin introducir ámbar.
- **Único consumidor actual**: `CasesPage`, para mostrar errores de la API (`variant="error"`).

### Icon (`shared/ui/Icon/Icon.tsx`)
Documentado en detalle en §9.

---

## 8. Estados interactivos

| Estado | Implementación real | Dónde |
|---|---|---|
| Default | Clases base de cada componente | Todos |
| Hover | `hover:bg-*`, `hover:text-*`, o `.nexus-glow-*` (box-shadow) | `Button`, filas de `DataTable`, ítems de `SideNav`, `EvidenceListItem` |
| Focus | `focus:border-primary focus:ring-1 focus:ring-primary/50` | `Input`, `Select`, buscador de `TopBar` |
| Active (navegación) | Ítem de `SideNav`: `text-primary border-l-2 border-primary bg-secondary-container/10 translate-x-1` + icono en modo `filled` | `SideNav` únicamente |
| Selected (fila) | `DataTable`: `bg-hairline/50` en la fila + `border-l-2 border-primary` en su primera celda | `DataTable` / `CaseTable` |
| Disabled | `Button`: atributo nativo `disabled` + `disabled:opacity-50 disabled:cursor-not-allowed`. Botones de icono de `TopBar` (notificaciones, huella): `disabled` + `disabled:opacity-60 disabled:cursor-not-allowed`. Buscador de `TopBar`: solo el atributo nativo `disabled`, **sin ninguna clase `disabled:*` propia**. Ítems "Dashboard"/"Configuración"/"Ayuda"/"Cerrar Sesión" de `SideNav`: `opacity-40`/`opacity-60` + `cursor-not-allowed` sin atributo `disabled` real (son `<span>`, no controles de formulario). El componente `Input` de `shared/ui` no define ningún `disabled:*` propio y no tiene ningún uso real con `disabled` (ver §7 y la discrepancia de §6) | `Button`, `TopBar`, `SideNav` |
| Loading | `Button` con `loading` sustituye el icono por un spinner (`progress_activity` + `animate-spin`) y fuerza `disabled` | `Button` (usado en `CaseForm` al guardar, en `CaseDetailDrawer` al añadir evidencia, en el modal de borrado) |
| Error | `Input`/`Select`: borde `error` + texto de ayuda en `error` (prop `error`, **declarada pero sin ningún consumidor que la use hoy** — ni `CaseForm` ni ningún otro componente pasa `error` a `Input`/`Select` actualmente); `Alert variant="error"` sí se usa activamente para errores de API | `Input`, `Select` (preparado, no usado); `Alert` (usado) |

---

## 9. Iconografía

- **Librería**: Material Symbols Outlined, cargada como webfont variable en `index.html` (`family=Material+Symbols+Outlined:wght,FILL@100..700,0..1`).
- **Punto único de acceso**: el componente `Icon` (`shared/ui/Icon/Icon.tsx`). Ningún otro archivo debe escribir `<span className="material-symbols-outlined">` directamente.
- **Props**: `name: string` (nombre del icono, p. ej. `"folder_shared"`), `filled?: boolean` (default `false`), `className?`.
- **Configuración de relleno**: `filled` controla `font-variation-settings: 'FILL' 0|1` inline — no se usa una clase Tailwind para esto porque el eje `FILL` es una variación de fuente, no un color. `filled=true` se usa para el icono del logo (siempre relleno) y para el icono del ítem de navegación activo en `SideNav`.
- **Tamaño y peso**: no se fija un tamaño por defecto en el propio componente; cada consumidor lo ajusta con `className` (p. ej. `text-[16px]`, `text-4xl`). No hay un token de tamaño de icono centralizado.
- **Regla de uso**: siempre a través de `Icon`, nunca instanciando el `<span>` a mano, para poder cambiar la librería de iconos en un solo punto si algún día fuera necesario.

---

## 10. Tablas y datos

`DataTable` (`shared/ui/DataTable/DataTable.tsx`) es genérico (`<T,>`), sin conocimiento de dominio:

- **Columnas**: array de `{key, header, align?, render}` — el módulo consumidor decide qué columnas mostrar y cómo renderizar cada celda (p. ej. `CaseTable` inyecta un `StatusBadge` en la columna `estado`).
- **Header**: `sticky top-0 bg-canvas border-b border-hairline`, texto en `label-caps`.
- **Filas**: cuerpo en `mono-data` (todo dato tabular es monoespaciado, coherente con el rol de JetBrains Mono documentado en §4).
- **Hover**: `hover:bg-hairline`, solo si la tabla recibe `onRowClick` (si no, las filas no son clicables y no muestran hover).
- **Selección**: se compara `getRowId(row) === selectedRowId`; la fila seleccionada recibe `bg-hairline/50` y su primera celda un `border-l-2 border-primary` (las demás filas tienen `border-l-2 border-transparent` en su primera celda, para que el layout no salte al seleccionar).
- **Vacío**: si `rows.length === 0`, se renderiza una única fila con `emptyMessage` centrado, ocupando todas las columnas (`colSpan`).
- **Scroll**: la tabla no gestiona su propio scroll; depende del contenedor donde se monte (en `CasesPage`, es el `Card` que la envuelve, vía `overflow-auto`).
- **Badges dentro de tabla**: se inyectan como `render` de columna, no como parte de `DataTable` — así se mantiene agnóstica al dominio.

Único consumidor actual: `CaseTable` (`modules/cases/components/CaseTable.tsx`), con columnas `ID CASO`, `NOMBRE`, `ESTADO` (`StatusBadge`), `RESPONSABLE`, `FECHA CREACIÓN` (alineada a la derecha) — todas mapeadas 1:1 a campos reales del backend (`app/modules/cases/schemas.py`), sin ninguna columna decorativa inventada.

---

## 11. Responsive

Único breakpoint set en uso: los de Tailwind por defecto (`md` = 768px, `xl` = 1280px). No hay breakpoints custom declarados en `tokens.css`.

| Elemento | < md (mobile) | md–xl (tablet/laptop) | ≥ xl (desktop) |
|---|---|---|---|
| **Sidebar** (`SideNav`) | Oculto por completo (`hidden md:flex`) — no existe menú hamburguesa ni alternativa mobile | Visible, `w-64` fijo | Visible, `w-64` fijo |
| **TopBar** | Wordmark "NEXUS" visible, buscador oculto, botón de huella oculto | Buscador visible, botón de huella visible | Igual que tablet |
| **Tabla** (`DataTable`/`CaseTable`) | Se renderiza igual; sin columnas ocultas — el desbordamiento horizontal lo resuelve el `overflow-auto` del `Card` contenedor | Igual | Igual |
| **Drawer** (`CaseDetailDrawer` vía `TableWithDrawerLayout`) | Oculto (`hidden xl:flex`) — **no existe ningún modo alternativo** para ver el detalle de un caso por debajo de 1280px; seleccionar una fila actualiza el estado pero el panel simplemente no es visible | Oculto (igual que mobile, hasta 1280px) | Visible, `w-96` fijo |
| **Contenido principal** | `p-gutter` (24px) constante en todos los tamaños vía `TableWithDrawerLayout` / páginas placeholder | Igual | Igual |

No hay `useMediaQuery` ni lógica JS de responsive en ningún componente: todo el comportamiento responsive se resuelve con clases condicionales de Tailwind (`hidden md:flex`, `hidden xl:flex`, etc.).

---

## 12. Arquitectura frontend

```
frontend/src/
├── app/        → router.tsx: único punto que conecta rutas con páginas de módulo.
├── styles/     → tokens.css, effects.css, globals.css. Única fuente de valores visuales.
├── shared/
│   ├── ui/     → componentes genéricos sin conocimiento de dominio (Button, Input...).
│   └── layout/ → AppShell, SideNav, TopBar, TableWithDrawerLayout. Estructura de página.
└── modules/
    └── <nombre>/
        ├── api/         → cliente HTTP contra el backend real de ese módulo.
        ├── types/        → tipos que reflejan literalmente los schemas del backend.
        ├── components/   → componentes específicos del dominio del módulo.
        └── pages/         → ensamblado final: layout de shared/ + componentes del módulo.
```

**Nota importante sobre discrepancia con este prompt**: no existe `frontend/src/pages/` como carpeta global. Cada módulo tiene su propio `pages/` interno (`modules/cases/pages/`, `modules/osint/pages/`, etc.) — así se decidió explícitamente para que cada módulo sea autocontenido (ver historial del proyecto, sección "Regla importante sobre pages"). Tampoco existe `tailwind.config.*`: Tailwind v4 usa configuración CSS-first, y toda la personalización vive en `styles/tokens.css` (bloque `@theme`) más el plugin `@tailwindcss/vite` en `vite.config.ts`.

- **`app/`**: hoy solo contiene `router.tsx`. Es responsabilidad exclusiva de ensamblar `AppShell` con las páginas de cada módulo; no contiene lógica de negocio ni estilos.
- **`styles/`**: fuente única de tokens y efectos. Ningún componente debe declarar un valor visual que pueda expresarse con un token existente.
- **`shared/ui/`**: piezas atómicas reutilizables por cualquier módulo, sin importar nada de `modules/`.
- **`shared/layout/`**: estructura de página compartida (AppShell y layouts de contenido como `TableWithDrawerLayout`).
- **`modules/<nombre>/`**: todo lo específico de un dominio (Casos, OSINT, Tracking...), con la subestructura fija `api/types/components/pages`.

---

## 13. Reglas de dependencia

```
modules/*  →  shared/*      (permitido y esperado)
shared/*   →  modules/*     (PROHIBIDO)
modules/A  →  modules/B     (PROHIBIDO)
```

Verificado por inspección directa del código actual: ningún archivo bajo `shared/` importa nada de `modules/`, y `modules/cases` no importa nada de `modules/osint|tracking|timeline|reports` (que hoy solo contienen una página placeholder cada uno, sin `api/types/components`).

**Por qué existe esta regla**: es el mismo principio de bajo acoplamiento que ya rige el backend (`CLAUDE.md`: "cada módulo debe poder desarrollarse por una persona distinta", relación exclusivamente vía `case_id`). Si `shared/` dependiera de un módulo, dejaría de ser reutilizable por los demás; si un módulo dependiera de otro, no podrían desarrollarse ni desplegarse de forma independiente. La única vía de comunicación entre módulos, cuando exista, debería pasar por identificadores de dominio (como `case_id` en el backend), nunca por imports directos de componentes o tipos de otro módulo.

---

## 14. Cómo crear un nuevo módulo

Ejemplo: añadir `modules/osint/` con funcionalidad real (hoy solo existe `modules/osint/pages/OSINTPage.tsx` como placeholder).

1. **Inspecciona el sistema existente** antes de escribir nada: lee este documento completo, y como referencia de implementación real, revisa `modules/cases/` de principio a fin (es el único módulo funcional y sirve de plantilla exacta de la estructura `api/types/components/pages`).
2. **Reutiliza `AppShell`**: no lo importes ni lo repliques — ya está montado por `app/router.tsx` como layout raíz. Tu módulo solo necesita exportar páginas que se renderizarán dentro de su `<Outlet />`.
3. **Reutiliza `shared/ui`**: para cualquier botón, input, select, tabla, badge, modal, alerta o icono, importa desde `@/shared/ui`. No copies el JSX/clases de `Casos` ni de ningún otro `design/*/code.html` — usa los componentes ya construidos.
4. **Crea componentes específicos del módulo** en `modules/osint/components/` (p. ej. un futuro `OSINTResultTable`, `IndicatorForm`) siguiendo el mismo patrón que `modules/cases/components/CaseTable.tsx`: componer primitivas de `shared/ui`, nunca reimplementarlas.
5. **Crea páginas** en `modules/osint/pages/`, sustituyendo (no envolviendo) el actual `OSINTPage.tsx` placeholder. Usa `TableWithDrawerLayout` si el patrón encaja (lista + detalle), o documenta y construye un nuevo layout en `shared/layout/` si el módulo lo necesita de verdad (p. ej. Línea Temporal casi seguro no encajará en `TableWithDrawerLayout`).
6. **Añade el routing**: en `app/router.tsx`, sustituye el `element={<OSINTPage />}` placeholder por tu página real; la ruta `path: 'osint'` ya existe.
7. **Integra el backend real**: crea `modules/osint/api/` siguiendo el patrón de `modules/cases/api/` (un `httpClient.ts` o equivalente + funciones tipadas 1:1 contra los endpoints reales de `app/modules/osint/routes.py` cuando exista). No inventes endpoints ni dupliques modelos del backend: los tipos de `modules/osint/types/` deben reflejar literalmente los schemas Pydantic reales.
8. **Mantén el responsive** usando los mismos breakpoints (`md`, `xl`) y los mismos patrones (`hidden md:flex`, `hidden xl:flex`) documentados en §11 — no introduzcas breakpoints nuevos.
9. **Evita duplicar estilos**: si necesitas un color, tipografía, radio o espaciado, comprueba primero si ya existe un token en `styles/tokens.css` (§3). Si necesitas un efecto de fondo, usa las clases `nexus-*` ya existentes (§5) — nunca definas tu propio grano, grid o glow.
10. **Mantén la identidad visual**: cualquier componente nuevo debe consumir clases de Tailwind que resuelvan a los tokens documentados (`bg-primary`, `text-on-surface-variant`, `font-label-caps`...), nunca valores hexadecimales ni tamaños arbitrarios sueltos en el JSX.

---

## 15. Reglas para desarrollar nuevos módulos con Claude Code

Instrucciones que cualquier miembro del equipo puede copiar directamente en su prompt al pedirle a Claude Code que construya un módulo nuevo:

```
- Antes de escribir código, lee frontend/DESIGN_SYSTEM.md completo.
- Inspecciona frontend/src/modules/cases/ como referencia de implementación real
  (es el único módulo funcional; su estructura api/types/components/pages es la plantilla).
- Reutiliza exclusivamente los tokens de frontend/src/styles/tokens.css. No crees
  una paleta de colores, tipografías o radios nueva.
- Reutiliza los componentes de frontend/src/shared/ui/ (Button, Input, Select, Card,
  DataTable, StatusBadge, Modal, Alert, Icon). No los reimplementes ni los copies
  con otro nombre dentro del módulo.
- No crees un AppShell, SideNav ni TopBar nuevos: ya existen en frontend/src/shared/layout/
  y se montan una sola vez desde app/router.tsx.
- No copies el diseño de ningún archivo design/*/code.html salvo Casos, y solo como
  contexto histórico: el sistema real ya está en frontend/src/styles/ y shared/.
- No introduzcas colores hexadecimales arbitrarios en el JSX. Si necesitas un color
  que no existe como token, dilo explícitamente en vez de inventarlo.
- No modifiques frontend/src/styles/, frontend/src/shared/ui/ ni frontend/src/shared/layout/
  salvo que sea estrictamente necesario y lo justifiques (p. ej. promover un componente
  realmente genérico descubierto en tu módulo a shared/ui).
- Mantén la arquitectura de módulos: tu código vive en modules/<tu-modulo>/api|types|components|pages.
- No importes nada de otro modules/* distinto al tuyo, y no dejes que shared/ importe
  nada de modules/.
- Antes de dar por terminado: ejecuta `tsc -b` y comprueba que no hay errores de TypeScript,
  ejecuta `npm run build` y comprueba que compila, prueba el resultado en mobile/tablet/desktop
  (breakpoints md y xl), y revisa la consola del navegador en busca de errores.
```

---

## 16. Qué NO hacer

- ❌ Introducir colores hexadecimales sueltos en componentes (`className="bg-[#123456]"`) cuando el valor podría/debería ser un token de `tokens.css`.
- ❌ Crear una segunda escala tipográfica o cargar fuentes adicionales a las tres ya declaradas en `index.html` (Space Grotesk, JetBrains Mono, Geist).
- ❌ Crear un segundo `SideNav`, `TopBar` o `AppShell` para un módulo nuevo. Solo existe uno de cada, en `shared/layout/`.
- ❌ Duplicar `Button`, `Input`, `Select`, `Card`, `DataTable`, `StatusBadge`, `Modal`, `Alert` o `Icon` dentro de un módulo con otro nombre.
- ❌ Escribir estilos que contradigan los tokens (p. ej. un botón con radio distinto a `rounded`/`rounded-lg`/`rounded-xl`, o un panel con `box-shadow` cuando el sistema usa exclusivamente bordes/relieve).
- ❌ Copiar el diseño de `design/Dashboard`, `design/Evidencias`, `design/OSINT`, `design/Tracking`, `design/Línea temporal`, `design/Informes` o `design/Configuración del sistema` — todos difieren visualmente entre sí y de Casos (etiquetas en inglés, sidebars distintos, en el caso de Evidencias una identidad completamente distinta sin sidebar). Solo `design/Casos/code.html` fue nunca fuente visual válida, y hoy esa fuente ya está traducida a `styles/` y `shared/`.
- ❌ Crear dependencias entre `modules/*` (ver §13).
- ❌ Modificar el backend (FastAPI/SQLAlchemy/Alembic) sin una necesidad técnica imprescindible y justificada.
- ❌ Introducir una librería de componentes UI de terceros (Material UI, Chakra, Ant Design...) que sustituya o compita con `shared/ui`.
- ❌ Añadir lógica de responsive en JavaScript (`useMediaQuery`, `window.innerWidth`...) cuando el patrón existente resuelve todo con clases de Tailwind condicionales.

---

## 17. Ejemplo conceptual de integración de un módulo

**Nota: esto es documentación de arquitectura, no código funcional.**

```
frontend/src/modules/osint/
├── api/
│   ├── httpClient.ts        # equivalente al de modules/cases/api/httpClient.ts
│   ├── osintApi.ts           # funciones tipadas 1:1 contra endpoints reales de /osint
│   └── index.ts
├── types/
│   ├── osintResult.ts        # refleja literalmente OsintResultRead/Create/Update del backend
│   └── index.ts
├── components/
│   ├── OSINTResultTable.tsx  # compone <DataTable> de shared/ui + <StatusBadge>
│   ├── OSINTResultDrawer.tsx # compone <Card>/panel propio, sigue el patrón de CaseDetailDrawer
│   └── index.ts
└── pages/
    ├── OSINTPage.tsx          # compone <TableWithDrawerLayout> con lo anterior
    └── index.ts
```

Conexión con el resto del sistema:

- `OSINTPage` importa **únicamente** de `@/shared/ui`, `@/shared/layout` y de su propio módulo (`../api`, `../types`, `../components`) — nunca de `@/modules/cases` ni de ningún otro módulo.
- `app/router.tsx` sustituye la entrada actual `{ path: 'osint', element: <OSINTPage /> }` (hoy apuntando al placeholder) por la nueva página real, sin tocar el resto de rutas.
- No se crea ningún `pages/` a nivel de `src/` — la página vive dentro del propio módulo, igual que en `modules/cases/pages/`.

---

## Verificación de este documento

- ✅ `frontend/DESIGN_SYSTEM.md` describe únicamente tokens, componentes y comportamientos verificados en `frontend/src` en el momento de escribirlo.
- ✅ No se documenta ningún componente que no exista (`Textarea`, `Tooltip`, `Tabs`, etc. no existen y no se mencionan como si existieran).
- ✅ No se documenta ningún color que no esté en `tokens.css`.
- ✅ Se señalan explícitamente los tokens/props declarados pero sin uso real (`radius-xl`, `spacing-unit`, `container-max`, `headline-lg`, `headline-lg-mobile`, `body-lg`, `nexus-glow-primary`, prop `error` de `Input`/`Select`) para que un desarrollador no asuma que están "probados en producción" solo por estar declarados.
