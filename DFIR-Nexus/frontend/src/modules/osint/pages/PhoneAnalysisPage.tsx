import { useState } from 'react'
import { Alert, Button, Card, Input } from '@/shared/ui'
import { ApiError } from '../api/httpClient'
import { phoneApi } from '../api/phoneApi'
import type { PhoneCase } from '../types/phone'
import { RiskGauge } from '../components/RiskGauge'
import { KVTable } from '../components/KVTable'
import { FlagsTable } from '../components/FlagsTable'
import { useCasoActivo } from '../state/CasoActivoContext'

function errorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return typeof error.detail === 'string' ? error.detail : 'La API rechazó la solicitud.'
  }
  return 'No se ha podido conectar con el backend.'
}

/** Panel de Análisis de teléfono. Datos reales de /analysis/phone (app/api/routes/phone_analysis.py). */
export function PhoneAnalysisPage() {
  // El expediente al que se atribuye este análisis lo elige el selector de
  // la cabecera del módulo, no esta página (ver state/CasoActivoContext).
  const { casoActivoId } = useCasoActivo()
  const [phone, setPhone] = useState('')
  const [region, setRegion] = useState('ES')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<PhoneCase | null>(null)

  const handleAnalyze = async () => {
    const trimmed = phone.trim()
    if (!trimmed) {
      setError('Escribe un número primero.')
      return
    }
    setLoading(true)
    setError(null)
    try {
      setResult(await phoneApi.analyze(trimmed, region.trim() || 'ES', casoActivoId))
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="h-full overflow-y-auto p-gutter flex flex-col gap-panel-gap [&>*]:shrink-0">
      <Card
        title="Análisis de teléfono"
        subtitle="Tipo de línea, operador y país — clave para detectar timos de falso premio o wangiri. Nunca busca de quién es el número."
      >
        <div className="p-6 flex flex-col gap-4">
          <div className="flex gap-3 items-end flex-wrap">
            <div className="flex-1 min-w-[220px]">
              <Input
                label="Número de teléfono"
                icon="call"
                placeholder="+34600123456"
                value={phone}
                onChange={(event) => setPhone(event.target.value)}
                onKeyDown={(event) => event.key === 'Enter' && handleAnalyze()}
              />
            </div>
            <div className="w-32">
              <Input
                label="Región por defecto"
                maxLength={2}
                value={region}
                onChange={(event) => setRegion(event.target.value.toUpperCase())}
              />
            </div>
            <Button variant="primary" loading={loading} onClick={handleAnalyze}>
              Analizar teléfono
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
                Caso #{result.id} — {result.phone?.international_format ?? phone}
              </div>

              {result.phone && (
                <KVTable
                  rows={[
                    ['País', result.phone.country_name],
                    ['Operador', result.phone.carrier],
                    ['Tipo de línea', result.phone.line_type],
                    ['Formato válido', result.phone.is_valid ? 'Sí' : 'No'],
                    ['Formato nacional', result.phone.national_format],
                  ]}
                />
              )}

              {result.community_reports && (
                <>
                  <span className="font-label-caps text-label-caps text-on-surface-variant">
                    Reportes de la comunidad (OpenSpam)
                  </span>
                  <KVTable
                    rows={[
                      ['Nº de reportes', result.community_reports.reports_count],
                      ['Categoría', result.community_reports.category],
                      ['Provincia', result.community_reports.province],
                      ['Nivel de peligro', result.community_reports.danger_level],
                    ]}
                  />
                </>
              )}

              {result.fraud_score && (
                <>
                  <span className="font-label-caps text-label-caps text-on-surface-variant">
                    Puntuación de fraude (IPQualityScore)
                  </span>
                  <KVTable
                    rows={[
                      ['Fraud score', result.fraud_score.fraud_score != null ? `${result.fraud_score.fraud_score}/100` : null],
                      ['VOIP', result.fraud_score.voip ? 'Sí' : 'No'],
                      ['Prepago', result.fraud_score.prepaid ? 'Sí' : 'No'],
                      ['Abuso reciente', result.fraud_score.recent_abuse ? 'Sí' : 'No'],
                      ['Filtrado en brecha de datos', result.fraud_score.leaked ? 'Sí' : 'No'],
                    ]}
                  />
                </>
              )}

              {result.carrier_intelligence && (
                <>
                  <span className="font-label-caps text-label-caps text-on-surface-variant">
                    Carrier en tiempo real (Twilio Lookup)
                  </span>
                  <KVTable
                    rows={[
                      ['Operador', result.carrier_intelligence.carrier_name],
                      ['Tipo de línea (en vivo)', result.carrier_intelligence.line_type],
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
