import { Fragment, type ReactNode } from 'react'

/**
 * Pinta la respuesta del modelo: markdown mínimo y referencias resaltadas.
 *
 * Se resuelve construyendo nodos de React, nunca con `dangerouslySetInnerHTML`
 * ni inyectando HTML — el texto lo escribe un LLM a partir de datos que
 * proceden en último término de logs y de fuentes externas, así que se trata
 * como dato, no como marcado. Es el mismo criterio de escapado que el módulo
 * de Informes aplica a sus cuatro formatos de salida.
 *
 * Se soporta a propósito solo lo que el asistente usa de verdad —párrafos,
 * listas, negrita y código en línea— en vez de añadir una dependencia de
 * markdown completa para esto.
 */

const NEGRITA_O_CODIGO = /(\*\*[^*]+\*\*|`[^`]+`|\[[A-Z]{2}\d+\])/g

function pintarLinea(texto: string, keyBase: string): ReactNode[] {
  return texto.split(NEGRITA_O_CODIGO).map((trozo, i) => {
    const key = `${keyBase}-${i}`
    if (trozo.startsWith('**') && trozo.endsWith('**')) {
      return (
        <strong key={key} className="text-on-surface font-semibold">
          {trozo.slice(2, -2)}
        </strong>
      )
    }
    if (trozo.startsWith('`') && trozo.endsWith('`')) {
      return (
        <code
          key={key}
          className="font-mono-data text-mono-data bg-surface-container-highest px-1.5 py-0.5 rounded text-[0.9em]"
        >
          {trozo.slice(1, -1)}
        </code>
      )
    }
    // Referencia a un registro del expediente: se marca para que se vea de un
    // vistazo qué parte de la respuesta está respaldada por una fila real.
    if (/^\[[A-Z]{2}\d+\]$/.test(trozo)) {
      return (
        <span
          key={key}
          title="Registro del expediente en el que se apoya esta afirmación"
          className="font-mono-data text-[0.8em] text-primary bg-secondary-container/20 border border-primary/30 rounded px-1 mx-0.5 align-baseline"
        >
          {trozo.slice(1, -1)}
        </span>
      )
    }
    return <Fragment key={key}>{trozo}</Fragment>
  })
}

export function RespuestaTexto({ texto }: { texto: string }) {
  const bloques: ReactNode[] = []
  let listaAbierta: ReactNode[] = []
  let listaOrdenada = false

  const cerrarLista = () => {
    if (listaAbierta.length === 0) return
    const Etiqueta = listaOrdenada ? 'ol' : 'ul'
    bloques.push(
      <Etiqueta
        key={`lista-${bloques.length}`}
        className={`pl-5 space-y-1 ${listaOrdenada ? 'list-decimal' : 'list-disc'}`}
      >
        {listaAbierta}
      </Etiqueta>,
    )
    listaAbierta = []
  }

  texto.split('\n').forEach((linea, i) => {
    const limpia = linea.trim()

    if (limpia === '') {
      cerrarLista()
      return
    }

    const vinieta = /^[-*]\s+(.*)$/.exec(limpia)
    const numerada = /^\d+[.)]\s+(.*)$/.exec(limpia)

    if (vinieta || numerada) {
      const esOrdenada = Boolean(numerada)
      if (listaAbierta.length > 0 && esOrdenada !== listaOrdenada) cerrarLista()
      listaOrdenada = esOrdenada
      const contenido = (vinieta ?? numerada)![1]
      listaAbierta.push(<li key={`li-${i}`}>{pintarLinea(contenido, `li-${i}`)}</li>)
      return
    }

    cerrarLista()
    bloques.push(
      <p key={`p-${i}`} className="leading-relaxed">
        {pintarLinea(limpia, `p-${i}`)}
      </p>,
    )
  })

  cerrarLista()

  return <div className="space-y-3 text-on-surface-variant">{bloques}</div>
}
