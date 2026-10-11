import { useState } from 'react'
import { Alert, Button, Card, Input } from '@/shared/ui'
import { ApiError } from '../api/httpClient'
import { cnmvApi } from '../api/cnmvApi'
import type { CnmvCheckCase } from '../types/cnmv'
import { RiskGauge } from '../components/RiskGauge'
import { FlagsTable } from '../components/FlagsTable'

function errorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return typeof error.detail === 'string' ? error.detail : 'La API rechazó la solicitud.'
  }
  return 'No se ha podido conectar con el backend.'
}

/** Panel de Verificación CNMV. Datos reales de /analysis/cnmv-check (app/api/routes/cnmv.py). */
export function CnmvCheckPage() {
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<CnmvCheckCase | null>(null)

  const handleCheck = async () => {
    const trimmed = query.trim()
    if (!trimmed) {
      setError('Escribe un nombre primero.')
      return
    }
    setLoading(true)
    setError(null)
    try {
      setResult(await cnmvApi.check(trimmed))
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  const hasFca = (result?.fca_matches?.length ?? 0) > 0
  const hasRegistry = (result?.registry_matches?.length ?? 0) > 0
  const hasWarnings = (result?.matches.length ?? 0) > 0

  return (
    <div className="h-full overflow-auto p-gutter flex flex-col gap-panel-gap">
      <Card
        title="Verificación CNMV"
        subtitle="Compara una empresa, broker o web contra las advertencias de la CNMV, el registro de entidades autorizadas (España) y el registro FCA (Reino Unido)."
      >
        <div className="p-6 flex flex-col gap-4">
          <div className="flex gap-3 items-end flex-wrap">
            <div className="flex-1 min-w-[240px]">
              <Input
                label="Nombre de la empresa o dominio"
                icon="gavel"
                placeholder="Aichaintrader"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                onKeyDown={(event) => event.key === 'Enter' && handleCheck()}
              />
            </div>
            <Button variant="primary" loading={loading} onClick={handleCheck}>
              Verificar entidad
            </Button>
          </div>
          {error && <Alert variant="error">{error}</Alert>}
        </div>
      </Card>

      {result && (
        <Card>
          <div className="p-6 flex gap-6 items-start flex-wrap">
            <RiskGauge score={result.risk_score} />
            <div className="flex-1 min-w-[280px]">
              <div className="font-headline-md text-headline-md text-on-surface mb-4 break-all">
                Caso #{result.id} — &ldquo;{result.query}&rdquo;
              </div>

              {hasWarnings && (
                <>
                  <span className="font-label-caps text-label-caps text-on-surface-variant">
                    Advertencias públicas de la CNMV ({result.match_count})
                  </span>
                  <div className="flex flex-col gap-2 my-3">
                    {result.matches.map((m, i) => (
                      <div key={i} className="border border-hairline rounded p-3 font-body-md text-body-md">
                        <div className="text-on-surface-variant text-xs mb-1">{m.fecha}</div>
                        <div className="text-on-surface whitespace-pre-line">{m.companias}</div>
                        {m.observaciones && <div className="text-on-surface-variant mt-1">{m.observaciones}</div>}
                      </div>
                    ))}
                  </div>
                </>
              )}

              {hasFca && (
                <>
                  <span className="font-label-caps text-label-caps text-on-surface-variant">
                    Registro FCA (Reino Unido)
                  </span>
                  <div className="flex flex-col gap-2 my-3">
                    {result.fca_matches!.map((m, i) => (
                      <div
                        key={i}
                        className="flex items-center justify-between gap-3 border border-hairline rounded p-3 font-mono-data text-mono-data"
                      >
                        <span>
                          {m.name}
                          {m.url && (
                            <a href={m.url} target="_blank" rel="noopener" className="text-primary ml-2">
                              ↗
                            </a>
                          )}
                        </span>
                        <span className="text-on-surface-variant text-xs">
                          {m.status} · {m.reference_number}
                        </span>
                      </div>
                    ))}
                  </div>
                </>
              )}

              {hasRegistry && (
                <>
                  <span className="font-label-caps text-label-caps text-on-surface-variant">
                    Registro de entidades autorizadas (CNMV)
                  </span>
                  <div className="flex flex-col gap-2 my-3">
                    {result.registry_matches!.map((m, i) => (
                      <div
                        key={i}
                        className="flex items-center justify-between gap-3 border border-hairline rounded p-3 font-mono-data text-mono-data"
                      >
                        <span>{m.name}</span>
                        <span className="text-on-surface-variant text-xs">{m.code}</span>
                      </div>
                    ))}
                  </div>
                </>
              )}

              {result.registry_matches !== null && !hasRegistry && (
                <p className="font-body-md text-body-md text-on-surface-variant mb-3">
                  No se ha encontrado ninguna entidad con este nombre en el registro.
                </p>
              )}

              {!hasWarnings && !hasFca && !hasRegistry && (
                <p className="font-body-md text-body-md text-on-surface-variant mb-3">
                  No se ha encontrado nada relevante en ninguna de las tres fuentes.
                </p>
              )}

              <span className="font-label-caps text-label-caps text-on-surface-variant">Señales</span>
              <div className="mt-2">
                <FlagsTable flags={result.risk_flags} />
              </div>

              {result.errors.length > 0 && <Alert variant="info">{result.errors.join(' · ')}</Alert>}
            </div>
          </div>
        </Card>
      )}
    </div>
  )
}
