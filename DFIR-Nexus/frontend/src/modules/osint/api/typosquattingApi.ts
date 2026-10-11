import { http } from './httpClient'
import type { TyposquattingCase, TyposquattingCaseListItem } from '../types/typosquatting'

/**
 * `caseId` es el expediente de Nexus (`cases.id`) al que se atribuye el
 * análisis. El backend lo aceptaba desde el principio; lo que faltaba era que
 * el frontend lo mandara — sin él, `osint_findings.case_id` queda a NULL y el
 * análisis no sale en el informe ni en la cronología de ningún caso. Lo elige
 * el selector de la cabecera del módulo (ver `state/CasoActivoContext`).
 * `null` es válido y significa exactamente eso: un análisis que todavía no
 * pertenece a ningún expediente.
 *
 * Ver también `emailApi`/`imageApi`: ahí el mismo dato viaja como
 * campo de un formulario multipart y no como JSON, porque esas dos rutas
 * reciben un fichero.
 */
export const typosquattingApi = {
  analyze: (domain: string, includeFullAnalysis: boolean, caseId: number | null = null) =>
    http.post<TyposquattingCase>('/analysis/typosquatting', {
      domain,
      include_full_analysis: includeFullAnalysis,
      max_full_analysis: 4,
      case_id: caseId,
    }),
  list: (skip = 0, limit = 50) =>
    http.get<TyposquattingCaseListItem[]>(`/typosquatting-cases?skip=${skip}&limit=${limit}`),
  get: (caseId: number) => http.get<TyposquattingCase>(`/typosquatting-cases/${caseId}`),
}
