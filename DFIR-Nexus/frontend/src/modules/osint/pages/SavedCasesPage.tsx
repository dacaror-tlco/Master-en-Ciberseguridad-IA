import { useCallback, useEffect, useState } from 'react'
import { Alert, Button, Card, Select, StatusBadge } from '@/shared/ui'
import { ApiError } from '../api/httpClient'
import { caseLinkApi } from '../api/caseLinkApi'
import { casesLookupApi } from '../api/casesLookupApi'
import { domainApi } from '../api/domainApi'
import { emailApi } from '../api/emailApi'
import { walletApi } from '../api/walletApi'
import { typosquattingApi } from '../api/typosquattingApi'
import { phoneApi } from '../api/phoneApi'
import { cnmvApi } from '../api/cnmvApi'
import { imageApi } from '../api/imageApi'
import { ipApi } from '../api/ipApi'
import { riskLevel } from '../components/riskLevel'
import { useSelection } from '../state/SelectionContext'
import type { CaseType } from '../types/report'
import type { CaseOption, OsintCaseType } from '../types/case'

function errorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return typeof error.detail === 'string' ? error.detail : 'La API rechazó la solicitud.'
  }
  return 'No se ha podido conectar con el backend.'
}

type Row = { id: number; label: string; risk_score: number; case_id: number | null }

const SECTIONS: { type: CaseType; title: string }[] = [
  { type: 'domain', title: 'Dominios' },
  { type: 'email', title: 'Emails' },
  { type: 'wallet', title: 'Wallets' },
  { type: 'typosquatting', title: 'Typosquatting' },
  { type: 'phone', title: 'Teléfonos' },
  { type: 'cnmv', title: 'Verificaciones CNMV' },
  { type: 'image', title: 'Imágenes' },
  { type: 'ip', title: 'IPs' },
]

const SIN_VINCULAR = 'sin-vincular'

/**
 * Panel de Casos guardados. Lista los 8 tipos de caso y permite marcarlos
 * para incluirlos en el Informe (selección compartida vía SelectionContext),
 * y vincular opcionalmente cada investigación con un caso del Módulo 1
 * (columna "Caso" + selector, ver PATCH /osint-cases/{tipo}/{id}/vinculacion).
 */
export function SavedCasesPage() {
  const { selected, toggle } = useSelection()
  const [rows, setRows] = useState<Record<CaseType, Row[]>>({
    domain: [], email: [], wallet: [], typosquatting: [], phone: [], cnmv: [], image: [], ip: [],
  })
  const [cases, setCases] = useState<CaseOption[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Estado de la vinculación en curso/errores, por fila (clave "tipo:id") —
  // no bloquea el resto de la pantalla ni se mezcla con `error` general.
  const [updatingKey, setUpdatingKey] = useState<string | null>(null)
  const [linkError, setLinkError] = useState<string | null>(null)
  const [linkWarning, setLinkWarning] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [domains, emails, wallets, typosquattings, phones, cnmvs, images, ips] = await Promise.all([
        domainApi.list(),
        emailApi.list(),
        walletApi.list(),
        typosquattingApi.list(),
        phoneApi.list(),
        cnmvApi.list(),
        imageApi.list(),
        ipApi.list(),
      ])
      setRows({
        domain: domains.map((c) => ({ id: c.id, label: c.domain, risk_score: c.risk_score, case_id: c.case_id })),
        email: emails.map((c) => ({
          id: c.id, label: c.from_address ?? '(sin remitente)', risk_score: c.risk_score, case_id: c.case_id,
        })),
        wallet: wallets.map((c) => ({
          id: c.id, label: `${c.address} (${c.chain})`, risk_score: c.risk_score, case_id: c.case_id,
        })),
        typosquatting: typosquattings.map((c) => ({
          id: c.id,
          label: `${c.domain} (${c.resolved_count} activas)`,
          risk_score: c.risk_score,
          case_id: c.case_id,
        })),
        phone: phones.map((c) => ({
          id: c.id, label: `${c.raw_phone} (${c.line_type ?? '?'})`, risk_score: c.risk_score, case_id: c.case_id,
        })),
        cnmv: cnmvs.map((c) => ({
          id: c.id,
          label: `"${c.query}" (${c.match_count} coincidencia${c.match_count === 1 ? '' : 's'})`,
          risk_score: c.risk_score,
          case_id: c.case_id,
        })),
        image: images.map((c) => ({
          id: c.id, label: c.filename ?? '(sin nombre)', risk_score: c.risk_score, case_id: c.case_id,
        })),
        ip: ips.map((c) => ({ id: c.id, label: c.ip, risk_score: c.risk_score, case_id: c.case_id })),
      })
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setLoading(false)
    }
  }, [])

  const loadCases = useCallback(async () => {
    try {
      setCases(await casesLookupApi.list())
    } catch {
      // El backend de Casos puede no estar levantado: OSINT sigue siendo
      // usable por sí solo (mismo criterio que modules/reports). Los
      // vínculos ya existentes se siguen mostrando (como "Caso #id"), solo
      // no se puede elegir uno nuevo hasta que Casos vuelva a responder.
      setCases([])
    }
  }, [])

  useEffect(() => {
    load()
    loadCases()
  }, [load, loadCases])

  const nombreDeCaso = (caseId: number | null): string => {
    if (caseId === null) return 'Sin vincular'
    const caso = cases.find((c) => c.id === caseId)
    return caso ? `Caso #${caso.id} — ${caso.nombre}` : `Caso #${caseId}`
  }

  const handleVincular = async (type: CaseType, row: Row, nuevoCaseId: number | null) => {
    if (nuevoCaseId === row.case_id) return
    const key = `${type}:${row.id}`
    setUpdatingKey(key)
    setLinkError(null)
    setLinkWarning(null)
    try {
      const resultado = await caseLinkApi.update(type as OsintCaseType, row.id, nuevoCaseId)
      setRows((prev) => ({
        ...prev,
        [type]: prev[type].map((r) => (r.id === row.id ? { ...r, case_id: resultado.case_id } : r)),
      }))
      if (resultado.cambiado && resultado.auditoria_registrada === false) {
        setLinkWarning(
          `La vinculación se guardó, pero no se pudo registrar en la auditoría del caso` +
            (resultado.auditoria_error ? ` (${resultado.auditoria_error})` : '') +
            '.',
        )
      }
    } catch (err) {
      setLinkError(errorMessage(err))
    } finally {
      setUpdatingKey(null)
    }
  }

  return (
    <div className="h-full overflow-y-auto p-gutter flex flex-col gap-panel-gap [&>*]:shrink-0">
      <Card
        title="Casos guardados"
        subtitle="Marca los casos que quieras incluir en el informe combinado. Puedes vincular opcionalmente cada investigación con un caso del Módulo 1."
        actions={
          <Button variant="ghost" size="sm" onClick={() => { load(); loadCases() }}>
            ↻ Actualizar listado
          </Button>
        }
      >
        <div className="p-6 flex flex-col gap-6">
          {error && <Alert variant="error">{error}</Alert>}
          {linkError && <Alert variant="error">{linkError}</Alert>}
          {linkWarning && <Alert variant="info">{linkWarning}</Alert>}
          {loading && <p className="font-mono-data text-mono-data text-on-surface-variant">Cargando…</p>}
          {SECTIONS.map(({ type, title }) => (
            <div key={type}>
              <h3 className="font-label-caps text-label-caps text-on-surface-variant mb-3">{title}</h3>
              {rows[type].length === 0 ? (
                <p className="font-body-md text-body-md text-on-surface-variant italic">
                  Todavía no hay casos de este tipo.
                </p>
              ) : (
                <div className="flex flex-col gap-2">
                  {rows[type].map((row) => {
                    const level = riskLevel(row.risk_score)
                    const tone = level.bucket === 'high' ? 'error' : level.bucket === 'medium' ? 'tertiary' : 'primary'
                    const key = `${type}:${row.id}`
                    return (
                      <div
                        key={row.id}
                        className="flex items-center gap-3 border border-hairline rounded p-3"
                      >
                        <input
                          type="checkbox"
                          checked={selected[type].has(row.id)}
                          onChange={() => toggle(type, row.id)}
                          className="w-4 h-4 accent-primary shrink-0"
                          aria-label={`Incluir ${row.label} en el informe`}
                        />
                        <span className="font-mono-data text-mono-data text-sm flex-1 truncate">{row.label}</span>
                        <span className="text-xs text-on-surface-variant">#{row.id}</span>
                        <StatusBadge label={`${level.label} · ${row.risk_score}`} tone={tone} />
                        <div className="w-56 shrink-0">
                          <Select
                            aria-label={`Caso vinculado a ${row.label}`}
                            value={row.case_id === null ? SIN_VINCULAR : String(row.case_id)}
                            disabled={updatingKey === key}
                            onChange={(e) =>
                              handleVincular(
                                type,
                                row,
                                e.target.value === SIN_VINCULAR ? null : Number(e.target.value),
                              )
                            }
                            options={[
                              { value: SIN_VINCULAR, label: 'Sin vincular' },
                              ...(row.case_id !== null && !cases.some((c) => c.id === row.case_id)
                                ? [{ value: String(row.case_id), label: nombreDeCaso(row.case_id) }]
                                : []),
                              ...cases.map((c) => ({ value: String(c.id), label: `Caso #${c.id} — ${c.nombre}` })),
                            ]}
                          />
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}
            </div>
          ))}
        </div>
      </Card>
    </div>
  )
}
