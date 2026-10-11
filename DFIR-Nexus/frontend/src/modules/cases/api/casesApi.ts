import { http } from './httpClient'
import type { AuditLogEntry, Case, CaseCreateInput, CaseUpdateInput } from '../types'

/**
 * Cliente para /cases, alineado 1:1 con app/modules/cases/routes.py.
 * No añade endpoints ni parámetros que no existan en el backend.
 */
export const casesApi = {
  list: (skip = 0, limit = 100) => http.get<Case[]>(`/cases?skip=${skip}&limit=${limit}`),
  get: (caseId: number) => http.get<Case>(`/cases/${caseId}`),
  create: (data: CaseCreateInput) => http.post<Case>('/cases', data),
  update: (caseId: number, data: CaseUpdateInput) => http.put<Case>(`/cases/${caseId}`, data),
  remove: (caseId: number) => http.delete<void>(`/cases/${caseId}`),
  auditLog: (caseId: number) => http.get<AuditLogEntry[]>(`/cases/${caseId}/auditoria`),
}
