import type { ReactNode } from "react";

export interface CardProps {
  title?: string;
  subtitle?: string;
  /** Nodo a la derecha de la cabecera (p. ej. botones de acción) */
  actions?: ReactNode;
  footer?: ReactNode;
  children: ReactNode;
  className?: string;
}

/**
 * Panel "glass" genérico. La cabecera solo se renderiza si hay title o
 * actions; el pie solo si hay footer. El cuerpo siempre va envuelto en
 * overflow-auto. No tiene flex-1 propio — pásalo explícitamente si hace
 * falta (ver DESIGN_SYSTEM.md §7).
 */
export function Card({ title, subtitle, actions, footer, children, className = "" }: CardProps) {
  const hasHeader = Boolean(title || actions);

  return (
    <div className={`nexus-glass-panel rounded-lg flex flex-col overflow-hidden ${className}`}>
      {hasHeader && (
        <div className="flex items-center justify-between px-gutter py-4 bg-surface-container-highest/30 border-b border-hairline shrink-0">
          <div>
            {title && <h2 className="font-headline text-headline-md text-on-surface">{title}</h2>}
            {subtitle && <p className="text-mono-data text-on-surface-variant mt-1">{subtitle}</p>}
          </div>
          {actions && <div className="flex items-center gap-2">{actions}</div>}
        </div>
      )}

      <div className="flex-1 overflow-auto">{children}</div>

      {footer && (
        <div className="px-gutter py-3 bg-surface-container-highest/50 border-t border-hairline shrink-0">
          {footer}
        </div>
      )}
    </div>
  );
}
