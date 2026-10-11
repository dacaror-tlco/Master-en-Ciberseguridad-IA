import { useState } from 'react'
import { Icon } from '@/shared/ui'
import type { Evidence, EvidenceIntegrityCheck } from '../types'

type EvidenceListItemProps = {
  evidence: Evidence
  onDelete: (evidence: Evidence) => void
  onVerifyIntegrity: (evidence: Evidence) => Promise<EvidenceIntegrityCheck>
}

const formatDate = (iso: string) =>
  new Date(iso).toLocaleString('es-ES', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })

const truncateHash = (hash: string) => `${hash.slice(0, 8)}…${hash.slice(-4)}`

/**
 * Literal del "nodo de evidencia" del aside de detalle en Casos/code.html.
 * `tipo` es texto libre en el backend (VARCHAR(50)): se usa un único icono
 * genérico en vez de inventar un mapeo tipo→icono que no existe en el modelo.
 *
 * Además del contenido original, muestra lo que el endurecimiento de
 * Evidence añadió y que un perito necesita ver de un vistazo: la fecha del
 * hecho forense (si se conoce, en vez de solo la de alta del registro) y la
 * huella de integridad, con una verificación bajo demanda contra el backend
 * (GET .../integridad) en vez de asumir que el hash mostrado sigue siendo
 * válido.
 */
export function EvidenceListItem({ evidence, onDelete, onVerifyIntegrity }: EvidenceListItemProps) {
  const [verificando, setVerificando] = useState(false)
  const [resultado, setResultado] = useState<EvidenceIntegrityCheck | null>(null)

  const handleVerify = async () => {
    setVerificando(true)
    try {
      setResultado(await onVerifyIntegrity(evidence))
    } finally {
      setVerificando(false)
    }
  }

  const fechaHecho = evidence.fecha_adquisicion ?? evidence.fecha_subida
  const fechaEsAdministrativa = evidence.fecha_adquisicion === null

  return (
    <div className="bg-canvas border border-hairline rounded p-3 flex gap-3 hover:border-primary/50 transition-colors relative group">
      <div className="w-10 h-10 rounded bg-hairline flex items-center justify-center shrink-0">
        <Icon name="inventory_2" className="text-on-surface-variant group-hover:text-primary transition-colors" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="font-mono-data text-xs text-on-surface font-bold truncate">{evidence.tipo}</p>
        <p className="font-body-md text-[11px] text-on-surface-variant mt-1 break-words">{evidence.valor}</p>
        {evidence.observaciones && (
          <p className="font-body-md text-[11px] text-on-surface-variant/70 mt-1 italic break-words">
            {evidence.observaciones}
          </p>
        )}

        <div className="flex flex-wrap items-center gap-x-3 gap-y-1 mt-2 text-[10px] font-mono-data text-on-surface-variant/80">
          <span title={fechaEsAdministrativa ? 'Fecha de alta del registro (no se conoce la de adquisición)' : 'Fecha de adquisición'}>
            <Icon name={fechaEsAdministrativa ? 'schedule' : 'event_available'} className="text-[12px] align-middle mr-0.5" />
            {formatDate(fechaHecho)}
          </span>
          <span title={`Huella SHA-256 del contenido probatorio: ${evidence.hash_valor}`}>
            <Icon name="fingerprint" className="text-[12px] align-middle mr-0.5" />
            {truncateHash(evidence.hash_valor)}
          </span>
        </div>

        <div className="mt-2 flex items-center gap-2">
          <button
            type="button"
            onClick={handleVerify}
            disabled={verificando}
            className="text-[10px] font-label-caps text-tertiary hover:text-primary transition-colors disabled:opacity-50"
          >
            {verificando ? 'Verificando…' : 'Verificar integridad'}
          </button>
          {resultado && (
            <span
              className={`flex items-center gap-1 text-[10px] font-label-caps ${
                resultado.integro ? 'text-primary' : 'text-error'
              }`}
            >
              <Icon name={resultado.integro ? 'verified' : 'gpp_maybe'} filled className="text-[13px]" />
              {resultado.integro ? 'Íntegra' : 'Hash no coincide'}
            </span>
          )}
        </div>
      </div>
      <button
        type="button"
        onClick={() => onDelete(evidence)}
        className="text-on-surface-variant hover:text-error transition-colors self-start opacity-0 group-hover:opacity-100"
        aria-label="Eliminar evidencia"
      >
        <Icon name="delete" className="text-[16px]" />
      </button>
    </div>
  )
}
