import { http } from './httpClient'
import type { PhoneCase, PhoneCaseListItem } from '../types/phone'

/**
 * `caseId` es el expediente de Nexus (`cases.id`) al que se atribuye el
 * análisis, y viaja como `case_id` en el cuerpo. El backend lo aceptaba desde
 * el principio; lo que faltaba era que el frontend lo mandara — sin él,
 * `osint_findings.case_id` queda a NULL y el análisis no sale en el informe ni
 * en la cronología de ningún caso. Lo elige el selector de la cabecera del
 * módulo (ver `state/CasoActivoContext`). `null` es válido y significa
 * exactamente eso: un análisis que todavía no pertenece a ningún expediente.
 */
export const phoneApi = {
  analyze: (phone: string, defaultRegion: string, caseId: number | null = null) =>
    http.post<PhoneCase>('/analysis/phone', {
      phone,
      default_region: defaultRegion,
      case_id: caseId,
    }),
  list: (skip = 0, limit = 50) => http.get<PhoneCaseListItem[]>(`/phone-cases?skip=${skip}&limit=${limit}`),
  get: (caseId: number) => http.get<PhoneCase>(`/phone-cases/${caseId}`),
}
