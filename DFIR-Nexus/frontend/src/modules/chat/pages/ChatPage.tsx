import { useEffect, useRef, useState } from 'react'
import { Alert, Button, Card, Icon, Select } from '@/shared/ui'
import {
  ApiError,
  casesLookupApi,
  chatApi,
  type CaseOption,
  type Mensaje,
} from '../api/chatApi'
import { RespuestaTexto } from '../components/RespuestaTexto'
import {
  borrarTodo,
  claveDe,
  guardarHilo,
  leerHilo,
  listarPreguntas,
  type EntradaHistorial,
  type Turno,
} from '../historial'

/**
 * Asistente conversacional del perito.
 *
 * Dos modos, y la interfaz distingue siempre en cuál está, porque la
 * diferencia no es cosmética: con un caso seleccionado, el asistente ha leído
 * su expediente y cada afirmación va respaldada por una fila concreta de la
 * base; sin caso, responde de conocimiento general y no ha consultado nada.
 * Dar a entender lo contrario sería lo peor que puede hacer esta pantalla.
 *
 * El historial vive aquí, en el cliente: el backend es sin estado y no guarda
 * la conversación (ver sharingan/app/modules/chat/schemas.py). Recargar la
 * página la borra, y eso es lo previsto — un chat de apoyo no es material
 * probatorio.
 */

const SUGERENCIAS_CON_CASO = [
  '¿Qué ocurrió en este caso, en orden cronológico?',
  '¿Cuál fue el vector de entrada más probable y en qué te apoyas?',
  '¿Qué evidencias hay recogidas y qué falta por documentar?',
  'Resume los indicadores OSINT de mayor riesgo.',
]

const SUGERENCIAS_SIN_CASO = [
  '¿Qué apartados exige la norma UNE 197010 en un informe pericial?',
  '¿Cómo se documenta una cadena de custodia correctamente?',
  '¿Qué diferencia hay entre un hallazgo acreditado y uno indiciario?',
  '¿Qué debo revisar en un log de autenticación tras un incidente?',
]

export function ChatPage() {
  const [cases, setCases] = useState<CaseOption[]>([])
  const [caseId, setCaseId] = useState<number | null>(null)
  // Se arranca con el hilo guardado del ámbito actual, no vacío: recargar la
  // página no debería tirar la conversación.
  const [turnos, setTurnos] = useState<Turno[]>(() => leerHilo(claveDe(null)))
  const [historialAbierto, setHistorialAbierto] = useState(false)
  const [preguntas, setPreguntas] = useState<EntradaHistorial[]>([])
  const [borrador, setBorrador] = useState('')
  const [enviando, setEnviando] = useState(false)
  const [segundos, setSegundos] = useState(0)
  // Texto que va llegando del modelo mientras responde. Es un borrador sin
  // verificar: al terminar se sustituye por la respuesta comprobada que
  // devuelve el backend (citas limpias, fuentes reales).
  const [parcial, setParcial] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [avisoCasos, setAvisoCasos] = useState<string | null>(null)

  const finDelHilo = useRef<HTMLDivElement>(null)

  useEffect(() => {
    casesLookupApi
      .list()
      .then(setCases)
      .catch(() =>
        setAvisoCasos(
          'No se ha podido cargar la lista de casos (backend de Casos, puerto 8000). ' +
            'El asistente sigue disponible en modo general.',
        ),
      )
  }, [])

  useEffect(() => {
    finDelHilo.current?.scrollIntoView({ behavior: 'smooth' })
  }, [turnos, enviando])

  // El hilo se guarda por caso. Sin esto, cambiar de caso o recargar perdería
  // la conversación, y el historial no tendría de dónde salir.
  useEffect(() => {
    guardarHilo(claveDe(caseId), turnos)
  }, [caseId, turnos])

  // Una respuesta sobre un caso tarda: con la API, segundos; con el modelo
  // local y sin GPU, más de un minuto. Enseñar el tiempo transcurrido evita
  // que parezca que se ha colgado.
  useEffect(() => {
    if (!enviando) return
    setSegundos(0)
    const id = setInterval(() => setSegundos((s) => s + 1), 1000)
    return () => clearInterval(id)
  }, [enviando])

  const casoActual = cases.find((c) => c.id === caseId)
  const sugerencias = caseId === null ? SUGERENCIAS_SIN_CASO : SUGERENCIAS_CON_CASO

  async function enviar(texto: string) {
    const mensaje = texto.trim()
    if (mensaje === '' || enviando) return

    const historial: Mensaje[] = turnos.map((t) => ({ rol: t.rol, contenido: t.contenido }))

    setTurnos((prev) => [...prev, { rol: 'usuario', contenido: mensaje, cuando: Date.now() }])
    setBorrador('')
    setError(null)
    setEnviando(true)
    const arranque = Date.now()

    try {
      setParcial('')
      const res = await chatApi.preguntarEnTrozos(mensaje, caseId, historial, (t) =>
        setParcial((prev) => prev + t),
      )
      setTurnos((prev) => [
        ...prev,
        {
          rol: 'asistente',
          contenido: res.respuesta,
          fuentes: res.fuentes,
          filasDeContexto: res.filas_de_contexto,
          advertencias: res.advertencias,
          modelo: res.modelo,
          segundos: Math.round((Date.now() - arranque) / 1000),
        },
      ])
    } catch (e) {
      // La pregunta se queda en el hilo (el usuario la escribió y sigue siendo
      // parte de la conversación), pero el error se muestra aparte para que no
      // se confunda con una respuesta del asistente.
      const detalle =
        e instanceof ApiError
          ? e.message
          : e instanceof Error
            ? e.message
            : 'Error desconocido al consultar al asistente.'
      setError(detalle)
    } finally {
      setEnviando(false)
      setParcial('')
    }
  }

  return (
    <div className="h-full flex flex-col p-gutter gap-panel-gap overflow-hidden">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="font-headline text-headline-md text-on-surface">Asistente</h1>
          <p className="text-on-surface-variant text-sm mt-1">
            {caseId === null
              ? 'Modo general: no hay ningún caso seleccionado, así que el asistente no ha leído ningún expediente.'
              : `Consultando el expediente del caso #${caseId}. Cada afirmación va referenciada al registro del que procede.`}
          </p>
        </div>

        <div className="flex items-end gap-3 w-full sm:w-auto">
          <Button
            variant="ghost"
            icon="history"
            onClick={() => {
              // Se relee al abrir, no en cada render: el almacén cambia con
              // cada turno y no hace falta consultarlo hasta que se mira.
              if (!historialAbierto) setPreguntas(listarPreguntas())
              setHistorialAbierto((abierto) => !abierto)
            }}
          >
            Historial
          </Button>
          <div className="w-full sm:w-80">
          <Select
            label="Caso"
            value={caseId === null ? '' : String(caseId)}
            onChange={(e) => {
              // Cambiar de caso cambia de conversación, no continúa la anterior.
              // No es solo comodidad: el historial se le reenvía al modelo en
              // cada turno, así que arrastrarlo metería las evidencias, IPs y
              // usuarios del caso anterior dentro del prompt de este. Con un
              // hilo por caso no hay nada que arrastrar, y al volver al caso
              // anterior su conversación sigue donde estaba.
              const nuevo = e.target.value === '' ? null : Number(e.target.value)
              setCaseId(nuevo)
              setTurnos(leerHilo(claveDe(nuevo)))
              setError(null)
              setParcial('')
            }}
            options={[
              { value: '', label: 'Sin caso — consulta general' },
              ...cases.map((c) => ({
                value: String(c.id),
                label: `#${c.id} · ${c.nombre} (${c.estado})`,
              })),
            ]}
          />
          </div>
        </div>
      </div>

      {historialAbierto && (
        <Card
          title={`Consultas anteriores (${preguntas.length})`}
          className="max-h-64 overflow-y-auto"
          actions={
            preguntas.length > 0 ? (
              <Button
                size="sm"
                variant="ghost"
                icon="delete_forever"
                onClick={() => {
                  borrarTodo()
                  setPreguntas([])
                  setTurnos([])
                }}
              >
                Borrar todo
              </Button>
            ) : undefined
          }
        >
          {preguntas.length === 0 ? (
            <p className="p-gutter text-on-surface-variant text-sm">
              Todavía no has consultado nada. Las preguntas se guardan en este navegador,
              agrupadas por caso.
            </p>
          ) : (
            <ul className="p-gutter space-y-2">
              {preguntas.map((entrada, i) => (
                <li key={`${entrada.clave}-${i}`}>
                  <button
                    type="button"
                    className="text-left w-full flex items-start gap-3 hover:text-primary transition-colors"
                    onClick={() => {
                      // Abre el hilo al que pertenece la pregunta, cambiando de
                      // caso si hace falta: una consulta solo se entiende junto
                      // al expediente sobre el que se hizo.
                      setCaseId(entrada.caseId)
                      setTurnos(leerHilo(entrada.clave))
                      setHistorialAbierto(false)
                      setError(null)
                    }}
                  >
                    <span className="font-mono-data text-mono-data text-primary shrink-0 text-xs pt-0.5">
                      {entrada.caseId === null ? 'general' : `#${entrada.caseId}`}
                    </span>
                    <span className="min-w-0">
                      <span className="block text-on-surface text-sm break-words">
                        {entrada.pregunta}
                      </span>
                      {entrada.cuando && (
                        <span className="block text-on-surface-variant opacity-50 text-xs font-mono-data">
                          {new Date(entrada.cuando).toLocaleString()}
                        </span>
                      )}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </Card>
      )}

      {avisoCasos && <Alert variant="info">{avisoCasos}</Alert>}
      {error && <Alert variant="error">{error}</Alert>}

      <div className="flex-1 overflow-y-auto rounded border border-hairline bg-surface-container-low p-gutter space-y-6">
        {turnos.length === 0 && (
          <div className="h-full flex flex-col items-center justify-center text-center gap-5 py-10">
            <div className="w-12 h-12 rounded-full bg-secondary-container/20 flex items-center justify-center">
              <Icon name="forum" className="text-primary" />
            </div>
            <div>
              <p className="font-label-caps text-label-caps text-on-surface">
                {casoActual ? casoActual.nombre : 'Consulta general'}
              </p>
              <p className="text-on-surface-variant text-sm mt-1 max-w-md">
                {caseId === null
                  ? 'Pregunta sobre metodología forense, normativa o redacción. Selecciona un caso arriba para que consulte su expediente.'
                  : 'Pregunta sobre las evidencias, los indicadores OSINT, los eventos de tracking y la cronología de este caso.'}
              </p>
            </div>
            <div className="flex flex-wrap gap-2 justify-center max-w-2xl">
              {sugerencias.map((s) => (
                <button
                  key={s}
                  type="button"
                  onClick={() => enviar(s)}
                  className="text-left text-sm text-on-surface-variant border border-hairline rounded px-3 py-2 hover:border-primary hover:text-primary transition-colors"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {turnos.map((turno, i) =>
          turno.rol === 'usuario' ? (
            <div key={i} className="flex justify-end">
              <div className="max-w-[85%] bg-secondary-container/20 border border-hairline rounded px-4 py-3 text-on-surface">
                {turno.contenido}
              </div>
            </div>
          ) : (
            <div key={i} className="flex gap-3">
              <div className="shrink-0 w-8 h-8 rounded bg-primary/10 border border-primary/30 flex items-center justify-center">
                <Icon name="fingerprint" className="text-primary text-[18px]" />
              </div>
              <div className="min-w-0 flex-1 space-y-3">
                <RespuestaTexto texto={turno.contenido} />
                {turno.advertencias?.map((a) => (
                  <Alert key={a} variant="error">
                    {a}
                  </Alert>
                ))}
                {turno.fuentes && turno.fuentes.length > 0 && (
                  <details className="border border-hairline rounded">
                    <summary className="cursor-pointer px-3 py-2 font-label-caps text-label-caps text-on-surface-variant hover:text-primary">
                      {turno.fuentes.length} registro
                      {turno.fuentes.length === 1 ? '' : 's'} citado
                      {turno.fuentes.length === 1 ? '' : 's'}
                    </summary>
                    <ul className="px-3 pb-3 space-y-2">
                      {turno.fuentes.map((f) => (
                        <li key={f.ref} className="flex gap-3 text-sm">
                          <span className="font-mono-data text-primary shrink-0">{f.ref}</span>
                          <span className="min-w-0">
                            <span className="text-on-surface break-words">{f.resumen}</span>
                            <span className="text-on-surface-variant opacity-60 font-mono-data text-xs block">
                              {f.tabla} · id {f.fila_id}
                            </span>
                          </span>
                        </li>
                      ))}
                    </ul>
                  </details>
                )}
                <p className="text-on-surface-variant opacity-50 text-xs font-mono-data">
                  {turno.filasDeContexto ? `${turno.filasDeContexto} registros del caso · ` : ''}
                  {turno.modelo}
                  {turno.segundos !== undefined ? ` · ${turno.segundos}s` : ''}
                </p>
              </div>
            </div>
          ),
        )}

        {enviando && (
          <div className="flex gap-3 items-start text-on-surface-variant">
            <div className="shrink-0 w-8 h-8 rounded bg-primary/10 border border-primary/30 flex items-center justify-center">
              <Icon name="fingerprint" className="text-primary text-[18px]" />
            </div>
            <div className="min-w-0 flex-1 space-y-2">
              {parcial ? (
                <RespuestaTexto texto={parcial} />
              ) : (
                <span className="text-sm animate-pulse">
                  {caseId === null ? 'Pensando…' : 'Consultando el expediente…'}
                </span>
              )}
              <p className="text-on-surface-variant opacity-50 text-xs font-mono-data">
                escribiendo… {segundos}s
              </p>
            </div>
          </div>
        )}

        <div ref={finDelHilo} />
      </div>

      <form
        className="flex items-end gap-3"
        onSubmit={(e) => {
          e.preventDefault()
          enviar(borrador)
        }}
      >
        <textarea
          value={borrador}
          onChange={(e) => setBorrador(e.target.value)}
          onKeyDown={(e) => {
            // Enter envía; Shift+Enter hace salto de línea.
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault()
              enviar(borrador)
            }
          }}
          rows={2}
          placeholder={
            caseId === null
              ? 'Pregunta al asistente…'
              : `Pregunta sobre el caso #${caseId}…`
          }
          className="flex-1 resize-none bg-canvas border border-hairline rounded px-4 py-3 text-on-surface
            focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary/50 transition-all"
        />
        <Button type="submit" icon="send" loading={enviando} disabled={borrador.trim() === ''}>
          Enviar
        </Button>
        {turnos.length > 0 && (
          <Button
            type="button"
            variant="ghost"
            icon="delete_sweep"
            onClick={() => {
              setTurnos([])
              setError(null)
            }}
          >
            Limpiar
          </Button>
        )}
      </form>
    </div>
  )
}

export default ChatPage
