import { Link, Outlet, useLocation } from 'react-router-dom'
import { Icon } from '@/shared/ui'
import { CasoActivoProvider } from '../state/CasoActivoContext'
import { SelectionProvider } from '../state/SelectionContext'
import { CasoActivoSelector } from './CasoActivoSelector'

type Tab = {
  label: string
  icon: string
  path: string
}

const TABS: Tab[] = [
  { label: 'Dominio', icon: 'language', path: 'domain' },
  { label: 'Email', icon: 'mail', path: 'email' },
  { label: 'Wallet', icon: 'account_balance_wallet', path: 'wallet' },
  { label: 'Typosquatting', icon: 'content_copy', path: 'typosquatting' },
  { label: 'Teléfono', icon: 'call', path: 'phone' },
  { label: 'CNMV', icon: 'gavel', path: 'cnmv' },
  { label: 'Imagen', icon: 'image', path: 'image' },
  { label: 'IP', icon: 'router', path: 'ip' },
  { label: 'Monitorización', icon: 'notifications', path: 'monitoring' },
  { label: 'Casos guardados', icon: 'folder_open', path: 'cases' },
  { label: 'Informe', icon: 'description', path: 'report' },
]

/**
 * Sub-navegación interna del módulo OSINT y Fraude. En Nexus el SideNav es
 * por módulo (una sola entrada "OSINT y Fraude"), así que los paneles de
 * scam-shield (antes pestañas del sidebar propio) se muestran aquí como
 * pestañas dentro del área de contenido del módulo.
 *
 * Dos estados compartidos por todo el módulo, y por eso viven aquí y no en
 * una página:
 *
 * - `SelectionProvider` — los casos marcados, que "Casos guardados" elige e
 *   "Informe" consume.
 * - `CasoActivoProvider` — el expediente de Nexus al que se atribuyen los
 *   análisis nuevos, con su selector encima de las pestañas. Es lo que llena
 *   `osint_findings.case_id`, sin lo cual un análisis no llega al informe
 *   pericial ni a la cronología de ningún caso.
 */
export function OsintLayout() {
  const location = useLocation()

  return (
    <CasoActivoProvider>
      <div className="h-full flex flex-col overflow-hidden">
        <CasoActivoSelector />
        <div className="border-b border-hairline px-gutter shrink-0 overflow-x-auto">
          <nav className="flex gap-1 w-max">
            {TABS.map((tab) => {
              const isActive = location.pathname.startsWith(`/osint/${tab.path}`)
              return (
                <Link
                  key={tab.label}
                  to={`/osint/${tab.path}`}
                  className={`flex items-center gap-2 px-4 py-3 font-label-caps text-label-caps whitespace-nowrap border-b-2 transition-colors ${
                    isActive
                      ? 'text-primary border-primary'
                      : 'text-on-surface-variant border-transparent hover:text-primary hover:border-hairline'
                  }`}
                >
                  <Icon name={tab.icon} filled={isActive} className="text-[16px]" />
                  {tab.label}
                </Link>
              )
            })}
          </nav>
        </div>
        <div className="flex-1 overflow-hidden">
          <SelectionProvider>
            <Outlet />
          </SelectionProvider>
        </div>
      </div>
    </CasoActivoProvider>
  )
}
