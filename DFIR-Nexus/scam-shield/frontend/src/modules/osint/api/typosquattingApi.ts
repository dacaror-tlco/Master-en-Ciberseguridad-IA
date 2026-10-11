import { http } from './httpClient'
import type { TyposquattingCase, TyposquattingCaseListItem } from '../types/typosquatting'

export const typosquattingApi = {
  analyze: (domain: string, includeFullAnalysis: boolean) =>
    http.post<TyposquattingCase>('/analysis/typosquatting', {
      domain,
      include_full_analysis: includeFullAnalysis,
      max_full_analysis: 4,
    }),
  list: (skip = 0, limit = 50) =>
    http.get<TyposquattingCaseListItem[]>(`/typosquatting-cases?skip=${skip}&limit=${limit}`),
  get: (caseId: number) => http.get<TyposquattingCase>(`/typosquatting-cases/${caseId}`),
}
