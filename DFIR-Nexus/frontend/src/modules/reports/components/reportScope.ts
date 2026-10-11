import type { ReportAnnex, ReportFormat, ReportScopeInput } from '../types'

/**
 * Estado del bloque de alcance, tal y como lo lleva el formulario. Se mantiene
 * como cadenas —lo que devuelven los `input`— y se traduce a
 * `ReportScopeInput` en `aScopeInput`, para que la conversión ocurra en un
 * solo sitio.
 */
export type ScopeState = {
  anexos: ReportAnnex[]
  formatos: ReportFormat[]
  desde: string
  hasta: string
  severidadMinima: string
  soloOsintConDetecciones: boolean
}

export const ANEXOS: { valor: ReportAnnex; etiqueta: string; ayuda: string }[] = [
  { valor: 'evidences', etiqueta: 'Anexo A — Evidencias', ayuda: 'Material aportado al caso' },
  { valor: 'osint', etiqueta: 'Anexo B — OSINT', ayuda: 'Indicadores consultados en fuentes abiertas' },
  { valor: 'tracking', etiqueta: 'Anexo C — Tracking', ayuda: 'Eventos del análisis post-incidente' },
]

export const FORMATOS: { valor: ReportFormat; etiqueta: string; fijo?: boolean }[] = [
  { valor: 'pdf', etiqueta: 'PDF', fijo: true },
  { valor: 'docx', etiqueta: 'DOCX' },
  { valor: 'html', etiqueta: 'HTML' },
  { valor: 'json', etiqueta: 'JSON' },
]

export const SEVERIDADES = [
  { value: '', label: 'Todas' },
  { value: 'baja', label: 'Baja o superior' },
  { value: 'media', label: 'Media o superior' },
  { value: 'alta', label: 'Alta o superior' },
  { value: 'critica', label: 'Solo críticas' },
]

export const ALCANCE_COMPLETO: ScopeState = {
  anexos: ANEXOS.map((a) => a.valor),
  formatos: FORMATOS.map((f) => f.valor),
  desde: '',
  hasta: '',
  severidadMinima: '',
  soloOsintConDetecciones: false,
}

/** Si el perito ha tocado algo. Gobierna el aviso y si se envía `opciones`. */
export function hayRecorte(estado: ScopeState): boolean {
  return (
    estado.anexos.length !== ANEXOS.length ||
    estado.formatos.length !== FORMATOS.length ||
    estado.desde !== '' ||
    estado.hasta !== '' ||
    estado.severidadMinima !== '' ||
    estado.soloOsintConDetecciones
  )
}

/**
 * Traduce el estado del formulario al cuerpo de la petición.
 *
 * Devuelve `null` cuando no hay nada elegido, para que una emisión completa
 * viaje sin el campo `opciones` y quede registrada como lo que es: el informe
 * de siempre, no un alcance que casualmente coincide con el total.
 */
export function aScopeInput(estado: ScopeState): ReportScopeInput | null {
  if (!hayRecorte(estado)) return null
  return {
    anexos: estado.anexos,
    formatos: estado.formatos,
    desde: estado.desde ? new Date(estado.desde).toISOString() : null,
    hasta: estado.hasta ? new Date(estado.hasta).toISOString() : null,
    severidad_minima: estado.severidadMinima || null,
    solo_osint_con_detecciones: estado.soloOsintConDetecciones,
  }
}
