import type { ReactNode } from "react";

import { Icon } from "../Icon";

export interface DataTableColumn<T> {
  key: string;
  header: string;
  align?: "left" | "right" | "center";
  render: (row: T) => ReactNode;
  /** Si es true y se pasa `onSort`, la cabecera se vuelve pulsable y
   *  alterna el orden por esa columna. Opcional: las columnas que no lo
   *  declaran se pintan como siempre. */
  sortable?: boolean;
  /** Clases extra para la celda y su cabecera: ancho, whitespace, etc.
   *  Sirve para que las columnas cortas no le roben sitio a la larga. */
  className?: string;
}

export interface DataTableProps<T> {
  columns: DataTableColumn<T>[];
  rows: T[];
  getRowId: (row: T) => string | number;
  selectedRowId?: string | number;
  onRowClick?: (row: T) => void;
  emptyMessage?: string;
  /** Columna por la que se esta ordenando ahora mismo. */
  sortKey?: string;
  sortDir?: "asc" | "desc";
  /** Se llama con la clave de la columna al pulsar su cabecera. */
  onSort?: (key: string) => void;
  /** "fixed" hace que los anchos declarados en cada columna manden de
   *  verdad; con "auto" (por defecto) el navegador los ensancha segun el
   *  contenido y las clases w-* quedan en sugerencia. */
  layout?: "auto" | "fixed";
}

const ALIGN_CLASSES: Record<NonNullable<DataTableColumn<unknown>["align"]>, string> = {
  left: "text-left",
  right: "text-right",
  center: "text-center",
};

/**
 * Tabla genérica <T,>, sin conocimiento de dominio. El módulo consumidor
 * decide columnas y cómo renderizar cada celda. Header sticky, cuerpo en
 * mono-data, hover solo si hay onRowClick, selección vía getRowId
 * (ver DESIGN_SYSTEM.md §10).
 */
export function DataTable<T>({
  columns,
  rows,
  getRowId,
  selectedRowId,
  onRowClick,
  emptyMessage = "No hay datos disponibles.",
  sortKey,
  sortDir,
  onSort,
  layout = "auto",
}: DataTableProps<T>) {
  return (
    <table className={`w-full border-collapse ${layout === "fixed" ? "table-fixed" : ""}`}>
      <thead className="sticky top-0 bg-canvas border-b border-hairline">
        <tr>
          {columns.map((col) => {
            const ordenable = Boolean(col.sortable && onSort);
            const activa = ordenable && sortKey === col.key;
            return (
              <th
                key={col.key}
                aria-sort={activa ? (sortDir === "asc" ? "ascending" : "descending") : undefined}
                className={`px-4 py-3 font-label text-label-caps uppercase ${
                  activa ? "text-on-surface" : "text-on-surface-variant"
                } ${ALIGN_CLASSES[col.align ?? "left"]} ${col.className ?? ""}`}
              >
                {ordenable ? (
                  <button
                    type="button"
                    onClick={() => onSort!(col.key)}
                    className="inline-flex items-center gap-1 uppercase hover:text-on-surface transition-colors"
                  >
                    {col.header}
                    {/* La flecha solo aparece en la columna activa, para no
                        llenar la cabecera de iconos. Se usa Icon y no un span
                        suelto: DESIGN_SYSTEM.md §9 lo exige. */}
                    <Icon
                      name={activa && sortDir === "desc" ? "arrow_downward" : "arrow_upward"}
                      className={`text-[16px] leading-none ${activa ? "opacity-100" : "opacity-0"}`}
                    />
                  </button>
                ) : (
                  col.header
                )}
              </th>
            );
          })}
        </tr>
      </thead>
      <tbody className="font-body text-mono-data text-on-surface">
        {rows.length === 0 ? (
          <tr>
            <td colSpan={columns.length} className="px-4 py-8 text-center text-on-surface-variant">
              {emptyMessage}
            </td>
          </tr>
        ) : (
          rows.map((row) => {
            const rowId = getRowId(row);
            const isSelected = selectedRowId !== undefined && rowId === selectedRowId;
            return (
              <tr
                key={rowId}
                onClick={onRowClick ? () => onRowClick(row) : undefined}
                className={`${onRowClick ? "cursor-pointer hover:bg-hairline" : ""} ${isSelected ? "bg-hairline/50" : ""}`}
              >
                {columns.map((col, idx) => (
                  <td
                    key={col.key}
                    className={`px-4 py-3 ${ALIGN_CLASSES[col.align ?? "left"]} ${col.className ?? ""} ${
                      idx === 0 ? `border-l-2 ${isSelected ? "border-primary" : "border-transparent"}` : ""
                    }`}
                  >
                    {col.render(row)}
                  </td>
                ))}
              </tr>
            );
          })
        )}
      </tbody>
    </table>
  );
}
