import { clearToken } from './session'

/**
 * Reacción uniforme a un 401 de una petición que sí llevaba token (sesión
 * caducada/invalidada a mitad de uso) — la llaman los cinco httpClient
 * independientes, cada uno con su propia copia de la comprobación
 * `response.status === 401`, pero todos delegan aquí el mismo efecto para
 * no divergir. Nunca se llama para un 401 de POST /auth/login (eso es
 * "credenciales incorrectas", no "sesión caducada": lo gestiona el propio
 * formulario de login, sin tocar la sesión).
 *
 * Comprobación de ruta para evitar un bucle de redirecciones si varias
 * peticiones en paralelo devuelven 401 a la vez.
 */
export function handleUnauthorized(): void {
  clearToken()
  if (window.location.pathname !== '/login') {
    window.location.assign('/login')
  }
}
