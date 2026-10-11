import { DataTable, StatusBadge } from '@/shared/ui'
import type { DataTableColumn } from '@/shared/ui'
import type { Report } from '../types'
import { formatUtc, reportCode, versionStatus } from './reportFormat'

type ReportTableProps = {
  reports: Report[]
  latestVersion: number | null
  selectedReportId?: number | null
  onSelect: (report: Report) => void
  emptyMessage: string
}

/*
 * Columnas mapeadas 1:1 a los campos reales de `ReportOut`. La única columna
 * derivada es ESTADO (vigente/histórico), que se calcula comparando `version`
 * con la última emitida — no hay ninguna columna decorativa sin respaldo en el
 * backend.
 */
export function ReportTable({
  reports,
  latestVersion,
  selectedReportId,
  onSelect,
  emptyMessage,
}: ReportTableProps) {
  const columns: DataTableColumn<Report>[] = [
    {
      key: 'codigo',
      header: 'CÓDIGO',
      render: (report) => <span className="text-primary font-bold">{reportCode(report)}</span>,
    },
    {
      key: 'version',
      header: 'VERSIÓN',
      render: (report) => <span className="text-on-surface">v{report.version}</span>,
    },
    {
      key: 'estado',
      header: 'ESTADO',
      render: (report) => <StatusBadge {...versionStatus(report.version === latestVersion)} />,
    },
    {
      key: 'generado_por',
      header: 'EMITIDO POR',
      render: (report) => <span className="text-on-surface-variant">{report.generado_por}</span>,
    },
    {
      key: 'fecha_generacion',
      header: 'FECHA DE EMISIÓN',
      align: 'right',
      render: (report) => (
        <span className="text-on-surface-variant">{formatUtc(report.fecha_generacion)}</span>
      ),
    },
  ]

  return (
    <DataTable
      columns={columns}
      rows={reports}
      getRowId={(report) => report.id}
      selectedRowId={selectedReportId}
      onRowClick={onSelect}
      emptyMessage={emptyMessage}
    />
  )
}
