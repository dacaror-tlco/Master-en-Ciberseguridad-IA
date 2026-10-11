import { useEffect, useState } from 'react'
import { Alert, Button, Card } from '@/shared/ui'
import { ApiError } from '../api/httpClient'
import { imageApi } from '../api/imageApi'
import type { FacialSearchResult, ImageCase, ReverseImageSearchResult } from '../types/image'
import { RiskGauge } from '../components/RiskGauge'
import { KVTable } from '../components/KVTable'
import { FlagsTable } from '../components/FlagsTable'

function errorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return typeof error.detail === 'string' ? error.detail : 'La API rechazó la solicitud.'
  }
  return 'No se ha podido conectar con el backend.'
}

/** Panel de Análisis de imagen. Datos reales de /analysis/image* (app/api/routes/image_analysis.py). */
export function ImageAnalysisPage() {
  const [file, setFile] = useState<File | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<ImageCase | null>(null)

  const [reverseSearchLoading, setReverseSearchLoading] = useState(false)
  const [reverseSearchResult, setReverseSearchResult] = useState<ReverseImageSearchResult | null>(null)
  const [reverseSearchError, setReverseSearchError] = useState<string | null>(null)

  const [pimeyesConfirmed, setPimeyesConfirmed] = useState(false)
  const [pimeyesNotes, setPimeyesNotes] = useState('')
  const [facialSearchLoading, setFacialSearchLoading] = useState(false)
  const [facialSearchResult, setFacialSearchResult] = useState<FacialSearchResult | null>(null)
  const [facialSearchError, setFacialSearchError] = useState<string | null>(null)

  useEffect(() => {
    if (!file) {
      setPreviewUrl(null)
      return
    }
    const url = URL.createObjectURL(file)
    setPreviewUrl(url)
    return () => URL.revokeObjectURL(url)
  }, [file])

  const handleAnalyze = async () => {
    if (!file) {
      setError('Selecciona una imagen primero.')
      return
    }
    setLoading(true)
    setError(null)
    setReverseSearchResult(null)
    setFacialSearchResult(null)
    try {
      setResult(await imageApi.analyze(file))
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  const handleReverseSearch = async () => {
    if (!result) return
    setReverseSearchLoading(true)
    setReverseSearchError(null)
    try {
      setReverseSearchResult(await imageApi.reverseSearch(result.id))
    } catch (err) {
      setReverseSearchError(errorMessage(err))
    } finally {
      setReverseSearchLoading(false)
    }
  }

  const handleFacialSearch = async () => {
    if (!result) return
    setFacialSearchLoading(true)
    setFacialSearchError(null)
    try {
      setFacialSearchResult(await imageApi.facialSearch(result.id, pimeyesConfirmed, pimeyesNotes.trim() || undefined))
    } catch (err) {
      setFacialSearchError(errorMessage(err))
    } finally {
      setFacialSearchLoading(false)
    }
  }

  return (
    <div className="h-full overflow-auto p-gutter flex flex-col gap-panel-gap">
      <Card
        title="Análisis de imagen"
        subtitle="Extrae metadatos EXIF y calcula una huella visual para detectar fotos recicladas entre casos. 100% offline, sin reconocimiento facial."
      >
        <div className="p-6 flex flex-col gap-4">
          <div className="flex gap-3 items-end flex-wrap">
            <div className="flex-1 min-w-[220px]">
              <label className="font-label-caps text-label-caps text-on-surface-variant block mb-1">
                Archivo de imagen
              </label>
              <input
                type="file"
                accept="image/*"
                onChange={(event) => setFile(event.target.files?.[0] ?? null)}
                className="w-full bg-canvas border border-dashed border-hairline rounded text-on-surface-variant text-xs p-2.5"
              />
            </div>
            <Button variant="primary" loading={loading} onClick={handleAnalyze}>
              Analizar imagen
            </Button>
          </div>
          {previewUrl && (
            <img src={previewUrl} alt="Vista previa" className="max-w-[180px] max-h-[180px] rounded border border-hairline" />
          )}
          {error && <Alert variant="error">{error}</Alert>}
        </div>
      </Card>

      {result && (
        <Card>
          <div className="p-6 flex gap-6 items-start flex-wrap">
            <RiskGauge score={result.risk_score} />
            <div className="flex-1 min-w-[280px]">
              <div className="font-headline-md text-headline-md text-on-surface mb-4 break-all">
                Caso #{result.id} — {result.filename || '(sin nombre)'}
              </div>

              <span className="font-label-caps text-label-caps text-on-surface-variant">Metadatos EXIF</span>
              <KVTable
                rows={[
                  ['Tiene metadatos', result.exif.has_exif ? 'Sí' : 'No'],
                  ['Cámara', [result.exif.camera_make, result.exif.camera_model].filter(Boolean).join(' ') || null],
                  ['Software', result.exif.software],
                  ['Fecha original', result.exif.date_taken],
                  [
                    'GPS',
                    result.exif.gps_latitude ? `${result.exif.gps_latitude}, ${result.exif.gps_longitude}` : null,
                  ],
                ]}
              />

              <span className="font-label-caps text-label-caps text-on-surface-variant">
                Coincidencias con otros casos
              </span>
              {result.matches.length > 0 ? (
                <div className="flex flex-col gap-2 my-3">
                  {result.matches.map((m) => (
                    <div
                      key={m.case_id}
                      className="flex items-center justify-between gap-3 border border-hairline rounded p-3 font-mono-data text-mono-data text-sm"
                    >
                      <span>
                        Caso #{m.case_id} — {m.filename || '(sin nombre)'}
                      </span>
                      <span className="text-tertiary">{m.similarity_percent}% similar</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="font-body-md text-body-md text-on-surface-variant mb-3">
                  No coincide con ninguna imagen analizada antes en esta herramienta.
                </p>
              )}

              <span className="font-label-caps text-label-caps text-on-surface-variant">Señales</span>
              <div className="mt-2 mb-4">
                <FlagsTable flags={result.risk_flags} />
              </div>

              <span className="font-label-caps text-label-caps text-on-surface-variant block mb-2">
                Comprobar búsqueda inversa manualmente
              </span>
              <div className="flex gap-2 flex-wrap">
                {Object.entries(result.reverse_search_links).map(([name, url]) => (
                  <a
                    key={name}
                    href={url}
                    target="_blank"
                    rel="noopener"
                    className="text-xs border border-hairline rounded px-3 py-1.5 text-on-surface-variant hover:text-primary"
                  >
                    {name} ↗
                  </a>
                ))}
              </div>
            </div>
          </div>
        </Card>
      )}

      {result && (
        <Card title="Búsqueda inversa en internet (SerpApi)" subtitle="Envía la foto a SerpApi/Google. Acción opcional y separada del análisis offline.">
          <div className="p-6 flex flex-col gap-3">
            <Button variant="ghost" loading={reverseSearchLoading} onClick={handleReverseSearch}>
              Buscar con SerpApi
            </Button>
            {reverseSearchError && <Alert variant="error">{reverseSearchError}</Alert>}
            {reverseSearchResult && (
              <div className="flex flex-col gap-2">
                <span className="text-xs text-on-surface-variant">
                  {reverseSearchResult.matches.length} coincidencia(s)
                </span>
                {reverseSearchResult.errors.length > 0 && (
                  <Alert variant="info">{reverseSearchResult.errors.join(' · ')}</Alert>
                )}
                {reverseSearchResult.matches.map((m, i) => (
                  <a
                    key={i}
                    href={m.url}
                    target="_blank"
                    rel="noopener"
                    className="border border-hairline rounded p-2 text-sm text-primary"
                  >
                    {m.page_title || m.source || m.url}
                  </a>
                ))}
              </div>
            )}
          </div>
        </Card>
      )}

      {result && (
        <Card title="Reconocimiento facial (PimEyes) — uso acotado">
          <div className="p-6 flex flex-col gap-3">
            <p className="text-xs text-on-surface-variant leading-relaxed">
              Procesa un dato biométrico. Solo úsalo si tienes una base legal concreta para este caso (ej.
              documentar una usurpación de identidad para una denuncia — RGPD art. 9.2.f). La confirmación y el
              resultado quedan sellados de forma permanente en la cadena de integridad. Esto no es asesoría legal.
            </p>
            <label className="flex items-center gap-2 text-sm text-on-surface-variant cursor-pointer">
              <input
                type="checkbox"
                checked={pimeyesConfirmed}
                onChange={(event) => setPimeyesConfirmed(event.target.checked)}
                className="w-4 h-4 accent-error"
              />
              Confirmo que existe base legal para buscar esta cara en este caso concreto
            </label>
            <textarea
              className="w-full bg-canvas border border-hairline rounded font-mono-data text-mono-data text-on-surface placeholder-on-surface-variant p-3 min-h-16"
              placeholder="Notas del caso (opcional) — quedan selladas junto con el resultado"
              value={pimeyesNotes}
              onChange={(event) => setPimeyesNotes(event.target.value)}
            />
            <div>
              <Button variant="danger" disabled={!pimeyesConfirmed} loading={facialSearchLoading} onClick={handleFacialSearch}>
                Buscar con PimEyes
              </Button>
            </div>
            {facialSearchError && <Alert variant="error">{facialSearchError}</Alert>}
            {facialSearchResult && (
              <div className="flex flex-col gap-2">
                <span className="text-xs text-on-surface-variant">
                  {facialSearchResult.matches.length} coincidencia(s)
                </span>
                {facialSearchResult.errors.length > 0 && (
                  <Alert variant="info">{facialSearchResult.errors.join(' · ')}</Alert>
                )}
                {facialSearchResult.matches.map((m, i) => (
                  <a
                    key={i}
                    href={m.url}
                    target="_blank"
                    rel="noopener"
                    className="border border-hairline rounded p-2 text-sm text-primary"
                  >
                    {m.page_title || m.url}
                  </a>
                ))}
              </div>
            )}
          </div>
        </Card>
      )}
    </div>
  )
}
