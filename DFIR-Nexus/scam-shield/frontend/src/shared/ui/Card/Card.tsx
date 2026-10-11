import type { ReactNode } from 'react'

type CardProps = {
  title?: ReactNode
  subtitle?: ReactNode
  actions?: ReactNode
  footer?: ReactNode
  children?: ReactNode
  className?: string
}

/**
 * Panel "glass" genérico. Literal del panel de la tabla de casos y del aside
 * de detalle en Casos/code.html: sin sombra, borde bicolor, cabecera con
 * fondo ligeramente más claro.
 */
export function Card({ title, subtitle, actions, footer, children, className = '' }: CardProps) {
  return (
    <div className={`nexus-glass-panel rounded-lg flex flex-col overflow-hidden ${className}`}>
      {(title || actions) && (
        <div className="px-6 py-4 border-b border-hairline bg-surface-container-highest/30 flex justify-between items-center shrink-0">
          <div>
            {title && <h2 className="font-headline-md text-headline-md text-on-surface mb-1">{title}</h2>}
            {subtitle && (
              <p className="font-mono-data text-mono-data text-on-surface-variant opacity-70">{subtitle}</p>
            )}
          </div>
          {actions && <div className="flex gap-2">{actions}</div>}
        </div>
      )}
      <div className="flex-1 overflow-auto">{children}</div>
      {footer && (
        <div className="p-4 bg-surface-container-highest/50 border-t border-hairline shrink-0">{footer}</div>
      )}
    </div>
  )
}
