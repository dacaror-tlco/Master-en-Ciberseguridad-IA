import type { ButtonHTMLAttributes, ReactNode } from 'react'
import { Icon } from '../Icon'

type ButtonVariant = 'primary' | 'ghost' | 'danger'
type ButtonSize = 'md' | 'sm'

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant
  size?: ButtonSize
  icon?: string
  loading?: boolean
  children?: ReactNode
}

/*
 * Variantes literales de Casos/code.html:
 * - primary: botón "NUEVA INVESTIGACIÓN" del sidebar.
 * - ghost: botón "FILTROS" del panel de casos (borde/tono tertiary).
 * - danger: tratamiento del enlace "Cerrar Sesión" del sidebar (tono error).
 */
const variantClasses: Record<ButtonVariant, string> = {
  primary: 'bg-primary text-on-primary hover:bg-primary-fixed',
  ghost:
    'border border-tertiary-container text-tertiary hover:bg-tertiary-container/10 nexus-glow-tertiary',
  danger: 'border border-error text-error hover:bg-error-container/20 nexus-glow-error',
}

const sizeClasses: Record<ButtonSize, string> = {
  md: 'py-3 px-4',
  sm: 'py-1.5 px-3',
}

export function Button({
  variant = 'primary',
  size = 'md',
  icon,
  loading = false,
  disabled,
  className = '',
  children,
  ...rest
}: ButtonProps) {
  return (
    <button
      className={`inline-flex items-center justify-center gap-2 rounded font-label-caps text-label-caps
        transition-colors disabled:cursor-not-allowed disabled:opacity-50
        ${variantClasses[variant]} ${sizeClasses[size]} ${className}`}
      disabled={disabled || loading}
      {...rest}
    >
      {loading ? (
        <Icon name="progress_activity" className="animate-spin text-[16px]" />
      ) : icon ? (
        <Icon name={icon} className="text-[16px]" />
      ) : null}
      {children}
    </button>
  )
}
