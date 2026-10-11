import type { ReactNode } from "react";
import { Icon } from "@/shared/ui/Icon";

export interface AlertProps {
  variant?: "info" | "success" | "error";
  children: ReactNode;
}

const VARIANT_CONFIG: Record<NonNullable<AlertProps["variant"]>, { icon: string; classes: string }> = {
  info: { icon: "info", classes: "border-tertiary text-tertiary" },
  success: { icon: "check_circle", classes: "border-primary text-primary" },
  error: { icon: "warning", classes: "border-error text-error" },
};

/**
 * Mensaje contextual en línea — no es un toast/notificación flotante,
 * ese patrón no existe en el sistema. Deliberadamente solo 3 variantes
 * (sin "warning" separado de "error"), sin introducir ámbar
 * (ver DESIGN_SYSTEM.md §7).
 */
export function Alert({ variant = "info", children }: AlertProps) {
  const { icon, classes } = VARIANT_CONFIG[variant];
  return (
    <div className={`flex items-start gap-3 rounded border px-4 py-3 bg-canvas/40 ${classes}`}>
      <Icon name={icon} className="text-[18px] shrink-0 mt-0.5" />
      <div className="text-body-md text-on-surface">{children}</div>
    </div>
  );
}
