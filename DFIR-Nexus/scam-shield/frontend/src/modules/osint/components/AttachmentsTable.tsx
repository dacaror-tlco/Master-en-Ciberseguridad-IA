import { Icon } from '@/shared/ui'
import type { EmailAttachmentInfo } from '../types/email'

type AttachmentsTableProps = {
  attachments: EmailAttachmentInfo[]
}

/** Puerto de attachmentsTable() del frontend anterior de scam-shield. */
export function AttachmentsTable({ attachments }: AttachmentsTableProps) {
  if (attachments.length === 0) return null

  return (
    <table className="w-full text-left border-collapse mb-4">
      <thead>
        <tr>
          <th className="py-2 px-2 font-label-caps text-label-caps text-on-surface-variant font-normal">Adjunto</th>
          <th className="py-2 px-2 font-label-caps text-label-caps text-on-surface-variant font-normal">Tamaño</th>
          <th className="py-2 px-2 font-label-caps text-label-caps text-on-surface-variant font-normal">SHA-256</th>
          <th className="py-2 px-2 font-label-caps text-label-caps text-on-surface-variant font-normal">Notas</th>
        </tr>
      </thead>
      <tbody className="font-mono-data text-mono-data text-xs">
        {attachments.map((att, index) => {
          const risky = att.is_dangerous_extension || att.has_double_extension
          const notes = [
            att.is_dangerous_extension && 'extensión ejecutable',
            att.has_double_extension && 'doble extensión',
          ].filter(Boolean)
          return (
            <tr key={index} className="border-b border-hairline">
              <td className="py-2 px-2">
                {risky && <Icon name="warning" filled className="text-error text-[14px] inline mr-1" />}
                {att.filename}
              </td>
              <td className="py-2 px-2">{(att.size_bytes / 1024).toFixed(1)} KB</td>
              <td className="py-2 px-2">{att.sha256.slice(0, 16)}…</td>
              <td className="py-2 px-2">{notes.join(', ') || '—'}</td>
            </tr>
          )
        })}
      </tbody>
    </table>
  )
}
