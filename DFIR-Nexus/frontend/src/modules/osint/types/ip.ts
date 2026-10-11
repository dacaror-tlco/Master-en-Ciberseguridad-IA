/** Refleja app/schemas/ip_analysis.py. No se inventa ningún campo. */
import type { AbuseIpInfo, RiskFlag } from './domain'

export type IpCase = {
  id: number
  created_at: string
  ip: string
  abuseipdb: AbuseIpInfo | null
  risk_flags: RiskFlag[]
  risk_score: number
  errors: string[]
  analyzed_at: string
}

export type IpCaseListItem = {
  id: number
  ip: string
  risk_score: number
  created_at: string
  case_id: number | null
}
