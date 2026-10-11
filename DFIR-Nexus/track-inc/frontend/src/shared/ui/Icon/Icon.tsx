export interface IconProps {
  /** Nombre del icono de Material Symbols, p. ej. "folder_shared" */
  name: string;
  /** Variación FILL (relleno). Default: false (outline) */
  filled?: boolean;
  className?: string;
}

/**
 * Punto único de acceso a Material Symbols Outlined. Ningún otro
 * archivo debe escribir <span className="material-symbols-outlined">
 * directamente (ver DESIGN_SYSTEM.md §9).
 */
export function Icon({ name, filled = false, className = "" }: IconProps) {
  return (
    <span
      className={`material-symbols-outlined select-none ${className}`}
      style={{ fontVariationSettings: `'FILL' ${filled ? 1 : 0}` }}
      aria-hidden="true"
    >
      {name}
    </span>
  );
}
