import type { ReactNode } from 'react'
import { createPortal } from 'react-dom'
import { useMediaQuery } from '../../hooks'

type TableWithDrawerLayoutProps = {
  main: ReactNode
  drawer?: ReactNode
  /**
   * Cierra el detalle. Solo tiene efecto por debajo de `xl`: el overlay a
   * pantalla completa lo usa para cerrarse al pulsar fuera del panel. En
   * `xl+` no hace falta — el propio `drawer` ya trae su cierre, si lo
   * necesita (ver `CaseDetailDrawer`/`ReportDetailDrawer`).
   */
  onCloseDrawer?: () => void
}

/**
 * Layout genérico "tabla + panel de detalle lateral", literal del <main> de
 * Casos/code.html: `p-gutter flex gap-panel-gap`. Reutilizable por cualquier
 * módulo que siga el mismo patrón (Tracking, OSINT...).
 *
 * En `xl+` (≥1280px) el detalle es el aside lateral de siempre. Por debajo,
 * el mismo `drawer` —sin duplicarlo— se muestra sobre un overlay a pantalla
 * completa con fondo, en vez de desaparecer. Es el mismo nodo en los dos
 * casos a propósito: `CaseDetailDrawer` y `ReportDetailDrawer` ya son
 * paneles autocontenidos con su propia cabecera, botón de cierre y pie de
 * acciones — envolverlos además en el `Modal` genérico añadiría una segunda
 * cabecera redundante encima de la suya. Por el mismo motivo, cierran con
 * Escape gratis: los dos ya llaman a `useCerrarConEscape(onClose)` por
 * dentro.
 *
 * El overlay se monta con `createPortal` sobre `document.body`, no en su
 * sitio natural del árbol — igual que `Modal` y por la misma razón exacta
 * (ver el comentario de `Modal.tsx`): esta página vive dentro de
 * `<main class="relative z-10">` (AppShell), que es SU PROPIO contexto de
 * apilamiento. Un overlay declarado aquí dentro con `z-40` compite contra el
 * `TopBar` (`z-40`) solo dentro de ese `z-10`, así que el `TopBar` —que está
 * fuera, al mismo nivel que `<main>`— seguía tapando el botón de cerrar del
 * panel (confirmado con Playwright/Firefox: el clic quedaba interceptado por
 * la cabecera). Sacarlo del árbol con un portal es lo único que de verdad
 * lo pone por encima.
 */
export function TableWithDrawerLayout({ main, drawer, onCloseDrawer }: TableWithDrawerLayoutProps) {
  const escritorio = useMediaQuery('(min-width: 1280px)')

  return (
    <div className="h-full overflow-hidden p-gutter flex gap-panel-gap">
      <div className="flex-1 flex flex-col relative overflow-hidden min-w-0">{main}</div>

      {escritorio && drawer && (
        <aside className="w-96 flex-col overflow-hidden flex border-l border-primary/20 relative shrink-0">
          {drawer}
        </aside>
      )}

      {!escritorio && drawer && createPortal(
        <div
          className="fixed inset-0 z-40 bg-canvas/80 backdrop-blur-sm flex justify-end"
          onClick={() => onCloseDrawer?.()}
        >
          <div
            className="w-full sm:w-[420px] h-full sm:p-4"
            onClick={(event) => event.stopPropagation()}
          >
            {drawer}
          </div>
        </div>,
        document.body,
      )}
    </div>
  )
}
