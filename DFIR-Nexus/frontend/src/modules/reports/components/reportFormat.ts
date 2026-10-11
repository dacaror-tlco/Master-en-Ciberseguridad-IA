import type { StatusTone } from '@/shared/ui'
import type { Report } from '../types'

/**
 * Código identificador del informe, idéntico al que imprime la portada del PDF
 * (`pdf_builder.py`: `INF-{case_id:04d}-v{version}`). Se recalcula aquí en vez
 * de pedirlo al backend porque el backend no lo devuelve como campo: es una
 * composición de dos campos que sí devuelve.
 */
export const reportCode = (report: Pick<Report, 'case_id' | 'version'>) =>
  `INF-${String(report.case_id).padStart(4, '0')}-v${report.version}`

/**
 * Fecha en UTC y con el mismo formato que el PDF (`%Y-%m-%d %H:%M UTC`), para
 * que lo que se ve en pantalla coincida literalmente con lo que va firmado en
 * el informe.
 *
 * Si la cadena no trae designador de zona (MySQL devuelve `DATETIME` sin
 * offset), se interpreta como UTC, que es lo que el backend estampa siempre
 * (`datetime.now(timezone.utc)`). Sin esto el navegador la leería como hora
 * local y la pantalla contradiría al PDF.
 */
export function formatUtc(iso: string): string {
  const hasTimezone = /(Z|[+-]\d{2}:?\d{2})$/.test(iso)
  const date = new Date(hasTimezone ? iso : `${iso}Z`)
  if (Number.isNaN(date.getTime())) return iso

  const pad = (value: number) => String(value).padStart(2, '0')
  return (
    `${date.getUTCFullYear()}-${pad(date.getUTCMonth() + 1)}-${pad(date.getUTCDate())} ` +
    `${pad(date.getUTCHours())}:${pad(date.getUTCMinutes())} UTC`
  )
}

/**
 * Un caso puede tener varias versiones del informe y solo la última está
 * vigente. No es un estado que venga del backend: se deduce comparando
 * `version`, igual que haría un perito al mirar la lista.
 *
 * Reutiliza los tonos ya existentes de `StatusBadge` (§17 de la guía de
 * módulos), sin introducir ningún color nuevo.
 */
export const versionStatus = (isLatest: boolean): { label: string; tone: StatusTone } =>
  isLatest ? { label: 'VIGENTE', tone: 'primary' } : { label: 'HISTÓRICO', tone: 'muted' }

const NOMBRE_ANEXO: Record<string, string> = {
  evidences: 'Anexo A — Evidencias',
  osint: 'Anexo B — OSINT',
  tracking: 'Anexo C — Tracking',
}

/**
 * Formatos que este informe tiene de verdad en el almacén.
 *
 * La fuente es `huellas`, no `opciones`: la huella solo se registra sobre los
 * bytes que se emitieron, así que sus claves son la lista de lo que existe.
 * Ofrecer un botón para un soporte que no se emitió solo consigue que el
 * perito reciba un 410 después de pulsarlo.
 *
 * Un informe sin huellas es anterior a que se registrasen y solo tiene PDF,
 * pero eso ya lo sabía la pantalla: se devuelve `null` para que quien llama
 * mantenga el comportamiento de siempre.
 */
export function formatosEmitidos(report: Pick<Report, 'huellas'>): string[] | null {
  if (!report.huellas) return null
  return Object.keys(report.huellas).filter((clave) => clave !== 'prompt')
}

/**
 * Resumen legible del alcance con el que se emitió el informe, para el panel
 * de detalle. `null` si documentó el caso completo —o si es anterior a que se
 * pudiera elegir—, que es cuando no hay nada que advertir.
 *
 * Deliberadamente NO sustituye a la declaración que lleva el propio documento
 * en su apartado 1: esto es una ayuda de pantalla, y el informe tiene que
 * poder defenderse solo, impreso y fuera de esta aplicación.
 */
export function describirAlcance(report: Pick<Report, 'opciones'>): string[] | null {
  const opciones = report.opciones
  if (!opciones) return null

  const lineas: string[] = []
  const excluidos = Object.keys(NOMBRE_ANEXO).filter(
    (anexo) => !opciones.anexos.includes(anexo as never),
  )
  if (excluidos.length > 0) {
    lineas.push(`Anexos excluidos: ${excluidos.map((a) => NOMBRE_ANEXO[a]).join(', ')}`)
  }
  if (opciones.desde || opciones.hasta) {
    const desde = opciones.desde ? formatUtc(opciones.desde) : 'el inicio del caso'
    const hasta = opciones.hasta ? formatUtc(opciones.hasta) : 'el presente'
    lineas.push(`Franja documentada: de ${desde} a ${hasta}`)
  }
  if (opciones.severidad_minima) {
    lineas.push(`Severidad mínima: ${opciones.severidad_minima} o superior`)
  }
  if (opciones.solo_osint_con_detecciones) {
    lineas.push('Solo indicadores OSINT con detecciones')
  }
  return lineas.length > 0 ? lineas : null
}
