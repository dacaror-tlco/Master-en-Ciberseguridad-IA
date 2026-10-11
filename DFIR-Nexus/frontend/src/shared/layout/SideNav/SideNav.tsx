import { useEffect, useRef } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { Icon, IconButton, useCerrarConEscape } from '../../ui'
import { clearToken } from '../../auth'
import { useMediaQuery } from '../../hooks'

type NavItem = {
  label: string
  icon: string
  path: string
}

/*
 * Orden y etiquetas heredados del sidebar de Casos/code.html, con dos cambios
 * respecto al original, ambos porque el menú prometía cosas que no existían:
 *
 * - **«Evidencias», retirada.** Apuntaba a `/cases`, exactamente igual que
 *   «Casos»: dos entradas distintas que llevaban a la misma pantalla, hasta el
 *   punto de necesitar un caso especial más abajo para no resaltarse las dos a
 *   la vez. Las evidencias existen y se gestionan (alta, listado y borrado),
 *   pero **dentro del panel de detalle de un caso**, que es como las modela el
 *   Módulo 1; no hay pantalla propia que enlazar. Si algún día el Módulo 1
 *   expone un `GET /evidences` global, esta entrada vuelve con destino propio.
 *
 * - **«Dashboard», ahora funcional** (`modules/dashboard`). Era una entrada
 *   deshabilitada «hasta que exista una decisión de producto»; esa decisión se
 *   tomó. No es un sexto módulo de la arquitectura: es una pantalla de entrada
 *   que solo lee lo que los módulos 1 y 2 ya publican.
 *
 * - **«Configuración», retirada del todo.** Estuvo deshabilitada porque no había
 *   nada que configurar, y no va a haberlo: lo único ajustable por un usuario es
 *   su contraseña y vive en «Mi perfil». Se probó a convertirla en una pantalla
 *   de estado de los cinco backends y **se descartó por criterio de seguridad**:
 *   enseñaba la topología interna —qué procesos hay, en qué puertos y contra qué
 *   URLs habla el navegador— a cualquier usuario autenticado, y eso es
 *   reconocimiento regalado a quien robe una sesión. Quien tenga que auditar la
 *   arquitectura mira el backend, no la interfaz.
 *
 * - **«Ayuda», ahora funcional** (ver `app/HelpPage.tsx`): el orden de trabajo
 *   de un expediente, por qué una evidencia no se edita ni un informe se
 *   corrige, y cómo comprobar la huella de un PDF por tu cuenta.
 */
const NAV_ITEMS: NavItem[] = [
  { label: 'Dashboard', icon: 'dashboard', path: '/dashboard' },
  { label: 'Casos', icon: 'folder_shared', path: '/cases' },
  { label: 'OSINT y Fraude', icon: 'public', path: '/osint' },
  { label: 'Tracking Post-Incidente', icon: 'radar', path: '/tracking' },
  { label: 'Línea Temporal', icon: 'timeline', path: '/timeline' },
  { label: 'Informes', icon: 'description', path: '/reports' },
  { label: 'Asistente', icon: 'forum', path: '/chat' },
]

type SideNavProps = {
  /** Solo tiene efecto por debajo de `xl`: si el drawer está abierto. */
  open: boolean
  onClose: () => void
}

/**
 * En `xl` (≥1280px) es la barra lateral fija de siempre. Por debajo, pasa a
 * ser un drawer off-canvas controlado por `open`/`onClose` (estado que vive
 * en `AppShell`, ver ese componente): fuera de pantalla por defecto,
 * desplegable desde el botón hamburguesa de `TopBar`, con overlay y cierre
 * por Escape/clic fuera/selección de ruta.
 *
 * Se mantiene SIEMPRE montado (nunca `display:none`) y se mueve con
 * `translate-x`, para poder animarlo; mientras está oculto se marca
 * `aria-hidden` y sus enlaces se sacan del orden de tabulación
 * (`tabIndex=-1`) para que no queden alcanzables "a ciegas".
 */
export function SideNav({ open, onClose }: SideNavProps) {
  const location = useLocation()
  const navigate = useNavigate()
  const escritorio = useMediaQuery('(min-width: 1280px)')
  const visible = escritorio || open
  const navRef = useRef<HTMLElement>(null)

  // En escritorio la barra es fija y no se "cierra" con Escape.
  useCerrarConEscape(!escritorio && open ? onClose : undefined)

  // Al abrir el drawer, el foco pasa a él: quien navega con teclado no se
  // queda en un botón hamburguesa que ya no tiene sentido tras abrirlo.
  useEffect(() => {
    if (!escritorio && open) navRef.current?.focus()
  }, [escritorio, open])

  function handleLogout() {
    clearToken()
    navigate('/login', { replace: true })
  }

  // Se marca el primer ítem cuya ruta encaje. Ya no hay dos entradas al mismo
  // destino (ver arriba), pero la regla se mantiene porque sigue siendo la
  // correcta con rutas anidadas: `/osint/wallet` debe resaltar «OSINT y
  // Fraude», no cualquier otra entrada que empiece igual.
  const activeLabel = NAV_ITEMS.find(
    (item) => location.pathname.startsWith(item.path),
  )?.label

  const tabIndexOculto = visible ? undefined : -1

  return (
    <>
      {!escritorio && open && (
        <div
          className="fixed inset-0 z-40 bg-canvas/70 backdrop-blur-sm"
          aria-hidden="true"
          onClick={onClose}
        />
      )}

      {/*
       * La barra entera es UNA sola zona de scroll (`overflow-y-auto` en el
       * <nav>, y nada de scroll por dentro). Antes solo scrolleaba la lista
       * de módulos, encajonada entre la cabecera y un pie anclado: en una
       * ventana de portátil las últimas entradas —Informes y Asistente—
       * quedaban fuera de vista y costaba dar con ellas, porque el scroll
       * vivía en una franja estrecha en mitad de la barra. Con una única
       * columna scrollable todo es alcanzable siempre, y con los espaciados
       * de abajo las nueve entradas caben sin scroll en pantallas normales.
       *
       * Posición: por debajo de `xl` es `fixed` (drawer, se anima con
       * `translate-x`); en `xl` vuelve a ser `static`, en su sitio de
       * siempre dentro del flex del AppShell.
       */}
      <nav
        ref={navRef}
        aria-label="Navegación principal"
        aria-hidden={!visible}
        tabIndex={-1}
        className={`bg-surface-container-low w-64 flex flex-col py-5 border-r border-hairline shrink-0
          overflow-y-auto fixed inset-y-0 left-0 z-40 h-full transition-transform duration-200 ease-out
          ${open ? 'translate-x-0' : '-translate-x-full'}
          xl:static xl:z-10 xl:translate-x-0`}
      >
        <div className="px-gutter mb-4 shrink-0">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded bg-primary flex items-center justify-center">
                <Icon name="fingerprint" filled className="text-on-primary" />
              </div>
              <h1 className="font-headline-md text-headline-md text-primary leading-none">NEXUS</h1>
            </div>
            <IconButton
              icon="close"
              label="Cerrar menú de navegación"
              onClick={onClose}
              tabIndex={tabIndexOculto}
              className="xl:hidden"
            />
          </div>
          <p className="font-mono-data text-mono-data text-on-surface-variant text-xs opacity-70">
            Forensic Assistant
          </p>
        </div>

        <div className="px-gutter mb-4 shrink-0">
          <Link
            to="/cases"
            tabIndex={tabIndexOculto}
            className="w-full bg-primary text-on-primary font-label-caps text-label-caps py-2.5 px-4 rounded flex items-center justify-center gap-2 hover:bg-primary-fixed transition-colors"
          >
            <Icon name="add" className="text-sm" />
            NUEVA INVESTIGACIÓN
          </Link>
        </div>

        <div className="px-4 space-y-0.5 shrink-0">
          {NAV_ITEMS.map((item) => {
            const isActive = item.label === activeLabel

            return (
              <Link
                key={item.label}
                to={item.path}
                tabIndex={tabIndexOculto}
                className={`flex items-center gap-3 px-4 py-2 rounded font-label-caps text-label-caps transition-all ${
                  isActive
                    ? 'text-primary border-l-2 border-primary bg-secondary-container/10 translate-x-1'
                    : 'text-on-surface-variant hover:text-primary hover:bg-surface-container-highest'
                }`}
              >
                <Icon name={item.icon} filled={isActive} />
                {item.label}
              </Link>
            )
          })}
        </div>

        <div className="shrink-0 px-4 pt-3 mt-3 border-t border-hairline space-y-1">
          <Link
            to="/ayuda"
            tabIndex={tabIndexOculto}
            className={`flex items-center gap-3 px-4 py-2 rounded font-label-caps text-label-caps transition-colors ${
              location.pathname.startsWith('/ayuda')
                ? 'text-primary bg-secondary-container/10'
                : 'text-on-surface-variant hover:text-primary hover:bg-surface-container-highest'
            }`}
          >
            <Icon name="help" filled={location.pathname.startsWith('/ayuda')} />
            Ayuda
          </Link>
          <button
            type="button"
            onClick={handleLogout}
            tabIndex={tabIndexOculto}
            className="w-full flex items-center gap-3 px-4 py-2 rounded text-error hover:bg-error-container/10 transition-colors font-label-caps text-label-caps"
          >
            <Icon name="logout" />
            Cerrar Sesión
          </button>
        </div>
      </nav>
    </>
  )
}
