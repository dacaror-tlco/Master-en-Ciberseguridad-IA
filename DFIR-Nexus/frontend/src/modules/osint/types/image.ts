/** Refleja app/schemas/image_analysis.py. No se inventa ningún campo. */
import type { RiskFlag } from './domain'

export type ExifInfo = {
  has_exif: boolean
  camera_make: string | null
  camera_model: string | null
  software: string | null
  date_taken: string | null
  gps_latitude: number | null
  gps_longitude: number | null
}

export type ImageMatch = {
  case_id: number
  filename: string | null
  similarity_percent: number
  analyzed_at: string
}

export type ImageCase = {
  id: number
  created_at: string
  filename: string | null
  perceptual_hash: string
  exif: ExifInfo
  matches: ImageMatch[]
  reverse_search_links: Record<string, string>
  risk_flags: RiskFlag[]
  risk_score: number
  errors: string[]
  analyzed_at: string
  raw_file_sha256: string | null
}

export type ImageCaseListItem = {
  id: number
  filename: string | null
  risk_score: number
  created_at: string
  case_id: number | null
}

export type ReverseImageMatch = {
  url: string
  page_title: string | null
  source: string | null
  thumbnail_url: string | null
}

export type ReverseImageSearchResult = {
  id: number
  image_case_id: number
  matches: ReverseImageMatch[]
  reverse_search_links: Record<string, string>
  risk_flags: RiskFlag[]
  risk_score: number
  errors: string[]
  analyzed_at: string
}

export type FacialSearchMatch = {
  url: string
  page_title: string | null
  thumbnail_url: string | null
  confidence: number | null
}

export type FacialSearchResult = {
  id: number
  image_case_id: number
  confirmed_legal_basis: boolean
  notes: string | null
  matches: FacialSearchMatch[]
  risk_flags: RiskFlag[]
  risk_score: number
  errors: string[]
  requested_at: string
}
