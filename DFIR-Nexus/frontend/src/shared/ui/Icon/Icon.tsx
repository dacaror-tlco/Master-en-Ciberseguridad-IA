type IconProps = {
  /** Nombre del icono de Material Symbols Outlined (p. ej. "folder_shared"). */
  name: string
  /** Estado relleno (font-variation-settings 'FILL' 1), usado en Casos para navegación activa. */
  filled?: boolean
  className?: string
}

/**
 * Wrapper único sobre Material Symbols Outlined, la iconografía literal de
 * Casos/code.html. Ningún componente debe usar <span class="material-symbols-outlined">
 * directamente: todos pasan por aquí para mantener un único punto de control.
 */
export function Icon({ name, filled = false, className = '' }: IconProps) {
  return (
    <span
      className={`material-symbols-outlined select-none ${className}`}
      style={{ fontVariationSettings: `'FILL' ${filled ? 1 : 0}` }}
      aria-hidden="true"
    >
      {name}
    </span>
  )
}
