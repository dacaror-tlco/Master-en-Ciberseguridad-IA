import type { TimelineEvent } from '../api/timelineApi'

/**
 * Layout temporal para el gráfico de línea temporal.
 *
 * Problema que resuelve: en casos reales (ver caso 8), hay huecos de
 * días o semanas entre clusters de eventos. Una escala lineal dejaría
 * el 90% del gráfico vacío y aplastaría los eventos reales contra un
 * borde.
 *
 * Solución: dividir los eventos en "clusters" (grupos separados por
 * huecos > `gapThresholdMs`) y comprimir cada hueco a un ancho fijo.
 * Dentro de un cluster, los eventos se distribuyen uniformemente.
 *
 * Es una decisión de diseño explícita: la posición X NO es
 * proporcional al tiempo dentro de un cluster. Se prioriza que los
 * eventos sean visibles y clicables sobre la fidelidad métrica.
 */

const GAP_THRESHOLD_MS = 12 * 60 * 60 * 1000 // 12 horas
const GAP_WIDTH_PX = 60
const HORIZONTAL_MARGIN_PX = 20

export interface TimeGap {
  /** Índice del cluster que queda a la izquierda de este hueco */
  clusterIndex: number
  xStart: number
  xEnd: number
  fromDate: Date
  toDate: Date
  /** Duración real del hueco en milisegundos */
  durationMs: number
}

export interface TimeCluster {
  events: TimelineEvent[]
  xStart: number
  xEnd: number
  xCenter: number
  startDate: Date
  endDate: Date
}

export interface TimeLayout {
  clusters: TimeCluster[]
  gaps: TimeGap[]
  positionOf: (eventId: number) => { x: number; clusterIndex: number } | null
  totalWidth: number
  minDate: Date | null
  maxDate: Date | null
}

export interface TimeScaleOptions {
  gapThresholdMs?: number
  gapWidthPx?: number
  marginPx?: number
}

export function computeTimeLayout(
  events: TimelineEvent[],
  totalWidth: number,
  options: TimeScaleOptions = {},
): TimeLayout {
  const {
    gapThresholdMs = GAP_THRESHOLD_MS,
    gapWidthPx = GAP_WIDTH_PX,
    marginPx = HORIZONTAL_MARGIN_PX,
  } = options

  if (events.length === 0) {
    return {
      clusters: [],
      gaps: [],
      positionOf: () => null,
      totalWidth,
      minDate: null,
      maxDate: null,
    }
  }

  // 1. Ordenar por fecha ascendente
  const sorted = [...events].sort(
    (a, b) => new Date(a.fecha_hora).getTime() - new Date(b.fecha_hora).getTime(),
  )

  // 2. Detectar clusters separados por huecos > umbral
  const rawClusters: TimelineEvent[][] = [[sorted[0]]]
  const rawGaps: { durationMs: number; fromDate: Date; toDate: Date }[] = []

  for (let i = 1; i < sorted.length; i++) {
    const prev = new Date(sorted[i - 1].fecha_hora)
    const curr = new Date(sorted[i].fecha_hora)
    const delta = curr.getTime() - prev.getTime()
    if (delta > gapThresholdMs) {
      rawGaps.push({ durationMs: delta, fromDate: prev, toDate: curr })
      rawClusters.push([sorted[i]])
    } else {
      rawClusters[rawClusters.length - 1].push(sorted[i])
    }
  }

  // 3. Repartir ancho: huecos fijos + clusters proporcionalmente
  const numGaps = rawGaps.length
  const numClusters = rawClusters.length
  const gapsTotalWidth = numGaps * gapWidthPx
  const availableForClusters = totalWidth - gapsTotalWidth - 2 * marginPx
  const clusterWidth = Math.max(availableForClusters / numClusters, 1)

  // 4. Asignar coordenadas X
  const clusters: TimeCluster[] = []
  const gaps: TimeGap[] = []
  let x = marginPx

  rawClusters.forEach((evts, i) => {
    const xStart = x
    const xEnd = x + clusterWidth

    clusters.push({
      events: evts,
      xStart,
      xEnd,
      xCenter: xStart + clusterWidth / 2,
      startDate: new Date(evts[0].fecha_hora),
      endDate: new Date(evts[evts.length - 1].fecha_hora),
    })

    x = xEnd

    if (i < numGaps) {
      gaps.push({
        clusterIndex: i,
        xStart: x,
        xEnd: x + gapWidthPx,
        fromDate: rawGaps[i].fromDate,
        toDate: rawGaps[i].toDate,
        durationMs: rawGaps[i].durationMs,
      })
      x += gapWidthPx
    }
  })

  // 5. Función de consulta: evento -> { x, clusterIndex }
  const positionOf = (eventId: number): { x: number; clusterIndex: number } | null => {
    for (let ci = 0; ci < clusters.length; ci++) {
      const cluster = clusters[ci]
      const idx = cluster.events.findIndex((e) => e.id === eventId)
      if (idx === -1) continue

      const n = cluster.events.length
      const slotWidth = (cluster.xEnd - cluster.xStart) / n
      const eventX = cluster.xStart + slotWidth * (idx + 0.5)
      return { x: eventX, clusterIndex: ci }
    }
    return null
  }

  return {
    clusters,
    gaps,
    positionOf,
    totalWidth,
    minDate: new Date(sorted[0].fecha_hora),
    maxDate: new Date(sorted[sorted.length - 1].fecha_hora),
  }
}

/** Formatea una duración en ms como texto legible: "3 días", "18 h", "45 min". */
export function formatGapDuration(ms: number): string {
  const seconds = Math.floor(ms / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)

  if (days >= 1) return `${days} día${days === 1 ? '' : 's'}`
  if (hours >= 1) return `${hours} h`
  if (minutes >= 1) return `${minutes} min`
  return `${seconds} s`
}
