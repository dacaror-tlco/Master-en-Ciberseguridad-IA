// En `npm run dev` (Vite en :5173, backend en :8000, orígenes distintos) el
// valor por defecto apunta al backend local. En producción el frontend
// compilado lo sirve el propio backend desde el mismo origen (ver
// app/main.py), así que ahí la base es relativa (cadena vacía) salvo que
// VITE_API_BASE_URL la sobreescriba explícitamente en build time.
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? (import.meta.env.DEV ? 'http://127.0.0.1:8000' : '')

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
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers:
      options?.body instanceof FormData
        ? options?.headers
        : { 'Content-Type': 'application/json', ...options?.headers },
  })

  if (response.status === 204) {
    return undefined as T
  }

  const body = await response.json().catch(() => null)

  if (!response.ok) {
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
