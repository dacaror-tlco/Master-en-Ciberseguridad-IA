import type { ButtonHTMLAttributes } from 'react'
import { Icon } from '../Icon'

type IconButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  icon: string
  /** Obligatorio: sin texto visible, es lo único que anuncia el botón. */
  label: string
  size?: 'sm' | 'md'
}

/*
 * Botón de solo icono, sin borde ni relleno de color.
 *
 * `Button` no sirve para esto: su variante `ghost` trae borde y resplandor
 * porque nace del botón «FILTROS» de Casos/code.html, y eso en la cabecera de
 * un panel pesa más que el contenido. Los icon-buttons del header del mismo
 * diseño (la campana, el avatar) son planos, y este recoge ese tratamiento.
 *
 * `label` no es opcional a propósito: un botón cuyo único contenido es un icono
 * de fuente no dice nada a un lector de pantalla, y el icono tampoco se lee. Va
 * a `aria-label` y a `title`, así que también aparece como tooltip.
 */
export function IconButton({
  icon,
  label,
  size = 'md',
  className = '',
  ...rest
}: IconButtonProps) {
  return (
    <button
      type="button"
      aria-label={label}
      title={label}
      className={`inline-flex items-center justify-center rounded-full p-2 text-on-surface-variant
        transition-colors hover:bg-surface-container-high hover:text-on-surface
        disabled:cursor-not-allowed disabled:opacity-50 ${className}`}
      {...rest}
    >
      <Icon name={icon} className={size === 'sm' ? 'text-[16px]' : 'text-[20px]'} />
    </button>
  )
}
