import type { ReactNode } from 'react'

type TableWithDrawerLayoutProps = {
  main: ReactNode
  drawer?: ReactNode
}

/**
 * Layout genérico "tabla + panel de detalle lateral", literal del <main> de
 * Casos/code.html: `p-gutter flex gap-panel-gap`, con el aside de detalle
 * oculto por debajo de `xl` (comportamiento responsive explícito del propio
 * archivo, no una extrapolación). Reutilizable por cualquier módulo futuro
 * que siga el mismo patrón (Tracking, OSINT...).
 */
export function TableWithDrawerLayout({ main, drawer }: TableWithDrawerLayoutProps) {
  return (
    <div className="h-full overflow-hidden p-gutter flex gap-panel-gap">
      <div className="flex-1 flex flex-col relative overflow-hidden min-w-0">{main}</div>
      {drawer && (
        <aside className="w-96 flex-col overflow-hidden hidden xl:flex border-l border-primary/20 relative shrink-0">
          {drawer}
        </aside>
      )}
    </div>
  )
}
