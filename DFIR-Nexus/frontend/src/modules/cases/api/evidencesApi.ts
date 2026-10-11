import { http } from './httpClient'
import type { Evidence, EvidenceCreateInput, EvidenceIntegrityCheck, EvidenceUpdateInput } from '../types'

/**
 * Cliente para /cases/{case_id}/evidences, alineado 1:1 con
 * app/modules/cases/routes.py. No añade endpoints que no existan en el backend.
 */
export const evidencesApi = {
  list: (caseId: number, skip = 0, limit = 100) =>
    http.get<Evidence[]>(`/cases/${caseId}/evidences?skip=${skip}&limit=${limit}`),
  create: (caseId: number, data: EvidenceCreateInput) =>
    http.post<Evidence>(`/cases/${caseId}/evidences`, data),
  update: (caseId: number, evidenceId: number, data: EvidenceUpdateInput) =>
    http.put<Evidence>(`/cases/${caseId}/evidences/${evidenceId}`, data),
  remove: (caseId: number, evidenceId: number) =>
    http.delete<void>(`/cases/${caseId}/evidences/${evidenceId}`),
  verifyIntegrity: (caseId: number, evidenceId: number) =>
    http.get<EvidenceIntegrityCheck>(`/cases/${caseId}/evidences/${evidenceId}/integridad`),
}
