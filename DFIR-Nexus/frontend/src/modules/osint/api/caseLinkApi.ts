import { http } from './httpClient'
import type { OsintCaseType, VinculacionUpdateResponse } from '../types/case'

/**
 * Cliente del único endpoint genérico de vinculación
 * (PATCH /osint-cases/{case_type}/{id}/vinculacion), común a los 8 tipos
 * de investigación — no hay un cliente por tipo, igual que el backend no
 * tiene un endpoint por tipo para esto.
 */
export const caseLinkApi = {
  update: (caseType: OsintCaseType, id: number, caseId: number | null) =>
    http.patch<VinculacionUpdateResponse>(`/osint-cases/${caseType}/${id}/vinculacion`, {
      case_id: caseId,
    }),
}
