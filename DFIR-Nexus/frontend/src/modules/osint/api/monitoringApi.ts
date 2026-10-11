import { http } from './httpClient'
import type { MonitoredSubject, RiskAlert } from '../types/monitoring'

export const monitoringApi = {
  listSubjects: () => http.get<MonitoredSubject[]>('/monitoring/subjects'),
  updateSubject: (subjectId: number, enabled: boolean) =>
    http.patch<MonitoredSubject>(`/monitoring/subjects/${subjectId}`, { enabled }),
  checkNow: (subjectId: number) =>
    http.post<{ subject: MonitoredSubject; alert: RiskAlert | null; error: string | null }>(
      `/monitoring/subjects/${subjectId}/check-now`,
    ),
  listAlerts: () => http.get<RiskAlert[]>('/alerts'),
  acknowledgeAlert: (alertId: number) => http.post<RiskAlert>(`/alerts/${alertId}/acknowledge`),
}
