import { Link } from 'react-router-dom'
import { Icon, IconButton } from '../../ui'
import { BuscadorGlobal } from './BuscadorGlobal'

type TopBarProps = {
  /** Abre el drawer de navegación (SideNav) en pantallas por debajo de `xl`. */
  onAbrirNav: () => void
}

/**
 * Header/TopBar. Sale del header de Casos/code.html, con dos cambios sobre el
 * mockup, los dos por lo mismo: allí había tres controles `disabled` de adorno.
 *
 * - **El buscador ahora busca** (ver `BuscadorGlobal`): expedientes por número,
 *   nombre o responsable, y lleva al caso seleccionado.
 * - **La campana de notificaciones y el icon-button de huella, retirados.** Un
 *   control apagado no comunica «función futura», comunica «esto no funciona», y
 *   es lo primero que alguien intenta pulsar. En las plataformas del sector la
 *   campana nunca es un adorno: en TheHive la disparan eventos reales
 *   (asignación de tarea, cierre de caso, SLA incumplido), en Velociraptor la
 *   alimenta un artefacto del servidor y en OpenCTI son disparadores que define
 *   el propio usuario — dejar el icono sin nada detrás promete algo que el
 *   sector entiende como una función de peso. La huella, además, repetía el
 *   icono del logotipo y no nombraba ninguna acción de la plataforma.
 *
 * Si las notificaciones se construyen, la campana vuelve con su función, no
 * antes; queda como trabajo futuro en la documentación.
 */
export function TopBar({ onAbrirNav }: TopBarProps) {
  return (
    <header className="bg-surface-container-low/80 backdrop-blur-md border-b border-hairline flex justify-between items-center w-full px-gutter h-16 z-40 shrink-0 gap-3">
      <div className="flex items-center gap-3 min-w-0 flex-1">
        <IconButton
          icon="menu"
          label="Abrir menú de navegación"
          onClick={onAbrirNav}
          className="xl:hidden shrink-0"
        />
        <h2 className="font-headline-md text-headline-md text-primary tracking-tighter xl:hidden shrink-0">
          NEXUS
        </h2>
        <div className="min-w-0 flex-1 flex">
          <BuscadorGlobal />
        </div>
      </div>
      <Link
        to="/perfil"
        title="Mi perfil"
        className="w-8 h-8 rounded-full border border-outline-variant overflow-hidden bg-surface-container-highest flex items-center justify-center hover:border-primary transition-colors shrink-0"
      >
        <Icon name="person" className="text-on-surface-variant text-[18px]" />
      </Link>
    </header>
  )
}
