import { useId, type SelectHTMLAttributes } from "react";
import { Icon } from "@/shared/ui/Icon";

export interface SelectOption {
  value: string;
  label: string;
}

export interface SelectProps extends Omit<SelectHTMLAttributes<HTMLSelectElement>, "children"> {
  label?: string;
  options: SelectOption[];
  error?: string;
}

/**
 * Selección de una opción entre una lista cerrada. Mismo contenedor
 * visual que Input (fondo canvas, borde hairline, foco primary), con
 * appearance-none e icono expand_more a la derecha. No existe en
 * Casos/code.html — extrapolación deliberada del lenguaje de Input
 * (ver DESIGN_SYSTEM.md §7).
 */
export function Select({ label, options, error, id, className = "", ...rest }: SelectProps) {
  const autoId = useId();
  const selectId = id ?? autoId;

  return (
    <div className="flex flex-col gap-1.5">
      {label && (
        <label htmlFor={selectId} className="font-label text-label-caps uppercase text-on-surface-variant">
          {label}
        </label>
      )}
      <div className="relative">
        <select
          id={selectId}
          className={`w-full appearance-none bg-canvas border rounded px-3 py-2 pr-9 font-body text-mono-data text-on-surface focus:border-primary focus:ring-1 focus:ring-primary/50 outline-none ${error ? "border-error" : "border-hairline"} ${className}`}
          {...rest}
        >
          {options.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
        <Icon name="expand_more" className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-[16px] text-on-surface-variant" />
      </div>
      {error && <span className="text-mono-data text-error">{error}</span>}
    </div>
  );
}
