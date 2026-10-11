import { useCallback, useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Alert, Button, Card, Modal } from '@/shared/ui'
import { TableWithDrawerLayout } from '@/shared/layout'
import { casesApi, evidencesApi, ApiError } from '../api'
import type {
  AuditLogEntry,
  Case,
  CaseCreateInput,
  CaseUpdateInput,
  Evidence,
  EvidenceCreateInput,
} from '../types'
import { CaseTable, CaseDetailDrawer, CaseForm } from '../components'

function errorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return typeof error.detail === 'string' ? error.detail : 'La API rechazó la solicitud.'
  }
  return 'No se ha podido conectar con el backend.'
}

/**
 * Página de Gestión de Casos. Usa datos reales de /cases y
 * /cases/{id}/evidences (app/modules/cases/routes.py): sin mocks.
 */
export function CasesPage() {
  const [cases, setCases] = useState<Case[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [selectedCase, setSelectedCase] = useState<Case | null>(null)
  const [evidences, setEvidences] = useState<Evidence[]>([])
  const [evidencesLoading, setEvidencesLoading] = useState(false)
  const [auditLog, setAuditLog] = useState<AuditLogEntry[]>([])
  const [auditLogLoading, setAuditLogLoading] = useState(false)

  const [formOpen, setFormOpen] = useState(false)
  const [formMode, setFormMode] = useState<'create' | 'edit'>('create')
  const [submitting, setSubmitting] = useState(false)

  const [deleteTarget, setDeleteTarget] = useState<Case | null>(null)
  const [deleting, setDeleting] = useState(false)

  const [searchParams, setSearchParams] = useSearchParams()

  const loadCases = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await casesApi.list()
      setCases(data)
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadCases()
  }, [loadCases])


  const loadEvidences = useCallback(async (caseId: number) => {
    setEvidencesLoading(true)
    try {
      const data = await evidencesApi.list(caseId)
      setEvidences(data)
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setEvidencesLoading(false)
    }
  }, [])

  const loadAuditLog = useCallback(async (caseId: number) => {
    setAuditLogLoading(true)
    try {
      const data = await casesApi.auditLog(caseId)
      setAuditLog(data)
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setAuditLogLoading(false)
    }
  }, [])

  /*
   * `/cases?caso=<id>` selecciona ese expediente al llegar. Es lo que usa el
   * buscador de la barra superior, que vive en `shared/layout` y por tanto no
   * puede tocar el estado de esta página: la URL es el único canal que los dos
   * comparten, y además hace el enlace compartible.
   *
   * El parámetro se limpia en cuanto se atiende, con `replace` para no dejar una
   * entrada más en el historial: si se quedara en la URL, cerrar el panel y
   * volver atrás lo reabriría, y no es lo que espera nadie.
   */
  useEffect(() => {
    const pedido = searchParams.get('caso')
    if (!pedido || cases.length === 0) return

    const encontrado = cases.find((item) => String(item.id) === pedido)
    if (encontrado) {
      setSelectedCase(encontrado)
      loadEvidences(encontrado.id)
      loadAuditLog(encontrado.id)
    } else {
      setError(`No existe ningún caso con el número ${pedido}, o ya no está disponible.`)
    }
    setSearchParams({}, { replace: true })
  }, [searchParams, setSearchParams, cases, loadEvidences, loadAuditLog])

  const handleSelectCase = (caseItem: Case) => {
    setSelectedCase(caseItem)
    loadEvidences(caseItem.id)
    loadAuditLog(caseItem.id)
  }

  const handleCreate = () => {
    setFormMode('create')
    setFormOpen(true)
  }

  const handleEdit = (caseItem?: Case) => {
    if (caseItem) setSelectedCase(caseItem)
    setFormMode('edit')
    setFormOpen(true)
  }

  const handleFormSubmit = async (data: CaseCreateInput | CaseUpdateInput) => {
    setSubmitting(true)
    setError(null)
    try {
      if (formMode === 'create') {
        const created = await casesApi.create(data as CaseCreateInput)
        await loadCases()
        setSelectedCase(created)
        setEvidences([])
        setAuditLog([])
        loadAuditLog(created.id)
      } else if (selectedCase) {
        const updated = await casesApi.update(selectedCase.id, data)
        await loadCases()
        setSelectedCase(updated)
        loadAuditLog(updated.id)
      }
      setFormOpen(false)
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setSubmitting(false)
    }
  }

  const handleConfirmDelete = async () => {
    if (!deleteTarget) return
    setDeleting(true)
    setError(null)
    try {
      await casesApi.remove(deleteTarget.id)
      if (selectedCase?.id === deleteTarget.id) {
        setSelectedCase(null)
        setEvidences([])
        setAuditLog([])
      }
      setDeleteTarget(null)
      await loadCases()
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setDeleting(false)
    }
  }

  const handleAddEvidence = async (data: EvidenceCreateInput) => {
    if (!selectedCase) return
    try {
      await evidencesApi.create(selectedCase.id, data)
      await loadEvidences(selectedCase.id)
      await loadAuditLog(selectedCase.id)
    } catch (err) {
      setError(errorMessage(err))
    }
  }

  const handleDeleteEvidence = async (evidence: Evidence) => {
    if (!selectedCase) return
    try {
      await evidencesApi.remove(selectedCase.id, evidence.id)
      await loadEvidences(selectedCase.id)
      await loadAuditLog(selectedCase.id)
    } catch (err) {
      setError(errorMessage(err))
    }
  }

  const handleVerifyEvidenceIntegrity = async (evidence: Evidence) => {
    if (!selectedCase) throw new Error('Sin caso seleccionado')
    return evidencesApi.verifyIntegrity(selectedCase.id, evidence.id)
  }

  return (
    <>
      <TableWithDrawerLayout
        main={
          <Card
            className="flex-1"
            title="Registro de Casos"
            subtitle={`Mostrando ${cases.length} caso${cases.length === 1 ? '' : 's'}`}
            actions={
              <Button variant="primary" size="sm" icon="add" onClick={handleCreate}>
                NUEVO CASO
              </Button>
            }
          >
            {error && (
              <div className="p-4">
                <Alert variant="error">{error}</Alert>
              </div>
            )}
            {loading ? (
              <p className="p-6 text-on-surface-variant font-mono-data">Cargando casos...</p>
            ) : (
              <CaseTable
                cases={cases}
                selectedCaseId={selectedCase?.id}
                onSelect={handleSelectCase}
                onView={handleSelectCase}
                onEdit={handleEdit}
                onDelete={setDeleteTarget}
              />
            )}
          </Card>
        }
        drawer={
          selectedCase ? (
            <CaseDetailDrawer
              caseItem={selectedCase}
              evidences={evidences}
              evidencesLoading={evidencesLoading}
              auditLog={auditLog}
              auditLogLoading={auditLogLoading}
              onEdit={handleEdit}
              onDelete={() => setDeleteTarget(selectedCase)}
              onAddEvidence={handleAddEvidence}
              onDeleteEvidence={handleDeleteEvidence}
              onVerifyEvidenceIntegrity={handleVerifyEvidenceIntegrity}
              onClose={() => setSelectedCase(null)}
            />
          ) : undefined
        }
        onCloseDrawer={() => setSelectedCase(null)}
      />

      <Modal
        open={formOpen}
        onClose={() => setFormOpen(false)}
        title={formMode === 'create' ? 'Nuevo caso' : 'Editar caso'}
      >
        <CaseForm
          initialValue={formMode === 'edit' ? (selectedCase ?? undefined) : undefined}
          submitting={submitting}
          onSubmit={handleFormSubmit}
          onCancel={() => setFormOpen(false)}
        />
      </Modal>

      <Modal
        open={deleteTarget !== null}
        onClose={() => setDeleteTarget(null)}
        title="Eliminar caso"
        footer={
          <>
            <Button variant="ghost" onClick={() => setDeleteTarget(null)}>
              Cancelar
            </Button>
            <Button variant="danger" onClick={handleConfirmDelete} loading={deleting}>
              Eliminar
            </Button>
          </>
        }
      >
        <p className="text-on-surface font-body-md text-body-md">
          ¿Seguro que quieres eliminar el caso <strong>{deleteTarget?.nombre}</strong>? El caso y sus
          evidencias se marcarán como eliminados y dejarán de aparecer en los listados, pero el
          registro y su historial de auditoría se conservan.
        </p>
      </Modal>
    </>
  )
}
