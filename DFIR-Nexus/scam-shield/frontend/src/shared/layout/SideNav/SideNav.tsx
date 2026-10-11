import { Link, useLocation } from 'react-router-dom'
import { Icon } from '../../ui'

type NavItem = {
  label: string
  icon: string
  /** Ruta real. `null` = elemento presente en el diseño pero sin página funcional en esta fase. */
  path: string | null
}

/*
 * Orden y etiquetas canónicos: mismo sidebar que la rama modulo-casos
 * (literal de Casos/code.html), pero desde el punto de vista de este
 * módulo (scam-shield = Módulo 2, OSINT y Fraude): aquí "OSINT y Fraude"
 * es la única entrada funcional, y el resto (incluido "Casos", que en
 * modulo-casos sí funciona) queda deshabilitado hasta que las ramas se
 * fusionen de verdad. Mantener el mismo orden/etiquetas en ambas ramas
 * facilita esa fusión futura sin sorpresas visuales.
 */
const NAV_ITEMS: NavItem[] = [
  { label: 'Dashboard', icon: 'dashboard', path: null },
  { label: 'Casos', icon: 'folder_shared', path: null },
  { label: 'Evidencias', icon: 'inventory_2', path: null },
  { label: 'OSINT y Fraude', icon: 'public', path: '/osint' },
  { label: 'Tracking Post-Incidente', icon: 'radar', path: null },
  { label: 'Línea Temporal', icon: 'timeline', path: null },
  { label: 'Informes', icon: 'description', path: null },
  { label: 'Configuración', icon: 'settings', path: null },
]

export function SideNav() {
  const location = useLocation()
  // Solo el primer ítem que coincide con la ruta actual se marca como activo,
  // para evitar que "Casos" y "Evidencias" (que comparten /cases en esta
  // fase) aparezcan resaltados los dos a la vez.
  const activeLabel = NAV_ITEMS.find(
    (item) => item.path !== null && location.pathname.startsWith(item.path),
  )?.label

  return (
    <nav className="bg-surface-container-low h-full w-64 flex-col py-margin-safe border-r border-hairline relative z-10 hidden md:flex shrink-0">
      <div className="px-gutter mb-8">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-8 h-8 rounded bg-primary flex items-center justify-center">
            <Icon name="fingerprint" filled className="text-on-primary" />
          </div>
          <h1 className="font-headline-md text-headline-md text-primary leading-none">NEXUS</h1>
        </div>
        <p className="font-mono-data text-mono-data text-on-surface-variant text-xs opacity-70">
          Forensic Assistant
        </p>
      </div>

      <div className="px-gutter mb-8">
        <Link
          to="/osint"
          className="w-full bg-primary text-on-primary font-label-caps text-label-caps py-3 px-4 rounded flex items-center justify-center gap-2 hover:bg-primary-fixed transition-colors"
        >
          <Icon name="add" className="text-sm" />
          NUEVO ANÁLISIS
        </Link>
      </div>

      <div className="flex-1 overflow-y-auto px-4 space-y-1">
        {NAV_ITEMS.map((item) => {
          const isActive = item.label === activeLabel

          if (item.path === null) {
            return (
              <span
                key={item.label}
                title="Próximamente"
                className="flex items-center gap-3 px-4 py-3 rounded text-on-surface-variant opacity-40 cursor-not-allowed font-label-caps text-label-caps"
              >
                <Icon name={item.icon} />
                {item.label}
              </span>
            )
          }

          return (
            <Link
              key={item.label}
              to={item.path}
              className={`flex items-center gap-3 px-4 py-3 rounded font-label-caps text-label-caps transition-all ${
                isActive
                  ? 'text-primary border-l-2 border-primary bg-secondary-container/10 translate-x-1'
                  : 'text-on-surface-variant hover:text-primary hover:bg-surface-container-highest'
              }`}
            >
              <Icon name={item.icon} filled={isActive} />
              {item.label}
            </Link>
          )
        })}
      </div>

      <div className="mt-auto px-4 pt-4 border-t border-hairline space-y-1">
        <span className="flex items-center gap-3 px-4 py-3 rounded text-on-surface-variant opacity-60 cursor-not-allowed font-label-caps text-label-caps">
          <Icon name="help" />
          Ayuda
        </span>
        <span className="flex items-center gap-3 px-4 py-3 rounded text-error opacity-60 cursor-not-allowed font-label-caps text-label-caps">
          <Icon name="logout" />
          Cerrar Sesión
        </span>
      </div>
    </nav>
  )
}
