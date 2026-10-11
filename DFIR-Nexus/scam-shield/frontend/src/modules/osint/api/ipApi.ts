import { http } from './httpClient'
import type { IpCase, IpCaseListItem } from '../types/ip'

export const ipApi = {
  analyze: (ip: string) => http.post<IpCase>('/analysis/ip', { ip }),
  list: (skip = 0, limit = 50) => http.get<IpCaseListItem[]>(`/ip-cases?skip=${skip}&limit=${limit}`),
  get: (caseId: number) => http.get<IpCase>(`/ip-cases/${caseId}`),
}
