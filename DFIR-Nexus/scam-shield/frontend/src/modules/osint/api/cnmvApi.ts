import { http } from './httpClient'
import type { CnmvCheckCase, CnmvCheckCaseListItem } from '../types/cnmv'

export const cnmvApi = {
  check: (query: string) => http.post<CnmvCheckCase>('/analysis/cnmv-check', { query }),
  list: (skip = 0, limit = 50) => http.get<CnmvCheckCaseListItem[]>(`/cnmv-check-cases?skip=${skip}&limit=${limit}`),
  get: (caseId: number) => http.get<CnmvCheckCase>(`/cnmv-check-cases/${caseId}`),
}
