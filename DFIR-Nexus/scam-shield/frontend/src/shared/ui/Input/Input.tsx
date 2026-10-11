import { useId } from 'react'
import type { InputHTMLAttributes } from 'react'
import { Icon } from '../Icon'

type InputProps = InputHTMLAttributes<HTMLInputElement> & {
  icon?: string
  label?: string
  error?: string
}

/**
 * Input de texto genérico. Estilo literal del buscador de Casos/code.html:
 * fondo canvas, borde hairline, foco en primary con ring.
 */
export function Input({ icon, label, error, id, className = '', ...rest }: InputProps) {
  const generatedId = useId()
  const inputId = id ?? generatedId
  return (
    <div className="flex flex-col gap-1 w-full">
      {label && (
        <label htmlFor={inputId} className="font-label-caps text-label-caps text-on-surface-variant">
          {label}
        </label>
      )}
      <div className="relative w-full">
        {icon && (
          <span className="absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant text-sm pointer-events-none">
            <Icon name={icon} className="text-[16px]" />
          </span>
        )}
        <input
          id={inputId}
          className={`w-full bg-canvas border rounded font-mono-data text-mono-data text-on-surface
            placeholder-on-surface-variant focus:outline-none focus:border-primary focus:ring-1
            focus:ring-primary/50 transition-all py-2 ${icon ? 'pl-9 pr-4' : 'px-4'}
            ${error ? 'border-error' : 'border-hairline'} ${className}`}
          {...rest}
        />
      </div>
      {error && <span className="text-error text-xs font-mono-data">{error}</span>}
    </div>
  )
}
