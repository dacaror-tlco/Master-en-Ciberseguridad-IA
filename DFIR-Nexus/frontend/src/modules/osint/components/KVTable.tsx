import type { ReactNode } from 'react'

type KVTableProps = {
  rows: [string, ReactNode][]
}

/**
 * Tabla clave/valor genérica para el detalle de un análisis (puerto de
 * kvTable() del frontend anterior de scam-shield). Filas con valor
 * null/undefined/'' muestran un guion, igual que antes.
 */
export function KVTable({ rows }: KVTableProps) {
  return (
    <table className="w-full text-left border-collapse font-mono-data text-mono-data mb-4">
      <tbody>
        {rows.map(([key, value]) => (
          <tr key={key} className="border-b border-hairline">
            <td className="py-1.5 px-2 text-on-surface-variant align-top w-2/5">{key}</td>
            <td className="py-1.5 px-2 text-on-surface align-top break-words">
              {value === null || value === undefined || value === '' ? '—' : value}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
