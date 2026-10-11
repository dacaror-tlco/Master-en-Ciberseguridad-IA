import { useState } from 'react'
import { Alert, Button, Card, Input } from '@/shared/ui'
import { ApiError } from '../api/httpClient'
import { ipApi } from '../api/ipApi'
import type { IpCase } from '../types/ip'
import { RiskGauge } from '../components/RiskGauge'
import { KVTable } from '../components/KVTable'
import { FlagsTable } from '../components/FlagsTable'

function errorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return typeof error.detail === 'string' ? error.detail : 'La API rechazó la solicitud.'
  }
  return 'No se ha podido conectar con el backend.'
}

/** Panel de Análisis de IP. Datos reales de /analysis/ip (app/api/routes/ip_analysis.py). */
export function IpAnalysisPage() {
  const [ip, setIp] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<IpCase | null>(null)

  const handleAnalyze = async () => {
    const trimmed = ip.trim()
    if (!trimmed) {
      setError('Escribe una IP primero.')
      return
    }
    setLoading(true)
    setError(null)
    try {
      setResult(await ipApi.analyze(trimmed))
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="h-full overflow-auto p-gutter flex flex-col gap-panel-gap">
      <Card
        title="Análisis de IP"
        subtitle="Reputación (AbuseIPDB) de una dirección IP: consenso de la comunidad de seguridad sobre fuerza bruta, escaneos, spam o phishing."
      >
        <div className="p-6 flex flex-col gap-4">
          <div className="flex gap-3 items-end flex-wrap">
            <div className="flex-1 min-w-[240px]">
              <Input
                label="Dirección IP"
                icon="router"
                placeholder="1.2.3.4"
                value={ip}
                onChange={(event) => setIp(event.target.value)}
                onKeyDown={(event) => event.key === 'Enter' && handleAnalyze()}
              />
            </div>
            <Button variant="primary" loading={loading} onClick={handleAnalyze}>
              Analizar IP
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
                Caso #{result.id} — {result.ip}
              </div>

              {result.abuseipdb && (
                <>
                  <span className="font-label-caps text-label-caps text-on-surface-variant">
                    Reputación (AbuseIPDB)
                  </span>
                  <KVTable
                    rows={[
                      ['Puntuación de abuso', `${result.abuseipdb.abuse_confidence_score}/100`],
                      ['Nº de reportes', result.abuseipdb.total_reports],
                      ['ISP', result.abuseipdb.isp],
                      ['Tipo de uso', result.abuseipdb.usage_type],
                      ['País', result.abuseipdb.country_code],
                      ['Nodo de salida Tor', result.abuseipdb.is_tor ? 'Sí' : 'No'],
                    ]}
                  />
                </>
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
