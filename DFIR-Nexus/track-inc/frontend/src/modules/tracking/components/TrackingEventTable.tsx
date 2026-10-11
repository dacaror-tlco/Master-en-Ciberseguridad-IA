import { DataTable, type DataTableColumn } from "@/shared/ui";
import { SeverityBadge } from "./SeverityBadge";
import { formatHora } from "./formatHora";
import type { TrackingEventOut } from "../types";

export interface TrackingEventTableProps {
  events: TrackingEventOut[];
  onRowClick?: (evento: TrackingEventOut) => void;
  selectedRowId?: string | number;
  sortKey?: string;
  sortDir?: "asc" | "desc";
  onSort?: (key: string) => void;
}

export function TrackingEventTable({ events, onRowClick, selectedRowId, sortKey, sortDir, onSort }: TrackingEventTableProps) {
  const columns: DataTableColumn<TrackingEventOut>[] = [
    { key: "id", header: "ID", className: "w-16 whitespace-nowrap truncate", render: (e) => `#${e.id}` },
    { key: "hora", header: "Hora", sortable: true, className: "w-56 whitespace-nowrap truncate", render: (e) => <span title={e.hora}>{formatHora(e.hora)}</span> },
    { key: "evento", header: "Evento", className: "truncate", render: (e) => <span title={e.evento}>{e.evento}</span> },
    { key: "severidad", header: "Severidad", sortable: true, className: "w-24 whitespace-nowrap", render: (e) => <SeverityBadge severidad={e.severidad} /> },
    { key: "fuente_log", header: "Fuente", className: "w-40 truncate", render: (e) => <span title={e.fuente_log ?? ""}>{e.fuente_log ?? "—"}</span> },
    { key: "usuario_detectado", header: "Usuario", className: "w-24 whitespace-nowrap truncate", render: (e) => e.usuario_detectado ?? "—" },
  ];

  // Ancho mínimo con scroll horizontal propio: en pantallas estrechas las
  // columnas fijas (hora, severidad...) dejaban la del comando sin sitio.
  return (
    <div className="overflow-x-auto">
      <div className="min-w-[760px]">
        <DataTable
          layout="fixed"
          columns={columns}
          rows={events}
          getRowId={(e) => e.id}
          onRowClick={onRowClick}
          selectedRowId={selectedRowId}
          sortKey={sortKey}
          sortDir={sortDir}
          onSort={onSort}
          emptyMessage="Sin eventos guardados para este caso."
        />
      </div>
    </div>
  );
}
