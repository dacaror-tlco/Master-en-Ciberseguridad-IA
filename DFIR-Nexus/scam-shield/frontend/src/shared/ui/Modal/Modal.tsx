import { useEffect } from 'react'
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
 */
export function Modal({ open, onClose, title, children, footer }: ModalProps) {
  useEffect(() => {
    if (!open) return
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [open, onClose])

  if (!open) return null

  return (
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
    </div>
  )
}
