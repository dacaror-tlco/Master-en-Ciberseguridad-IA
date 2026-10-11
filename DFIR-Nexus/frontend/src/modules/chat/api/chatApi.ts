/**
 * Cliente HTTP del asistente conversacional.
 *
 * Dos URLs base, mismo criterio que `modules/reports` (ver DESIGN_SYSTEM §17
 * y docs/CONTRATOS.md): el chat lo sirve el backend de Informes —es el que ya
 * tiene el cliente de IA y la lectura de las seis tablas del contrato—, y la
 * lista de casos del selector viene del backend de Casos, que es su
 * propietario. Este módulo no importa nada de `modules/reports`: la regla
 * `modules/A → modules/B` está prohibida (§13), así que repite su cliente
 * mínimo en vez de reutilizarlo.
 *
 * El JWT se adjunta igual que en los demás módulos (`shared/auth`): un 401
 * con token puesto significa sesión caducada y se trata en un solo sitio,
 * `handleUnauthorized()`. Aquí hay dos caminos que lo necesitan y no uno,
 * porque `/chat/stream` no pasa por `request()`: usa `fetch` a pelo para
 * leer el cuerpo por trozos.
 */
import { getToken, handleUnauthorized } from '@/shared/auth'
const DEFAULT_CHAT_BASE_URL = 'http://localhost:8003'
const DEFAULT_CASES_BASE_URL = 'http://localhost:8000'

/** Backend de Informes, que es donde vive `POST /chat`. */
export const CHAT_API_BASE_URL = import.meta.env.VITE_REPORTS_API_URL ?? DEFAULT_CHAT_BASE_URL

/** Backend de Casos, solo para poblar el selector. */
export const CASES_API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? DEFAULT_CASES_BASE_URL

export type Rol = 'usuario' | 'asistente'

export interface Mensaje {
  rol: Rol
  contenido: string
}

/** Una fila real de la base que el asistente ha citado en su respuesta. */
export interface FuenteCitada {
  ref: string
  tabla: string
  fila_id: string
  resumen: string
}

export interface ChatResponse {
  respuesta: string
  fuentes: FuenteCitada[]
  con_contexto_de_caso: boolean
  /** Proveedor y modelo: `ollama/qwen2.5:3b-instruct`. Se muestra en la interfaz. */
  modelo: string
  filas_de_contexto: number
  /** Citas retiradas, colecciones recortadas, registros no disponibles. */
  advertencias: string[]
}

export interface CaseOption {
  id: number
  nombre: string
  estado: string
  responsable?: string | null
}

export class ApiError extends Error {
  status: number

  constructor(status: number, detail: unknown) {
    super(typeof detail === 'string' ? detail : `Error ${status}`)
    this.status = status
  }
}

async function request<T>(baseUrl: string, path: string, options?: RequestInit): Promise<T> {
  const token = getToken()
  const response = await fetch(`${baseUrl}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options?.headers,
    },
  })

  const body = await response.json().catch(() => null)
  if (!response.ok) {
    if (response.status === 401 && token) {
      handleUnauthorized()
    }
    throw new ApiError(response.status, body?.detail ?? body)
  }
  return body as T
}

export const chatApi = {
  /** POST /chat — el backend es sin estado: el historial viaja en cada turno. */
  preguntar: (mensaje: string, caseId: number | null, historial: Mensaje[]) =>
    request<ChatResponse>(CHAT_API_BASE_URL, '/chat', {
      method: 'POST',
      // `historial_case_id` va siempre igual a `case_id` porque la interfaz
      // mantiene un hilo por caso y nunca arrastra el de otro. Se declara de
      // todas formas: es lo que le permite al servidor comprobarlo en vez de
      // fiarse (ver historial.ts y ChatRequest.historial_case_id).
      body: JSON.stringify({
        mensaje,
        case_id: caseId,
        historial,
        historial_case_id: caseId,
      }),
    }),

  /**
   * POST /chat/stream — la misma respuesta, pero según el modelo la escribe.
   *
   * `onTrozo` recibe texto parcial para ir pintándolo; lo que devuelve la
   * promesa es la respuesta **verificada** por el backend, y es la que debe
   * quedar en pantalla. Los trozos son un borrador sin comprobar: si el modelo
   * se inventa una cita, aparece en ellos y desaparece en la versión final.
   */
  async preguntarEnTrozos(
    mensaje: string,
    caseId: number | null,
    historial: Mensaje[],
    onTrozo: (texto: string) => void,
    señal?: AbortSignal,
  ): Promise<ChatResponse> {
    const token = getToken()
    const respuesta = await fetch(`${CHAT_API_BASE_URL}/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({
        mensaje,
        case_id: caseId,
        historial,
        historial_case_id: caseId,
      }),
      signal: señal,
    })

    if (!respuesta.ok || !respuesta.body) {
      const cuerpo = await respuesta.json().catch(() => null)
      // El 401 se comprueba antes de abrir el flujo, que es el único momento
      // en que puede llegar como código HTTP: una vez emitido el primer
      // trozo la cabecera ya salió, y el backend manda los fallos como
      // evento `error` (ver chat/routes.py).
      if (respuesta.status === 401 && token) {
        handleUnauthorized()
      }
      throw new ApiError(respuesta.status, cuerpo?.detail ?? 'No se pudo abrir el flujo.')
    }

    const lector = respuesta.body.getReader()
    const decodificador = new TextDecoder()
    // Un evento SSE puede llegar partido entre dos lecturas, así que se acumula
    // y solo se procesan los bloques terminados en línea en blanco.
    let pendiente = ''
    let final: ChatResponse | null = null

    for (;;) {
      const { done, value } = await lector.read()
      if (done) break
      pendiente += decodificador.decode(value, { stream: true })

      const bloques = pendiente.split('\n\n')
      pendiente = bloques.pop() ?? ''

      for (const bloque of bloques) {
        const evento = /^event:\s*(.+)$/m.exec(bloque)?.[1]?.trim()
        const datos = /^data:\s*(.+)$/m.exec(bloque)?.[1]
        if (!evento || !datos) continue

        const carga = JSON.parse(datos)
        if (evento === 'trozo') onTrozo(carga.texto as string)
        else if (evento === 'fin') final = carga as ChatResponse
        else if (evento === 'error') throw new ApiError(502, carga.detail)
      }
    }

    if (!final) {
      throw new ApiError(502, 'El flujo terminó sin devolver la respuesta verificada.')
    }
    return final
  },
}

export const casesLookupApi = {
  /** `GET /cases` del Módulo 1 — no se inventa ninguna ruta propia. */
  list: () => request<CaseOption[]>(CASES_API_BASE_URL, '/cases?skip=0&limit=100'),
}
