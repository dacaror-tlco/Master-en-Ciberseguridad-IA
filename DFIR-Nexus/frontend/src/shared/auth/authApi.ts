/**
 * Cliente mínimo para POST /auth/login y GET /auth/me. Vive en shared/auth
 * (no en modules/cases) porque LoginPage y AuthGuard lo necesitan desde
 * fuera de cualquier módulo funcional — pero, al ser shared/*, no puede
 * importar modules/cases/api/httpClient (regla: shared/* nunca importa
 * modules/*), así que hace su propio fetch mínimo, sin duplicar el resto
 * del cliente de Casos. /auth vive en el backend de Casos (autoridad de
 * identidad, ver propuesta de identidad y acceso), de ahí que reutilice
 * VITE_API_BASE_URL, la misma variable que ya usa modules/cases.
 */
const AUTH_API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export class AuthApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

export interface LoginResponse {
  access_token: string
  token_type: string
  expires_in: number
}

export interface MeResponse {
  id: number
  nombre: string
  email: string
  rol: 'admin' | 'analyst'
  activo: boolean
  fecha_creacion: string
  fecha_actualizacion: string
  ultimo_login: string | null
}

export async function login(email: string, password: string): Promise<LoginResponse> {
  const response = await fetch(`${AUTH_API_BASE_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  })
  const body = await response.json().catch(() => null)
  if (!response.ok) {
    throw new AuthApiError(
      response.status,
      typeof body?.detail === 'string' ? body.detail : 'No se ha podido iniciar sesión.',
    )
  }
  return body as LoginResponse
}

export async function me(token: string): Promise<MeResponse> {
  const response = await fetch(`${AUTH_API_BASE_URL}/auth/me`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!response.ok) {
    throw new AuthApiError(response.status, 'Sesión inválida.')
  }
  return response.json()
}

/**
 * PUT /auth/me/password. El usuario objetivo lo decide siempre el propio
 * backend a partir del JWT (ver auth/dependencies.py::get_current_user) —
 * esta función nunca envía ningún identificador de usuario, solo el
 * token de la sesión activa.
 */
export async function changePassword(
  token: string,
  contrasenaActual: string,
  contrasenaNueva: string,
  confirmacionContrasenaNueva: string,
): Promise<void> {
  const response = await fetch(`${AUTH_API_BASE_URL}/auth/me/password`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
    body: JSON.stringify({
      contrasena_actual: contrasenaActual,
      contrasena_nueva: contrasenaNueva,
      confirmacion_contrasena_nueva: confirmacionContrasenaNueva,
    }),
  })
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    throw new AuthApiError(
      response.status,
      typeof body?.detail === 'string' ? body.detail : 'No se ha podido cambiar la contraseña.',
    )
  }
}

export interface ActivityEntry {
  id: number
  evento: string
  user_id: number | null
  actor_user_id: number | null
  detalle: Record<string, unknown> | null
  creado_en: string
}

/** GET /auth/me/actividad — siempre la del usuario del token, nunca la de
 * otro (el backend la resuelve por JWT, no acepta ningún id). */
export async function getActivity(token: string): Promise<ActivityEntry[]> {
  const response = await fetch(`${AUTH_API_BASE_URL}/auth/me/actividad`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!response.ok) {
    throw new AuthApiError(response.status, 'No se ha podido cargar la actividad reciente.')
  }
  return response.json()
}
