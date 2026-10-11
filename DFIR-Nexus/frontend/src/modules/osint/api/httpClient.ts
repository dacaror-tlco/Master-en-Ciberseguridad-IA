import { getToken, handleUnauthorized } from '@/shared/auth'

// OSINT y Fraude (scam-shield) es un backend independiente del de Casos
// (puerto propio, ver docs/CONTRATOS.md) — variable propia y no
// VITE_API_BASE_URL, que ya usa modules/cases para el suyo (mismo motivo
// que Tracking/Timeline/Informes: puertos distintos, variable distinta).
const API_BASE_URL = import.meta.env.VITE_OSINT_API_URL ?? 'http://localhost:8124'

/**
 * Error tipado de la API. `detail` conserva el cuerpo real devuelto por
 * FastAPI (string en los 4xx de negocio, array de errores en los 422 de
 * validación de Pydantic) para que la UI pueda mostrarlo tal cual.
 * Mismo patrón que modules/cases/api/httpClient.ts (rama modulo-casos).
 */
export class ApiError extends Error {
  status: number
  detail: unknown

  constructor(status: number, detail: unknown) {
    super(typeof detail === 'string' ? detail : `Error ${status}`)
    this.status = status
    this.detail = detail
  }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const token = getToken()
  const baseHeaders: Record<string, string> = options?.body instanceof FormData
    ? {}
    : { 'Content-Type': 'application/json' }
  if (token) {
    baseHeaders.Authorization = `Bearer ${token}`
  }
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: { ...baseHeaders, ...options?.headers },
  })

  if (response.status === 204) {
    return undefined as T
  }

  const body = await response.json().catch(() => null)

  if (!response.ok) {
    if (response.status === 401 && token) {
      handleUnauthorized()
    }
    throw new ApiError(response.status, body?.detail ?? body)
  }

  return body as T
}

export const http = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, data?: unknown) =>
    request<T>(path, {
      method: 'POST',
      body: data instanceof FormData ? data : data !== undefined ? JSON.stringify(data) : undefined,
    }),
  patch: <T>(path: string, data: unknown) =>
    request<T>(path, { method: 'PATCH', body: JSON.stringify(data) }),
  delete: <T>(path: string) => request<T>(path, { method: 'DELETE' }),
}

// --- Backend de Casos (Módulo 1) --------------------------------------
//
// Segunda URL base, aparte, a propósito: Casos es un backend independiente
// de OSINT (puerto propio), solo se usa para poblar el selector de "a qué
// caso vincular esta investigación" (ver casesLookupApi.ts). Mismo patrón
// ya usado en modules/reports/api/httpClient.ts para lo mismo.
export const CASES_API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

async function requestCases<T>(path: string, options?: RequestInit): Promise<T> {
  const token = getToken()
  const response = await fetch(`${CASES_API_BASE_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options?.headers,
    },
  })

  if (response.status === 204) {
    return undefined as T
  }

  const body = await response.json().catch(() => null)

  if (!response.ok) {
    if (response.status === 401 && token) {
      handleUnauthorized()
    }
    throw new ApiError(response.status, body?.detail ?? body)
  }

  return body as T
}

export const casesHttp = {
  get: <T>(path: string) => requestCases<T>(path),
}
