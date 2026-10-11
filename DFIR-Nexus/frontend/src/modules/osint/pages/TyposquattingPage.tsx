import { useState } from 'react'
import { Alert, Button, Card, Input } from '@/shared/ui'
import { ApiError } from '../api/httpClient'
import { typosquattingApi } from '../api/typosquattingApi'
import type { TyposquattingCase } from '../types/typosquatting'
import { RiskGauge } from '../components/RiskGauge'
import { KVTable } from '../components/KVTable'
import { FlagsTable } from '../components/FlagsTable'
import { riskLevel } from '../components/riskLevel'
import { useCasoActivo } from '../state/CasoActivoContext'

function errorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return typeof error.detail === 'string' ? error.detail : 'La API rechazó la solicitud.'
  }
  return 'No se ha podido conectar con el backend.'
}

/** Panel de Detector de typosquatting. Datos reales de /analysis/typosquatting. */
export function TyposquattingPage() {
  // El expediente al que se atribuye este análisis lo elige el selector de
  // la cabecera del módulo, no esta página (ver state/CasoActivoContext).
  const { casoActivoId } = useCasoActivo()
  const [domain, setDomain] = useState('')
  const [deep, setDeep] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<TyposquattingCase | null>(null)

  const handleAnalyze = async () => {
    const trimmed = domain.trim()
    if (!trimmed) {
      setError('Escribe un dominio primero.')
      return
    }
    setLoading(true)
    setError(null)
    try {
      setResult(await typosquattingApi.analyze(trimmed, deep, casoActivoId))
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="h-full overflow-y-auto p-gutter flex flex-col gap-panel-gap [&>*]:shrink-0">
      <Card
        title="Detector de typosquatting"
        subtitle="Genera variantes típicas de suplantación de tu dominio legítimo y comprueba cuáles están registradas de verdad."
      >
        <div className="p-6 flex flex-col gap-4">
          <div className="flex gap-3 items-end flex-wrap">
            <div className="flex-1 min-w-[240px]">
              <Input
                label="Dominio legítimo a proteger"
                icon="content_copy"
                placeholder="tubanco.es"
                value={domain}
                onChange={(event) => setDomain(event.target.value)}
                onKeyDown={(event) => event.key === 'Enter' && handleAnalyze()}
              />
            </div>
            <Button variant="primary" loading={loading} onClick={handleAnalyze}>
              Buscar variantes activas
            </Button>
          </div>
          <label className="flex items-center gap-2 text-sm text-on-surface-variant font-body-md text-body-md cursor-pointer">
            <input
              type="checkbox"
              checked={deep}
              onChange={(event) => setDeep(event.target.checked)}
              className="w-4 h-4 accent-primary"
            />
            Analizar en profundidad las variantes activas (WHOIS/SSL/VirusTotal) — más lento, máx. 4 variantes
          </label>
          {error && <Alert variant="error">{error}</Alert>}
        </div>
      </Card>

      {result && (
        <Card>
          <div className="p-6 flex gap-6 items-start flex-wrap">
            <RiskGauge score={result.risk_score} />
            <div className="flex-1 min-w-[280px]">
              <div className="font-headline-md text-headline-md text-on-surface mb-4 break-all">
                Caso #{result.id} — {result.domain}
              </div>

              <KVTable
                rows={[
                  ['Variantes generadas', result.variants_generated],
                  ['Variantes activas encontradas', result.resolved_count],
                ]}
              />

              <span className="font-label-caps text-label-caps text-on-surface-variant">Señales</span>
              <div className="mt-2 mb-4">
                <FlagsTable flags={result.risk_flags} />
              </div>

              {result.candidates.length > 0 ? (
                <>
                  <span className="font-label-caps text-label-caps text-on-surface-variant">
                    Variantes activas
                  </span>
                  <div className="overflow-x-auto mt-2">
                  <table className="w-full text-left border-collapse">
                    <thead>
                      <tr>
                        <th className="py-2 px-2 font-label-caps text-label-caps text-on-surface-variant font-normal">Dominio</th>
                        <th className="py-2 px-2 font-label-caps text-label-caps text-on-surface-variant font-normal">Técnica</th>
                        <th className="py-2 px-2 font-label-caps text-label-caps text-on-surface-variant font-normal">IP</th>
                        <th className="py-2 px-2 font-label-caps text-label-caps text-on-surface-variant font-normal">Score</th>
                      </tr>
                    </thead>
                    <tbody className="font-mono-data text-mono-data">
                      {result.candidates.map((c, i) => (
                        <tr key={i} className="border-b border-hairline">
                          <td className="py-2 px-2">{c.variant}</td>
                          <td className="py-2 px-2 text-on-surface-variant text-xs">{c.technique}</td>
                          <td className="py-2 px-2">{c.ip_address ?? '—'}</td>
                          <td className="py-2 px-2">
                            {c.risk_score !== null ? (
                              <span className="flex items-center gap-2">
                                <span style={{ color: riskLevel(c.risk_score).colorVar }}>{c.risk_score}</span>
                                <span className="text-on-surface-variant text-xs">
                                  {c.fully_analyzed ? 'completo' : 'IP'}
                                </span>
                              </span>
                            ) : (
                              <span className="text-on-surface-variant text-xs">sin analizar</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  </div>
                </>
              ) : (
                <p className="font-body-md text-body-md text-on-surface-variant">
                  No se encontró ninguna variante activa — buena señal.
                </p>
              )}

              {result.errors.length > 0 && <Alert variant="info">{result.errors.join(' · ')}</Alert>}
            </div>
          </div>
        </Card>
      )}
    </div>
  )
}
