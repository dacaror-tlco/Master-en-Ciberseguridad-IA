import { useEffect, useState } from 'react'
import { Alert, Button, Card, DataTable, Input, type DataTableColumn } from '@/shared/ui'
import { getTimelineEvents, refreshTimeline, type TimelineEvent } from '../api/timelineApi'
import { TimelineChart } from '../components/TimelineChart'
import { EventDetailCard } from '../components/EventDetailCard'

type ViewMode = 'table' | 'chart'

function formatRelativeTime(then: Date, now: Date): string {
  const s = Math.max(0, Math.floor((now.getTime() - then.getTime()) / 1000))
  if (s < 5) return 'ahora mismo'
  if (s < 60) return `hace ${s} s`
  const m = Math.floor(s / 60)
  if (m < 60) return `hace ${m} min`
  const h = Math.floor(m / 60)
  if (h < 24) return `hace ${h} h`
  return `hace ${Math.floor(h / 24)} d`
}

/**
 * Fase 2 (auditoría Módulo 4):
 * - Renombrado "Refrescar" → "Recalcular" (describe lo que hace: POST
 *   que reconstruye la timeline desde las 3 fuentes, no una simple
 *   recarga de página).
 * - Indicador "Última actualización: hace X" en la cabecera, que se
 *   actualiza solo cada 10 s.
 * - Auto-carga silenciosa al cambiar el ID del caso (debounce 500 ms):
 *   el usuario ve datos sin pulsar "Cargar".
 * - Badge "Actualizando…" mientras corre el recálculo.
 * - Errores del backend ahora se muestran con el `detail` real (H-12
 *   estaba en `timelineApi.ts`, ya resuelto allí).
 *
 * Fase 3 (visualización): alterna entre tabla y un gráfico SVG propio
 * con carriles por origen (`viewMode`); al seleccionar un evento en el
 * gráfico se muestra su detalle debajo (`selectedEvent`). `selectedEvent`
 * se limpia en cada carga/recálculo para no dejar seleccionado un evento
 * que ya no está en el resultado nuevo.
 */
export function TimelinePage() {
  const [caseId, setCaseId] = useState<string>('')
  const [events, setEvents] = useState<TimelineEvent[]>([])
  const [loading, setLoading] = useState(false) // GET en curso (explícito)
  const [refreshing, setRefreshing] = useState(false) // POST en curso
  const [lastLoaded, setLastLoaded] = useState<Date | null>(null)
  const [now, setNow] = useState(() => new Date())
  const [message, setMessage] = useState<{ variant: 'success' | 'error' | 'info'; text: string } | null>(null)
  const [viewMode, setViewMode] = useState<ViewMode>('table')
  const [selectedEvent, setSelectedEvent] = useState<TimelineEvent | null>(null)

  const parsedCaseId = caseId.trim() === '' ? null : Number(caseId)
  const validCaseId =
    parsedCaseId !== null && Number.isInteger(parsedCaseId) && parsedCaseId > 0 ? parsedCaseId : null

  // Re-render cada 10 s para que el indicador "hace X" avance sin acción del usuario.
  useEffect(() => {
    const id = window.setInterval(() => setNow(new Date()), 10_000)
    return () => window.clearInterval(id)
  }, [])

  async function load(id: number, opts: { silent?: boolean } = {}) {
    if (!opts.silent) {
      setLoading(true)
      setMessage(null)
    }
    try {
      const data = await getTimelineEvents(id)
      setEvents(data)
      setLastLoaded(new Date())
      setSelectedEvent(null)
      if (!opts.silent) setMessage({ variant: 'info', text: `${data.length} eventos cargados.` })
    } catch (e) {
      setMessage({ variant: 'error', text: e instanceof Error ? e.message : 'Error al cargar la línea temporal.' })
    } finally {
      if (!opts.silent) setLoading(false)
    }
  }

  async function recalc(id: number) {
    setRefreshing(true)
    setMessage(null)
    try {
      const data = await refreshTimeline(id)
      setEvents(data)
      setLastLoaded(new Date())
      setSelectedEvent(null)
      setMessage({ variant: 'success', text: `Línea temporal recalculada: ${data.length} eventos.` })
    } catch (e) {
      setMessage({
        variant: 'error',
        text: e instanceof Error ? e.message : 'Error al recalcular la línea temporal.',
      })
    } finally {
      setRefreshing(false)
    }
  }

  // Auto-carga silenciosa al cambiar el caseId (debounce 500 ms para no
  // disparar un fetch por cada tecla).
  useEffect(() => {
    if (!validCaseId) return
    const t = window.setTimeout(() => {
      void load(validCaseId, { silent: true })
    }, 500)
    return () => window.clearTimeout(t)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [validCaseId])

  const busy = loading || refreshing

  const columns: DataTableColumn<TimelineEvent>[] = [
    { key: 'orden', header: '#', render: (e) => e.orden },
    { key: 'fecha_hora', header: 'Fecha', render: (e) => new Date(e.fecha_hora).toLocaleString() },
    { key: 'origen_modulo', header: 'Origen', render: (e) => e.origen_modulo },
    { key: 'descripcion', header: 'Descripción', render: (e) => e.descripcion },
  ]

  return (
    <div className="h-full overflow-y-auto p-gutter flex flex-col gap-panel-gap [&>*]:shrink-0">
      <div className="flex items-baseline justify-between gap-4 flex-wrap">
        <h1 className="font-headline text-headline-md text-on-surface">Línea Temporal</h1>
        <div className="flex items-center gap-3">
          <span className="text-body-sm text-on-surface-variant" aria-live="polite">
            {refreshing
              ? 'Actualizando…'
              : lastLoaded
                ? `Última actualización: ${formatRelativeTime(lastLoaded, now)}`
                : ''}
          </span>
          <div className="flex gap-1">
            <Button
              size="sm"
              variant={viewMode === 'table' ? 'primary' : 'ghost'}
              icon="table_chart"
              onClick={() => setViewMode('table')}
            >
              Tabla
            </Button>
            <Button
              size="sm"
              variant={viewMode === 'chart' ? 'primary' : 'ghost'}
              icon="timeline"
              onClick={() => setViewMode('chart')}
            >
              Gráfico
            </Button>
          </div>
        </div>
      </div>

      {message && <Alert variant={message.variant}>{message.text}</Alert>}

      <Card title="Caso">
        <div className="p-gutter flex items-end gap-3 max-w-lg">
          <Input
            label="ID del caso"
            type="number"
            min={1}
            value={caseId}
            onChange={(e) => setCaseId(e.target.value)}
          />
          <Button
            size="sm"
            variant="ghost"
            loading={loading}
            disabled={!validCaseId || busy}
            onClick={() => validCaseId && load(validCaseId)}
          >
            Cargar
          </Button>
          <Button
            size="sm"
            icon="refresh"
            loading={refreshing}
            disabled={!validCaseId || busy}
            onClick={() => validCaseId && recalc(validCaseId)}
          >
            Recalcular
          </Button>
        </div>
      </Card>

      {viewMode === 'table' ? (
        <Card title={`Eventos (${events.length})`}>
          <DataTable
            columns={columns}
            rows={events}
            getRowId={(e) => e.id}
            emptyMessage="Sin eventos para este caso."
          />
        </Card>
      ) : (
        <Card title={`Eventos (${events.length})`}>
          <div className="p-4">
            <TimelineChart
              events={events}
              selectedEventId={selectedEvent?.id ?? null}
              onSelectEvent={(ev) => setSelectedEvent(ev)}
            />
          </div>
        </Card>
      )}

      {viewMode === 'chart' && selectedEvent && (
        <EventDetailCard event={selectedEvent} onClose={() => setSelectedEvent(null)} />
      )}
    </div>
  )
}

export default TimelinePage
