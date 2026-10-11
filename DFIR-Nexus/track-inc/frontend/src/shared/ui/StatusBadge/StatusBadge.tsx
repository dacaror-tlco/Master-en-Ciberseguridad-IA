export type StatusBadgeTone = "primary" | "tertiary" | "neutral" | "muted";

export interface StatusBadgeProps {
  label: string;
  tone: StatusBadgeTone;
}

const TONE_CLASSES: Record<StatusBadgeTone, string> = {
  primary: "bg-secondary-container text-on-secondary-container",
  tertiary: "bg-transparent border border-tertiary-container text-tertiary",
  neutral: "bg-hairline text-on-surface-variant border border-outline-variant",
  muted: "bg-hairline text-on-surface-variant border border-outline-variant opacity-60",
};

/**
 * Representa visualmente un estado con una etiqueta y un tono, sin
 * conocer el dominio (no sabe qué es un "Case" o un "TrackingEvent").
 * Quien decide el tono es el módulo consumidor, vía su propio mapeo
 * (ver DESIGN_SYSTEM.md §7 — patrón CaseStatusMap).
 */
export function StatusBadge({ label, tone }: StatusBadgeProps) {
  return (
    <span className={`inline-flex items-center rounded px-2 py-0.5 font-label text-label-caps uppercase ${TONE_CLASSES[tone]}`}>
      {label}
    </span>
  );
}
