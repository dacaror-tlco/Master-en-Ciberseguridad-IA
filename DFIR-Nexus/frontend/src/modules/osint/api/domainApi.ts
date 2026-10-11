import { http } from './httpClient'
import type { DomainCase, DomainCaseListItem } from '../types/domain'

/**
 * Cliente para /analysis/domain y /domain-analysis-cases, alineado 1:1 con
 * app/modules/osint/domain/routes.py. No añade endpoints ni parámetros
 * que no existan en el backend.
 *
 * Antes era /cases: renombrada en la integración con Nexus (Fase 1, ver
 * docs/CONTRATOS.md) porque colisionaba con el /cases de Casos (Módulo 1).
 */
/**
 * `caseId` es el expediente de Nexus (`cases.id`) al que se atribuye el
 * análisis, y viaja como `case_id` en el cuerpo. El backend lo aceptaba desde
 * el principio; lo que faltaba era que el frontend lo mandara — sin él,
 * `osint_findings.case_id` queda a NULL y el análisis no sale en el informe ni
 * en la cronología de ningún caso. Lo elige el selector de la cabecera del
 * módulo (ver `state/CasoActivoContext`). `null` es válido y significa
 * exactamente eso: un análisis que todavía no pertenece a ningún expediente.
 */
export const domainApi = {
  analyze: (domain: string, caseId: number | null = null) =>
    http.post<DomainCase>('/analysis/domain', { domain, case_id: caseId }),
  list: (skip = 0, limit = 50) => http.get<DomainCaseListItem[]>(`/domain-analysis-cases?skip=${skip}&limit=${limit}`),
  get: (caseId: number) => http.get<DomainCase>(`/domain-analysis-cases/${caseId}`),
}
