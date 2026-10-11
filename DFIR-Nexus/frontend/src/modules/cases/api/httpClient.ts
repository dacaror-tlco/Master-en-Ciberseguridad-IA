import { getToken, handleUnauthorized } from '@/shared/auth'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

/**
 * Error tipado de la API. `detail` conserva el cuerpo real devuelto por
 * FastAPI (string en los 404 de negocio, array de errores en los 422 de
 * validación de Pydantic) para que la UI pueda mostrarlo tal cual.
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
  const response = await fetch(`${API_BASE_URL}${path}`, {
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
    // Solo una petición que SÍ llevaba token puede significar "sesión
    // caducada"; sin token, un 401 es un rechazo normal (aún no hay
    // ningún endpoint protegido en esta fase, pero la comprobación queda
    // lista para cuando lo haya).
    if (response.status === 401 && token) {
      handleUnauthorized()
    }
    throw new ApiError(response.status, body?.detail ?? body)
  }

  return body as T
}

export const http = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, data: unknown) =>
    request<T>(path, { method: 'POST', body: JSON.stringify(data) }),
  put: <T>(path: string, data: unknown) =>
    request<T>(path, { method: 'PUT', body: JSON.stringify(data) }),
  delete: <T>(path: string) => request<T>(path, { method: 'DELETE' }),
}
