import { useEffect } from 'react'
import { registrarModalAbierto } from './modalAbierto'
import { createPortal } from 'react-dom'
import type { ReactNode } from 'react'
import { Icon } from '../Icon'

type ModalProps = {
  open: boolean
  onClose: () => void
  title: string
  children: ReactNode
  footer?: ReactNode
}

/**
 * Modal genérico. Casos/code.html no incluye un modal propio; se extrapola
 * del nivel de elevación 2 ("Modals/Popovers") documentado en DESIGN.md,
 * que no entra en conflicto con los tokens de Casos: mismo glass-panel,
 * con backdrop-filter: blur para diferenciarlo de un Card estático.
 *
 * Se monta con `createPortal` sobre `document.body`, y eso **no es opcional**.
 * El modal se declara dentro de la página, que vive en
 * `<main class="relative z-10">`, hermano del `TopBar` (`z-40`) dentro del
 * mismo contenedor de AppShell. Un `z-index` solo compite dentro de su
 * contexto de apilamiento, así que el `z-50` del modal quedaba atrapado bajo
 * ese `z-10` y la barra superior le tapaba la cabecera: en el modal de
 * «Generar informe» no se leía el título ni se podía pulsar la X. Subir el
 * `z-index` no lo arregla —ningún valor escapa del contexto padre—; sacarlo
 * del árbol, sí.
 */
export function Modal({ open, onClose, title, children, footer }: ModalProps) {
  useEffect(() => {
    if (!open) return

    /*
     * Se apunta como capa abierta: los paneles de detalle también cierran con
     * Escape y necesitan saber que hay algo por encima (ver `modalAbierto.ts`).
     */
    const darDeBaja = registrarModalAbierto()

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKeyDown)

    return () => {
      darDeBaja()
      window.removeEventListener('keydown', onKeyDown)
    }
  }, [open, onClose])

  if (!open) return null

  return createPortal(
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-canvas/80 backdrop-blur-sm p-4"
      onClick={onClose}
    >
      <div
        className="nexus-glass-panel backdrop-blur-md rounded-lg w-full max-w-lg flex flex-col max-h-[90vh]"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="px-6 py-4 border-b border-hairline bg-surface-container-highest/30 flex justify-between items-center shrink-0">
          <h2 className="font-headline-md text-headline-md text-on-surface">{title}</h2>
          <button
            type="button"
            onClick={onClose}
            className="text-on-surface-variant hover:text-on-surface transition-colors"
            aria-label="Cerrar"
          >
            <Icon name="close" />
          </button>
        </div>
        <div className="flex-1 overflow-auto p-6">{children}</div>
        {footer && (
          <div className="p-4 border-t border-hairline bg-surface-container-highest/50 flex justify-end gap-2 shrink-0">
            {footer}
          </div>
        )}
      </div>
    </div>,
    document.body,
  )
}
