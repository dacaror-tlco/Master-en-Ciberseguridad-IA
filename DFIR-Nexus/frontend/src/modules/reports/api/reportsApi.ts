import { createHttpClient, REPORTS_API_BASE_URL } from './httpClient'
import type { Report, ReportFormat, ReportGenerateInput } from '../types'

const http = createHttpClient(REPORTS_API_BASE_URL)

/**
 * Nombre de fichero que anuncia el backend en `Content-Disposition`, con un
 * respaldo por si la cabecera no llega (un proxy puede quitarla: el gateway de
 * producción es un nginx por delante).
 *
 * Se acepta tanto `filename*=UTF-8''…` (RFC 5987, el que usa FastAPI cuando el
 * nombre lleva acentos) como el `filename="…"` de toda la vida, y se prefiere el
 * primero porque es el que conserva los caracteres.
 */
function nombreDeFichero(
  contentDisposition: string | null,
  reportId: number,
  formato: ReportFormat,
): string {
  const extendido = contentDisposition?.match(/filename\*=UTF-8''([^;]+)/i)
  if (extendido) {
    try {
      return decodeURIComponent(extendido[1].trim())
    } catch {
      // Cabecera mal formada: mejor el nombre de respaldo que un nombre roto.
    }
  }

  const sencillo = contentDisposition?.match(/filename="?([^";]+)"?/i)
  if (sencillo) return sencillo[1].trim()

  return `informe-${reportId}.${formato}`
}

/**
 * Cliente de /reports, alineado 1:1 con
 * sharingan/app/modules/reports/routes.py. No existe ningún otro endpoint:
 * los informes no se editan ni se borran (un informe pericial emitido es
 * inmutable; corregirlo significa generar una versión nueva).
 */
export const reportsApi = {
  /** POST /reports/generate — emite el informe en los cuatro formatos y crea una versión nueva. */
  generate: (data: ReportGenerateInput) => http.post<Report>('/reports/generate', data),

  /** GET /reports/{id} */
  get: (reportId: number) => http.get<Report>(`/reports/${reportId}`),

  /** GET /cases/{case_id}/reports — todas las versiones emitidas del caso. */
  listForCase: (caseId: number) => http.get<Report[]>(`/cases/${caseId}/reports`),

  /**
   * GET /reports/{id}/download — descarga el informe en el soporte pedido.
   *
   * Va por `fetch` y devuelve el contenido, **no una URL**. Antes se exponía la
   * URL y se navegaba a ella, aprovechando que el backend manda su propio
   * `Content-Disposition`; eso dejó de funcionar en la Fase 4, cuando Informes
   * pasó a exigir JWT: una navegación del navegador no lleva la cabecera
   * `Authorization`, así que el endpoint responde 401 y el usuario ve un error
   * en vez de su informe. El token solo viaja en peticiones que lo añaden a
   * mano, o sea por `fetch`.
   *
   * El nombre de fichero se sigue tomando del backend, leyéndolo de la misma
   * cabecera, para no duplicar aquí el criterio de cómo se llama un informe.
   *
   * Sin `formato` el backend devuelve el PDF, así que se omite el parámetro en
   * ese caso y la URL queda idéntica a la de siempre.
   */
  descargar: async (
    reportId: number,
    formato: ReportFormat = 'pdf',
  ): Promise<{ blob: Blob; nombre: string }> => {
    const query = formato === 'pdf' ? '' : `?formato=${formato}`
    const { blob, contentDisposition } = await http.getBlob(
      `/reports/${reportId}/download${query}`,
    )
    return { blob, nombre: nombreDeFichero(contentDisposition, reportId, formato) }
  },

  /**
   * GET /reports/{id}/prompt — instrucciones literales que se enviaron a la
   * IA para redactar este informe. No es una copia del informe en otro
   * soporte, sino el registro de cómo se redactó, y por eso va aparte de
   * `descargar`. Devuelve 410 en los informes que se emitieron antes de que se
   * archivase, y 409 si el fichero no cuadra con su huella.
   *
   * Por `fetch` y no como URL por lo mismo que `descargar`: este endpoint
   * también exige JWT desde la Fase 4.
   */
  descargarPrompt: async (reportId: number): Promise<Blob> => {
    const { blob } = await http.getBlob(`/reports/${reportId}/prompt`)
    return blob
  },
}
