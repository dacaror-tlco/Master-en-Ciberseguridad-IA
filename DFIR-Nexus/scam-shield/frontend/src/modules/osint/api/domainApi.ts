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
export const domainApi = {
  analyze: (domain: string) => http.post<DomainCase>('/analysis/domain', { domain }),
  list: (skip = 0, limit = 50) => http.get<DomainCaseListItem[]>(`/domain-analysis-cases?skip=${skip}&limit=${limit}`),
  get: (caseId: number) => http.get<DomainCase>(`/domain-analysis-cases/${caseId}`),
}
