import { http } from './httpClient'
import type { PhoneCase, PhoneCaseListItem } from '../types/phone'

export const phoneApi = {
  analyze: (phone: string, defaultRegion: string) =>
    http.post<PhoneCase>('/analysis/phone', { phone, default_region: defaultRegion }),
  list: (skip = 0, limit = 50) => http.get<PhoneCaseListItem[]>(`/phone-cases?skip=${skip}&limit=${limit}`),
  get: (caseId: number) => http.get<PhoneCase>(`/phone-cases/${caseId}`),
}
