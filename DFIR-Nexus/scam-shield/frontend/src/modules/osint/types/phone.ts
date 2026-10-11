/** Refleja app/schemas/phone_analysis.py. No se inventa ningún campo. */
import type { RiskFlag } from './domain'

export type PhoneInfo = {
  e164: string
  international_format: string
  national_format: string
  country_code: number
  country_name: string | null
  region_description: string | null
  carrier: string | null
  line_type: string
  is_valid: boolean
  is_possible: boolean
  timezones: string[]
}

export type CommunityReportInfo = {
  reports_count: number
  category: string | null
  province: string | null
  danger_level: string | null
}

export type FraudScoreInfo = {
  fraud_score: number | null
  voip: boolean
  prepaid: boolean
  recent_abuse: boolean
  leaked: boolean
  spammer: boolean
  active: boolean | null
  line_type: string | null
  carrier: string | null
}

export type CarrierIntelligenceInfo = {
  carrier_name: string | null
  line_type: string | null
  mobile_country_code: string | null
  mobile_network_code: string | null
}

export type PhoneCase = {
  id: number
  created_at: string
  phone: PhoneInfo | null
  community_reports: CommunityReportInfo | null
  fraud_score: FraudScoreInfo | null
  carrier_intelligence: CarrierIntelligenceInfo | null
  risk_flags: RiskFlag[]
  risk_score: number
  errors: string[]
  analyzed_at: string
}

export type PhoneCaseListItem = {
  id: number
  raw_phone: string
  line_type: string | null
  risk_score: number
  created_at: string
}
