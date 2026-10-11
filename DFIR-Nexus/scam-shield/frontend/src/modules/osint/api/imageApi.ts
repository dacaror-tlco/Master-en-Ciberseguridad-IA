import { http } from './httpClient'
import type { FacialSearchResult, ImageCase, ImageCaseListItem, ReverseImageSearchResult } from '../types/image'

export const imageApi = {
  analyze: async (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return http.post<ImageCase>('/analysis/image', formData)
  },
  reverseSearch: (caseId: number) => http.post<ReverseImageSearchResult>(`/analysis/image/${caseId}/reverse-search`),
  facialSearch: async (caseId: number, confirmedLegalBasis: boolean, notes?: string) => {
    const formData = new FormData()
    formData.append('confirmed_legal_basis', String(confirmedLegalBasis))
    if (notes) formData.append('notes', notes)
    return http.post<FacialSearchResult>(`/analysis/image/${caseId}/facial-search`, formData)
  },
  list: (skip = 0, limit = 50) => http.get<ImageCaseListItem[]>(`/image-cases?skip=${skip}&limit=${limit}`),
  get: (caseId: number) => http.get<ImageCase>(`/image-cases/${caseId}`),
}
