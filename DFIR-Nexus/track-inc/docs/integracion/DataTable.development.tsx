import type { ReactNode } from 'react'

import { Icon } from '../Icon'

export type DataTableColumn<T> = {
  key: string
  header: string
  align?: 'left' | 'right'
  render: (row: T) => ReactNode
  /** Opcional: con `onSort`, la cabecera se vuelve pulsable y alterna el
   *  orden por esta columna. Las columnas que no lo declaran no cambian. */
  sortable?: boolean
  /** Opcional: clases extra para la celda y su cabecera (ancho, truncado...). */
  className?: string
}

type DataTableProps<T> = {
  columns: DataTableColumn<T>[]
  rows: T[]
  getRowId: (row: T) => string | number
  selectedRowId?: string | number | null
  onRowClick?: (row: T) => void
  emptyMessage?: string
  /** Opcional: columna por la que se está ordenando ahora mismo. */
  sortKey?: string
  sortDir?: 'asc' | 'desc'
  /** Opcional: se llama con la clave de la columna al pulsar su cabecera. */
  onSort?: (key: string) => void
  /** Opcional: 'fixed' hace que los anchos declarados en `className` manden
   *  de verdad; con 'auto' (por defecto) el navegador los reparte. */
  layout?: 'auto' | 'fixed'
}

/**
 * Tabla de datos genérica. Estilo literal de la tabla de casos en
 * Casos/code.html: header sticky, filas en mono-data, hover y fila
 * seleccionada marcada con un borde izquierdo de 2px en `primary`.
 * No conoce el dominio de las filas que recibe.
 *
 * Ordenación, clases por columna y `layout` son opcionales: sin ellos la
 * tabla se pinta exactamente igual que antes.
 */
export function DataTable<T>({
  columns,
  rows,
  getRowId,
  selectedRowId,
  onRowClick,
  emptyMessage = 'No hay resultados.',
  sortKey,
  sortDir,
  onSort,
  layout = 'auto',
}: DataTableProps<T>) {
  return (
    <table className={`w-full text-left border-collapse ${layout === 'fixed' ? 'table-fixed' : ''}`}>
      <thead className="sticky top-0 bg-canvas border-b border-hairline z-10">
        <tr>
          {columns.map((column) => {
            const ordenable = Boolean(column.sortable && onSort)
            const activa = ordenable && sortKey === column.key
            return (
              <th
                key={column.key}
                aria-sort={activa ? (sortDir === 'asc' ? 'ascending' : 'descending') : undefined}
                className={`py-3 px-6 font-label-caps text-label-caps font-normal
                  ${activa ? 'text-on-surface' : 'text-on-surface-variant'}
                  ${column.align === 'right' ? 'text-right' : ''} ${column.className ?? ''}`}
              >
                {ordenable ? (
                  <button
                    type="button"
                    onClick={() => onSort?.(column.key)}
                    className="inline-flex items-center gap-1 uppercase hover:text-on-surface transition-colors"
                  >
                    {column.header}
                    <Icon
                      name={activa && sortDir === 'desc' ? 'arrow_downward' : 'arrow_upward'}
                      className={`text-[16px] leading-none ${activa ? 'opacity-100' : 'opacity-0'}`}
                    />
                  </button>
                ) : (
                  column.header
                )}
              </th>
            )
          })}
        </tr>
      </thead>
      <tbody className="font-mono-data text-mono-data">
        {rows.length === 0 && (
          <tr>
            <td colSpan={columns.length} className="py-8 px-6 text-center text-on-surface-variant">
              {emptyMessage}
            </td>
          </tr>
        )}
        {rows.map((row) => {
          const rowId = getRowId(row)
          const isSelected = rowId === selectedRowId
          return (
            <tr
              key={rowId}
              onClick={() => onRowClick?.(row)}
              className={`border-b border-hairline transition-colors relative
                ${onRowClick ? 'cursor-pointer hover:bg-hairline' : ''}
                ${isSelected ? 'bg-hairline/50' : ''}`}
            >
              {columns.map((column, index) => (
                <td
                  key={column.key}
                  className={`py-4 px-6 ${column.align === 'right' ? 'text-right' : ''} ${column.className ?? ''}
                    ${index === 0 ? `border-l-2 ${isSelected ? 'border-primary' : 'border-transparent'}` : ''}`}
                >
                  {column.render(row)}
                </td>
              ))}
            </tr>
          )
        })}
      </tbody>
    </table>
  )
}
