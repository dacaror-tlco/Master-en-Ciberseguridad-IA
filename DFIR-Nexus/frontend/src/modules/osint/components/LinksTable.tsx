import { StatusBadge } from '@/shared/ui'
import type { EmailLinkInfo } from '../types/email'

type LinksTableProps = {
  links: EmailLinkInfo[]
}

/** Puerto de linksTable() del frontend anterior de scam-shield. */
export function LinksTable({ links }: LinksTableProps) {
  if (links.length === 0) return null

  return (
    <div className="overflow-x-auto mb-4">
    <table className="w-full text-left border-collapse">
      <thead>
        <tr>
          <th className="py-2 px-2 font-label-caps text-label-caps text-on-surface-variant font-normal">Enlace</th>
          <th className="py-2 px-2 font-label-caps text-label-caps text-on-surface-variant font-normal">Dominio destino</th>
          <th className="py-2 px-2 font-label-caps text-label-caps text-on-surface-variant font-normal">Notas</th>
        </tr>
      </thead>
      <tbody className="font-mono-data text-mono-data text-xs">
        {links.map((link, index) => {
          const dest = link.redirects_to ?? link.domain
          return (
            <tr key={index} className="border-b border-hairline">
              <td className="py-2 px-2 break-all">{link.url}</td>
              <td className="py-2 px-2">{dest ?? '—'}</td>
              <td className="py-2 px-2 flex flex-col gap-1 items-start">
                {link.is_shortener && (
                  <span>acortador{link.redirects_to ? ` → ${link.redirects_to}` : ' (destino no resuelto)'}</span>
                )}
                {link.suspected_brand && <StatusBadge tone="error" label={`IMITA A "${link.suspected_brand.toUpperCase()}"`} />}
                {link.domain_age_days !== null && <span>dominio de {link.domain_age_days} días</span>}
                {!!link.virustotal_malicious_count && (
                  <StatusBadge tone="error" label={`${link.virustotal_malicious_count} MOTORES VT MALICIOSO`} />
                )}
              </td>
            </tr>
          )
        })}
      </tbody>
    </table>
    </div>
  )
}
