import { http } from './httpClient'
import type { FacialSearchResult, ImageCase, ImageCaseListItem, ReverseImageSearchResult } from '../types/image'

/**
 * `caseId` es el expediente de Nexus (`cases.id`) al que se atribuye el
 * análisis. El backend lo aceptaba desde el principio; lo que faltaba era que
 * el frontend lo mandara — sin él, `osint_findings.case_id` queda a NULL y el
 * análisis no sale en el informe ni en la cronología de ningún caso. Lo elige
 * el selector de la cabecera del módulo (ver `state/CasoActivoContext`).
 * `null` es válido y significa exactamente eso: un análisis que todavía no
 * pertenece a ningún expediente.
 *
 * Va como campo del formulario y no como JSON porque esta ruta
 * recibe la imagen como multipart; se omite cuando es `null` para no mandarle
 * la cadena "null" a un `Form(None)` de tipo entero (sería un 422).
 *
 * Solo lo lleva `analyze`: la búsqueda inversa y la facial son acciones sobre
 * un ImageCase que ya existe, así que heredan el expediente de ese caso y no
 * lo vuelven a declarar.
 */
export const imageApi = {
  analyze: async (file: File, caseId: number | null = null) => {
    const formData = new FormData()
    formData.append('file', file)
    if (caseId !== null) formData.append('case_id', String(caseId))
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
