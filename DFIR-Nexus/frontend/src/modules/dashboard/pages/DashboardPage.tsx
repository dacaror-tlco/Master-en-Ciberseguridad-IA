import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Alert, Card, Icon, StatusBadge, type StatusTone } from '@/shared/ui'
import {
  dashboardApi,
  TOPE_CASOS,
  type CaseResumen,
  type EstadoCaso,
  type Fuente,
  type OsintFinding,
} from '../api/dashboardApi'

/**
 * Panel de inicio.
 *
 * Existía como entrada muerta del menú desde el diseño original: se veía, no
 * llevaba a ninguna parte, y convivía con otra entrada («Evidencias») que
 * llevaba exactamente al mismo sitio que «Casos». Esta página la sustituye por
 * algo que sí responde a la pregunta con la que uno abre una herramienta
 * pericial: qué hay abierto y qué ha aparecido últimamente.
 *
 * Regla que sigue el panel: **no inventa cifras**. Solo cuenta lo que puede
 * leer de una vez —casos y análisis OSINT— y dice de dónde sale cada número y
 * qué se está dejando fuera. Un panel de control que redondea o estima es peor
 * que no tenerlo, porque se toman decisiones mirándolo.
 */

const ETIQUETA_ESTADO: Record<EstadoCaso, string> = {
  abierto: 'Abierto',
  en_progreso: 'En progreso',
  cerrado: 'Cerrado',
  archivado: 'Archivado',
}

const TONO_ESTADO: Record<EstadoCaso, StatusTone> = {
  abierto: 'primary',
  en_progreso: 'tertiary',
  cerrado: 'neutral',
  archivado: 'muted',
}

const ORDEN_ESTADOS: EstadoCaso[] = ['abierto', 'en_progreso', 'cerrado', 'archivado']

/** Riesgo alto: el Módulo 2 lo etiqueta en inglés o en español según el análisis. */
const RIESGO_ALTO = new Set(['alto', 'high', 'critical', 'critico'])

function Cifra({
  valor,
  etiqueta,
  destino,
  icono,
  acento = false,
}: {
  valor: number | string
  etiqueta: string
  destino: string
  icono: string
  acento?: boolean
}) {
  return (
    <Link
      to={destino}
      className="flex-1 min-w-[180px] border border-hairline rounded p-gutter hover:border-primary transition-colors"
    >
      <div className="flex items-center gap-2 mb-2 text-on-surface-variant">
        <Icon name={icono} className="text-[18px]" />
        <span className="font-label-caps text-label-caps">{etiqueta}</span>
      </div>
      <p
        className={`font-headline text-headline-md ${acento ? 'text-error' : 'text-on-surface'}`}
      >
        {valor}
      </p>
    </Link>
  )
}

export function DashboardPage() {
  const [casos, setCasos] = useState<Fuente<CaseResumen> | null>(null)
  const [osint, setOsint] = useState<Fuente<OsintFinding> | null>(null)

  useEffect(() => {
    dashboardApi.casos().then(setCasos)
    dashboardApi.osint().then(setOsint)
  }, [])

  const cargando = casos === null || osint === null
  const listaCasos = casos?.datos ?? []
  const listaOsint = osint?.datos ?? []

  const porEstado = ORDEN_ESTADOS.map((estado) => ({
    estado,
    total: listaCasos.filter((c) => c.estado === estado).length,
  }))
  const activos = listaCasos.filter(
    (c) => c.estado === 'abierto' || c.estado === 'en_progreso',
  ).length
  const riesgoAlto = listaOsint.filter((f) => RIESGO_ALTO.has(f.risk_level.toLowerCase())).length

  const recientes = [...listaCasos]
    .sort((a, b) => b.fecha_creacion.localeCompare(a.fecha_creacion))
    .slice(0, 5)
  const ultimosAnalisis = [...listaOsint]
    .sort((a, b) => b.analyzed_at.localeCompare(a.analyzed_at))
    .slice(0, 5)

  return (
    <div className="h-full overflow-y-auto p-gutter flex flex-col gap-panel-gap [&>*]:shrink-0">
      <div>
        <h1 className="font-headline text-headline-md text-on-surface">Dashboard</h1>
        <p className="text-on-surface-variant text-sm mt-1">
          Estado de las investigaciones abiertas y de los últimos análisis registrados.
        </p>
      </div>

      {casos?.error && <Alert variant="error">{casos.error}</Alert>}
      {osint?.error && <Alert variant="error">{osint.error}</Alert>}

      {cargando ? (
        <Card>
          <p className="p-gutter text-on-surface-variant animate-pulse">Cargando…</p>
        </Card>
      ) : (
        <>
          <Card title="Resumen">
            <div className="p-gutter flex flex-wrap gap-4">
              <Cifra
                valor={listaCasos.length}
                etiqueta="Casos registrados"
                destino="/cases"
                icono="folder_shared"
              />
              <Cifra
                valor={activos}
                etiqueta="Investigaciones activas"
                destino="/cases"
                icono="pending_actions"
              />
              <Cifra
                valor={listaOsint.length}
                etiqueta="Análisis OSINT"
                destino="/osint/cases"
                icono="public"
              />
              <Cifra
                valor={riesgoAlto}
                etiqueta="Indicadores de riesgo alto"
                destino="/osint/cases"
                icono="gpp_maybe"
                acento={riesgoAlto > 0}
              />
            </div>
            {listaCasos.length >= TOPE_CASOS && (
              <div className="px-gutter pb-gutter">
                <Alert variant="info">
                  Se han leído los primeros {TOPE_CASOS} casos: los recuentos de arriba no
                  incluyen los que haya por encima de ese número.
                </Alert>
              </div>
            )}
          </Card>

          <Card title="Casos por estado">
            <div className="p-gutter flex flex-wrap gap-6">
              {porEstado.map(({ estado, total }) => (
                <div key={estado} className="flex items-center gap-3">
                  <StatusBadge label={ETIQUETA_ESTADO[estado]} tone={TONO_ESTADO[estado]} />
                  <span className="font-mono-data text-mono-data text-on-surface">{total}</span>
                </div>
              ))}
            </div>
          </Card>

          <div className="flex flex-wrap gap-panel-gap [&>*]:flex-1 [&>*]:min-w-[320px]">
            <Card title="Últimos casos">
              {recientes.length === 0 ? (
                <p className="p-gutter text-on-surface-variant">
                  No hay casos registrados todavía.
                </p>
              ) : (
                <ul className="p-gutter space-y-3">
                  {recientes.map((caso) => (
                    <li key={caso.id}>
                      <Link
                        to="/cases"
                        className="flex items-start gap-3 hover:text-primary transition-colors"
                      >
                        <span className="font-mono-data text-mono-data text-primary shrink-0">
                          #{caso.id}
                        </span>
                        <span className="min-w-0">
                          <span className="block text-on-surface break-words">{caso.nombre}</span>
                          <span className="block text-on-surface-variant opacity-60 text-xs font-mono-data">
                            {ETIQUETA_ESTADO[caso.estado]} ·{' '}
                            {new Date(caso.fecha_creacion).toLocaleDateString()} ·{' '}
                            {caso.responsable || 'sin responsable'}
                          </span>
                        </span>
                      </Link>
                    </li>
                  ))}
                </ul>
              )}
            </Card>

            <Card title="Últimos análisis OSINT">
              {ultimosAnalisis.length === 0 ? (
                <p className="p-gutter text-on-surface-variant">
                  No consta ningún análisis OSINT registrado.
                </p>
              ) : (
                <ul className="p-gutter space-y-3">
                  {ultimosAnalisis.map((f) => (
                    <li key={f.id} className="flex items-start gap-3">
                      <span className="shrink-0">
                        <StatusBadge
                          label={f.risk_level}
                          tone={RIESGO_ALTO.has(f.risk_level.toLowerCase()) ? 'error' : 'neutral'}
                        />
                      </span>
                      <span className="min-w-0">
                        <span className="block text-on-surface font-mono-data text-mono-data break-all">
                          {f.subject_value}
                        </span>
                        <span className="block text-on-surface-variant opacity-60 text-xs">
                          {f.headline}
                        </span>
                        <span className="block text-on-surface-variant opacity-50 text-xs font-mono-data">
                          {/* Un hallazgo sin case_id no está vinculado a ningún expediente, y
                              eso hay que decirlo: es justo lo que impide que salga en el
                              Anexo B del informe de ese caso. */}
                          {f.case_id === null
                            ? 'sin caso asociado'
                            : `caso #${f.case_id}`}{' '}
                          · {new Date(f.analyzed_at).toLocaleDateString()}
                        </span>
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </Card>
          </div>

          <Card title="Qué no cuenta este panel">
            <p className="p-gutter text-on-surface-variant text-sm">
              Solo aparecen casos y análisis OSINT. Los eventos de tracking, la cronología y
              los informes emitidos no se totalizan aquí porque sus backends solo los exponen
              caso a caso: sumarlos exigiría una petición por caso, y esta pantalla dejaría de
              abrirse en cuanto el registro creciera. Cada uno de esos módulos tiene su propia
              pantalla en el menú.
            </p>
          </Card>
        </>
      )}
    </div>
  )
}

export default DashboardPage
