/**
 * Solo los dos campos que la UI de OSINT necesita para el selector de
 * vinculación — evita importar `modules/cases/` (prohibido, ver
 * DESIGN_SYSTEM §13). Calco de `modules/reports/types/report.ts::CaseOption`.
 */
export type CaseOption = {
  id: number
  nombre: string
}

/** Los 8 tipos de investigación que expone /osint/cases. */
export type OsintCaseType =
  | 'domain'
  | 'email'
  | 'wallet'
  | 'typosquatting'
  | 'phone'
  | 'cnmv'
  | 'image'
  | 'ip'

export type VinculacionUpdateResponse = {
  case_type: string
  id: number
  case_id: number | null
  cambiado: boolean
  auditoria_registrada: boolean | null
  auditoria_error: string | null
}
