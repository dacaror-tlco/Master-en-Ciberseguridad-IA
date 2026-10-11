import { DataTable, StatusBadge, type DataTableColumn } from "@/shared/ui";
import { CASE_STATUS_MAP } from "./CaseStatusMap";
import type { Case } from "../types";

export interface CaseTableProps {
  cases: Case[];
  selectedCaseId?: number;
  onRowClick?: (c: Case) => void;
}

/**
 * Columnas ID CASO, NOMBRE, ESTADO, RESPONSABLE, FECHA CREACIÓN — todas
 * mapeadas 1:1 a campos reales del backend, sin ninguna decorativa
 * inventada (ver DESIGN_SYSTEM.md §10).
 */
export function CaseTable({ cases, selectedCaseId, onRowClick }: CaseTableProps) {
  const columns: DataTableColumn<Case>[] = [
    { key: "id", header: "ID Caso", render: (c) => `#${c.id}` },
    { key: "nombre", header: "Nombre", render: (c) => c.nombre },
    {
      key: "estado",
      header: "Estado",
      render: (c) => {
        const status = CASE_STATUS_MAP[c.estado];
        return <StatusBadge label={status.label} tone={status.tone} />;
      },
    },
    { key: "responsable", header: "Responsable", render: (c) => c.responsable ?? "—" },
    {
      key: "fecha_creacion",
      header: "Fecha creación",
      align: "right",
      render: (c) => (c.fecha_creacion ? new Date(c.fecha_creacion).toLocaleDateString() : "—"),
    },
  ];

  return (
    <DataTable
      columns={columns}
      rows={cases}
      getRowId={(c) => c.id}
      selectedRowId={selectedCaseId}
      onRowClick={onRowClick}
      emptyMessage="No hay casos todavía."
    />
  );
}
