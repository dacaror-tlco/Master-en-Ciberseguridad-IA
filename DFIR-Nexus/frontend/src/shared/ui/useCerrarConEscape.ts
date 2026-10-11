import { useEffect } from 'react'
import { hayModalAbierto } from './Modal/modalAbierto'

/**
 * Cierra con Escape un panel de detalle.
 *
 * Vive en `shared/ui` y no dentro de un módulo porque lo usan los paneles de
 * Casos y de Informes, y un módulo no puede importar de otro (ver CLAUDE.md).
 *
 * No lo hace el layout `TableWithDrawerLayout` aunque parezca su sitio: el
 * layout recibe un `ReactNode` ya montado y no sabe qué hay abierto ni cómo se
 * cierra. Quien tiene el estado es la página, y quien está en pantalla es el
 * panel, así que escucha el panel.
 *
 * Con un modal abierto la pulsación no es del panel: el modal está por encima y
 * también cierra con Escape, así que sin la guarda una sola pulsación cerraría
 * el modal y, de paso, el panel de debajo.
 */
export function useCerrarConEscape(onClose?: () => void) {
  useEffect(() => {
    if (!onClose) return
    const alPulsar = (evento: KeyboardEvent) => {
      if (evento.key === 'Escape' && !hayModalAbierto()) onClose()
    }
    window.addEventListener('keydown', alPulsar)
    return () => window.removeEventListener('keydown', alPulsar)
  }, [onClose])
}
