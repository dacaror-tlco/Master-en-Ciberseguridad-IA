import { Icon } from '../../ui'

/**
 * Header/TopBar genérico. Literal del header de Casos/code.html: buscador,
 * icon-buttons y avatar. El buscador y las notificaciones son decorativos en
 * esta fase: no existe backend de búsqueda global ni de notificaciones, y no
 * se ha solicitado implementarlos todavía.
 */
export function TopBar() {
  return (
    <header className="bg-surface-container-low/80 backdrop-blur-md border-b border-hairline flex justify-between items-center w-full px-gutter h-16 z-40 shrink-0">
      <div className="flex items-center gap-4 w-1/3">
        <h2 className="font-headline-md text-headline-md text-primary tracking-tighter md:hidden">NEXUS</h2>
        <div className="relative w-full max-w-md hidden md:block">
          <span className="absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant text-sm">
            <Icon name="search" className="text-[16px]" />
          </span>
          <input
            className="w-full bg-canvas border border-hairline rounded px-9 py-2 font-mono-data text-mono-data
              text-on-surface placeholder-on-surface-variant focus:outline-none focus:border-primary
              focus:ring-1 focus:ring-primary/50 transition-all"
            placeholder="ID de Caso, Nombre, Entidad..."
            type="text"
            disabled
          />
        </div>
      </div>
      <div className="flex items-center gap-4">
        <button
          type="button"
          disabled
          className="text-on-surface-variant hover:bg-surface-container-high transition-colors duration-200 p-2 rounded-full disabled:cursor-not-allowed disabled:opacity-60"
        >
          <Icon name="notifications" />
        </button>
        <button
          type="button"
          disabled
          className="text-on-surface-variant hover:bg-surface-container-high transition-colors duration-200 p-2 rounded-full hidden md:block disabled:cursor-not-allowed disabled:opacity-60"
        >
          <Icon name="fingerprint" />
        </button>
        <div className="w-8 h-8 rounded-full border border-outline-variant overflow-hidden ml-2 bg-surface-container-highest flex items-center justify-center">
          <Icon name="person" className="text-on-surface-variant text-[18px]" />
        </div>
      </div>
    </header>
  )
}
