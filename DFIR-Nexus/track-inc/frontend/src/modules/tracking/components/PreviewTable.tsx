import { DataTable, type DataTableColumn } from "@/shared/ui";
import { SeverityBadge } from "./SeverityBadge";
import { formatHora } from "./formatHora";
import type { AnalyzePreviewItem } from "../types";

export interface PreviewTableProps {
  items: AnalyzePreviewItem[];
  onRowClick?: (item: AnalyzePreviewItem) => void;
  selectedRowId?: string | number;
  sortKey?: string;
  sortDir?: "asc" | "desc";
  onSort?: (key: string) => void;
}

export function PreviewTable({ items, onRowClick, selectedRowId, sortKey, sortDir, onSort }: PreviewTableProps) {
  const columns: DataTableColumn<AnalyzePreviewItem>[] = [
    // Numero de linea dentro del fichero de log, no la posicion en la
    // tabla: se mantiene aunque se invierta el orden.
    {
      key: "linea",
      header: "Línea",
      align: "right",
      className: "w-14",
      render: (e) => (e.numero_linea != null ? e.numero_linea : "—"),
    },
    { key: "hora", header: "Hora", sortable: true, className: "w-56 whitespace-nowrap truncate", render: (e) => <span title={e.hora}>{formatHora(e.hora)}</span> },
    {
      key: "evento",
      header: "Evento",
      // Una linea por evento: la tabla se lee como un log. Si no cabe se
      // corta con puntos suspensivos, y el comando completo se ve entero
      // en el panel de detalle al pulsar la fila.
      className: "truncate",
      render: (e) => <span title={e.evento}>{e.evento}</span>,
    },
    { key: "severidad", header: "Severidad", sortable: true, className: "w-24 whitespace-nowrap", render: (e) => <SeverityBadge severidad={e.severidad} /> },
    { key: "usuario", header: "Usuario", className: "w-24 whitespace-nowrap truncate", render: (e) => e.usuario_detectado ?? "—" },
    { key: "regla", header: "Regla", className: "w-40 truncate", render: (e) => <span title={e.regla ?? ""}>{e.regla ?? "—"}</span> },
  ];

  // Ancho mínimo con scroll horizontal propio: en pantallas estrechas las
  // columnas fijas (hora, severidad...) dejaban la del comando sin sitio.
  return (
    <div className="overflow-x-auto">
      <div className="min-w-[760px]">
        <DataTable
          layout="fixed"
          columns={columns}
          rows={items}
          getRowId={(e) => `${e.numero_linea ?? e.hora}-${e.evento}`}
          onRowClick={onRowClick}
          selectedRowId={selectedRowId}
          sortKey={sortKey}
          sortDir={sortDir}
          onSort={onSort}
          emptyMessage="Sin eventos que mostrar."
        />
      </div>
    </div>
  );
}
