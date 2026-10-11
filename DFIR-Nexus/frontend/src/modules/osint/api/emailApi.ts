import { http } from './httpClient'
import type { EmailCase, EmailCaseListItem } from '../types/email'

/**
 * `caseId` es el expediente de Nexus (`cases.id`) al que se atribuye el
 * análisis. El backend lo aceptaba desde el principio; lo que faltaba era que
 * el frontend lo mandara — sin él, `osint_findings.case_id` queda a NULL y el
 * análisis no sale en el informe ni en la cronología de ningún caso. Lo elige
 * el selector de la cabecera del módulo (ver `state/CasoActivoContext`).
 * `null` es válido y significa exactamente eso: un análisis que todavía no
 * pertenece a ningún expediente.
 *
 * En `analyzeFile` va como campo del formulario, no como JSON: esa
 * ruta recibe el .eml como multipart y FastAPI lo lee con `Form(None)`. Se
 * omite del formulario cuando es `null` — un `Form` opcional al que se le
 * manda la cadena "null" intentaría convertirla a entero y devolvería un 422.
 */
export const emailApi = {
  analyzeRaw: (raw_email: string, caseId: number | null = null) =>
    http.post<EmailCase>('/analysis/email', { raw_email, case_id: caseId }),
  analyzeFile: async (file: File, caseId: number | null = null) => {
    const formData = new FormData()
    formData.append('file', file)
    if (caseId !== null) formData.append('case_id', String(caseId))
    return http.post<EmailCase>('/analysis/email/file', formData)
  },
  list: (skip = 0, limit = 50) => http.get<EmailCaseListItem[]>(`/email-cases?skip=${skip}&limit=${limit}`),
  get: (caseId: number) => http.get<EmailCase>(`/email-cases/${caseId}`),
}
