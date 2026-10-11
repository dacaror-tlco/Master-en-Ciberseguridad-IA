import { ApiError } from './httpClient'
import type { ConsolidatedRequest, ConsolidatedResponse, ReportRequest } from '../types/report'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'

export const reportApi = {
  consolidated: async (payload: ConsolidatedRequest) => {
    const response = await fetch(`${API_BASE_URL}/analysis/consolidated`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    const body = await response.json().catch(() => null)
    if (!response.ok) throw new ApiError(response.status, body?.detail ?? body)
    return body as ConsolidatedResponse
  },
  /** Devuelve el PDF como Blob — /analysis/reports/generate no responde JSON. */
  generatePdf: async (payload: ReportRequest) => {
    const response = await fetch(`${API_BASE_URL}/analysis/reports/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    if (!response.ok) {
      const body = await response.json().catch(() => null)
      throw new ApiError(response.status, body?.detail ?? body)
    }
    return response.blob()
  },
}
