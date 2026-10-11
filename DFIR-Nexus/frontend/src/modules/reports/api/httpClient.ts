/**
 * Cliente HTTP del módulo Informes. Equivalente al de `modules/cases/api/`
 * (cada módulo tiene el suyo, ver DESIGN_SYSTEM §17): no se importa el del
 * módulo Casos porque `modules/A → modules/B` está prohibido (§13).
 *
 * Dos URLs base, y no una, a propósito y de forma permanente (no temporal:
 * ver docs/CONTRATOS.md): Informes es un backend independiente del de
 * Casos, cada uno su propio proceso y puerto. `VITE_REPORTS_API_URL`
 * apunta al backend de este módulo; `VITE_API_BASE_URL` (la misma que ya
 * usa `modules/cases`) solo para poblar el selector de casos.
 */
import { getToken, handleUnauthorized } from '@/shared/auth'

const DEFAULT_REPORTS_BASE_URL = 'http://localhost:8003'
const DEFAULT_CASES_BASE_URL = 'http://localhost:8000'

/** Backend de Informes (este módulo): `/reports`, `/cases/{id}/reports`. */
export const REPORTS_API_BASE_URL = import.meta.env.VITE_REPORTS_API_URL ?? DEFAULT_REPORTS_BASE_URL

/** Backend de Casos, solo para poblar el selector de casos. */
export const CASES_API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? DEFAULT_CASES_BASE_URL

/**
 * Error tipado de la API. `detail` conserva el cuerpo real de FastAPI (string
 * en los errores de negocio, array en los 422 de validación de Pydantic).
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

async function request<T>(baseUrl: string, path: string, options?: RequestInit): Promise<T> {
  const token = getToken()
  const response = await fetch(`${baseUrl}${path}`, {
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

/**
 * Igual que `request`, pero devuelve el cuerpo como `Blob` y no como JSON.
 *
 * Existe porque las descargas de informes también tienen que llevar el token:
 * navegar a la URL no lo lleva (ver `reportsApi.descargar`). Se devuelve además
 * el `Content-Disposition` tal cual, para que quien descarga pueda usar el
 * nombre de fichero que fija el backend.
 *
 * El error sí se lee como JSON: cuando el backend falla responde con el `detail`
 * de FastAPI, no con el fichero.
 */
async function requestBlob(
  baseUrl: string,
  path: string,
): Promise<{ blob: Blob; contentDisposition: string | null }> {
  const token = getToken()
  const response = await fetch(`${baseUrl}${path}`, {
    headers: { ...(token ? { Authorization: `Bearer ${token}` } : {}) },
  })

  if (!response.ok) {
    if (response.status === 401 && token) {
      handleUnauthorized()
    }
    const body = await response.json().catch(() => null)
    throw new ApiError(response.status, body?.detail ?? body)
  }

  return {
    blob: await response.blob(),
    contentDisposition: response.headers.get('Content-Disposition'),
  }
}

export function createHttpClient(baseUrl: string) {
  return {
    get: <T>(path: string) => request<T>(baseUrl, path),
    post: <T>(path: string, data: unknown) =>
      request<T>(baseUrl, path, { method: 'POST', body: JSON.stringify(data) }),
    getBlob: (path: string) => requestBlob(baseUrl, path),
  }
}
