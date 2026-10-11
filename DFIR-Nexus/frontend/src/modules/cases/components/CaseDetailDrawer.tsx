import { useState } from 'react'
import type { FormEvent } from 'react'
import { Alert, Button, Icon, IconButton, Input, StatusBadge, useCerrarConEscape } from '@/shared/ui'
import type { AuditLogEntry, Case, Evidence, EvidenceCreateInput, EvidenceIntegrityCheck } from '../types'
import { CASE_STATUS_MAP } from './CaseStatusMap'
import { EvidenceListItem } from './EvidenceListItem'
import { AuditLogList } from './AuditLogList'

type CaseDetailDrawerProps = {
  caseItem: Case
  evidences: Evidence[]
  evidencesLoading: boolean
  auditLog: AuditLogEntry[]
  auditLogLoading: boolean
  onEdit: () => void
  onDelete: () => void
  onAddEvidence: (data: EvidenceCreateInput) => Promise<void>
  onDeleteEvidence: (evidence: Evidence) => void
  onVerifyEvidenceIntegrity: (evidence: Evidence) => Promise<EvidenceIntegrityCheck>
  /** Cierra el panel. Sin esto no había forma de quitarlo de en medio. */
  onClose?: () => void
}

const formatDate = (iso: string) =>
  new Date(iso).toLocaleString('es-ES', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })

/**
 * Umbral a partir del cual la descripción se pliega. No mide el desbordamiento
 * real con un `ref`: a tres líneas plegadas, cualquier texto por encima de esto
 * las llena en la práctica, y una medición no cambiaría la decisión.
 */
const DESCRIPCION_LARGA = 180

/**
 * Descripción del caso en la cabecera del panel.
 *
 * Dos cosas que hacía mal y que solo se ven con una descripción de verdad:
 *
 * * **No respetaba los saltos de línea.** El campo es un `TEXT` y el formulario
 *   es un `textarea`, así que puede traer párrafos; un `<p>` a secas los colapsa
 *   y deja un muro de texto. De ahí `whitespace-pre-line`.
 * * **Crecía sin límite dentro de la cabecera**, que es fija y está por encima
 *   de la zona con scroll: una descripción de dos párrafos empujaba las
 *   evidencias fuera del panel. Ahora se plega a tres líneas y se despliega si
 *   se pide.
 */
function Descripcion({ texto }: { texto: string }) {
  const [desplegada, setDesplegada] = useState(false)
  const esLarga = texto.length > DESCRIPCION_LARGA

  return (
    <>
      <p
        className={`font-body-md text-body-md text-on-surface-variant text-sm whitespace-pre-line ${
          esLarga && !desplegada ? 'line-clamp-3' : 'max-h-48 overflow-y-auto'
        }`}
      >
        {texto}
      </p>
      {esLarga && (
        <button
          type="button"
          onClick={() => setDesplegada((valor) => !valor)}
          className="mt-1 text-primary font-label-caps text-label-caps text-[10px] hover:underline"
        >
          {desplegada ? 'Ver menos' : 'Ver descripción completa'}
        </button>
      )}
    </>
  )
}

/**
 * Panel de detalle de caso. Literal del aside de Casos/code.html, adaptado a
 * los campos reales del backend (estado, responsable, fecha_creacion) en vez
 * de los campos ficticios del mock (analista asignado, prioridad, %).
 * La gestión de evidencias vive aquí porque el backend actual no expone un
 * módulo de Evidencias independiente (ver CLAUDE.md, Módulo 1).
 *
 * Un caso eliminado (borrado lógico) o archivado (registro histórico
 * inmutable) no admite edición ni nuevas evidencias: los controles
 * correspondientes se deshabilitan en vez de dejar que el backend los
 * rechace con un 409 sin explicación en la UI.
 */
export function CaseDetailDrawer({
  caseItem,
  evidences,
  evidencesLoading,
  auditLog,
  auditLogLoading,
  onEdit,
  onDelete,
  onAddEvidence,
  onDeleteEvidence,
  onVerifyEvidenceIntegrity,
  onClose,
}: CaseDetailDrawerProps) {
  useCerrarConEscape(onClose)
  const [tipo, setTipo] = useState('')
  const [valor, setValor] = useState('')
  const [submittingEvidence, setSubmittingEvidence] = useState(false)

  const soloLectura = caseItem.eliminado || caseItem.estado === 'archivado'

  const handleAddEvidence = async (event: FormEvent) => {
    event.preventDefault()
    if (!tipo || !valor) return
    setSubmittingEvidence(true)
    try {
      await onAddEvidence({ tipo, valor })
      setTipo('')
      setValor('')
    } finally {
      setSubmittingEvidence(false)
    }
  }

  return (
    /*
     * El panel entero es UNA zona de scroll, y el pie de acciones se queda
     * pegado abajo con `sticky`.
     *
     * Antes solo scrolleaba la franja central, encajonada entre una cabecera
     * alta (chip, título, descripción y avisos) y un pie anclado. En un panel de
     * 384 px eso deja una ventanita, y con un caso con varias evidencias y su
     * registro de auditoría el scroll quedaba escondido en mitad del panel — el
     * mismo problema que ya se arregló en la barra lateral, y por el mismo
     * motivo: el scroll tiene que abarcar todo el alto para que se vea que está.
     *
     * `sticky` y no un pie fijo fuera del scroll porque así Editar y Eliminar
     * siguen alcanzables sin bajar hasta el final, que era lo que el pie anclado
     * resolvía bien y no había que perder. Su fondo pasa a ser opaco: el
     * translúcido de antes dejaba ver el texto pasando por debajo.
     */
    <div className="nexus-glass-panel rounded-lg flex flex-col overflow-y-auto h-full">
      <div className="px-6 py-5 border-b border-hairline bg-surface-container-lowest shrink-0">
        <div className="flex justify-between items-start mb-2">
          <span className="text-primary font-mono-data text-xs px-2 py-1 bg-primary/10 rounded border border-primary/20">
            #{caseItem.id}
          </span>
          <div className="flex items-center gap-1">
            <StatusBadge {...CASE_STATUS_MAP[caseItem.estado]} />
            {onClose && (
              <IconButton icon="close" label="Cerrar el panel" size="sm" onClick={onClose} />
            )}
          </div>
        </div>
        <h3 className="font-headline-md text-headline-md text-on-surface leading-tight mb-2">
          {caseItem.nombre}
        </h3>
        {caseItem.descripcion && (
          <Descripcion texto={caseItem.descripcion} />
        )}
        {caseItem.eliminado && (
          <div className="mt-3">
            <Alert variant="error">
              Este caso está eliminado{caseItem.fecha_eliminacion && ` desde ${formatDate(caseItem.fecha_eliminacion)}`}.
              El registro se conserva, pero no admite nuevas operaciones.
            </Alert>
          </div>
        )}
        {!caseItem.eliminado && caseItem.estado === 'archivado' && (
          <div className="mt-3">
            <Alert variant="info">Caso archivado: registro histórico, no editable.</Alert>
          </div>
        )}
      </div>

      <div className="p-6 space-y-6">
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1">
            <span className="font-label-caps text-label-caps text-on-surface-variant text-[10px]">
              RESPONSABLE
            </span>
            <p className="font-mono-data text-sm text-on-surface">{caseItem.responsable}</p>
          </div>
          <div className="space-y-1">
            <span className="font-label-caps text-label-caps text-on-surface-variant text-[10px]">
              FECHA CREACIÓN
            </span>
            <p className="font-mono-data text-sm text-on-surface">{formatDate(caseItem.fecha_creacion)}</p>
          </div>
          <div className="space-y-1">
            <span className="font-label-caps text-label-caps text-on-surface-variant text-[10px]">
              ÚLTIMA ACTUALIZACIÓN
            </span>
            <p className="font-mono-data text-sm text-on-surface">{formatDate(caseItem.fecha_actualizacion)}</p>
          </div>
        </div>

        <div>
          <div className="flex items-center gap-2 mb-3 border-b border-hairline pb-2">
            <Icon name="account_tree" className="text-tertiary text-sm" />
            <h4 className="font-label-caps text-label-caps text-tertiary">
              NODOS DE EVIDENCIA ({evidences.length})
            </h4>
          </div>

          {evidencesLoading ? (
            <p className="text-on-surface-variant text-xs font-mono-data">Cargando evidencias...</p>
          ) : (
            <div className="space-y-2">
              {evidences.map((evidence) => (
                <EvidenceListItem
                  key={evidence.id}
                  evidence={evidence}
                  onDelete={onDeleteEvidence}
                  onVerifyIntegrity={onVerifyEvidenceIntegrity}
                />
              ))}
              {evidences.length === 0 && (
                <p className="text-on-surface-variant text-xs font-mono-data">
                  Este caso todavía no tiene evidencias registradas.
                </p>
              )}
            </div>
          )}

          {!soloLectura && (
            <form onSubmit={handleAddEvidence} className="flex flex-col gap-2 mt-3">
              <Input placeholder="Tipo (p. ej. disco, log, correo)" value={tipo} onChange={(e) => setTipo(e.target.value)} />
              <Input placeholder="Valor" value={valor} onChange={(e) => setValor(e.target.value)} />
              <Button type="submit" variant="ghost" size="sm" icon="add" loading={submittingEvidence}>
                Añadir evidencia
              </Button>
            </form>
          )}
        </div>

        <div>
          <div className="flex items-center gap-2 mb-3 border-b border-hairline pb-2">
            <Icon name="history" className="text-tertiary text-sm" />
            <h4 className="font-label-caps text-label-caps text-tertiary">AUDITORÍA</h4>
          </div>
          <AuditLogList entries={auditLog} loading={auditLogLoading} />
        </div>
      </div>

      <div className="sticky bottom-0 mt-auto p-4 bg-surface-container-highest border-t border-hairline flex gap-2">
        <Button
          variant="ghost"
          size="sm"
          icon="edit"
          onClick={onEdit}
          disabled={soloLectura}
          className="flex-1"
        >
          Editar
        </Button>
        <Button
          variant="danger"
          size="sm"
          icon="delete"
          onClick={onDelete}
          disabled={caseItem.eliminado}
          className="flex-1"
        >
          Eliminar
        </Button>
      </div>
    </div>
  )
}
