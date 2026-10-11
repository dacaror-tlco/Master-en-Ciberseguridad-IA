export type StatusTone = 'primary' | 'tertiary' | 'neutral' | 'muted' | 'error'

type StatusBadgeProps = {
  label: string
  tone: StatusTone
}

/*
 * Tonos literales/extrapolados de Casos/code.html:
 * - primary: tratamiento del badge "INVESTIGANDO" (bg-secondary-container).
 * - neutral: tratamiento de los badges "EN ESPERA" / "CERRADO".
 * - tertiary: extrapolado del botón "FILTROS" (borde/tono tertiary), no hay
 *   badge tertiary en el mock pero reutiliza el mismo lenguaje de color.
 * - muted: variante "neutro atenuado" (opacity-60), pedida explícitamente
 *   para el estado "archivado" sin introducir un color nuevo.
 * - error: añadido para severidad/riesgo (módulo OSINT y, en el propio
 *   modelo de datos de Nexus, `tracking_events.severidad`). Reutiliza el
 *   token `error` ya presente en tokens.css (el mismo que usa <Alert
 *   variant="error">), no introduce ningún color nuevo.
 */
const toneClasses: Record<StatusTone, string> = {
  primary: 'bg-secondary-container text-on-secondary-container',
  tertiary: 'bg-transparent text-tertiary border border-tertiary-container',
  neutral: 'bg-hairline text-on-surface-variant border border-outline-variant',
  muted: 'bg-hairline text-on-surface-variant border border-outline-variant opacity-60',
  error: 'bg-error-container/20 text-error border border-error/40',
}

/**
 * StatusBadge no sabe qué es un Case: solo representa una etiqueta + un tono.
 * El mapeo estado→tono vive en el módulo que lo consume (modules/cases).
 */
export function StatusBadge({ label, tone }: StatusBadgeProps) {
  return (
    <span
      className={`inline-block px-2 py-1 text-[10px] rounded font-label-caps tracking-wider ${toneClasses[tone]}`}
    >
      {label}
    </span>
  )
}
