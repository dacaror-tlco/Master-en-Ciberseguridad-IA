/**
 * Único lugar que toca almacenamiento de sesión en el frontend. Guarda
 * ÚNICAMENTE el JWT — ni email, ni nombre, ni rol, ni ningún otro dato:
 * lo demás se obtiene siempre fresco vía GET /auth/me cuando hace falta
 * (ver propuesta de identidad y acceso, decisiones de frontend).
 *
 * localStorage en esta fase (no cookies httpOnly): el JWT queda expuesto
 * a un XSS en este origen — riesgo aceptado y documentado, no oculto;
 * cookies httpOnly/sesiones de servidor quedan como evolución futura
 * fuera de alcance de esta fase.
 */
const TOKEN_KEY = 'nexus_auth_token'

export function getToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY)
  } catch {
    return null
  }
}

export function saveToken(token: string): void {
  try {
    localStorage.setItem(TOKEN_KEY, token)
  } catch {
    // localStorage no disponible (navegación privada, cuota, etc.): la
    // sesión no persistirá entre recargas, pero no es un error fatal.
  }
}

export function clearToken(): void {
  try {
    localStorage.removeItem(TOKEN_KEY)
  } catch {
    // ver saveToken
  }
}

export function hasSession(): boolean {
  return getToken() !== null
}

/**
 * Lee `exp` directamente del propio JWT, sin verificar su firma — es
 * seguro para esto porque el payload de un JWT nunca es secreto (va en
 * base64, no cifrado; cualquiera que ya tenga el token puede leerlo) y
 * aquí se usa ÚNICAMENTE para mostrar "sesión expira a las…" en la
 * pantalla de Perfil, nunca para decidir nada de autorización — eso
 * sigue siendo, siempre, responsabilidad exclusiva del backend.
 */
export function getTokenExpiry(token: string): Date | null {
  try {
    const payloadSegment = token.split('.')[1]
    if (!payloadSegment) return null
    const base64 = payloadSegment.replace(/-/g, '+').replace(/_/g, '/')
    const payload = JSON.parse(atob(base64)) as { exp?: number }
    return typeof payload.exp === 'number' ? new Date(payload.exp * 1000) : null
  } catch {
    return null
  }
}
