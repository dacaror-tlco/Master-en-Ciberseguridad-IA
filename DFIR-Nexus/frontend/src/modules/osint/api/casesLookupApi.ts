import { casesHttp } from './httpClient'
import type { CaseOption } from '../types/case'

/**
 * Lectura del listado de casos del Módulo 1, y nada más: esta UI necesita
 * saber a qué caso puede vincularse una investigación. Es el mismo
 * endpoint real `GET /cases` que usa el módulo Casos (no se inventa
 * ninguno), consumido aquí a través del cliente propio del módulo en vez
 * de importar su código — calco de
 * `modules/reports/api/casesLookupApi.ts`, mismo motivo.
 */
export const casesLookupApi = {
  list: () => casesHttp.get<CaseOption[]>('/cases?skip=0&limit=100'),
}
