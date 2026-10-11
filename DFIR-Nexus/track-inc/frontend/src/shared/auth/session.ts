/**
 * Único lugar que toca almacenamiento de sesión en el frontend. Guarda
 * ÚNICAMENTE el JWT — ni email, ni nombre, ni rol: lo demás se obtiene
 * siempre fresco vía `GET /auth/me` contra el backend de Casos, que es el
 * dueño de la identidad.
 *
 * Copia del fichero del frontend único de `development` (misma clave y
 * mismas funciones, para que al integrar no haya dos sesiones distintas).
 * En este módulo suelto no hay pantalla de login: si no hay token, las
 * peticiones salen sin cabecera y el backend decide (ver
 * TRACKING_AUTH_DESACTIVADA en app/modules/auth/dependencies.py).
 *
 * localStorage en esta fase, no cookies httpOnly: el JWT queda expuesto a
 * un XSS en este origen — riesgo asumido y documentado por el equipo, no
 * oculto.
 */
const TOKEN_KEY = "nexus_auth_token";

export function getToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    // Sin localStorage (navegación privada, cuota, permisos): se trabaja
    // sin sesión en vez de romper la aplicación.
    return null;
  }
}

export function saveToken(token: string): void {
  try {
    localStorage.setItem(TOKEN_KEY, token);
  } catch {
    // ver getToken: la sesión no persistirá entre recargas, pero no es fatal
  }
}

export function clearToken(): void {
  try {
    localStorage.removeItem(TOKEN_KEY);
  } catch {
    // ver getToken
  }
}

export function hasSession(): boolean {
  return getToken() !== null;
}
