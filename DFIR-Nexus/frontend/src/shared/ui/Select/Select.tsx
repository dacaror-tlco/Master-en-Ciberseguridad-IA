import { useId } from 'react'
import type { SelectHTMLAttributes } from 'react'
import { Icon } from '../Icon'

type SelectOption = { value: string; label: string }

type SelectProps = Omit<SelectHTMLAttributes<HTMLSelectElement>, 'children'> & {
  label?: string
  options: SelectOption[]
  error?: string
}

/**
 * Select genérico. Extrapolado del mismo contenedor visual que Input
 * (Casos/code.html no incluye un select propio): mismo fondo, borde y foco,
 * con un chevron a la derecha en vez de un icono a la izquierda.
 */
export function Select({ label, options, error, id, className = '', ...rest }: SelectProps) {
  const generatedId = useId()
  const selectId = id ?? generatedId
  return (
    <div className="flex flex-col gap-1 w-full">
      {label && (
        <label htmlFor={selectId} className="font-label-caps text-label-caps text-on-surface-variant">
          {label}
        </label>
      )}
      <div className="relative w-full">
        <select
          id={selectId}
          className={`w-full appearance-none bg-canvas border rounded font-mono-data text-mono-data
            text-on-surface focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary/50
            transition-all py-2 pl-4 pr-9 ${error ? 'border-error' : 'border-hairline'} ${className}`}
          {...rest}
        >
          {options.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
        <span className="absolute right-3 top-1/2 -translate-y-1/2 text-on-surface-variant pointer-events-none">
          <Icon name="expand_more" className="text-[18px]" />
        </span>
      </div>
      {error && <span className="text-error text-xs font-mono-data">{error}</span>}
    </div>
  )
}
