import { useState } from 'react'
import type { FormEvent } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { Alert, Button, Card, Icon, Input } from '@/shared/ui'
import { AuthApiError, login, saveToken } from '@/shared/auth'

/**
 * /login, deliberadamente fuera de AppShell (sin sidebar ni topbar): es la
 * única pantalla de la aplicación en la que todavía no hay una sesión.
 * Reutiliza los mismos efectos ambientales y componentes (Card/Input/
 * Button/Alert/Icon) que el resto de Nexus para mantener una sola
 * identidad visual, en vez de un sistema de estilos propio para esta
 * pantalla.
 */
export function LoginPage() {
  const navigate = useNavigate()
  const location = useLocation()
  // Mensaje opcional que otra pantalla deja al redirigir aquí (p. ej.
  // Perfil, tras un cambio de contraseña) — vía navigate(..., { state }),
  // no vía query string ni nada persistido: desaparece si se recarga.
  const infoMessage = (location.state as { info?: string } | null)?.info ?? null
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      const { access_token } = await login(email, password)
      // Nunca se guarda la contraseña, en ningún momento — solo el token
      // que devuelve el backend tras validarla.
      saveToken(access_token)
      navigate('/', { replace: true })
    } catch (err) {
      setError(
        err instanceof AuthApiError && err.status === 401
          ? 'Email o contraseña incorrectos.'
          : 'No se ha podido conectar con el servidor.',
      )
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="nexus-canvas nexus-scrollbars relative flex h-screen items-center justify-center overflow-hidden text-on-background font-body-md">
      <div className="nexus-scanline" />
      <div className="absolute inset-0 nexus-mist-gradient pointer-events-none z-0" />
      <div className="nexus-noise-overlay" />

      <div className="relative z-10 w-full max-w-sm px-gutter">
        <div className="flex items-center justify-center gap-3 mb-8">
          <div className="w-10 h-10 rounded bg-primary flex items-center justify-center">
            <Icon name="fingerprint" filled className="text-on-primary" />
          </div>
          <div>
            <h1 className="font-headline-md text-headline-md text-primary leading-none">NEXUS</h1>
            <p className="font-mono-data text-mono-data text-on-surface-variant text-xs opacity-70">
              Forensic Assistant
            </p>
          </div>
        </div>

        <Card title="Iniciar sesión">
          <form onSubmit={handleSubmit} className="flex flex-col gap-4 p-6">
            {infoMessage && !error && <Alert variant="success">{infoMessage}</Alert>}
            {error && <Alert variant="error">{error}</Alert>}
            <Input
              label="Email"
              type="email"
              icon="mail"
              autoComplete="username"
              required
              value={email}
              onChange={(event) => setEmail(event.target.value)}
            />
            <Input
              label="Contraseña"
              type="password"
              icon="lock"
              autoComplete="current-password"
              required
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
            <Button type="submit" loading={submitting} className="mt-2 justify-center">
              Entrar
            </Button>
          </form>
        </Card>
      </div>
    </div>
  )
}
