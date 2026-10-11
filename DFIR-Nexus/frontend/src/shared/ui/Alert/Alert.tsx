import type { ReactNode } from 'react'
import { Icon } from '../Icon'

type AlertVariant = 'info' | 'success' | 'error'

type AlertProps = {
  variant?: AlertVariant
  children: ReactNode
}

/*
 * Casos/code.html no define un componente de alerta, pero sí el lenguaje de
 * color que se reutiliza aquí: el tag "ALTA / CRÍTICA" (icono "warning" +
 * texto en `error`) y los tokens *-container ya presentes en su propia
 * escala de color. No se introduce ningún tono ajeno al archivo de origen.
 */
const variantConfig: Record<AlertVariant, { classes: string; icon: string; iconColor: string }> = {
  info: { classes: 'border-tertiary bg-tertiary-container/10', icon: 'info', iconColor: 'text-tertiary' },
  success: {
    classes: 'border-primary bg-secondary-container/10',
    icon: 'check_circle',
    iconColor: 'text-primary',
  },
  error: { classes: 'border-error bg-error-container/10', icon: 'warning', iconColor: 'text-error' },
}

export function Alert({ variant = 'info', children }: AlertProps) {
  const config = variantConfig[variant]
  return (
    <div className={`flex items-start gap-3 border-l-2 rounded p-3 font-body-md text-body-md ${config.classes}`}>
      <Icon name={config.icon} filled className={`${config.iconColor} text-[18px] mt-0.5`} />
      <div className="text-on-surface">{children}</div>
    </div>
  )
}
