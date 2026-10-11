import type { TimelineEvent } from '../api/timelineApi'
import { computeTimeLayout, formatGapDuration } from '../utils/timeScale'

const ORIGINS = ['evidence', 'tracking', 'osint'] as const
type Origin = (typeof ORIGINS)[number]

const ORIGIN_LABELS: Record<Origin, string> = {
  evidence: 'Evidencia',
  tracking: 'Tracking',
  osint: 'OSINT',
}

const ORIGIN_COLORS: Record<Origin, string> = {
  evidence: 'var(--color-error)',
  tracking: 'var(--color-primary)',
  osint: 'var(--color-tertiary)',
}

const SVG_WIDTH = 900
const LABEL_WIDTH = 90
const LANE_HEIGHT = 42
const TOP_MARGIN = 20
const BOTTOM_MARGIN = 50
const SVG_HEIGHT = TOP_MARGIN + LANE_HEIGHT * ORIGINS.length + BOTTOM_MARGIN

function formatDate(d: Date): string {
  return d.toLocaleDateString('es-ES', { day: '2-digit', month: 'short' })
}

interface Props {
  events: TimelineEvent[]
  selectedEventId?: number | null
  onSelectEvent: (event: TimelineEvent) => void
}

/**
 * Gráfico SVG horizontal con 3 carriles (uno por origen) y compresión de
 * huecos temporales > 12 h. La lógica de posicionamiento vive en
 * utils/timeScale.ts; este componente solo pinta.
 *
 * - Sin zoom/pan (v1). Si el caso abarca mucho, la compresión de huecos
 *   mantiene todos los eventos visibles.
 * - Al hacer click en un punto se llama `onSelectEvent`; el resaltado del
 *   evento seleccionado lo controla el padre vía `selectedEventId`.
 * - Hover: tooltip nativo del navegador (elemento <title>).
 */
export function TimelineChart({ events, selectedEventId, onSelectEvent }: Props) {
  if (events.length === 0) {
    return (
      <div className="p-8 text-center text-sm text-on-surface-variant">
        Sin eventos para representar.
      </div>
    )
  }

  const layout = computeTimeLayout(events, SVG_WIDTH - LABEL_WIDTH)

  const laneY: Record<Origin, number> = {} as Record<Origin, number>
  ORIGINS.forEach((orig, i) => {
    laneY[orig] = TOP_MARGIN + i * LANE_HEIGHT + LANE_HEIGHT / 2
  })

  return (
    <div className="overflow-x-auto">
      <svg
        viewBox={`0 0 ${SVG_WIDTH} ${SVG_HEIGHT}`}
        width="100%"
        style={{ minWidth: 640, maxWidth: SVG_WIDTH, display: 'block' }}
        role="img"
        aria-label="Línea temporal visual del caso"
      >
        {/* Etiquetas de carril */}
        {ORIGINS.map((orig) => (
          <text
            key={`label-${orig}`}
            x={LABEL_WIDTH - 12}
            y={laneY[orig] + 4}
            textAnchor="end"
            fill="var(--color-on-surface-variant)"
            fontSize={11}
            fontFamily="var(--font-mono-data, monospace)"
          >
            {ORIGIN_LABELS[orig]}
          </text>
        ))}

        {/* Líneas base por carril */}
        {ORIGINS.map((orig) => (
          <line
            key={`baseline-${orig}`}
            x1={LABEL_WIDTH}
            y1={laneY[orig]}
            x2={SVG_WIDTH - 10}
            y2={laneY[orig]}
            stroke="var(--color-outline-variant)"
            strokeDasharray="2 4"
          />
        ))}

        {/* Eje temporal */}
        <line
          x1={LABEL_WIDTH}
          y1={SVG_HEIGHT - BOTTOM_MARGIN}
          x2={SVG_WIDTH - 10}
          y2={SVG_HEIGHT - BOTTOM_MARGIN}
          stroke="var(--color-outline)"
        />

        {/* Fechas extremas */}
        {layout.minDate && (
          <text
            x={LABEL_WIDTH}
            y={SVG_HEIGHT - BOTTOM_MARGIN + 16}
            fill="var(--color-on-surface-variant)"
            fontSize={10}
            textAnchor="start"
          >
            {formatDate(layout.minDate)}
          </text>
        )}
        {layout.maxDate && (
          <text
            x={SVG_WIDTH - 10}
            y={SVG_HEIGHT - BOTTOM_MARGIN + 16}
            fill="var(--color-on-surface-variant)"
            fontSize={10}
            textAnchor="end"
          >
            {formatDate(layout.maxDate)}
          </text>
        )}

        {/* Marcadores de huecos comprimidos */}
        {layout.gaps.map((gap, idx) => {
          const gx1 = LABEL_WIDTH + gap.xStart
          const gx2 = LABEL_WIDTH + gap.xEnd
          const cx = (gx1 + gx2) / 2
          return (
            <g key={`gap-${idx}`}>
              <rect
                x={gx1}
                y={TOP_MARGIN}
                width={gx2 - gx1}
                height={LANE_HEIGHT * ORIGINS.length}
                fill="var(--color-surface-container-lowest)"
                opacity={0.5}
              />
              <line
                x1={gx1}
                y1={TOP_MARGIN}
                x2={gx1}
                y2={SVG_HEIGHT - BOTTOM_MARGIN}
                stroke="var(--color-outline-variant)"
                strokeDasharray="1 3"
              />
              <line
                x1={gx2}
                y1={TOP_MARGIN}
                x2={gx2}
                y2={SVG_HEIGHT - BOTTOM_MARGIN}
                stroke="var(--color-outline-variant)"
                strokeDasharray="1 3"
              />
              <text
                x={cx}
                y={SVG_HEIGHT - BOTTOM_MARGIN + 16}
                textAnchor="middle"
                fill="var(--color-on-surface-variant)"
                fontSize={10}
                fontStyle="italic"
              >
                {`⌇ ${formatGapDuration(gap.durationMs)}`}
              </text>
            </g>
          )
        })}

        {/* Puntos de eventos */}
        {events.map((ev) => {
          const pos = layout.positionOf(ev.id)
          if (!pos) return null
          const lane = ev.origen_modulo as Origin
          const y = laneY[lane] ?? laneY.tracking
          const x = LABEL_WIDTH + pos.x
          const isSelected = ev.id === selectedEventId
          const color = ORIGIN_COLORS[lane] ?? 'var(--color-on-surface)'

          return (
            <g
              key={ev.id}
              onClick={() => onSelectEvent(ev)}
              style={{ cursor: 'pointer' }}
            >
              {isSelected && (
                <circle cx={x} cy={y} r={12} fill={color} opacity={0.3} />
              )}
              <circle
                cx={x}
                cy={y}
                r={isSelected ? 7 : 6}
                fill={color}
                stroke="var(--color-background)"
                strokeWidth={1.5}
              />
              {/* Zona de click ampliada */}
              <circle cx={x} cy={y} r={14} fill="transparent" />
              <title>
                {`#${ev.orden} · ${ORIGIN_LABELS[lane]}\n${new Date(ev.fecha_hora).toLocaleString('es-ES')}\n${ev.descripcion}`}
              </title>
            </g>
          )
        })}
      </svg>
    </div>
  )
}

export default TimelineChart
