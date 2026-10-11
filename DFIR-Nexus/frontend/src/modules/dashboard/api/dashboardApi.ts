/**
 * Datos del panel de inicio.
 *
 * Dos peticiones y **solo dos**, a propósito: el registro de casos (Módulo 1)
 * y el registro consolidado de análisis OSINT (Módulo 2). Ambos devuelven una
 * lista completa de una vez, así que el panel cuesta lo mismo con 2 casos que
 * con 100.
 *
 * Lo que deliberadamente NO se muestra son los recuentos de tracking, de
 * cronología y de informes. Sus backends solo exponen esos datos **por caso**
 * (`/cases/{id}/tracking/events`, `/timeline/cases/{id}`,
 * `/cases/{id}/reports`), así que un total exigiría una petición por caso: con
 * dos casos parece gratis y con doscientos convierte abrir la pantalla de
 * inicio en doscientas llamadas. Si el equipo quiere esas cifras, lo correcto
 * es pedir a cada módulo un endpoint de recuento, no simularlo desde aquí.
 *
 * Cada módulo tiene su cliente HTTP (DESIGN_SYSTEM §17) y `modules/A` no
 * importa `modules/B` (§13), así que este repite el suyo en vez de reutilizar
 * el de Casos.
 */
import { getToken, handleUnauthorized } from '@/shared/auth'
const DEFAULT_CASES_BASE_URL = 'http://localhost:8000'
const DEFAULT_OSINT_BASE_URL = 'http://localhost:8124'

export const CASES_API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? DEFAULT_CASES_BASE_URL
export const OSINT_API_BASE_URL = import.meta.env.VITE_OSINT_API_URL ?? DEFAULT_OSINT_BASE_URL

/** Tope de casos que se leen. Coincide con el `limit` que admite el Módulo 1. */
export const TOPE_CASOS = 100

export type EstadoCaso = 'abierto' | 'en_progreso' | 'cerrado' | 'archivado'

export interface CaseResumen {
  id: number
  nombre: string
  estado: EstadoCaso
  fecha_creacion: string
  responsable: string | null
}

export interface OsintFinding {
  id: number
  case_id: number | null
  case_type: string
  subject_type: string
  subject_value: string
  risk_score: number
  risk_level: string
  headline: string
  analyzed_at: string
}

/**
 * Lo que el panel ha podido leer de cada fuente.
 *
 * Cada bloque se pide por separado y **el fallo de uno no tumba el panel**: si
 * el backend de OSINT no está levantado, se sigue viendo el de casos y se dice
 * que el otro no está disponible. Un panel que se queda en blanco entero
 * porque falta un proceso no informa de nada.
 */
export interface Fuente<T> {
  datos: T[]
  error: string | null
}

async function leer<T>(url: string, queFalta: string): Promise<Fuente<T>> {
  const token = getToken()
  try {
    const respuesta = await fetch(url, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
    if (!respuesta.ok) {
      // El 401 es la excepción a la tolerancia de arriba: no es «esta fuente
      // no está disponible», es «la sesión ya no vale». Degradar el panel y
      // seguir mostrándolo sería mentir — y además las dos fuentes fallarían
      // igual, dejando una pantalla vacía sin explicar por qué. Se corta y se
      // manda a /login como en el resto de la aplicación.
      if (respuesta.status === 401 && token) {
        handleUnauthorized()
      }
      return { datos: [], error: `${queFalta}: el servicio respondió ${respuesta.status}.` }
    }
    return { datos: (await respuesta.json()) as T[], error: null }
  } catch {
    return { datos: [], error: `${queFalta}: no responde. ¿Está arrancado su backend?` }
  }
}

export const dashboardApi = {
  casos: () =>
    leer<CaseResumen>(
      `${CASES_API_BASE_URL}/cases?skip=0&limit=${TOPE_CASOS}`,
      'Registro de casos (Módulo 1, puerto 8000)',
    ),

  osint: () =>
    leer<OsintFinding>(
      `${OSINT_API_BASE_URL}/osint-findings`,
      'Análisis OSINT (Módulo 2, puerto 8124)',
    ),
}
