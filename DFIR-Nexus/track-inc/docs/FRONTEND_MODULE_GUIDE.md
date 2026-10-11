# Guía de desarrollo de módulos frontend — NEXUS

## 1. Objetivo

El frontend de NEXUS se ha desarrollado siguiendo un sistema de diseño común para que todos los módulos de la plataforma tengan una apariencia coherente.

Actualmente está implementado funcionalmente el módulo:

* Gestión de Casos

La arquitectura está preparada para incorporar posteriormente:

* OSINT y Fraude
* Tracking Post-Incidente
* Línea Temporal
* Generador de Informes

El objetivo es que cada compañero pueda desarrollar su módulo de forma independiente sin romper el diseño ni la arquitectura existente.

---

# 2. Tecnologías utilizadas

El frontend utiliza:

* React
* TypeScript
* Vite
* Tailwind CSS
* React Router
* Material Symbols
* Node.js / npm

La comunicación con el backend se realiza mediante HTTP utilizando la API REST de FastAPI.

El frontend no accede directamente a MySQL.

La arquitectura es:

```text
┌───────────────────────────┐
│          Usuario          │
└─────────────┬─────────────┘
              │
              ▼
┌───────────────────────────┐
│      React + Vite         │
│        Frontend           │
└─────────────┬─────────────┘
              │ HTTP/REST
              ▼
┌───────────────────────────┐
│        FastAPI            │
│         Backend           │
└─────────────┬─────────────┘
              │
              ▼
┌───────────────────────────┐
│          MySQL            │
└───────────────────────────┘
```

---

# 3. Estructura principal

La estructura actual es:

```text
frontend/
├── .env
├── .env.example
├── index.html
├── vite.config.ts
├── tsconfig.app.json
│
└── src/
    ├── app/
    │   └── router.tsx
    │
    ├── styles/
    │   ├── tokens.css
    │   ├── effects.css
    │   └── globals.css
    │
    ├── shared/
    │   ├── ui/
    │   │   ├── Button/
    │   │   ├── Input/
    │   │   ├── Select/
    │   │   ├── Card/
    │   │   ├── DataTable/
    │   │   ├── StatusBadge/
    │   │   ├── Modal/
    │   │   ├── Alert/
    │   │   └── Icon/
    │   │
    │   └── layout/
    │       ├── AppShell/
    │       ├── SideNav/
    │       ├── TopBar/
    │       └── TableWithDrawerLayout/
    │
    ├── modules/
    │   ├── cases/
    │   ├── osint/
    │   ├── tracking/
    │   ├── timeline/
    │   └── reports/
    │
    └── pages/
```

---

# 4. Regla fundamental de arquitectura

La arquitectura sigue una separación entre componentes compartidos y módulos.

La regla es:

```text
modules/*
     ↓
shared/*
```

Los módulos pueden utilizar componentes de `shared`.

Pero:

```text
shared/*
     X
modules/*
```

Los componentes compartidos NO deben importar componentes específicos de un módulo.

Además:

```text
modules/cases
      X
modules/osint
      X
modules/tracking
      X
modules/timeline
      X
modules/reports
```

Un módulo no debe depender directamente de otro módulo.

Esto permite que cinco personas puedan trabajar en paralelo.

---

# 5. Sistema de diseño

La pantalla:

```text
design/Casos/code.html
```

es la **fuente de verdad visual** del sistema.

No deben copiarse estilos de otras pantallas generadas por Stitch.

Los siguientes elementos deben mantenerse coherentes:

* colores
* tipografías
* tamaños
* radios
* bordes
* espaciado
* efectos
* glows
* iconografía
* estados
* estructura general

Los tokens se encuentran principalmente en:

```text
src/styles/tokens.css
```

Los efectos globales están en:

```text
src/styles/effects.css
```

Y los estilos generales:

```text
src/styles/globals.css
```

---

# 6. AppShell

`AppShell` es el contenedor principal de la aplicación.

Se encarga de montar:

```text
AppShell
├── SideNav
├── TopBar
└── contenido de la página
```

También aplica los efectos globales:

* ruido/grain
* investigation grid
* mist gradient
* scanline

Estos efectos deben existir únicamente una vez.

Un módulo nuevo NO debe volver a crear estos efectos.

Por ejemplo:

```tsx
<AppShell>
    <MiModulo />
</AppShell>
```

No se debe implementar otro fondo dentro de `MiModulo`.

---

# 7. Sidebar

El sidebar es compartido por toda la aplicación.

Actualmente contempla conceptualmente:

* Dashboard
* Gestión de Casos
* Evidencias
* OSINT
* Tracking
* Línea Temporal
* Informes
* Configuración

No todos tienen que estar implementados todavía.

Cuando un nuevo módulo se implemente, se añadirá su ruta correspondiente sin modificar innecesariamente el diseño del sidebar.

---

# 8. TopBar

El `TopBar` también es global.

Incluye los elementos visuales definidos por el diseño de Casos:

* buscador
* botones de acción
* avatar
* navegación superior

Los módulos no deben crear su propio TopBar salvo que exista una necesidad excepcional y justificada.

---

# 9. Componentes reutilizables

Antes de crear un componente nuevo, hay que comprobar si ya existe en:

```text
src/shared/ui/
```

Componentes disponibles:

```text
Button
Input
Select
Card
DataTable
StatusBadge
Modal
Alert
Icon
```

Por ejemplo, si OSINT necesita un botón:

NO crear:

```text
modules/osint/components/OSINTButton.tsx
```

si simplemente se trata de un botón estándar.

Debe utilizar:

```text
shared/ui/Button
```

---

# 10. Cuándo crear un componente propio

Un componente debe pertenecer al módulo cuando contiene lógica específica del dominio.

Por ejemplo:

```text
modules/osint/components/IndicatorResultCard
```

puede ser correcto porque representa información específica de OSINT.

En cambio:

```text
Button
Input
Modal
Badge
Table
```

son componentes genéricos y deben mantenerse en:

```text
shared/ui/
```

---

# 11. Layouts reutilizables

Existe:

```text
shared/layout/TableWithDrawerLayout
```

Este patrón está basado en la pantalla de Gestión de Casos.

Permite construir interfaces como:

```text
┌───────────────┬───────────────────────┬───────────────┐
│               │                       │               │
│   Sidebar     │      Contenido        │    Detalle    │
│               │      principal        │               │
│               │                       │               │
└───────────────┴───────────────────────┴───────────────┘
```

Un módulo nuevo debe reutilizar este layout si encaja con su funcionalidad.

Si no encaja, se puede crear un nuevo layout dentro de:

```text
shared/layout/
```

pero solamente si realmente es un patrón reutilizable.

---

# 12. Desarrollo de un nuevo módulo

Cada compañero debe trabajar dentro de:

```text
frontend/src/modules/<modulo>/
```

Por ejemplo, OSINT:

```text
frontend/src/modules/osint/
├── api/
├── types/
├── components/
└── pages/
```

Tracking:

```text
frontend/src/modules/tracking/
├── api/
├── types/
├── components/
└── pages/
```

Timeline:

```text
frontend/src/modules/timeline/
├── api/
├── types/
├── components/
└── pages/
```

Reports:

```text
frontend/src/modules/reports/
├── api/
├── types/
├── components/
└── pages/
```

---

# 13. Comunicación con el backend

Cada módulo debe comunicarse con FastAPI mediante los endpoints reales.

Antes de escribir código, Claude debe:

1. Revisar el backend.
2. Revisar `routes.py`.
3. Revisar `schemas.py`.
4. Revisar `models.py`.
5. Identificar los endpoints disponibles.
6. Identificar los métodos HTTP.
7. Identificar los parámetros.
8. Identificar el formato de respuesta.

Nunca se deben inventar endpoints.

Ejemplo:

```text
React
  │
  │ GET /cases
  ▼
FastAPI
  │
  ▼
SQLAlchemy
  │
  ▼
MySQL
```

---

# 14. Variables de entorno

La URL del backend se configura mediante:

```text
VITE_API_BASE_URL
```

Ejemplo:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Cada desarrollador debe crear su propio:

```text
frontend/.env
```

a partir de:

```text
frontend/.env.example
```

El `.env` no debe subirse a Git si contiene información sensible.

---

# 15. Responsive

El frontend debe mantener el comportamiento responsive definido por el sistema.

Reglas actuales:

### Desktop

Sidebar visible.

### Tablet

El contenido se adapta al espacio disponible.

### Mobile

El sidebar se oculta.

El buscador del TopBar también puede ocultarse en tamaños reducidos.

Los módulos deben comprobar al menos:

```text
375px
800px
1440px
1920px
```

No se deben introducir comportamientos responsive completamente diferentes sin necesidad.

---

# 16. Estados visuales

Los componentes interactivos utilizan estados consistentes:

```text
default
hover
focus
active
selected
disabled
loading
error
```

Los colores deben proceder de los tokens existentes.

No se deben introducir colores arbitrarios como:

```css
#ff0000
#00ff00
#123456
```

si el color no forma parte del sistema de diseño.

---

# 17. StatusBadge

Los estados de casos proceden directamente del backend:

```text
abierto
en_progreso
cerrado
archivado
```

Su representación visual es:

```text
abierto
→ ABIERTO
→ primary / verde

en_progreso
→ EN PROGRESO
→ tertiary

cerrado
→ CERRADO
→ neutro

archivado
→ ARCHIVADO
→ neutro atenuado
```

No introducir ámbar.

---

# 18. Regla para Claude Code

Cuando un compañero empiece un módulo nuevo, debe proporcionar a Claude Code:

1. `CLAUDE.md`
2. `FRONTEND_MODULE_GUIDE.md`
3. `frontend/src/styles/tokens.css`
4. `frontend/src/styles/effects.css`
5. `frontend/src/styles/globals.css`
6. `frontend/src/shared/`
7. El backend correspondiente
8. Los diseños de Stitch de su módulo

Claude debe considerar el frontend existente como una base que debe extenderse, no como un proyecto que debe rehacerse.

---

# 19. Prompt recomendado para un nuevo módulo

Antes de comenzar a programar, el compañero puede utilizar un prompt similar a este:

> Quiero implementar el módulo [NOMBRE DEL MÓDULO] dentro del frontend existente de NEXUS.
>
> Antes de escribir código, lee completamente:
>
> * CLAUDE.md
> * FRONTEND_MODULE_GUIDE.md
> * frontend/src/styles/tokens.css
> * frontend/src/styles/effects.css
> * frontend/src/styles/globals.css
>
> Inspecciona también:
>
> * frontend/src/shared/
> * frontend/src/modules/cases/
> * frontend/src/app/router.tsx
> * el backend correspondiente a este módulo
>
> Este frontend ya tiene un sistema de diseño implementado y NO debe reconstruirse.
>
> El módulo nuevo debe integrarse en la arquitectura existente.
>
> Respeta estrictamente:
>
> ```text
> modules/* → shared/*
> shared/* → nunca modules/*
> modules/* → nunca otro module
> ```
>
> Reutiliza todos los componentes genéricos existentes antes de crear otros nuevos.
>
> No crees botones, inputs, tablas, modales, badges o layouts duplicados si ya existe un componente equivalente en `shared/ui` o `shared/layout`.
>
> Utiliza exclusivamente los design tokens existentes.
>
> No introduzcas nuevos colores, tipografías, radios, sombras o efectos sin justificar técnicamente que son necesarios.
>
> Utiliza `AppShell`, `SideNav` y `TopBar` existentes.
>
> Mantén los efectos globales únicamente en `AppShell`.
>
> Antes de implementar la comunicación con el backend, inspecciona los endpoints reales del módulo y utiliza únicamente esos endpoints.
>
> No inventes endpoints.
>
> No modifiques el backend salvo que sea estrictamente imprescindible y explica previamente el motivo.
>
> Implementa únicamente el módulo [NOMBRE].
>
> No modifiques ni rehagas Gestión de Casos.
>
> Añade únicamente las rutas y componentes necesarios para el nuevo módulo.
>
> Antes de terminar:
>
> 1. Comprueba TypeScript.
> 2. Comprueba que Vite compila.
> 3. Comprueba las rutas.
> 4. Comprueba la comunicación con FastAPI.
> 5. Comprueba el responsive.
> 6. Comprueba que no existen errores de consola.
> 7. Comprueba que no se han introducido colores fuera de los tokens.
> 8. Comprueba que no existen dependencias entre módulos.
>
> Al finalizar, explica:
>
> * archivos creados;
> * archivos modificados;
> * componentes reutilizados;
> * endpoints utilizados;
> * rutas añadidas;
> * decisiones de diseño;
> * pruebas realizadas;
> * problemas encontrados.
>
> No implementes funcionalidades pertenecientes a otros módulos.

---

# 20. Flujo de trabajo recomendado

Cada compañero debería seguir este proceso:

```text
1. Actualizar rama
        ↓
2. Leer CLAUDE.md
        ↓
3. Leer FRONTEND_MODULE_GUIDE.md
        ↓
4. Revisar shared/
        ↓
5. Revisar backend del módulo
        ↓
6. Revisar diseños de Stitch
        ↓
7. Pedir a Claude análisis
        ↓
8. Revisar propuesta
        ↓
9. Implementar
        ↓
10. Probar
        ↓
11. Commit
        ↓
12. Pull Request
        ↓
13. development
        ↓
14. production
```

---

# 21. Regla importante para trabajar en equipo

No se deben modificar directamente los componentes compartidos para solucionar una necesidad específica de un módulo.

Si OSINT necesita algo que solo sirve para OSINT:

```text
modules/osint/components/
```

Si Timeline necesita un componente genérico que podría utilizar cualquier módulo:

```text
shared/ui/
```

La decisión de promover un componente a `shared/` debe hacerse únicamente cuando realmente sea reutilizable.

Esto evita que cinco desarrolladores modifiquen simultáneamente los mismos archivos.

---

# 22. Objetivo final

La finalidad de esta arquitectura es que la incorporación de un nuevo módulo sea:

```text
Nuevo módulo
     │
     ├── API
     ├── Types
     ├── Components
     └── Pages
             │
             ▼
        Shared UI
             │
             ▼
         AppShell
             │
             ▼
        Diseño NEXUS
```

De esta forma, cada compañero puede desarrollar su módulo de forma relativamente independiente mientras toda la aplicación mantiene una única identidad visual y arquitectónica.
