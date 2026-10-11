import { useEffect, useRef, useState } from 'react'
import { Alert, Button, Card, Input } from '@/shared/ui'
import { ApiError } from '../api/httpClient'
import { walletApi } from '../api/walletApi'
import type { ExtractedAddress, WalletCase } from '../types/wallet'
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

const CHAIN_LABELS: Record<string, string> = { BTC: 'Bitcoin', ETH: 'Ethereum/EVM', TRON: 'Tron (TRC20)' }

/** Panel de Trazado de wallet cripto. Datos reales de /analysis/wallet (app/api/routes/wallet_analysis.py). */
export function WalletAnalysisPage() {
  // El expediente al que se atribuye este análisis lo elige el selector de
  // la cabecera del módulo, no esta página (ver state/CasoActivoContext).
  const { casoActivoId } = useCasoActivo()
  const [address, setAddress] = useState('')
  const [formatHint, setFormatHint] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<WalletCase | null>(null)

  const [extractText, setExtractText] = useState('')
  const [extractLoading, setExtractLoading] = useState(false)
  const [extractError, setExtractError] = useState<string | null>(null)
  const [candidates, setCandidates] = useState<ExtractedAddress[] | null>(null)

  const formatTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    if (formatTimer.current) clearTimeout(formatTimer.current)
    const trimmed = address.trim()
    if (!trimmed) {
      setFormatHint(null)
      return
    }
    formatTimer.current = setTimeout(async () => {
      try {
        const fmt = await walletApi.format(trimmed)
        if (!fmt.chain) setFormatHint('Formato no reconocido todavía')
        else setFormatHint(`Detectado: ${CHAIN_LABELS[fmt.chain] ?? fmt.chain}${fmt.subtype ? ' — ' + fmt.subtype : ''}`)
      } catch {
        setFormatHint(null)
      }
    }, 300)
    return () => {
      if (formatTimer.current) clearTimeout(formatTimer.current)
    }
  }, [address])

  const handleAnalyze = async (addressOverride?: string) => {
    const trimmed = (addressOverride ?? address).trim()
    if (!trimmed) {
      setError('Escribe una dirección primero.')
      return
    }
    setLoading(true)
    setError(null)
    try {
      setResult(await walletApi.analyze(trimmed, casoActivoId))
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  const handleExtract = async () => {
    if (!extractText.trim()) {
      setExtractError('Pega un texto primero.')
      return
    }
    setExtractLoading(true)
    setExtractError(null)
    setCandidates(null)
    try {
      const data = await walletApi.extractAddresses(extractText)
      setCandidates(data.candidates)
    } catch (err) {
      setExtractError(errorMessage(err))
    } finally {
      setExtractLoading(false)
    }
  }

  const chainLabel = result?.wallet.evm_network ? `${result.wallet.chain} — ${result.wallet.evm_network}` : result?.wallet.chain
  const flowUnit = result?.wallet.token ?? result?.wallet.chain

  return (
    <div className="h-full overflow-y-auto p-gutter flex flex-col gap-panel-gap [&>*]:shrink-0">
      <Card
        title="Trazado de wallet cripto"
        subtitle="Histórico de una dirección BTC, ETH (también BSC/Polygon) o Tron/TRC20 (USDT): recogida de fondos, salida rápida y cruce con la lista OFAC."
      >
        <div className="p-6 flex flex-col gap-4">
          <div className="flex gap-3 items-end flex-wrap">
            <div className="flex-1 min-w-[280px]">
              <Input
                label="Dirección BTC, ETH o Tron (TRC20)"
                icon="account_balance_wallet"
                placeholder="1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"
                value={address}
                onChange={(event) => setAddress(event.target.value)}
                onKeyDown={(event) => event.key === 'Enter' && handleAnalyze()}
              />
              {formatHint && <p className="text-xs text-on-surface-variant mt-1">{formatHint}</p>}
            </div>
            <Button variant="primary" loading={loading} onClick={() => handleAnalyze()}>
              Analizar wallet
            </Button>
          </div>
          {error && <Alert variant="error">{error}</Alert>}
        </div>
      </Card>

      <Card title="¿No encuentras la dirección?" subtitle="Pega aquí el mensaje sospechoso completo — buscamos direcciones dentro del texto.">
        <div className="p-6 flex flex-col gap-3">
          <textarea
            className="w-full bg-canvas border border-hairline rounded font-mono-data text-mono-data text-on-surface placeholder-on-surface-variant focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary/50 transition-all p-3 min-h-24"
            placeholder="Pega el chat, email o mensaje de WhatsApp tal cual."
            value={extractText}
            onChange={(event) => setExtractText(event.target.value)}
          />
          <div>
            <Button variant="ghost" loading={extractLoading} onClick={handleExtract}>
              Buscar direcciones en el texto
            </Button>
          </div>
          {extractError && <Alert variant="error">{extractError}</Alert>}
          {candidates && (
            candidates.length === 0 ? (
              <p className="font-body-md text-body-md text-on-surface-variant">
                No se ha encontrado ninguna dirección reconocible en ese texto.
              </p>
            ) : (
              <div className="flex flex-wrap gap-2">
                {candidates.map((c, i) => (
                  <span
                    key={i}
                    className="inline-flex items-center gap-2 border border-hairline rounded-full px-3 py-1.5 text-xs font-mono-data"
                  >
                    {c.address} ({c.chain})
                    <button
                      type="button"
                      className="text-primary underline"
                      onClick={() => {
                        setAddress(c.address)
                        handleAnalyze(c.address)
                      }}
                    >
                      Analizar
                    </button>
                  </span>
                ))}
              </div>
            )
          )}
        </div>
      </Card>

      {result && (
        <Card>
          <div className="p-6 flex gap-6 items-start flex-wrap">
            <RiskGauge score={result.risk_score} />
            <div className="flex-1 min-w-[280px]">
              <div className="font-headline-md text-headline-md text-on-surface mb-4 break-all">
                Caso #{result.id} — {result.wallet.address} ({chainLabel})
              </div>

              <KVTable
                rows={[
                  ['Transacciones analizadas', result.wallet.n_transactions],
                  ['Total recibido', `${result.wallet.total_received} ${flowUnit}`],
                  ['Total enviado', `${result.wallet.total_sent} ${flowUnit}`],
                  ['Balance actual', `${result.wallet.balance} ${result.wallet.chain}`],
                  ['Primera transacción', result.wallet.first_transaction_at],
                  ['Remitentes distintos', result.wallet.unique_senders_recent],
                ]}
              />
              {result.wallet.note && (
                <p className="font-body-md text-body-md text-on-surface-variant mb-3">{result.wallet.note}</p>
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
