import { http } from './httpClient'
import type { AddressFormat, ExtractedAddress, WalletCase, WalletCaseListItem } from '../types/wallet'

/**
 * `caseId` es el expediente de Nexus (`cases.id`) al que se atribuye el
 * análisis, y viaja como `case_id` en el cuerpo. El backend lo aceptaba desde
 * el principio; lo que faltaba era que el frontend lo mandara — sin él,
 * `osint_findings.case_id` queda a NULL y el análisis no sale en el informe ni
 * en la cronología de ningún caso. Lo elige el selector de la cabecera del
 * módulo (ver `state/CasoActivoContext`). `null` es válido y significa
 * exactamente eso: un análisis que todavía no pertenece a ningún expediente.
 */
export const walletApi = {
  analyze: (address: string, caseId: number | null = null) =>
    http.post<WalletCase>('/analysis/wallet', { address, case_id: caseId }),
  extractAddresses: (text: string) =>
    http.post<{ candidates: ExtractedAddress[] }>('/analysis/wallet/extract-addresses', { text }),
  format: (address: string) => http.get<AddressFormat>(`/analysis/wallet/format?address=${encodeURIComponent(address)}`),
  list: (skip = 0, limit = 50) => http.get<WalletCaseListItem[]>(`/wallet-cases?skip=${skip}&limit=${limit}`),
  get: (caseId: number) => http.get<WalletCase>(`/wallet-cases/${caseId}`),
}
