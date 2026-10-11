/** Refleja app/schemas/cnmv.py. No se inventa ningún campo. */
import type { RiskFlag } from './domain'

export type CnmvMatch = {
  fecha: string
  companias: string
  observaciones: string | null
}

export type FcaMatch = {
  name: string
  reference_number: string
  status: string
  type_of_business: string | null
  url: string | null
}

export type CnmvRegisteredEntity = {
  code: string
  name: string
}

export type CnmvCheckCase = {
  id: number
  created_at: string
  query: string
  match_count: number
  matches: CnmvMatch[]
  fca_matches: FcaMatch[] | null
  registry_matches: CnmvRegisteredEntity[] | null
  risk_flags: RiskFlag[]
  risk_score: number
  errors: string[]
  analyzed_at: string
}

export type CnmvCheckCaseListItem = {
  id: number
  query: string
  match_count: number
  risk_score: number
  created_at: string
}
