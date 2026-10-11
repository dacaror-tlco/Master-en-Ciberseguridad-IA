import type { ButtonHTMLAttributes } from "react";
import { Icon } from "@/shared/ui/Icon";

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "ghost" | "danger";
  size?: "md" | "sm";
  /** Nombre de icono opcional a la izquierda del texto */
  icon?: string;
  loading?: boolean;
}

const VARIANT_CLASSES: Record<NonNullable<ButtonProps["variant"]>, string> = {
  primary: "bg-primary text-on-primary hover:bg-primary/90",
  ghost: "border border-tertiary-container text-tertiary nexus-glow-tertiary bg-transparent",
  danger: "border border-error text-error nexus-glow-error bg-transparent",
};

const SIZE_CLASSES: Record<NonNullable<ButtonProps["size"]>, string> = {
  md: "py-3 px-4",
  sm: "py-1.5 px-3",
};

/**
 * Único botón del sistema — toda acción clicable pasa por aquí.
 * Para navegación pura usa <Link> de React Router, Button no soporta href
 * (ver DESIGN_SYSTEM.md §7).
 */
export function Button({
  variant = "primary",
  size = "md",
  icon,
  loading = false,
  disabled,
  children,
  className = "",
  ...rest
}: ButtonProps) {
  return (
    <button
      disabled={disabled || loading}
      className={`inline-flex items-center justify-center gap-2 rounded font-label uppercase text-label-caps transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${VARIANT_CLASSES[variant]} ${SIZE_CLASSES[size]} ${className}`}
      {...rest}
    >
      {loading ? (
        <Icon name="progress_activity" className="animate-spin text-[16px]" />
      ) : (
        icon && <Icon name={icon} className="text-[16px]" />
      )}
      {children}
    </button>
  );
}
