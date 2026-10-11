import type { FuenteCitada } from './api/chatApi'

/**
 * Conversaciones del asistente, guardadas en el navegador.
 *
 * **Un hilo por caso**, y esa es la pieza clave: no es solo comodidad, es lo
 * que impide mezclar expedientes. La conversación se le reenvía al modelo en
 * cada turno, así que arrastrar los turnos del caso 8 a una pregunta sobre el
 * caso 1 metía las evidencias, las IPs y los usuarios del 8 dentro del prompt
 * del 1 — reproducido antes de arreglarlo. Con un hilo por caso, cambiar el
 * desplegable cambia de conversación y no hay nada que arrastrar. El servidor
 * lo comprueba además por su cuenta (`ChatRequest.historial_case_id`).
 *
 * **En `localStorage` y no en la base de datos**, a propósito y en coherencia
 * con lo ya decidido para el backend (ver `sharingan/app/modules/chat/
 * schemas.py`): el chat es apoyo al perito, no material probatorio, y una
 * tabla nueva tocaría el modelo de datos oficial — que exige acuerdo de equipo
 * (CLAUDE.md, regla 4). Consecuencias, que la interfaz dice: el historial es
 * de este navegador, no viaja entre equipos y desaparece al borrar los datos
 * del sitio.
 *
 * Ojo con lo que esto implica: aquí quedan guardados datos del expediente en
 * el disco del perito. Es la misma máquina que ya los muestra en pantalla, así
 * que no añade exposición nueva, pero por eso existe el botón de borrar todo.
 */

export type Turno = {
  rol: 'usuario' | 'asistente'
  contenido: string
  fuentes?: FuenteCitada[]
  filasDeContexto?: number
  advertencias?: string[]
  modelo?: string
  segundos?: number
  /** Milisegundos epoch. Solo se rellena en los turnos del usuario. */
  cuando?: number
}

/** Clave del hilo: `general` o `caso-8`. */
export type ClaveHilo = string

export function claveDe(caseId: number | null): ClaveHilo {
  return caseId === null ? 'general' : `caso-${caseId}`
}

export function caseIdDe(clave: ClaveHilo): number | null {
  return clave === 'general' ? null : Number(clave.slice('caso-'.length))
}

type Almacen = Record<ClaveHilo, Turno[]>

const CLAVE_ALMACEN = 'nexus.chat.hilos.v1'

/**
 * Tope de turnos por hilo. `localStorage` ronda los 5 MB y un expediente
 * citado ocupa; sin tope, una sesión larga acabaría lanzando `QuotaExceeded`
 * justo al guardar, es decir al terminar de esperar una respuesta.
 */
const MAX_TURNOS = 40

function leerAlmacen(): Almacen {
  // Todo acceso va envuelto: en ventana privada, con las cookies de sitio
  // bloqueadas o en una captura de miniatura, el mero `getItem` lanza. Un
  // historial es una comodidad; que su ausencia tumbe el chat, no.
  try {
    const bruto = localStorage.getItem(CLAVE_ALMACEN)
    return bruto ? (JSON.parse(bruto) as Almacen) : {}
  } catch {
    return {}
  }
}

function escribirAlmacen(almacen: Almacen): void {
  try {
    localStorage.setItem(CLAVE_ALMACEN, JSON.stringify(almacen))
  } catch {
    // Sin espacio o sin permiso: se sigue sin historial persistente. La
    // conversación en curso vive en el estado de React y no se pierde.
  }
}

export function leerHilo(clave: ClaveHilo): Turno[] {
  return leerAlmacen()[clave] ?? []
}

export function guardarHilo(clave: ClaveHilo, turnos: Turno[]): void {
  const almacen = leerAlmacen()
  if (turnos.length === 0) delete almacen[clave]
  else almacen[clave] = turnos.slice(-MAX_TURNOS)
  escribirAlmacen(almacen)
}

export function borrarTodo(): void {
  try {
    localStorage.removeItem(CLAVE_ALMACEN)
  } catch {
    /* nada que hacer */
  }
}

export type EntradaHistorial = {
  clave: ClaveHilo
  caseId: number | null
  pregunta: string
  cuando?: number
}

/**
 * Las preguntas hechas, de la más reciente a la más antigua, con el caso al
 * que pertenecen. Es lo que alimenta el panel de historial.
 */
export function listarPreguntas(tope = 50): EntradaHistorial[] {
  const almacen = leerAlmacen()
  const entradas: EntradaHistorial[] = []

  for (const [clave, turnos] of Object.entries(almacen)) {
    for (const turno of turnos) {
      if (turno.rol !== 'usuario') continue
      entradas.push({
        clave,
        caseId: caseIdDe(clave),
        pregunta: turno.contenido,
        cuando: turno.cuando,
      })
    }
  }

  // Sin marca de tiempo (turnos guardados antes de que existiera el campo) van
  // al final en vez de colarse arriba como si fuesen de 1970.
  entradas.sort((a, b) => (b.cuando ?? 0) - (a.cuando ?? 0))
  return entradas.slice(0, tope)
}
