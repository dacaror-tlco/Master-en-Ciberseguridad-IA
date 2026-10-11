import { useId, type InputHTMLAttributes } from "react";
import { Icon } from "@/shared/ui/Icon";

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  icon?: string;
  label?: string;
  error?: string;
}

/**
 * Campo de texto de una línea. Genera un id automático con useId() si no
 * se pasa uno explícito, para que label/input queden siempre asociados
 * (ver DESIGN_SYSTEM.md §7).
 */
export function Input({ icon, label, error, id, className = "", ...rest }: InputProps) {
  const autoId = useId();
  const inputId = id ?? autoId;

  return (
    <div className="flex flex-col gap-1.5">
      {label && (
        <label htmlFor={inputId} className="font-label text-label-caps uppercase text-on-surface-variant">
          {label}
        </label>
      )}
      <div className="relative">
        {icon && (
          <Icon name={icon} className="absolute left-3 top-1/2 -translate-y-1/2 text-[16px] text-on-surface-variant" />
        )}
        <input
          id={inputId}
          className={`w-full bg-canvas border rounded px-3 py-2 font-body text-mono-data text-on-surface placeholder:text-on-surface-variant focus:border-primary focus:ring-1 focus:ring-primary/50 outline-none ${icon ? "pl-9" : ""} ${error ? "border-error" : "border-hairline"} ${className}`}
          {...rest}
        />
      </div>
      {error && <span className="text-mono-data text-error">{error}</span>}
    </div>
  );
}
