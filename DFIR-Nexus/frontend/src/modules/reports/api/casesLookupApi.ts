import { createHttpClient, CASES_API_BASE_URL } from './httpClient'
import type { CaseOption } from '../types'

const http = createHttpClient(CASES_API_BASE_URL)

/**
 * Lectura del listado de casos del Módulo 1, y nada más: este módulo necesita
 * saber sobre qué caso emitir el informe. Es el mismo endpoint real
 * `GET /cases` que usa el módulo Casos (no se inventa ninguno), consumido aquí
 * a través del cliente propio del módulo en vez de importando su código.
 *
 * Si el backend del Módulo 1 no está levantado, la página cae en la entrada
 * manual del `case_id`: el módulo Informes sigue siendo usable por sí solo.
 */
export const casesLookupApi = {
  list: () => http.get<CaseOption[]>('/cases?skip=0&limit=100'),
}
