import type { StatusTone } from '@/shared/ui'
import type { EstadoCaso } from '../types'

/**
 * Único lugar del módulo Casos donde se traduce el enum real del backend
 * (abierto/en_progreso/cerrado/archivado, ver CLAUDE.md) a una etiqueta y un
 * tono visual. Mapeo aprobado explícitamente:
 *   abierto      -> ABIERTO      -> primary (verde)
 *   en_progreso  -> EN PROGRESO  -> tertiary
 *   cerrado      -> CERRADO      -> neutral (outline-variant)
 *   archivado    -> ARCHIVADO    -> muted (neutro atenuado)
 * No se introduce ningún color ajeno a los tokens de Casos/code.html.
 */
export const CASE_STATUS_MAP: Record<EstadoCaso, { label: string; tone: StatusTone }> = {
  abierto: { label: 'ABIERTO', tone: 'primary' },
  en_progreso: { label: 'EN PROGRESO', tone: 'tertiary' },
  cerrado: { label: 'CERRADO', tone: 'neutral' },
  archivado: { label: 'ARCHIVADO', tone: 'muted' },
}
