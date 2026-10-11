import { useCallback, useEffect, useState } from 'react'
import { Alert, Button, Card, StatusBadge } from '@/shared/ui'
import { ApiError } from '../api/httpClient'
import { monitoringApi } from '../api/monitoringApi'
import type { MonitoredSubject, RiskAlert } from '../types/monitoring'
import { severityTone } from '../components/riskLevel'

function errorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return typeof error.detail === 'string' ? error.detail : 'La API rechazó la solicitud.'
  }
  return 'No se ha podido conectar con el backend.'
}

const BUCKET_LABEL: Record<string, string> = { high: 'ALTA', medium: 'MEDIA', low: 'BAJA' }

/**
 * Panel de Monitorización continua. Datos reales de /monitoring/subjects y
 * /alerts (app/api/routes/monitoring.py).
 */
export function MonitoringPage() {
  const [alerts, setAlerts] = useState<RiskAlert[]>([])
  const [subjects, setSubjects] = useState<MonitoredSubject[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [checkingId, setCheckingId] = useState<number | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [alertsData, subjectsData] = await Promise.all([monitoringApi.listAlerts(), monitoringApi.listSubjects()])
      setAlerts(alertsData)
      setSubjects(subjectsData)
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const handleAcknowledge = async (alertId: number) => {
    try {
      await monitoringApi.acknowledgeAlert(alertId)
    } finally {
      load()
    }
  }

  const handleToggle = async (subjectId: number, enabled: boolean) => {
    try {
      await monitoringApi.updateSubject(subjectId, enabled)
      load()
    } catch (err) {
      setError(errorMessage(err))
    }
  }

  const handleCheckNow = async (subjectId: number) => {
    setCheckingId(subjectId)
    try {
      await monitoringApi.checkNow(subjectId)
    } finally {
      setCheckingId(null)
      load()
    }
  }

  return (
    <div className="h-full overflow-y-auto p-gutter flex flex-col gap-panel-gap [&>*]:shrink-0">
      <Card
        title="Monitorización continua"
        subtitle="Cada sujeto analizado (dominio, wallet, teléfono, typosquatting, verificación CNMV) se re-comprueba periódicamente. Si el riesgo sube de nivel, aparece aquí como alerta."
        actions={
          <Button variant="ghost" size="sm" onClick={load}>
            ↻ Actualizar
          </Button>
        }
      >
        <div className="p-6 flex flex-col gap-6">
          {error && <Alert variant="error">{error}</Alert>}
          {loading && <p className="font-mono-data text-mono-data text-on-surface-variant">Cargando…</p>}

          <div>
            <h3 className="font-label-caps text-label-caps text-on-surface-variant mb-3">Alertas</h3>
            {alerts.length === 0 ? (
              <p className="font-body-md text-body-md text-on-surface-variant italic">
                No hay alertas todavía — se generan cuando un sujeto monitorizado sube de nivel de riesgo.
              </p>
            ) : (
              <div className="flex flex-col gap-2">
                {alerts.map((a) => (
                  <div
                    key={a.id}
                    className={`flex flex-col gap-1 border border-hairline rounded p-3 ${a.acknowledged ? 'opacity-55' : ''}`}
                  >
                    <div className="flex items-center gap-3">
                      <StatusBadge label={BUCKET_LABEL[a.new_bucket] ?? a.new_bucket} tone={severityTone(a.new_bucket as 'low' | 'medium' | 'high')} />
                      <span className="font-mono-data text-mono-data text-sm">
                        {a.case_type} · {a.identifier}
                      </span>
                      {!a.acknowledged && (
                        <Button variant="ghost" size="sm" className="ml-auto" onClick={() => handleAcknowledge(a.id)}>
                          Marcar leída
                        </Button>
                      )}
                      {a.acknowledged && <span className="ml-auto text-xs text-on-surface-variant">leída</span>}
                    </div>
                    <div className="text-xs text-on-surface-variant">
                      {a.reason} · {new Date(a.detected_at).toLocaleString()}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div>
            <h3 className="font-label-caps text-label-caps text-on-surface-variant mb-3">Sujetos monitorizados</h3>
            {subjects.length === 0 ? (
              <p className="font-body-md text-body-md text-on-surface-variant italic">
                Todavía no hay nada monitorizado — analiza un dominio, wallet, teléfono, typosquatting o
                verificación CNMV primero.
              </p>
            ) : (
              <div className="flex flex-col gap-2">
                {subjects.map((s) => {
                  const bucket = s.last_bucket ?? 'low'
                  return (
                    <div key={s.id} className="flex items-center gap-3 border border-hairline rounded p-3 flex-wrap">
                      <label className="flex items-center cursor-pointer" title="Activar/desactivar monitorización">
                        <input
                          type="checkbox"
                          checked={s.enabled}
                          onChange={(event) => handleToggle(s.id, event.target.checked)}
                          className="w-4 h-4 accent-primary"
                        />
                      </label>
                      <span className="font-mono-data text-mono-data text-sm">
                        {s.case_type} · {s.identifier}
                      </span>
                      <StatusBadge
                        label={`${BUCKET_LABEL[bucket] ?? bucket}${s.last_score !== null ? ' · ' + s.last_score : ''}`}
                        tone={severityTone(bucket as 'low' | 'medium' | 'high')}
                      />
                      <span className="text-xs text-on-surface-variant">
                        cada {s.check_interval_hours}h · último: {s.last_checked_at ? new Date(s.last_checked_at).toLocaleString() : 'nunca'}
                      </span>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="ml-auto"
                        loading={checkingId === s.id}
                        onClick={() => handleCheckNow(s.id)}
                      >
                        Comprobar ahora
                      </Button>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        </div>
      </Card>
    </div>
  )
}
