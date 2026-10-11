import { useCallback, useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { Alert, Button, Card, Input, Modal, Select } from '@/shared/ui'
import { TableWithDrawerLayout } from '@/shared/layout'
import { ApiError, casesLookupApi, reportsApi } from '../api'
import type { CaseOption, Report, ReportGenerateInput } from '../types'
import { ReportDetailDrawer, ReportGenerateForm, ReportTable } from '../components'

/**
 * Traduce un fallo de la API a un mensaje para el perito.
 *
 * El backend del Módulo 5 ya devuelve `detail` en castellano explicando la
 * causa (caso sin cronología, IA no disponible, narrativa no firmable, PDF
 * desaparecido), así que se muestra tal cual. El mapeo por código solo cubre
 * los casos en los que `detail` no es texto — p. ej. los 422 de validación de
 * Pydantic, que llegan como array.
 */
function errorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (typeof error.detail === 'string') return error.detail
    if (error.status === 422) return 'Los datos enviados no son válidos.'
    return `La API ha respondido con un error ${error.status}.`
  }
  return 'No se ha podido conectar con el backend de informes.'
}

/**
 * Página del Módulo 5 (Generador de Informes).
 *
 * Un informe pertenece siempre a un caso, así que la pantalla se organiza
 * alrededor de un caso: se elige uno, se ven todas las versiones emitidas para
 * él y se puede emitir una nueva. Los informes no se editan ni se borran —el
 * backend no expone esas operaciones— porque un informe pericial emitido es
 * inmutable: corregirlo significa emitir una versión nueva.
 */
export function ReportsPage() {
  const [cases, setCases] = useState<CaseOption[]>([])
  const [casesUnavailable, setCasesUnavailable] = useState(false)

  const [selectedCaseId, setSelectedCaseId] = useState<number | null>(null)
  const [manualCaseId, setManualCaseId] = useState('')

  const [reports, setReports] = useState<Report[]>([])
  const [loadingReports, setLoadingReports] = useState(false)
  const [selectedReport, setSelectedReport] = useState<Report | null>(null)

  const [formOpen, setFormOpen] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    casesLookupApi
      .list()
      .then(setCases)
      .catch(() => setCasesUnavailable(true))
  }, [])

  const loadReports = useCallback(async (caseId: number) => {
    setLoadingReports(true)
    setError(null)
    try {
      const data = await reportsApi.listForCase(caseId)
      // El backend los devuelve por versión ascendente; en pantalla interesa
      // ver primero la última emitida.
      setReports([...data].sort((a, b) => b.version - a.version))
    } catch (err) {
      setError(errorMessage(err))
      setReports([])
    } finally {
      setLoadingReports(false)
    }
  }, [])

  const selectCase = (caseId: number | null) => {
    setSelectedCaseId(caseId)
    setSelectedReport(null)
    setReports([])
    if (caseId !== null) loadReports(caseId)
  }

  const handleManualCaseSubmit = (event: FormEvent) => {
    event.preventDefault()
    const parsed = Number(manualCaseId)
    if (Number.isInteger(parsed) && parsed > 0) selectCase(parsed)
  }

  const handleGenerate = async (data: ReportGenerateInput) => {
    setGenerating(true)
    setError(null)
    try {
      const created = await reportsApi.generate(data)
      setFormOpen(false)
      setSelectedCaseId(created.case_id)
      await loadReports(created.case_id)
      setSelectedReport(created)
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setGenerating(false)
    }
  }

  const latestVersion = reports.length > 0 ? Math.max(...reports.map((report) => report.version)) : null
  const selectedCaseName = cases.find((item) => item.id === selectedCaseId)?.nombre

  return (
    <>
      <TableWithDrawerLayout
        main={
          <Card
            className="flex-1"
            title="Informes periciales"
            subtitle={
              selectedCaseId === null
                ? 'Selecciona un caso para ver sus informes'
                : `Caso #${selectedCaseId} · ${reports.length} ${reports.length === 1 ? 'versión emitida' : 'versiones emitidas'}`
            }
            actions={
              <Button variant="primary" size="sm" icon="auto_awesome" onClick={() => setFormOpen(true)}>
                GENERAR INFORME
              </Button>
            }
          >
            <div className="px-6 py-4 border-b border-hairline flex flex-wrap items-end gap-3">
              {casesUnavailable ? (
                <form onSubmit={handleManualCaseSubmit} className="flex items-end gap-2">
                  <div className="w-40">
                    <Input
                      label="ID del caso"
                      type="number"
                      min={1}
                      value={manualCaseId}
                      onChange={(event) => setManualCaseId(event.target.value)}
                    />
                  </div>
                  <Button type="submit" variant="ghost" size="sm" icon="search">
                    Ver informes
                  </Button>
                </form>
              ) : (
                <div className="w-80">
                  <Select
                    label="Caso"
                    options={[
                      { value: '', label: 'Selecciona un caso' },
                      ...cases.map((item) => ({
                        value: String(item.id),
                        label: `#${item.id} — ${item.nombre}`,
                      })),
                    ]}
                    value={selectedCaseId === null ? '' : String(selectedCaseId)}
                    onChange={(event) =>
                      selectCase(event.target.value === '' ? null : Number(event.target.value))
                    }
                  />
                </div>
              )}
            </div>

            {casesUnavailable && (
              <div className="px-6 pt-4">
                <Alert variant="info">
                  No se ha podido leer el listado de casos del Módulo 1, así que el caso se indica por su
                  identificador. Es lo esperado mientras los dos backends sean aplicaciones separadas.
                </Alert>
              </div>
            )}

            {error && (
              <div className="px-6 pt-4">
                <Alert variant="error">{error}</Alert>
              </div>
            )}

            {loadingReports ? (
              <p className="p-6 text-on-surface-variant font-mono-data">Cargando informes...</p>
            ) : (
              <ReportTable
                reports={reports}
                latestVersion={latestVersion}
                selectedReportId={selectedReport?.id}
                onSelect={setSelectedReport}
                emptyMessage={
                  selectedCaseId === null
                    ? 'Elige un caso para ver los informes emitidos.'
                    : 'Este caso todavía no tiene ningún informe emitido.'
                }
              />
            )}
          </Card>
        }
        drawer={
          selectedReport ? (
            <ReportDetailDrawer
              report={selectedReport}
              isLatest={selectedReport.version === latestVersion}
              caseName={selectedCaseName}
              onClose={() => setSelectedReport(null)}
            />
          ) : undefined
        }
        onCloseDrawer={() => setSelectedReport(null)}
      />

      <Modal open={formOpen} onClose={() => setFormOpen(false)} title="Generar informe pericial">
        <ReportGenerateForm
          cases={cases}
          initialCaseId={selectedCaseId}
          submitting={generating}
          onSubmit={handleGenerate}
          onCancel={() => setFormOpen(false)}
        />
      </Modal>
    </>
  )
}
