import { Button, Card } from '@/shared/ui'
import type { TimelineEvent } from '../api/timelineApi'

const ORIGIN_LABELS: Record<string, string> = {
  evidence: 'Evidencia',
  tracking: 'Tracking',
  osint: 'OSINT',
}

interface Props {
  event: TimelineEvent
  onClose: () => void
}

/**
 * Detalle del evento seleccionado en el gráfico. Se muestra debajo del
 * TimelineChart cuando el usuario hace click en un punto. En v2 pasará a
 * ser un drawer lateral (ver plan de Fase 3 en docs/AUDITORIA_TIMELINE.md).
 */
export function EventDetailCard({ event, onClose }: Props) {
  return (
    <Card
      title={`Evento #${event.orden}`}
      subtitle={ORIGIN_LABELS[event.origen_modulo] ?? event.origen_modulo}
      actions={
        <Button variant="ghost" size="sm" icon="close" onClick={onClose}>
          Cerrar
        </Button>
      }
    >
      <div className="p-6 flex flex-col gap-3 text-body-md">
        <div className="flex gap-4">
          <span className="text-on-surface-variant w-24 shrink-0">Fecha</span>
          <span className="text-on-surface">
            {new Date(event.fecha_hora).toLocaleString('es-ES')}
          </span>
        </div>
        <div className="flex gap-4">
          <span className="text-on-surface-variant w-24 shrink-0">Origen</span>
          <span className="text-on-surface">
            {ORIGIN_LABELS[event.origen_modulo] ?? event.origen_modulo}
            {' · '}
            <span className="text-on-surface-variant">id {event.origen_id}</span>
          </span>
        </div>
        <div className="flex gap-4">
          <span className="text-on-surface-variant w-24 shrink-0">Descripción</span>
          <span className="text-on-surface whitespace-pre-wrap">{event.descripcion}</span>
        </div>
      </div>
    </Card>
  )
}

export default EventDetailCard
