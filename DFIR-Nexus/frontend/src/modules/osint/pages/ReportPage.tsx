import { useState } from 'react'
import { Alert, Button, Card } from '@/shared/ui'
import { ApiError } from '../api/httpClient'
import { reportApi } from '../api/reportApi'
import { useSelection } from '../state/SelectionContext'
import type { CaseType } from '../types/report'

function errorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return typeof error.detail === 'string' ? error.detail : 'La API rechazó la solicitud.'
  }
  return 'No se ha podido conectar con el backend.'
}

const CHIP_LABELS: [CaseType, string][] = [
  ['domain', 'Dominios'],
  ['email', 'Emails'],
  ['wallet', 'Wallets'],
  ['typosquatting', 'Typosquatting'],
  ['phone', 'Teléfonos'],
  ['cnmv', 'CNMV'],
  ['image', 'Imágenes'],
  ['ip', 'IPs'],
]

/**
 * Panel de Informe. Combina los casos marcados en "Casos guardados" en un
 * PDF (POST /reports/generate) y ofrece una valoración consolidada con IA
 * (POST /analysis/consolidated, que solo admite dominio/email/wallet/
 * typosquatting — ver app/schemas/consolidated.py).
 */
export function ReportPage() {
  const { selected, totalSelected } = useSelection()
  const [victimNotes, setVictimNotes] = useState('')
  const [aiNarrative, setAiNarrative] = useState<string | null>(null)

  const [aiLoading, setAiLoading] = useState(false)
  const [aiStatus, setAiStatus] = useState<string | null>(null)
  const [aiError, setAiError] = useState<string | null>(null)

  const [pdfLoading, setPdfLoading] = useState(false)
  const [pdfStatus, setPdfStatus] = useState<string | null>(null)
  const [pdfError, setPdfError] = useState<string | null>(null)

  const hasConsolidatedEligible =
    selected.domain.size > 0 || selected.email.size > 0 || selected.wallet.size > 0 || selected.typosquatting.size > 0

  const handleGenerateAi = async () => {
    if (!hasConsolidatedEligible) {
      setAiStatus(null)
      setAiError('Selecciona al menos un caso de dominio, email, wallet o typosquatting en "Casos guardados".')
      return
    }
    setAiLoading(true)
    setAiStatus(null)
    setAiError(null)
    try {
      const data = await reportApi.consolidated({
        domain_case_ids: [...selected.domain],
        email_case_ids: [...selected.email],
        wallet_case_ids: [...selected.wallet],
        typosquatting_case_ids: [...selected.typosquatting],
        victim_notes: victimNotes.trim() || null,
        include_ai_narrative: true,
      })
      setAiStatus(
        `Score consolidado: ${data.consolidated_score}/100${
          data.correlation_flags.length ? ` · ${data.correlation_flags.length} correlación(es) detectada(s)` : ''
        }`,
      )
      if (data.ai_narrative) {
        setAiNarrative(data.ai_narrative)
      } else {
        setAiError(`Sin narrativa: ${data.ai_narrative_error ?? 'motivo desconocido'}`)
      }
    } catch (err) {
      setAiError(errorMessage(err))
    } finally {
      setAiLoading(false)
    }
  }

  const handleDownloadPdf = async () => {
    if (totalSelected === 0) {
      setPdfError('Selecciona al menos un caso en "Casos guardados" primero.')
      return
    }
    setPdfLoading(true)
    setPdfStatus(null)
    setPdfError(null)
    try {
      const blob = await reportApi.generatePdf({
        domain_case_ids: [...selected.domain],
        email_case_ids: [...selected.email],
        wallet_case_ids: [...selected.wallet],
        typosquatting_case_ids: [...selected.typosquatting],
        phone_case_ids: [...selected.phone],
        cnmv_check_case_ids: [...selected.cnmv],
        image_case_ids: [...selected.image],
        ip_case_ids: [...selected.ip],
        victim_notes: victimNotes.trim() || null,
        ai_narrative: aiNarrative,
      })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'informe_scamshield.pdf'
      document.body.appendChild(a)
      a.click()
      a.remove()
      URL.revokeObjectURL(url)
      setPdfStatus('Informe descargado correctamente.')
    } catch (err) {
      setPdfError(errorMessage(err))
    } finally {
      setPdfLoading(false)
    }
  }

  return (
    <div className="h-full overflow-y-auto p-gutter flex flex-col gap-panel-gap [&>*]:shrink-0">
      <Card title="Generar informe" subtitle="Combina los casos seleccionados en 'Casos guardados' en un único PDF.">
        <div className="p-6 flex flex-col gap-6">
          <div className="flex flex-wrap gap-2">
            {CHIP_LABELS.map(([type, label]) => (
              <span key={type} className="text-xs font-mono-data border border-hairline rounded-full px-3 py-1.5 text-on-surface-variant">
                {label}: {selected[type].size}
              </span>
            ))}
          </div>

          <div>
            <label className="font-label-caps text-label-caps text-on-surface-variant block mb-1">
              Relato de los hechos (opcional)
            </label>
            <textarea
              className="w-full bg-canvas border border-hairline rounded font-body-md text-body-md text-on-surface placeholder-on-surface-variant p-3 min-h-24"
              placeholder="Describe qué pasó, en tus propias palabras. Se incluye tal cual en el informe."
              value={victimNotes}
              onChange={(event) => setVictimNotes(event.target.value)}
            />
          </div>

          <div className="border border-hairline rounded p-4 flex flex-col gap-3">
            <div className="flex justify-between items-center">
              <strong className="text-sm text-on-surface">Valoración consolidada con IA</strong>
              <span className="text-xs text-on-surface-variant">
                opcional · necesita ANTHROPIC_API_KEY en el backend
              </span>
            </div>
            <p className="text-xs text-on-surface-variant leading-relaxed">
              Detecta correlaciones entre módulos (dominio/email/wallet/typosquatting) y redacta un párrafo
              explicativo. Sin la API key configurada, esto simplemente no se rellena.
            </p>
            <div>
              <Button variant="ghost" loading={aiLoading} onClick={handleGenerateAi}>
                Generar valoración con IA
              </Button>
            </div>
            {aiStatus && <p className="text-xs text-primary">{aiStatus}</p>}
            {aiError && <Alert variant="info">{aiError}</Alert>}
            {aiNarrative && (
              <div className="border border-primary/40 bg-hairline/30 rounded p-3 text-sm whitespace-pre-wrap">
                {aiNarrative}
              </div>
            )}
          </div>

          <div>
            <Button variant="primary" icon="download" loading={pdfLoading} onClick={handleDownloadPdf}>
              Descargar informe PDF
            </Button>
          </div>
          {pdfStatus && <p className="text-xs text-primary">{pdfStatus}</p>}
          {pdfError && <Alert variant="error">{pdfError}</Alert>}
        </div>
      </Card>
    </div>
  )
}
