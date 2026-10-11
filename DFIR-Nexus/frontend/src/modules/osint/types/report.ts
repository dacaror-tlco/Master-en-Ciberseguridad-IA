/** Refleja app/schemas/{report,consolidated}.py. No se inventa ningún campo. */
import type { RiskFlag } from './domain'

/** IDs seleccionables para el informe PDF (app/schemas/report.py::ReportRequest). */
export type CaseType =
  | 'domain'
  | 'email'
  | 'wallet'
  | 'typosquatting'
  | 'phone'
  | 'cnmv'
  | 'image'
  | 'ip'

export type ReportRequest = {
  domain_case_ids: number[]
  email_case_ids: number[]
  wallet_case_ids: number[]
  typosquatting_case_ids: number[]
  phone_case_ids: number[]
  cnmv_check_case_ids: number[]
  image_case_ids: number[]
  ip_case_ids: number[]
  victim_notes: string | null
  ai_narrative: string | null
}

/**
 * ConsolidatedRequest solo admite estos 4 tipos (app/schemas/consolidated.py) —
 * a diferencia de ReportRequest, el backend no acepta phone/cnmv/image/ip aquí.
 */
export type ConsolidatedRequest = {
  domain_case_ids: number[]
  email_case_ids: number[]
  wallet_case_ids: number[]
  typosquatting_case_ids: number[]
  victim_notes: string | null
  include_ai_narrative: boolean
}

export type ConsolidatedResponse = {
  consolidated_score: number
  correlation_flags: RiskFlag[]
  ai_narrative: string | null
  ai_narrative_error: string | null
}
