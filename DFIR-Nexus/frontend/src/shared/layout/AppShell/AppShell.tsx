import { useEffect, useState } from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import { SideNav } from '../SideNav/SideNav'
import { TopBar } from '../TopBar/TopBar'

/**
 * Estructura principal de la aplicación: SideNav + TopBar + MainContent.
 * Monta UNA sola vez los efectos visuales globales de Casos/code.html
 * (grid punteado, ruido, niebla, scanline, scrollbar). Ninguna página debe
 * volver a declarar estos efectos: solo componen su contenido dentro de
 * <Outlet /> y heredan automáticamente la identidad visual de Nexus.
 *
 * Por debajo de `xl` (1280px) el SideNav pasa a ser un drawer off-canvas: el
 * estado de apertura vive aquí porque lo controlan dos componentes distintos
 * (el botón hamburguesa de TopBar lo abre, SideNav se cierra a sí mismo) y
 * ninguno de los dos puede importar del otro.
 */
export function AppShell() {
  const [navAbierto, setNavAbierto] = useState(false)
  const location = useLocation()

  // Cierra el drawer al cambiar de ruta, sea cual sea el disparador
  // (un enlace del propio SideNav, el botón "atrás" del navegador...).
  useEffect(() => {
    setNavAbierto(false)
  }, [location.pathname])

  return (
    <div className="nexus-canvas nexus-scrollbars relative flex h-screen overflow-hidden text-on-background font-body-md">
      <div className="nexus-scanline" />
      <div className="absolute inset-0 nexus-mist-gradient pointer-events-none z-0" />
      <div className="nexus-noise-overlay" />

      <SideNav open={navAbierto} onClose={() => setNavAbierto(false)} />

      <div className="flex-1 flex flex-col relative z-10 min-w-0">
        <TopBar onAbrirNav={() => setNavAbierto(true)} />
        <main className="flex-1 overflow-hidden relative z-10">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
