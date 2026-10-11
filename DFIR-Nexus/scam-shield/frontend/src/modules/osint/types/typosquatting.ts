/** Refleja app/schemas/typosquatting.py. No se inventa ningún campo. */
import type { AbuseIpInfo, RiskFlag } from './domain'

export type TyposquattingCandidate = {
  variant: string
  technique: string
  resolves: boolean
  ip_address: string | null
  abuseipdb: AbuseIpInfo | null
  risk_score: number | null
  risk_flags: RiskFlag[]
  fully_analyzed: boolean
}

export type TyposquattingCase = {
  id: number
  created_at: string
  domain: string
  analyzed_at: string
  variants_generated: number
  resolved_count: number
  candidates: TyposquattingCandidate[]
  risk_flags: RiskFlag[]
  risk_score: number
  errors: string[]
}

export type TyposquattingCaseListItem = {
  id: number
  domain: string
  resolved_count: number
  risk_score: number
  created_at: string
}
