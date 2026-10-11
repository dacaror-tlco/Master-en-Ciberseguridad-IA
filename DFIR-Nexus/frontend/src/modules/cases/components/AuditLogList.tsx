import { Icon } from '@/shared/ui'
import type { AccionAuditoria, AuditLogEntry } from '../types'

const ETIQUETAS: Record<AccionAuditoria, string> = {
  case_creado: 'Caso creado',
  case_actualizado: 'Caso actualizado',
  case_estado_cambiado: 'Cambio de estado',
  case_eliminado: 'Caso eliminado',
  evidence_creada: 'Evidencia añadida',
  evidence_actualizada: 'Evidencia actualizada',
  evidence_eliminada: 'Evidencia eliminada',
  osint_vinculacion_cambiada: 'Vinculación OSINT',
}

const ICONOS: Record<AccionAuditoria, string> = {
  case_creado: 'add_circle',
  case_actualizado: 'edit',
  case_estado_cambiado: 'sync_alt',
  case_eliminado: 'delete_forever',
  evidence_creada: 'note_add',
  evidence_actualizada: 'edit_note',
  evidence_eliminada: 'delete',
  osint_vinculacion_cambiada: 'travel_explore',
}

const formatDate = (iso: string) =>
  new Date(iso).toLocaleString('es-ES', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })

function describirDetalle(entrada: AuditLogEntry): string | null {
  const detalle = entrada.detalle
  if (!detalle) return null
  if (entrada.accion === 'case_estado_cambiado' && 'de' in detalle && 'a' in detalle) {
    return `${detalle.de} → ${detalle.a}`
  }
  if (entrada.accion === 'osint_vinculacion_cambiada') {
    const tipo = typeof detalle.case_type === 'string' ? detalle.case_type : '?'
    const id = typeof detalle.source_id === 'number' ? detalle.source_id : '?'
    const sujeto = typeof detalle.subject_value === 'string' ? ` "${detalle.subject_value}"` : ''
    const de = detalle.de === null || detalle.de === undefined ? 'sin caso' : `caso #${detalle.de}`
    const a = detalle.a === null || detalle.a === undefined ? 'sin caso' : `caso #${detalle.a}`
    return `${tipo} #${id}${sujeto}: ${de} → ${a}`
  }
  if ('campos' in detalle && Array.isArray(detalle.campos)) {
    return detalle.campos.join(', ')
  }
  return null
}

type AuditLogListProps = {
  entries: AuditLogEntry[]
  loading: boolean
}

/**
 * Rastro de auditoría del caso (GET /cases/{id}/auditoria): qué ocurrió,
 * cuándo, y sobre qué (caso o evidencia concreta). `actor` es hoy siempre
 * "api" — el proyecto no tiene autenticación (ver CLAUDE.md) — así que
 * deliberadamente no se muestra como si identificara a una persona real.
 */
export function AuditLogList({ entries, loading }: AuditLogListProps) {
  if (loading) {
    return <p className="text-on-surface-variant text-xs font-mono-data">Cargando auditoría...</p>
  }
  if (entries.length === 0) {
    return <p className="text-on-surface-variant text-xs font-mono-data">Sin actividad registrada.</p>
  }
  return (
    <ul className="space-y-2">
      {entries.map((entrada) => {
        const detalle = describirDetalle(entrada)
        return (
          <li key={entrada.id} className="flex items-start gap-2 text-[11px]">
            <Icon name={ICONOS[entrada.accion]} className="text-tertiary text-[14px] mt-0.5 shrink-0" />
            <div className="min-w-0">
              <p className="font-body-md text-on-surface">
                {ETIQUETAS[entrada.accion]}
                {detalle && <span className="text-on-surface-variant"> · {detalle}</span>}
                {entrada.evidence_id !== null && (
                  <span className="text-on-surface-variant"> · evidencia #{entrada.evidence_id}</span>
                )}
              </p>
              <p className="font-mono-data text-on-surface-variant/70">{formatDate(entrada.creado_en)}</p>
            </div>
          </li>
        )
      })}
    </ul>
  )
}
