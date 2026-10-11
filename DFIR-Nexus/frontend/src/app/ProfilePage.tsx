import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { Alert, Button, Card, Icon, Input, StatusBadge } from '@/shared/ui'
import type { StatusTone } from '@/shared/ui'
import {
  AuthApiError,
  changePassword,
  clearToken,
  getActivity,
  getToken,
  getTokenExpiry,
  me,
} from '@/shared/auth'
import type { ActivityEntry, MeResponse } from '@/shared/auth'

const formatDate = (iso: string) =>
  new Date(iso).toLocaleString('es-ES', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })

const ROL_LABEL: Record<MeResponse['rol'], string> = { admin: 'Administrador', analyst: 'Analista' }

/**
 * Clases de las dos listas de datos de la pantalla.
 *
 * Una columna en móvil y dos a partir de `sm`: con la etiqueta y el valor
 * siempre en la misma fila, un email largo en fuente monoespaciada no cabe a
 * 400 px y la tarjeta desbordaba a lo ancho. `break-words` remata lo que aun así
 * no quepa.
 */
const CLASES_DL =
  'grid grid-cols-1 sm:grid-cols-[auto_1fr] gap-x-4 gap-y-1 sm:gap-y-3 text-sm ' +
  '[&>dd]:mb-2 sm:[&>dd]:mb-0 [&>dd]:min-w-0 [&>dd]:break-words'

const EVENTO_INFO: Record<string, { label: string; icon: string; tone: StatusTone }> = {
  login_exitoso: { label: 'Inicio de sesión correcto', icon: 'login', tone: 'primary' },
  login_fallido: { label: 'Intento de inicio de sesión con contraseña incorrecta', icon: 'warning', tone: 'error' },
  contrasena_cambiada: { label: 'Contraseña modificada', icon: 'lock_reset', tone: 'primary' },
  usuario_creado: { label: 'Cuenta creada', icon: 'person_add', tone: 'neutral' },
  usuario_desactivado: { label: 'Cuenta desactivada', icon: 'block', tone: 'error' },
  usuario_reactivado: { label: 'Cuenta reactivada', icon: 'check_circle', tone: 'primary' },
  rol_cambiado: { label: 'Rol modificado', icon: 'shield_person', tone: 'tertiary' },
}

function describirEvento(entrada: ActivityEntry) {
  const info = EVENTO_INFO[entrada.evento] ?? { label: entrada.evento, icon: 'info', tone: 'neutral' as StatusTone }
  let detalle: string | null = null
  if (entrada.evento === 'rol_cambiado' && entrada.detalle) {
    const de = entrada.detalle.de
    const a = entrada.detalle.a
    if (typeof de === 'string' && typeof a === 'string') detalle = `${de} → ${a}`
  }
  return { ...info, detalle }
}

/** Campo de contraseña con botón de mostrar/ocultar — no forma parte de
 * Input (shared/ui) porque es la única pantalla que lo necesita; no se
 * justifica tocar un componente compartido por esto. */
function PasswordField(props: {
  label: string
  autoComplete: string
  value: string
  onChange: (value: string) => void
}) {
  const [visible, setVisible] = useState(false)
  return (
    <div className="relative">
      <Input
        label={props.label}
        type={visible ? 'text' : 'password'}
        icon="lock"
        autoComplete={props.autoComplete}
        required
        value={props.value}
        onChange={(event) => props.onChange(event.target.value)}
      />
      <button
        type="button"
        onClick={() => setVisible((v) => !v)}
        aria-label={visible ? 'Ocultar contraseña' : 'Mostrar contraseña'}
        className="absolute right-3 top-1/2 translate-y-[0.35rem] text-on-surface-variant hover:text-on-surface transition-colors"
      >
        <Icon name={visible ? 'visibility_off' : 'visibility'} className="text-[16px]" />
      </button>
    </div>
  )
}

/**
 * /perfil — información de la propia cuenta, sesión, cambio de
 * contraseña y actividad reciente. Deliberadamente distinta de la
 * administración de usuarios (PUT /auth/users/{id}): aquí el usuario
 * solo puede ver/tocar SU PROPIA cuenta, ser admin no cambia nada en
 * esta pantalla. Vive en AppShell (sidebar + topbar) para integrarse
 * visualmente con el resto de Nexus, a diferencia de /login.
 */
export function ProfilePage() {
  const navigate = useNavigate()

  const [profile, setProfile] = useState<MeResponse | null>(null)
  const [loadingProfile, setLoadingProfile] = useState(true)
  const [profileError, setProfileError] = useState<string | null>(null)

  const [activity, setActivity] = useState<ActivityEntry[]>([])
  const [loadingActivity, setLoadingActivity] = useState(true)

  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [passwordError, setPasswordError] = useState<string | null>(null)
  const [changingPassword, setChangingPassword] = useState(false)

  useEffect(() => {
    const token = getToken()
    if (!token) return
    me(token)
      .then(setProfile)
      .catch(() => setProfileError('No se ha podido cargar la información de la cuenta.'))
      .finally(() => setLoadingProfile(false))
    getActivity(token)
      .then(setActivity)
      .catch(() => {
        /* la actividad es informativa, no crítica: un fallo aquí no debe bloquear el resto de la pantalla */
      })
      .finally(() => setLoadingActivity(false))
  }, [])

  function handleLogout() {
    clearToken()
    navigate('/login', { replace: true })
  }

  async function handleChangePassword(event: FormEvent) {
    event.preventDefault()
    setPasswordError(null)

    if (newPassword !== confirmPassword) {
      setPasswordError('La nueva contraseña y su confirmación no coinciden.')
      return
    }
    if (newPassword.length < 8) {
      setPasswordError('La nueva contraseña debe tener al menos 8 caracteres.')
      return
    }

    const token = getToken()
    if (!token) {
      setPasswordError('Sesión no disponible. Vuelve a iniciar sesión.')
      return
    }

    setChangingPassword(true)
    try {
      await changePassword(token, currentPassword, newPassword, confirmPassword)
      // JWT sin estado, sin revocación inmediata (fuera de alcance): la
      // única forma de invalidar la sesión actual es eliminarla aquí, en
      // el propio cliente, y forzar un nuevo login.
      clearToken()
      navigate('/login', {
        replace: true,
        state: { info: 'Contraseña actualizada correctamente. Inicia sesión de nuevo.' },
      })
    } catch (err) {
      setPasswordError(
        err instanceof AuthApiError ? err.message : 'No se ha podido cambiar la contraseña.',
      )
    } finally {
      setChangingPassword(false)
    }
  }

  const token = getToken()
  const expiry = token ? getTokenExpiry(token) : null

  return (
    /*
     * `[&>*]:shrink-0` es lo que hace que la página scrollee. En una columna
     * flex de altura fija los hijos encogen antes que desbordar, así que sin
     * esto las dos últimas tarjetas —Seguridad y Actividad reciente— se
     * aplastaban a cero y no había nada que scrollear: la página parecía
     * terminar en «Sesión». Mismo arreglo que ya llevan Cronología, el panel de
     * inicio y las once pantallas de OSINT.
     */
    <div className="h-full overflow-y-auto p-gutter flex flex-col gap-panel-gap [&>*]:shrink-0">
      <h1 className="font-headline text-headline-md text-on-surface">Mi perfil</h1>

      {profileError && <Alert variant="error">{profileError}</Alert>}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-panel-gap items-start">
        <Card title="Información de la cuenta">
          <div className="p-6">
            {loadingProfile || !profile ? (
              <p className="text-on-surface-variant text-sm font-mono-data">Cargando…</p>
            ) : (
              <dl className={CLASES_DL}>
                <dt className="text-on-surface-variant font-label-caps text-label-caps">Nombre</dt>
                <dd className="text-on-surface">{profile.nombre}</dd>

                <dt className="text-on-surface-variant font-label-caps text-label-caps">Email</dt>
                <dd className="text-on-surface font-mono-data">{profile.email}</dd>

                <dt className="text-on-surface-variant font-label-caps text-label-caps">Rol</dt>
                <dd>
                  <StatusBadge
                    label={ROL_LABEL[profile.rol]}
                    tone={profile.rol === 'admin' ? 'tertiary' : 'primary'}
                  />
                </dd>

                <dt className="text-on-surface-variant font-label-caps text-label-caps">Estado</dt>
                <dd>
                  <StatusBadge label={profile.activo ? 'Activa' : 'Inactiva'} tone={profile.activo ? 'primary' : 'muted'} />
                </dd>

                <dt className="text-on-surface-variant font-label-caps text-label-caps">Creada</dt>
                <dd className="text-on-surface font-mono-data">{formatDate(profile.fecha_creacion)}</dd>

                <dt className="text-on-surface-variant font-label-caps text-label-caps">Último acceso</dt>
                <dd className="text-on-surface font-mono-data">
                  {profile.ultimo_login ? formatDate(profile.ultimo_login) : 'Sin registro previo'}
                </dd>
              </dl>
            )}
          </div>
        </Card>

        <Card title="Sesión">
          <div className="p-6 flex flex-col gap-4">
            <dl className={CLASES_DL}>
              <dt className="text-on-surface-variant font-label-caps text-label-caps">Estado</dt>
              <dd>
                <StatusBadge label={token ? 'Sesión activa' : 'Sin sesión'} tone={token ? 'primary' : 'muted'} />
              </dd>
              <dt className="text-on-surface-variant font-label-caps text-label-caps">Expira</dt>
              <dd className="text-on-surface font-mono-data">{expiry ? formatDate(expiry.toISOString()) : 'No disponible'}</dd>
            </dl>
            <Button variant="danger" icon="logout" onClick={handleLogout} className="self-start">
              Cerrar sesión
            </Button>
          </div>
        </Card>
      </div>

      <Card title="Seguridad" subtitle="Cambiar contraseña">
        <form onSubmit={handleChangePassword} className="p-6 flex flex-col gap-4 max-w-md">
          {passwordError && <Alert variant="error">{passwordError}</Alert>}
          <PasswordField
            label="Contraseña actual"
            autoComplete="current-password"
            value={currentPassword}
            onChange={setCurrentPassword}
          />
          <PasswordField
            label="Nueva contraseña"
            autoComplete="new-password"
            value={newPassword}
            onChange={setNewPassword}
          />
          <PasswordField
            label="Confirmar nueva contraseña"
            autoComplete="new-password"
            value={confirmPassword}
            onChange={setConfirmPassword}
          />
          <Button type="submit" loading={changingPassword} className="mt-2 justify-center self-start">
            Cambiar contraseña
          </Button>
        </form>
      </Card>

      <Card title="Actividad reciente">
        <div className="p-6">
          {loadingActivity ? (
            <p className="text-on-surface-variant text-sm font-mono-data">Cargando…</p>
          ) : activity.length === 0 ? (
            <p className="text-on-surface-variant text-sm font-mono-data">Sin actividad registrada.</p>
          ) : (
            <ul className="space-y-3">
              {activity.map((entrada) => {
                const { label, icon, detalle } = describirEvento(entrada)
                return (
                  <li key={entrada.id} className="flex items-start gap-3 text-sm">
                    <Icon name={icon} className="text-tertiary text-[16px] mt-0.5 shrink-0" />
                    <div className="min-w-0">
                      <p className="text-on-surface">
                        {label}
                        {detalle && <span className="text-on-surface-variant"> · {detalle}</span>}
                      </p>
                      <p className="font-mono-data text-on-surface-variant/70 text-xs">
                        {formatDate(entrada.creado_en)}
                      </p>
                    </div>
                  </li>
                )
              })}
            </ul>
          )}
        </div>
      </Card>
    </div>
  )
}
