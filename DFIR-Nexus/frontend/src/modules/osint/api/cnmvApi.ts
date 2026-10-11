import { http } from './httpClient'
import type { CnmvCheckCase, CnmvCheckCaseListItem } from '../types/cnmv'

/**
 * `caseId` es el expediente de Nexus (`cases.id`) al que se atribuye el
 * análisis, y viaja como `case_id` en el cuerpo. El backend lo aceptaba desde
 * el principio; lo que faltaba era que el frontend lo mandara — sin él,
 * `osint_findings.case_id` queda a NULL y el análisis no sale en el informe ni
 * en la cronología de ningún caso. Lo elige el selector de la cabecera del
 * módulo (ver `state/CasoActivoContext`). `null` es válido y significa
 * exactamente eso: un análisis que todavía no pertenece a ningún expediente.
 */
export const cnmvApi = {
  check: (query: string, caseId: number | null = null) =>
    http.post<CnmvCheckCase>('/analysis/cnmv-check', { query, case_id: caseId }),
  list: (skip = 0, limit = 50) => http.get<CnmvCheckCaseListItem[]>(`/cnmv-check-cases?skip=${skip}&limit=${limit}`),
  get: (caseId: number) => http.get<CnmvCheckCase>(`/cnmv-check-cases/${caseId}`),
}
