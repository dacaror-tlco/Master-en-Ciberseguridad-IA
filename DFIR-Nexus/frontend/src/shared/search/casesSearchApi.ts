import { getToken, handleUnauthorized } from '../auth'

/**
 * Lectura mínima de `GET /cases` para el buscador de la barra superior.
 *
 * Vive en `shared/` y no en `modules/cases` porque quien lo usa es el `TopBar`,
 * que es `shared/layout`, y `shared/*` no puede importar de `modules/*` (ver
 * CLAUDE.md). Es una lectura de cuatro campos, no una segunda capa de acceso al
 * módulo de Casos: el dueño de la tabla sigue siendo el Módulo 1 y esto le habla
 * por HTTP como cualquier otro cliente.
 */
const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export type CasoBuscable = {
  id: number
  nombre: string
  responsable: string
  estado: string
  eliminado: boolean
}

/**
 * Trae los casos sobre los que buscar.
 *
 * **El filtrado es en el cliente**, porque `GET /cases` solo acepta `skip`,
 * `limit` e `incluir_eliminados`: no hay búsqueda en el servidor. Con los casos
 * que maneja el equipo eso es una petición y nada más, pero **no escala**: si la
 * base creciera a cientos de expedientes, esto tiene que pasar a ser un endpoint
 * de búsqueda en el Módulo 1 y no un filtro aquí.
 *
 * Los eliminados no se piden: el buscador es para llegar a un caso y trabajarlo,
 * y un caso eliminado no admite operaciones. Siguen siendo alcanzables desde el
 * listado de Casos, que es donde se gestiona esa vista.
 */
export async function listarCasosBuscables(): Promise<CasoBuscable[]> {
  const token = getToken()
  const respuesta = await fetch(`${BASE_URL}/cases?limit=500`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  })

  if (!respuesta.ok) {
    if (respuesta.status === 401 && token) handleUnauthorized()
    throw new Error(`No se ha podido leer la lista de casos (${respuesta.status})`)
  }

  return respuesta.json()
}

/**
 * Normaliza para comparar: sin mayúsculas y sin tildes.
 *
 * Sin quitar las tildes, buscar «suplantacion» no encontraría «suplantación», y
 * es exactamente lo que alguien teclea con prisa.
 */
export function normalizar(texto: string): string {
  return texto
    .toLowerCase()
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
}

/**
 * Casos que encajan con lo escrito, ordenados por lo que más probablemente se
 * buscaba.
 *
 * Se busca por número de expediente, por nombre y por responsable, que son los
 * tres datos con los que alguien se refiere a un caso en voz alta. El orden pone
 * primero la coincidencia exacta de id y después los nombres que empiezan por lo
 * escrito, antes que los que solo lo contienen en medio.
 */
export function filtrarCasos(casos: CasoBuscable[], consulta: string): CasoBuscable[] {
  const aguja = normalizar(consulta.trim())
  if (!aguja) return []

  const puntuar = (caso: CasoBuscable): number => {
    const nombre = normalizar(caso.nombre)
    if (String(caso.id) === aguja) return 0
    if (nombre.startsWith(aguja)) return 1
    if (String(caso.id).startsWith(aguja)) return 2
    if (nombre.includes(aguja)) return 3
    if (normalizar(caso.responsable).includes(aguja)) return 4
    return Number.POSITIVE_INFINITY
  }

  return casos
    .map((caso) => ({ caso, orden: puntuar(caso) }))
    .filter(({ orden }) => Number.isFinite(orden))
    .sort((a, b) => a.orden - b.orden || a.caso.id - b.caso.id)
    .map(({ caso }) => caso)
}
