import { StatusBadge } from '@/shared/ui'
import { severityTone } from './riskLevel'
import type { RiskFlag } from '../types/domain'

type FlagsTableProps = {
  flags: RiskFlag[]
}

const SEVERITY_LABEL: Record<RiskFlag['severity'], string> = {
  high: 'ALTA',
  medium: 'MEDIA',
  low: 'BAJA',
}

/** Puerto de flagsTable() del frontend anterior de scam-shield. */
export function FlagsTable({ flags }: FlagsTableProps) {
  if (flags.length === 0) {
    return <p className="font-body-md text-body-md text-on-surface-variant">No se detectaron señales de riesgo.</p>
  }

  return (
    <table className="w-full text-left border-collapse mb-4">
      <thead>
        <tr>
          <th className="py-2 px-2 font-label-caps text-label-caps text-on-surface-variant font-normal">
            Severidad
          </th>
          <th className="py-2 px-2 font-label-caps text-label-caps text-on-surface-variant font-normal">Señal</th>
          <th className="py-2 px-2 font-label-caps text-label-caps text-on-surface-variant font-normal">
            Descripción
          </th>
        </tr>
      </thead>
      <tbody className="font-mono-data text-mono-data">
        {flags.map((flag, index) => (
          <tr key={`${flag.code}-${index}`} className="border-b border-hairline">
            <td className="py-2 px-2 align-top">
              <StatusBadge label={SEVERITY_LABEL[flag.severity]} tone={severityTone(flag.severity)} />
            </td>
            <td className="py-2 px-2 align-top text-xs">{flag.code}</td>
            <td className="py-2 px-2 align-top font-body-md text-body-md text-on-surface">{flag.description}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
