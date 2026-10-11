/** Refleja app/schemas/email_analysis.py. No se inventa ningún campo. */
import type { AbuseIpInfo, RiskFlag, WhoisInfo } from './domain'

export type EmailHeaderInfo = {
  from_address: string | null
  from_display_name: string | null
  reply_to: string | null
  return_path: string | null
  subject: string | null
  date: string | null
  spf_result: string | null
  dkim_result: string | null
  dmarc_result: string | null
  originating_ip: string | null
  received_hop_count: number
}

export type EmailLinkInfo = {
  url: string
  domain: string | null
  is_shortener: boolean
  redirects_to: string | null
  suspected_brand: string | null
  domain_age_days: number | null
  virustotal_malicious_count: number | null
  checked: boolean
}

export type EmailAttachmentInfo = {
  filename: string
  extension: string | null
  size_bytes: number
  sha256: string
  is_dangerous_extension: boolean
  has_double_extension: boolean
}

export type EmailCase = {
  id: number
  created_at: string
  headers: EmailHeaderInfo
  sender_domain_whois: WhoisInfo | null
  originating_ip_abuseipdb: AbuseIpInfo | null
  links: EmailLinkInfo[]
  attachments: EmailAttachmentInfo[]
  is_raw_source: boolean
  risk_flags: RiskFlag[]
  risk_score: number
  errors: string[]
  analyzed_at: string
  raw_email_sha256: string | null
  ai_explanation: string | null
}

export type EmailCaseListItem = {
  id: number
  from_address: string | null
  subject: string | null
  risk_score: number
  created_at: string
  case_id: number | null
}
