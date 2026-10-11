import { Outlet } from 'react-router-dom'
import { SideNav } from '../SideNav/SideNav'
import { TopBar } from '../TopBar/TopBar'

/**
 * Estructura principal de la aplicación: SideNav + TopBar + MainContent.
 * Monta UNA sola vez los efectos visuales globales de Casos/code.html
 * (grid punteado, ruido, niebla, scanline, scrollbar). Ninguna página debe
 * volver a declarar estos efectos: solo componen su contenido dentro de
 * <Outlet /> y heredan automáticamente la identidad visual de Nexus.
 */
export function AppShell() {
  return (
    <div className="nexus-canvas nexus-scrollbars relative flex h-screen overflow-hidden text-on-background font-body-md">
      <div className="nexus-scanline" />
      <div className="absolute inset-0 nexus-mist-gradient pointer-events-none z-0" />
      <div className="nexus-noise-overlay" />

      <SideNav />

      <div className="flex-1 flex flex-col relative z-10 min-w-0">
        <TopBar />
        <main className="flex-1 overflow-hidden relative z-10">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
