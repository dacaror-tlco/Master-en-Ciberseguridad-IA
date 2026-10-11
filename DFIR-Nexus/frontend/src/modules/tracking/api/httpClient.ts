import { getToken, handleUnauthorized } from "@/shared/auth";

// VITE_TRACKING_API_URL, la variable propia de Tracking en el frontend unico
// de development (VITE_API_BASE_URL es la de Casos: usarla aqui mandaria las
// peticiones al backend equivocado). Sus valores:
//   - development, `npm run dev:all`: http://localhost:8001 (su .env)
//   - despliegue con pasarela: /api/tracking
//   - este modulo por separado: vacia (frontend/.env.production) = mismo
//     origen, porque el propio backend sirve el frontend.
// Sin la variable, el mismo valor por defecto que en development.
const API_BASE_URL = import.meta.env.VITE_TRACKING_API_URL ?? "http://localhost:8001";

/**
 * Error tipado de la API. Mismo contrato que Casos, OSINT e Informes:
 * `new ApiError(status, detail)`, con `detail` tal cual lo devuelve FastAPI
 * (texto en los errores de negocio, lista en los 422 de validación).
 *
 * Antes este módulo tenía los parámetros invertidos — mismo nombre de clase,
 * contrato distinto entre módulos del mismo frontend.
 */
export class ApiError extends Error {
  status: number;
  detail: unknown;

  constructor(status: number, detail: unknown) {
    super(describirError(detail, `Error ${status}`));
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

/**
 * Mensaje legible a partir del `detail` de FastAPI.
 *
 * En los 422 es una LISTA de errores de validación; antes se mostraba tal
 * cual y el perito veía "[object Object]".
 */
function describirError(detail: unknown, porDefecto: string): string {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((d: { loc?: unknown[]; msg?: string }) => {
        const campo = Array.isArray(d.loc) ? d.loc.filter((p) => p !== "body").join(".") : "";
        return campo ? `${campo}: ${d.msg}` : (d.msg ?? JSON.stringify(d));
      })
      .join("; ");
  }
  return detail ? JSON.stringify(detail) : porDefecto;
}

/**
 * Toda llamada a la API pasa por aquí, así que aquí se pone el JWT: una sola
 * copia de la cabecera para los cinco endpoints, y un único sitio donde
 * reaccionar a la sesión caducada. El token lo emite el backend de Casos
 * (pantalla de login del frontend de `development`); con este módulo suelto
 * no hay ninguno y las peticiones salen sin cabecera.
 */
export async function httpRequest<T>(path: string, options?: RequestInit): Promise<T> {
  const token = getToken();
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      // las cabeceras de quien llama van después: mandan sobre las de aquí
      ...options?.headers,
    },
  });
  if (!response.ok) {
    const cuerpo = await response.json().catch(() => null);
    // 401 con token = la sesión ha caducado a mitad de uso; sin token es un
    // error normal de la API, que la pantalla muestra como cualquier otro.
    if (response.status === 401 && token) handleUnauthorized();
    throw new ApiError(response.status, (cuerpo as { detail?: unknown } | null)?.detail ?? cuerpo);
  }
  if (response.status === 204) return undefined as T;
  return response.json();
}
