// Por defecto, mismo origen: el backend sirve el frontend compilado, asi que
// la API esta en el mismo host y puerto desde el que se abrio la pagina
// (sea 127.0.0.1:8000, localhost o el 8089 de Docker). Solo el modo desarrollo
// (Vite en :5173) necesita apuntar al backend, via VITE_API_BASE_URL.
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export async function httpRequest<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, options);
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      detail = body.detail ?? JSON.stringify(body);
    } catch {
      // el cuerpo no era JSON, se mantiene el statusText
    }
    throw new ApiError(detail, response.status);
  }
  if (response.status === 204) return undefined as T;
  return response.json();
}
