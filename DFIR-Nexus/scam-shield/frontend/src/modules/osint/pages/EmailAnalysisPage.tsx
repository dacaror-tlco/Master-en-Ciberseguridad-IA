import { useRef, useState } from 'react'
import { Alert, Button, Card } from '@/shared/ui'
import { ApiError } from '../api/httpClient'
import { emailApi } from '../api/emailApi'
import type { EmailCase } from '../types/email'
import { RiskGauge } from '../components/RiskGauge'
import { KVTable } from '../components/KVTable'
import { FlagsTable } from '../components/FlagsTable'
import { LinksTable } from '../components/LinksTable'
import { AttachmentsTable } from '../components/AttachmentsTable'

function errorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return typeof error.detail === 'string' ? error.detail : 'La API rechazó la solicitud.'
  }
  return 'No se ha podido conectar con el backend.'
}

/**
 * Panel de Forense de email. Datos reales de /analysis/email y
 * /analysis/email/file (app/api/routes/email_analysis.py). Admite pegar
 * texto O subir un archivo (.eml/.txt) — uno de los dos es obligatorio.
 */
export function EmailAnalysisPage() {
  const [pastedText, setPastedText] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const fileInputRef = useRef<HTMLInputElement | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<EmailCase | null>(null)

  const handleClear = () => {
    setPastedText('')
    setFile(null)
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  const handleAnalyze = async () => {
    const trimmed = pastedText.trim()
    if (!file && !trimmed) {
      setError('Pega el email arriba o selecciona un archivo.')
      return
    }
    setLoading(true)
    setError(null)
    try {
      const data = file ? await emailApi.analyzeFile(file) : await emailApi.analyzeRaw(trimmed)
      setResult(data)
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="h-full overflow-auto p-gutter flex flex-col gap-panel-gap">
      <Card
        title="Forense de email"
        subtitle="Analiza cabeceras técnicas (SPF/DKIM/DMARC), enlaces del cuerpo, adjuntos y suplantación de marca en un email sospechoso."
      >
        <div className="p-6 flex flex-col gap-4">
          <div className="flex flex-col gap-2">
            <div className="flex justify-between items-center">
              <label className="font-label-caps text-label-caps text-on-surface-variant">
                Pega aquí el email (idealmente cabeceras + cuerpo completos)
              </label>
              <Button variant="ghost" size="sm" onClick={handleClear}>
                Limpiar
              </Button>
            </div>
            <textarea
              className="w-full bg-canvas border border-hairline rounded font-mono-data text-mono-data text-on-surface placeholder-on-surface-variant focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary/50 transition-all p-3 min-h-32"
              placeholder="Pega el email tal cual, o mejor su código fuente (ver hint abajo)."
              value={pastedText}
              onChange={(event) => setPastedText(event.target.value)}
            />
          </div>

          <div className="flex gap-3 items-end flex-wrap">
            <div className="flex-1 min-w-[220px]">
              <label className="font-label-caps text-label-caps text-on-surface-variant block mb-1">
                …o sube el archivo (.eml / .txt)
              </label>
              <input
                ref={fileInputRef}
                type="file"
                accept=".eml,.txt"
                onChange={(event) => setFile(event.target.files?.[0] ?? null)}
                className="w-full bg-canvas border border-dashed border-hairline rounded text-on-surface-variant text-xs p-2.5"
              />
            </div>
            <Button variant="primary" loading={loading} onClick={handleAnalyze}>
              Analizar email
            </Button>
          </div>

          <p className="text-xs text-on-surface-variant leading-relaxed">
            Para el análisis más fiable (SPF/DKIM/DMARC), usa el código fuente original: en Gmail, menú ⋮ del
            mensaje → <em>Mostrar original</em>. En Outlook: Archivo → Propiedades → Encabezados de Internet. Si
            no puedes conseguirlo, pega igualmente el texto que ves.
          </p>
          {error && <Alert variant="error">{error}</Alert>}
        </div>
      </Card>

      {result && (
        <Card>
          <div className="p-6 flex gap-6 items-start flex-wrap">
            <RiskGauge score={result.risk_score} />
            <div className="flex-1 min-w-[280px]">
              <div className="font-headline-md text-headline-md text-on-surface mb-4 break-all">
                Caso #{result.id} — {result.headers.subject || '(sin asunto)'}
              </div>

              {result.is_raw_source === false && (
                <Alert variant="info">
                  No se detectó código fuente real (sin cabeceras técnicas) — no se pudo verificar
                  SPF/DKIM/DMARC. El análisis se basa en el contenido (enlaces, adjuntos, remitente).
                </Alert>
              )}

              <KVTable
                rows={[
                  ['Remitente', result.headers.from_address],
                  ['Nombre mostrado', result.headers.from_display_name],
                  ['Responder a', result.headers.reply_to],
                  ['SPF', result.headers.spf_result],
                  ['DKIM', result.headers.dkim_result],
                  ['DMARC', result.headers.dmarc_result],
                  ['IP de origen', result.headers.originating_ip],
                ]}
              />

              {result.headers.originating_ip && (
                <>
                  <span className="font-label-caps text-label-caps text-on-surface-variant">
                    IP de origen{result.originating_ip_abuseipdb ? ' — reputación (AbuseIPDB)' : ''}
                  </span>
                  <KVTable
                    rows={
                      result.originating_ip_abuseipdb
                        ? [
                            ['Puntuación de abuso', `${result.originating_ip_abuseipdb.abuse_confidence_score}/100`],
                            ['Nº de reportes', result.originating_ip_abuseipdb.total_reports],
                            ['ISP', result.originating_ip_abuseipdb.isp],
                            ['País', result.originating_ip_abuseipdb.country_code],
                            ['Nodo Tor', result.originating_ip_abuseipdb.is_tor ? 'Sí' : 'No'],
                          ]
                        : [['Reputación', 'No se pudo consultar AbuseIPDB para esta IP']]
                    }
                  />
                </>
              )}

              <span className="font-label-caps text-label-caps text-on-surface-variant">Señales</span>
              <div className="mt-2 mb-2">
                <FlagsTable flags={result.risk_flags} />
              </div>

              {result.links.length > 0 && (
                <>
                  <span className="font-label-caps text-label-caps text-on-surface-variant">
                    Enlaces del cuerpo ({result.links.length})
                  </span>
                  <div className="mt-2">
                    <LinksTable links={result.links} />
                  </div>
                </>
              )}

              {result.attachments.length > 0 && (
                <>
                  <span className="font-label-caps text-label-caps text-on-surface-variant">
                    Adjuntos ({result.attachments.length})
                  </span>
                  <div className="mt-2">
                    <AttachmentsTable attachments={result.attachments} />
                  </div>
                </>
              )}

              {result.ai_explanation && (
                <div className="p-3 bg-hairline/30 rounded text-sm mb-3">
                  <strong>Explicación:</strong> {result.ai_explanation}
                </div>
              )}

              {result.errors.length > 0 && <Alert variant="info">{result.errors.join(' · ')}</Alert>}
            </div>
          </div>
        </Card>
      )}
    </div>
  )
}
