import { http } from './httpClient'
import type { EmailCase, EmailCaseListItem } from '../types/email'

export const emailApi = {
  analyzeRaw: (raw_email: string) => http.post<EmailCase>('/analysis/email', { raw_email }),
  analyzeFile: async (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return http.post<EmailCase>('/analysis/email/file', formData)
  },
  list: (skip = 0, limit = 50) => http.get<EmailCaseListItem[]>(`/email-cases?skip=${skip}&limit=${limit}`),
  get: (caseId: number) => http.get<EmailCase>(`/email-cases/${caseId}`),
}
