import { useCallback, useEffect, useState } from 'react'
import { Alert, Button, Card, StatusBadge } from '@/shared/ui'
import { ApiError } from '../api/httpClient'
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

function errorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return typeof error.detail === 'string' ? error.detail : 'La API rechazó la solicitud.'
  }
  return 'No se ha podido conectar con el backend.'
}

type Row = { id: number; label: string; risk_score: number }

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

/**
 * Panel de Casos guardados. Lista los 8 tipos de caso y permite marcarlos
 * para incluirlos en el Informe (selección compartida vía SelectionContext).
 */
export function SavedCasesPage() {
  const { selected, toggle } = useSelection()
  const [rows, setRows] = useState<Record<CaseType, Row[]>>({
    domain: [], email: [], wallet: [], typosquatting: [], phone: [], cnmv: [], image: [], ip: [],
  })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

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
        domain: domains.map((c) => ({ id: c.id, label: c.domain, risk_score: c.risk_score })),
        email: emails.map((c) => ({ id: c.id, label: c.from_address ?? '(sin remitente)', risk_score: c.risk_score })),
        wallet: wallets.map((c) => ({ id: c.id, label: `${c.address} (${c.chain})`, risk_score: c.risk_score })),
        typosquatting: typosquattings.map((c) => ({
          id: c.id,
          label: `${c.domain} (${c.resolved_count} activas)`,
          risk_score: c.risk_score,
        })),
        phone: phones.map((c) => ({ id: c.id, label: `${c.raw_phone} (${c.line_type ?? '?'})`, risk_score: c.risk_score })),
        cnmv: cnmvs.map((c) => ({
          id: c.id,
          label: `"${c.query}" (${c.match_count} coincidencia${c.match_count === 1 ? '' : 's'})`,
          risk_score: c.risk_score,
        })),
        image: images.map((c) => ({ id: c.id, label: c.filename ?? '(sin nombre)', risk_score: c.risk_score })),
        ip: ips.map((c) => ({ id: c.id, label: c.ip, risk_score: c.risk_score })),
      })
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  return (
    <div className="h-full overflow-auto p-gutter flex flex-col gap-panel-gap">
      <Card
        title="Casos guardados"
        subtitle="Marca los casos que quieras incluir en el informe combinado."
        actions={
          <Button variant="ghost" size="sm" onClick={load}>
            ↻ Actualizar listado
          </Button>
        }
      >
        <div className="p-6 flex flex-col gap-6">
          {error && <Alert variant="error">{error}</Alert>}
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
                    return (
                      <label
                        key={row.id}
                        className="flex items-center gap-3 border border-hairline rounded p-3 cursor-pointer"
                      >
                        <input
                          type="checkbox"
                          checked={selected[type].has(row.id)}
                          onChange={() => toggle(type, row.id)}
                          className="w-4 h-4 accent-primary shrink-0"
                        />
                        <span className="font-mono-data text-mono-data text-sm flex-1 truncate">{row.label}</span>
                        <span className="text-xs text-on-surface-variant">#{row.id}</span>
                        <StatusBadge label={`${level.label} · ${row.risk_score}`} tone={tone} />
                      </label>
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
