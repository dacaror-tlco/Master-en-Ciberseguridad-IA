import type { StatusTone } from '@/shared/ui'

/**
 * Casos/code.html (fuente única del sistema visual, ver CLAUDE.md de Nexus)
 * no define un tono "warning/medio" propio: reutilizamos directamente los
 * tonos de <StatusBadge> (primary=verde/éxito, tertiary=azul/info,
 * error=rojo) para representar los 3 niveles de riesgo, en vez de inventar
 * un ámbar nuevo.
 */
export type RiskBucket = 'low' | 'medium' | 'high'

export type RiskLevel = {
  bucket: RiskBucket
  label: string
  colorVar: string
}

export function riskLevel(score: number): RiskLevel {
  if (score >= 60) return { bucket: 'high', label: 'RIESGO ALTO', colorVar: 'var(--color-error)' }
  if (score >= 30) return { bucket: 'medium', label: 'RIESGO MEDIO', colorVar: 'var(--color-tertiary)' }
  return { bucket: 'low', label: 'RIESGO BAJO', colorVar: 'var(--color-primary)' }
}

export function severityTone(severity: RiskBucket): StatusTone {
  if (severity === 'high') return 'error'
  if (severity === 'medium') return 'tertiary'
  return 'primary'
}
