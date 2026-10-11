import { http } from './httpClient'
import type { AddressFormat, ExtractedAddress, WalletCase, WalletCaseListItem } from '../types/wallet'

export const walletApi = {
  analyze: (address: string) => http.post<WalletCase>('/analysis/wallet', { address }),
  extractAddresses: (text: string) =>
    http.post<{ candidates: ExtractedAddress[] }>('/analysis/wallet/extract-addresses', { text }),
  format: (address: string) => http.get<AddressFormat>(`/analysis/wallet/format?address=${encodeURIComponent(address)}`),
  list: (skip = 0, limit = 50) => http.get<WalletCaseListItem[]>(`/wallet-cases?skip=${skip}&limit=${limit}`),
  get: (caseId: number) => http.get<WalletCase>(`/wallet-cases/${caseId}`),
}
