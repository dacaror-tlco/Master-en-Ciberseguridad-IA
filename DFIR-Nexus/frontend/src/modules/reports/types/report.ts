/**
 * Refleja literalmente `ReportOut` de sharingan/app/modules/reports/schemas.py.
 * No se añade ningún campo que el backend no devuelva.
 */
export type Report = {
  id: number
  case_id: number
  fecha_generacion: string
  resumen_ia: string
  archivo_pdf: string
  generado_por: string
  version: number
  notas: string | null
  /**
   * Huella SHA-256 de cada copia emitida, por formato (`{ pdf: '…', docx: '…' }`).
   * `null` en los informes emitidos antes de que el backend las registrase: a
   * esos no se les calcula ahora, porque el hash del fichero que hoy está en
   * disco no demostraría que sea el que se emitió.
   */
  huellas: Record<string, string> | null
  /**
   * Alcance con el que se emitió este informe: qué anexos entraron, qué franja
   * de la cronología se documentó y en qué formatos se emitió.
   *
   * Es lo que explica que dos informes del mismo caso digan cosas distintas
   * sin que hayan cambiado los datos. `null` en los emitidos antes de que se
   * pudiera elegir, que documentaban el caso entero.
   */
  opciones: ReportScope | null
}

/** Los tres anexos, nombrados como `timeline_events.origen_modulo` apunta a ellos. */
export type ReportAnnex = 'evidences' | 'osint' | 'tracking'

/** `reports.opciones` tal y como lo devuelve el backend (`OpcionesInforme.como_json`). */
export type ReportScope = {
  anexos: ReportAnnex[]
  formatos: ReportFormat[]
  desde: string | null
  hasta: string | null
  severidad_minima: string | null
  solo_osint_con_detecciones: boolean
}

/**
 * Soportes en los que se puede descargar un informe, tal y como los declara
 * `FormatoInforme` en sharingan/app/modules/reports/formats.py.
 *
 * Los cuatro se emiten en la misma generación y dicen lo mismo: el PDF es el
 * documento firmado y los demás son copias con el mismo código y la misma
 * fecha. No se componen al descargarlos, así que pedir un formato de un
 * informe emitido antes de que esto existiera devuelve 410.
 */
export type ReportFormat = 'pdf' | 'docx' | 'html' | 'json'

/** Cuerpo de POST /reports/generate (`ReportGenerateRequest`). */
export type ReportGenerateInput = {
  case_id: number
  generado_por: string
  notas?: string | null
  /**
   * Alcance de esta emisión. Omitirlo emite el informe completo, que es lo que
   * hacía el endpoint antes de que existiera este campo.
   */
  opciones?: ReportScopeInput | null
}

/**
 * Lo que se envía en `opciones`. Todo opcional: solo se manda lo que el perito
 * ha tocado, para que una emisión sin recortes viaje igual que antes.
 *
 * El backend rechaza con 422 un alcance imposible —ningún anexo, sin PDF,
 * franja invertida— y también uno que deje la cronología vacía. El formulario
 * evita los tres primeros; el cuarto depende de los datos del caso y solo se
 * puede saber al generar.
 */
export type ReportScopeInput = {
  anexos?: ReportAnnex[]
  formatos?: ReportFormat[]
  desde?: string | null
  hasta?: string | null
  severidad_minima?: string | null
  solo_osint_con_detecciones?: boolean
}

/**
 * Lectura mínima de un caso, solo para poder elegirlo en el selector.
 *
 * No es —ni pretende ser— el tipo `Case` del Módulo 1: declararlo aquí con los
 * dos campos que esta pantalla necesita evita importar nada de
 * `modules/cases/`, prohibido por la regla de dependencias del Design System
 * (§13). La relación entre módulos pasa por `case_id`, igual que en el backend.
 */
export type CaseOption = {
  id: number
  nombre: string
}
