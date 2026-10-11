import type { ReactNode } from 'react'

export type DataTableColumn<T> = {
  key: string
  header: string
  align?: 'left' | 'right'
  render: (row: T) => ReactNode
}

type DataTableProps<T> = {
  columns: DataTableColumn<T>[]
  rows: T[]
  getRowId: (row: T) => string | number
  selectedRowId?: string | number | null
  onRowClick?: (row: T) => void
  emptyMessage?: string
}

/**
 * Tabla de datos genérica. Estilo literal de la tabla de casos en
 * Casos/code.html: header sticky, filas en mono-data, hover y fila
 * seleccionada marcada con un borde izquierdo de 2px en `primary`.
 * No conoce el dominio de las filas que recibe.
 */
export function DataTable<T>({
  columns,
  rows,
  getRowId,
  selectedRowId,
  onRowClick,
  emptyMessage = 'No hay resultados.',
}: DataTableProps<T>) {
  return (
    <table className="w-full text-left border-collapse">
      <thead className="sticky top-0 bg-canvas border-b border-hairline z-10">
        <tr>
          {columns.map((column) => (
            <th
              key={column.key}
              className={`py-3 px-6 font-label-caps text-label-caps text-on-surface-variant font-normal
                ${column.align === 'right' ? 'text-right' : ''}`}
            >
              {column.header}
            </th>
          ))}
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
                  className={`py-4 px-6 ${column.align === 'right' ? 'text-right' : ''}
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
