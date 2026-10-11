import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Icon, IconButton, StatusBadge } from '../../ui'
import type { StatusTone } from '../../ui'
import { filtrarCasos, listarCasosBuscables } from '../../search'
import type { CasoBuscable } from '../../search'
import { useMediaQuery } from '../../hooks'

/**
 * Buscador de expedientes de la barra superior.
 *
 * Estuvo puesto y deshabilitado desde el mockup. Ahora busca de verdad: por
 * número de expediente, por nombre y por responsable, y al elegir un resultado
 * lleva al listado de Casos con ese caso ya seleccionado
 * (`/cases?caso=<id>`).
 *
 * **La lista se pide una sola vez, al primer foco**, no en cada pulsación ni al
 * montar la barra: el filtrado es en cliente (ver `casesSearchApi`) y la barra
 * está en todas las pantallas, así que cargarla siempre sería una petición por
 * navegación para algo que casi nunca se usa. Se refresca al volver a enfocar
 * si la anterior falló, para que un backend que estaba caído no deje el buscador
 * muerto hasta recargar.
 */
const MAXIMO_RESULTADOS = 6

const TONO_ESTADO: Record<string, StatusTone> = {
  abierto: 'primary',
  en_progreso: 'tertiary',
  cerrado: 'neutral',
  archivado: 'muted',
}

const ETIQUETA_ESTADO: Record<string, string> = {
  abierto: 'Abierto',
  en_progreso: 'En progreso',
  cerrado: 'Cerrado',
  archivado: 'Archivado',
}

export function BuscadorGlobal() {
  const navigate = useNavigate()
  const escritorio = useMediaQuery('(min-width: 768px)')
  const [consulta, setConsulta] = useState('')
  const [casos, setCasos] = useState<CasoBuscable[] | null>(null)
  const [cargando, setCargando] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [abierto, setAbierto] = useState(false)
  const [resaltado, setResaltado] = useState(0)
  // Por debajo de `md` el buscador arranca colapsado en un icono: expandirlo
  // es una acción explícita, para no competir por sitio con el botón
  // hamburguesa y el logo en una cabecera de 320px de ancho.
  const [expandidoMovil, setExpandidoMovil] = useState(false)
  const contenedor = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const resultados = casos ? filtrarCasos(casos, consulta).slice(0, MAXIMO_RESULTADOS) : []

  // Cerrar al pulsar fuera. Con `blur` del input no basta: al hacer clic en un
  // resultado el input pierde el foco antes de que el clic llegue, y la lista
  // desaparecía justo debajo del cursor.
  useEffect(() => {
    if (!abierto) return
    const alPulsarFuera = (evento: MouseEvent) => {
      if (!contenedor.current?.contains(evento.target as Node)) setAbierto(false)
    }
    document.addEventListener('mousedown', alPulsarFuera)
    return () => document.removeEventListener('mousedown', alPulsarFuera)
  }, [abierto])

  const cargarSiHaceFalta = async () => {
    if (casos !== null || cargando) return
    setCargando(true)
    setError(null)
    try {
      setCasos(await listarCasosBuscables())
    } catch {
      setError('No se ha podido cargar la lista de casos.')
    } finally {
      setCargando(false)
    }
  }

  const abrirCaso = (caso: CasoBuscable) => {
    setConsulta('')
    setAbierto(false)
    setExpandidoMovil(false)
    navigate(`/cases?caso=${caso.id}`)
  }

  // Foco automático al expandir en móvil: quien pulsa la lupa espera poder
  // escribir sin un segundo toque sobre el campo.
  useEffect(() => {
    if (expandidoMovil) inputRef.current?.focus()
  }, [expandidoMovil])

  const alTeclear = (evento: React.KeyboardEvent<HTMLInputElement>) => {
    if (evento.key === 'Escape') {
      // Con texto escrito, Escape limpia; vacío, cierra (y en móvil, además
      // colapsa de vuelta al icono). Así una pulsación no hace dos cosas a
      // la vez y hay que volver a escribir desde cero.
      if (consulta) setConsulta('')
      else {
        setAbierto(false)
        setExpandidoMovil(false)
      }
      return
    }
    if (resultados.length === 0) return
    if (evento.key === 'ArrowDown') {
      evento.preventDefault()
      setResaltado((actual) => (actual + 1) % resultados.length)
    } else if (evento.key === 'ArrowUp') {
      evento.preventDefault()
      setResaltado((actual) => (actual - 1 + resultados.length) % resultados.length)
    } else if (evento.key === 'Enter') {
      evento.preventDefault()
      abrirCaso(resultados[Math.min(resaltado, resultados.length - 1)])
    }
  }

  const hayAlgoQueMostrar = abierto && (consulta.trim() !== '' || cargando || error !== null)

  // Campo + desplegable de resultados: el mismo bloque, tanto en el buscador
  // inline de escritorio como dentro del panel expandible de móvil/tablet.
  const cuerpo = (
    <div ref={contenedor} className="relative w-full">
      <span className="absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant text-sm pointer-events-none">
        <Icon name="search" className="text-[16px]" />
      </span>
      <input
        ref={inputRef}
        className="w-full bg-canvas border border-hairline rounded px-9 py-2 font-mono-data text-mono-data
          text-on-surface placeholder-on-surface-variant focus:outline-none focus:border-primary
          focus:ring-1 focus:ring-primary/50 transition-all"
        placeholder="ID de Caso, Nombre, Responsable..."
        type="search"
        value={consulta}
        aria-label="Buscar un expediente"
        onFocus={() => {
          setAbierto(true)
          void cargarSiHaceFalta()
        }}
        onChange={(evento) => {
          setConsulta(evento.target.value)
          setResaltado(0)
          setAbierto(true)
        }}
        onKeyDown={alTeclear}
      />

      {hayAlgoQueMostrar && (
        <div className="absolute left-0 right-0 top-full mt-1 z-50 nexus-glass-panel rounded border border-hairline overflow-hidden">
          {cargando && (
            <p className="px-3 py-2 font-mono-data text-mono-data text-on-surface-variant">
              Cargando expedientes…
            </p>
          )}

          {error && (
            <p className="px-3 py-2 font-mono-data text-mono-data text-error">{error}</p>
          )}

          {!cargando && !error && resultados.length === 0 && (
            <p className="px-3 py-2 font-mono-data text-mono-data text-on-surface-variant">
              Ningún expediente coincide con «{consulta.trim()}».
            </p>
          )}

          {resultados.map((caso, indice) => (
            <button
              key={caso.id}
              type="button"
              onMouseEnter={() => setResaltado(indice)}
              onClick={() => abrirCaso(caso)}
              className={`w-full text-left px-3 py-2 flex items-center gap-3 transition-colors ${
                indice === resaltado ? 'bg-surface-container-highest' : ''
              }`}
            >
              <span className="text-primary font-mono-data text-xs shrink-0">#{caso.id}</span>
              <span className="text-on-surface text-sm truncate flex-1">{caso.nombre}</span>
              <StatusBadge
                label={ETIQUETA_ESTADO[caso.estado] ?? caso.estado}
                tone={TONO_ESTADO[caso.estado] ?? 'neutral'}
              />
            </button>
          ))}
        </div>
      )}
    </div>
  )

  // Escritorio (`md+`): igual que siempre, inline y con ancho acotado.
  if (escritorio) {
    return <div className="w-full max-w-md">{cuerpo}</div>
  }

  // Móvil/tablet estrecho (`<md`), colapsado: un icono, nunca oculto del
  // todo. Al pulsarlo se expande en una franja bajo la cabecera con el
  // mismo campo y los mismos resultados que en escritorio.
  if (!expandidoMovil) {
    return (
      <IconButton
        icon="search"
        label="Buscar un expediente"
        onClick={() => setExpandidoMovil(true)}
      />
    )
  }

  return (
    <>
      <div
        className="fixed inset-0 z-30"
        aria-hidden="true"
        onClick={() => {
          setAbierto(false)
          setExpandidoMovil(false)
        }}
      />
      <div className="fixed inset-x-0 top-16 z-40 p-gutter bg-surface-container-low/95 backdrop-blur-md border-b border-hairline flex items-center gap-2">
        <div className="flex-1 min-w-0">{cuerpo}</div>
        <IconButton
          icon="close"
          label="Cerrar el buscador"
          onClick={() => {
            setAbierto(false)
            setExpandidoMovil(false)
          }}
        />
      </div>
    </>
  )
}
