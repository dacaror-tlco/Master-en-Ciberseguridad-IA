/** Refleja app/schemas/monitoring.py. No se inventa ningún campo. */

export type MonitoredSubject = {
  id: number
  case_type: string
  identifier: string
  enabled: boolean
  check_interval_hours: number
  last_case_id: number | null
  last_score: number | null
  last_bucket: string | null
  last_checked_at: string | null
  created_at: string
}

export type RiskAlert = {
  id: number
  subject_id: number
  case_type: string
  identifier: string
  previous_case_id: number | null
  previous_score: number | null
  previous_bucket: string | null
  new_case_id: number
  new_score: number
  new_bucket: string
  reason: string
  new_flag_codes: string[]
  acknowledged: boolean
  detected_at: string
}
