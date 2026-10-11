import type { MouseEvent } from 'react'
import { DataTable, Icon, StatusBadge } from '@/shared/ui'
import type { DataTableColumn } from '@/shared/ui'
import type { Case } from '../types'
import { CASE_STATUS_MAP } from './CaseStatusMap'

type CaseTableProps = {
  cases: Case[]
  selectedCaseId?: number | null
  onSelect: (caseItem: Case) => void
  onView: (caseItem: Case) => void
  onEdit: (caseItem: Case) => void
  onDelete: (caseItem: Case) => void
}

const formatDate = (iso: string) =>
  new Date(iso).toLocaleString('es-ES', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })

/*
 * Columnas alineadas con los campos reales de `cases` (CLAUDE.md /
 * schemas.py): no se muestra ninguna columna ("última actividad", etc.) que
 * no exista en el backend, a diferencia del mock original de Casos/code.html.
 *
 * Columna ACCIONES: por debajo de `xl`, `TableWithDrawerLayout` muestra el
 * panel de detalle (CaseDetailDrawer, con sus propios botones
 * Editar/Eliminar) sobre un overlay en vez del aside fijo, pero solo tras
 * seleccionar la fila. Estos tres iconos siguen aquí como atajo directo
 * —sobre todo Eliminar, que si no exigiría abrir el detalle entero para una
 * acción de una sola pulsación— y funcionan en cualquier ancho de ventana.
 */
export function CaseTable({ cases, selectedCaseId, onSelect, onView, onEdit, onDelete }: CaseTableProps) {
  const columns: DataTableColumn<Case>[] = [
    { key: 'id', header: 'ID CASO', render: (c) => <span className="text-primary font-bold">#{c.id}</span> },
    { key: 'nombre', header: 'NOMBRE', render: (c) => <span className="text-on-surface">{c.nombre}</span> },
    {
      key: 'estado',
      header: 'ESTADO',
      render: (c) => <StatusBadge {...CASE_STATUS_MAP[c.estado]} />,
    },
    {
      key: 'responsable',
      header: 'RESPONSABLE',
      render: (c) => <span className="text-on-surface-variant">{c.responsable}</span>,
    },
    {
      key: 'fecha_creacion',
      header: 'FECHA CREACIÓN',
      align: 'right',
      render: (c) => <span className="text-on-surface-variant">{formatDate(c.fecha_creacion)}</span>,
    },
    {
      key: 'acciones',
      header: 'ACCIONES',
      align: 'right',
      render: (c) => {
        const soloLectura = c.eliminado || c.estado === 'archivado'
        const stop = (event: MouseEvent, action: () => void) => {
          event.stopPropagation()
          action()
        }
        return (
          <div className="flex items-center justify-end gap-3">
            <button
              type="button"
              onClick={(e) => stop(e, () => onView(c))}
              className="text-on-surface-variant hover:text-primary transition-colors"
              aria-label={`Ver caso #${c.id}`}
              title="Ver detalle"
            >
              <Icon name="visibility" className="text-[16px]" />
            </button>
            <button
              type="button"
              onClick={(e) => stop(e, () => onEdit(c))}
              disabled={soloLectura}
              className="text-on-surface-variant hover:text-tertiary transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
              aria-label={`Editar caso #${c.id}`}
              title={soloLectura ? 'No editable (eliminado o archivado)' : 'Editar'}
            >
              <Icon name="edit" className="text-[16px]" />
            </button>
            <button
              type="button"
              onClick={(e) => stop(e, () => onDelete(c))}
              disabled={c.eliminado}
              className="text-on-surface-variant hover:text-error transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
              aria-label={`Eliminar caso #${c.id}`}
              title={c.eliminado ? 'Ya eliminado' : 'Eliminar'}
            >
              <Icon name="delete" className="text-[16px]" />
            </button>
          </div>
        )
      },
    },
  ]

  return (
    <DataTable
      columns={columns}
      rows={cases}
      getRowId={(c) => c.id}
      selectedRowId={selectedCaseId}
      onRowClick={onSelect}
      emptyMessage="No hay casos registrados todavía."
    />
  )
}
