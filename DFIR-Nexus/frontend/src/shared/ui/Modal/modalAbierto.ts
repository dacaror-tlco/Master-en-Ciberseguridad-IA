/**
 * Cuántos modales hay abiertos ahora mismo.
 *
 * Lo necesitan dos sitios: `Modal`, que se apunta y se borra al abrirse y
 * cerrarse, y los paneles de detalle, que cierran con Escape igual que el modal
 * y tienen que dejar pasar la pulsación cuando hay un modal por encima — si no,
 * una sola pulsación cerraría el modal y, de paso, el panel de debajo.
 *
 * Se cuenta en vez de marcar un sí/no para que dos modales encadenados no se
 * pisen: el que se cierra primero no puede borrar la marca del que sigue
 * abierto.
 *
 * Vive en un módulo aparte y no dentro de `Modal.tsx` porque un fichero que
 * exporta un componente y además otras cosas rompe el fast refresh de Vite
 * (`react(only-export-components)`).
 */
let abiertos = 0

/** Apunta un modal abierto y devuelve la función que lo da de baja. */
export function registrarModalAbierto(): () => void {
  abiertos += 1
  let dadoDeBaja = false
  return () => {
    // Idempotente: en desarrollo React monta y desmonta los efectos dos veces,
    // y un contador que se decrementa de más acabaría en negativo.
    if (dadoDeBaja) return
    dadoDeBaja = true
    abiertos = Math.max(0, abiertos - 1)
  }
}

export function hayModalAbierto(): boolean {
  return abiertos > 0
}
