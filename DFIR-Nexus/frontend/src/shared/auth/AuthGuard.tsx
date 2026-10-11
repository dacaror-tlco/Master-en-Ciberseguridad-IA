import { useEffect, useState } from 'react'
import { Navigate, Outlet } from 'react-router-dom'
import { me } from './authApi'
import { clearToken, getToken } from './session'

type EstadoSesion = 'comprobando' | 'valida' | 'invalida'

/**
 * Protección de RUTAS a nivel de frontend, únicamente por UX: impide que
 * la aplicación se muestre sin una sesión localmente válida. La
 * autorización real ocurre siempre en cada backend (fases 3 y 4) — este
 * guard nunca debe tratarse como un mecanismo de seguridad en sí mismo.
 *
 * Sin token en localStorage: redirige de inmediato, sin llamar a la red.
 * Con token: se valida contra GET /auth/me antes de mostrar la
 * aplicación — así una recarga de página con un token ya caducado (o
 * corrompido) desde la última visita no deja ver la aplicación ni un
 * instante; si /auth/me falla, se limpia la sesión y se redirige.
 */
export function AuthGuard() {
  const [token] = useState(() => getToken())
  const [estado, setEstado] = useState<EstadoSesion>(token ? 'comprobando' : 'invalida')

  useEffect(() => {
    if (!token) return
    let cancelado = false
    me(token)
      .then(() => {
        if (!cancelado) setEstado('valida')
      })
      .catch(() => {
        if (!cancelado) {
          clearToken()
          setEstado('invalida')
        }
      })
    return () => {
      cancelado = true
    }
  }, [token])

  if (estado === 'invalida') {
    return <Navigate to="/login" replace />
  }

  if (estado === 'comprobando') {
    return (
      <div className="nexus-canvas relative flex h-screen items-center justify-center overflow-hidden text-on-surface-variant font-mono-data text-mono-data">
        Comprobando sesión…
      </div>
    )
  }

  return <Outlet />
}
