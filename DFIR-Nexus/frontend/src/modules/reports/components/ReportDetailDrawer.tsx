import { useState } from 'react'
import type { ReactNode } from 'react'
import { Alert, Button, Icon, IconButton, StatusBadge, useCerrarConEscape } from '@/shared/ui'
import { ApiError, reportsApi } from '../api'
import type { Report, ReportFormat } from '../types'
import {
  describirAlcance,
  formatUtc,
  formatosEmitidos,
  reportCode,
  versionStatus,
} from './reportFormat'

type ReportDetailDrawerProps = {
  report: Report
  isLatest: boolean
  caseName?: string
  /** Cierra el panel. Sin esto no había forma de quitarlo de en medio. */
  onClose?: () => void
}

const OTROS_FORMATOS: { formato: ReportFormat; etiqueta: string; icono: string }[] = [
  { formato: 'docx', etiqueta: 'DOCX', icono: 'description' },
  { formato: 'html', etiqueta: 'HTML', icono: 'language' },
  { formato: 'json', etiqueta: 'JSON', icono: 'data_object' },
]

/**
 * Separa el texto guardado en `reports.resumen_ia`, que el backend almacena
 * como `HALLAZGOS\n\n...\n\nCONCLUSIONES\n\n...` (`ai_narrative.texto_plano`).
 * Si algún informe antiguo no siguiera ese formato, se muestra tal cual en vez
 * de perder contenido.
 */
function splitNarrative(resumen: string): { hallazgos: string; conclusiones: string } | null {
  const match = resumen.match(/^HALLAZGOS\s+([\s\S]*?)\s+CONCLUSIONES\s+([\s\S]*)$/)
  if (!match) return null
  return { hallazgos: match[1].trim(), conclusiones: match[2].trim() }
}

/**
 * Entrega un blob al usuario como fichero guardado.
 *
 * Las tres líneas del enlace sintético son la única forma de que la descarga
 * lleve nombre: `window.open` de una URL de blob abre el contenido en una
 * pestaña y lo llama como el identificador del blob, que es un UUID.
 */
function guardarComoFichero(blob: Blob, nombre: string) {
  const url = URL.createObjectURL(blob)
  const enlace = document.createElement('a')
  enlace.href = url
  enlace.download = nombre
  document.body.appendChild(enlace)
  enlace.click()
  enlace.remove()
  // Sin esto el blob se queda en memoria hasta que se recarga la página, y un
  // informe con anexos no es pequeño.
  URL.revokeObjectURL(url)
}

/**
 * Abre un blob en otra pestaña, para lo que existe para leerse y no para
 * guardarse (el HTML del informe y las instrucciones enviadas a la IA).
 *
 * La URL no se revoca de inmediato, al contrario que en `guardarComoFichero`:
 * la pestaña que se acaba de abrir todavía la está cargando y revocarla ahí la
 * dejaría en blanco.
 */
function abrirEnPestana(blob: Blob) {
  const url = URL.createObjectURL(blob)
  window.open(url, '_blank', 'noopener')
  setTimeout(() => URL.revokeObjectURL(url), 60_000)
}

/** El `detail` real del backend cuando lo hay; si no, un mensaje del sitio. */
function mensajeDeError(error: unknown, respaldo: string): string {
  if (error instanceof ApiError && typeof error.detail === 'string') return error.detail
  return respaldo
}

function Section({ icon, title, children }: { icon: string; title: string; children: ReactNode }) {
  return (
    <div>
      <div className="flex items-center gap-2 mb-3 border-b border-hairline pb-2">
        <Icon name={icon} className="text-tertiary text-sm" />
        <h4 className="font-label-caps text-label-caps text-tertiary">{title}</h4>
      </div>
      {children}
    </div>
  )
}

/**
 * Panel de detalle de un informe. Sigue el mismo patrón visual que
 * `CaseDetailDrawer` (cabecera con chip + badge, cuerpo, y pie de acciones
 * pegado abajo sobre un scroll único), compuesto solo con primitivas de
 * `shared/ui`.
 *
 * El documento que vale es el PDF firmado: esta pantalla es una vista previa
 * de lo que contiene, no un sustituto, y así se dice explícitamente al final.
 */
export function ReportDetailDrawer({
  report,
  isLatest,
  caseName,
  onClose,
}: ReportDetailDrawerProps) {
  useCerrarConEscape(onClose)
  const narrative = splitNarrative(report.resumen_ia)

  const alcance = describirAlcance(report)

  /*
   * Los soportes que se ofrecen son los que de verdad se emitieron. Un
   * informe sin huellas registradas es anterior a eso y solo tiene PDF, pero
   * ese caso ya lo cubría el mensaje del backend: se dejan los tres botones
   * para no cambiar lo que esa pantalla hacía con los informes antiguos.
   */
  const emitidos = formatosEmitidos(report)
  const otrosSoportes = emitidos
    ? OTROS_FORMATOS.filter(({ formato }) => emitidos.includes(formato))
    : OTROS_FORMATOS

  /*
   * La descarga se pide por `fetch` y se entrega desde un blob, no navegando a
   * la URL del backend.
   *
   * Navegar era lo que se hacía antes y dejó de valer al entrar la Fase 4:
   * Informes exige JWT y una navegación del navegador no manda la cabecera
   * `Authorization`, así que el endpoint contestaba 401 y el usuario se
   * quedaba mirando un error en vez de su informe. El token solo viaja si lo
   * pone el código, o sea por `fetch` (ver `reportsApi.descargar`).
   */
  const [descargando, setDescargando] = useState<ReportFormat | 'prompt' | null>(null)
  const [errorDescarga, setErrorDescarga] = useState<string | null>(null)

  const handleDownload = async (formato: ReportFormat = 'pdf') => {
    setDescargando(formato)
    setErrorDescarga(null)
    try {
      const { blob, nombre } = await reportsApi.descargar(report.id, formato)
      /*
       * El HTML el backend lo sirve `inline` porque existe para leerlo, no para
       * guardarlo, así que se abre en otra pestaña en vez de descargarse. Sigue
       * llevando su CSP `default-src 'none'` incrustada en el propio documento
       * —la cabecera del backend no viaja en una URL de blob—, que es para lo
       * que el Módulo 5 la puso también dentro del HTML.
       */
      if (formato === 'html') {
        abrirEnPestana(blob)
      } else {
        guardarComoFichero(blob, nombre)
      }
    } catch (err) {
      setErrorDescarga(mensajeDeError(err, `No se ha podido descargar el ${formato.toUpperCase()}.`))
    } finally {
      setDescargando(null)
    }
  }

  const handleVerInstrucciones = async () => {
    setDescargando('prompt')
    setErrorDescarga(null)
    try {
      abrirEnPestana(await reportsApi.descargarPrompt(report.id))
    } catch (err) {
      setErrorDescarga(
        mensajeDeError(err, 'No se han podido recuperar las instrucciones enviadas a la IA.'),
      )
    } finally {
      setDescargando(null)
    }
  }

  return (
    /*
     * Una sola zona de scroll para todo el panel, con el pie de soportes
     * `sticky`. Mismo criterio que el panel de Casos y que la barra lateral: un
     * scroll encajonado entre cabecera y pie, en una columna de 384 px, es una
     * ventanita que no se ve. Ver `CaseDetailDrawer` para el razonamiento
     * completo.
     */
    <div className="nexus-glass-panel rounded-lg flex flex-col overflow-y-auto h-full">
      <div className="px-6 py-5 border-b border-hairline bg-surface-container-lowest">
        <div className="flex justify-between items-start mb-2">
          <span className="text-primary font-mono-data text-xs px-2 py-1 bg-primary/10 rounded border border-primary/20">
            #{report.id}
          </span>
          <div className="flex items-center gap-1">
            <StatusBadge {...versionStatus(isLatest)} />
            {onClose && (
              <IconButton icon="close" label="Cerrar el panel" size="sm" onClick={onClose} />
            )}
          </div>
        </div>
        <h3 className="font-headline-md text-headline-md text-on-surface leading-tight mb-2">
          {reportCode(report)}
        </h3>
        <p className="font-body-md text-body-md text-on-surface-variant text-sm">
          {caseName ? `${caseName} · ` : ''}Caso #{report.case_id}
        </p>
      </div>

      <div className="p-6 space-y-6">
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1">
            <span className="font-label-caps text-label-caps text-on-surface-variant text-[10px]">
              EMITIDO POR
            </span>
            <p className="font-mono-data text-sm text-on-surface">{report.generado_por}</p>
          </div>
          <div className="space-y-1">
            <span className="font-label-caps text-label-caps text-on-surface-variant text-[10px]">
              FECHA DE EMISIÓN
            </span>
            <p className="font-mono-data text-sm text-on-surface">{formatUtc(report.fecha_generacion)}</p>
          </div>
        </div>

        {report.notas && (
          <Section icon="edit_note" title="NOTAS DEL PERITO">
            <p className="font-body-md text-body-md text-on-surface-variant whitespace-pre-wrap">
              {report.notas}
            </p>
          </Section>
        )}

        {narrative ? (
          <>
            <Section icon="search_insights" title="HALLAZGOS">
              <p className="font-body-md text-body-md text-on-surface whitespace-pre-wrap">
                {narrative.hallazgos}
              </p>
            </Section>
            <Section icon="gavel" title="CONCLUSIONES">
              <p className="font-body-md text-body-md text-on-surface whitespace-pre-wrap">
                {narrative.conclusiones}
              </p>
            </Section>
          </>
        ) : (
          <Section icon="description" title="RESUMEN">
            <p className="font-body-md text-body-md text-on-surface whitespace-pre-wrap">
              {report.resumen_ia}
            </p>
          </Section>
        )}

        {/*
          Se muestra la del PDF porque es el documento que se firma. Sirve para
          contrastar un fichero que ya se descargó —o que llega de otra
          persona— sin depender de que la API haga la comprobación: el backend
          la publica también en la cabecera `X-Informe-SHA256`.
        */}
        {/*
          Solo aparece si el informe no cubrió el caso entero. Es una ayuda de
          pantalla: la declaración que vale es la que lleva el propio documento
          en su apartado 1, porque el informe tiene que defenderse solo, impreso
          y fuera de esta aplicación.
        */}
        {alcance && (
          <Section icon="tune" title="ALCANCE DE ESTA EMISIÓN">
            <ul className="font-mono-data text-mono-data text-on-surface space-y-1">
              {alcance.map((linea) => (
                <li key={linea}>· {linea}</li>
              ))}
            </ul>
            <p className="font-mono-data text-mono-data text-on-surface-variant opacity-70 mt-2">
              Este informe no documenta el caso completo. El documento lo declara en su apartado
              «Objeto y alcance».
            </p>
          </Section>
        )}

        {report.huellas?.pdf && (
          <Section icon="fingerprint" title="HUELLA DEL PDF (SHA-256)">
            <p className="font-mono-data text-xs text-on-surface break-all select-all">
              {report.huellas.pdf}
            </p>
            <p className="font-mono-data text-mono-data text-on-surface-variant opacity-70 mt-2">
              Comprueba el fichero descargado con <code>sha256sum</code> (o{' '}
              <code>Get-FileHash</code> en Windows): si no coincide, no es este informe.
            </p>

            {/*
              Las instrucciones enviadas a la IA viven aquí y no en el pie de
              acciones, donde eran un quinto botón al lado de los cuatro
              soportes. No son un soporte del informe: son el registro de cómo se
              redactó, y su sitio es junto a la huella, que es la otra cosa de
              esta pantalla que existe para comprobar el documento en vez de
              creérselo. Es lo que hace verificable el apartado 8.
            */}
            {report.huellas.prompt && (
              <button
                type="button"
                onClick={handleVerInstrucciones}
                disabled={descargando !== null}
                className="mt-3 inline-flex items-center gap-1.5 text-primary font-mono-data text-mono-data hover:underline disabled:opacity-50 disabled:cursor-not-allowed"
                title={`Instrucciones enviadas a la IA para ${reportCode(report)}`}
              >
                <Icon name="terminal" className="text-[14px]" />
                {descargando === 'prompt'
                  ? 'Abriendo…'
                  : 'Ver las instrucciones que se enviaron a la IA'}
              </button>
            )}
          </Section>
        )}

        <p className="font-mono-data text-mono-data text-on-surface-variant opacity-70">
          Vista previa del contenido redactado. El documento pericial completo —con cronología,
          metodología, anexos y declaración sobre el uso de IA— es el PDF.
        </p>
      </div>

      <div className="sticky bottom-0 mt-auto p-4 bg-surface-container-highest border-t border-hairline space-y-3">
        {/*
          El error se enseña aquí, junto al botón que lo provocó. Antes la
          descarga era una navegación y un fallo se veía como una página de
          error del navegador, fuera de la aplicación.
        */}
        {errorDescarga && <Alert variant="error">{errorDescarga}</Alert>}

        <Button
          variant="ghost"
          size="sm"
          icon="download"
          loading={descargando === 'pdf'}
          disabled={descargando !== null}
          onClick={() => handleDownload('pdf')}
          className="w-full"
        >
          Descargar PDF
        </Button>

        {/*
          El PDF es el documento firmado y por eso conserva el botón principal.
          Los otros tres soportes se emitieron en la misma generación y dicen lo
          mismo, así que se ofrecen como alternativa secundaria, no como
          opciones equivalentes.
        */}
        {/*
          Se oculta entero si esta emisión solo pidió el PDF: un botón que
          lleva a un 410 es peor que no ofrecerlo.
        */}
        {otrosSoportes.length > 0 && (
        <div>
          <span className="font-label-caps text-label-caps text-on-surface-variant text-[10px]">
            MISMO INFORME EN OTRO SOPORTE
          </span>
          {/*
            Una columna en móvil (<sm): a 320-390px, tres columnas dejaban
            cada botón en ~90px con su propio padding, demasiado justo para
            icono + "DOCX"/"HTML"/"JSON" con margen. De `sm` en adelante
            (tablet y el aside de escritorio) se mantiene la rejilla de 3.
          */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 mt-2">
            {otrosSoportes.map(({ formato, etiqueta, icono }) => (
              <Button
                key={formato}
                variant="ghost"
                size="sm"
                icon={icono}
                loading={descargando === formato}
                disabled={descargando !== null}
                onClick={() => handleDownload(formato)}
                title={`Descargar ${etiqueta} de ${reportCode(report)}`}
              >
                {etiqueta}
              </Button>
            ))}
          </div>
        </div>
        )}

        {/*
          El pie se queda solo con los soportes del informe: el PDF, que es el
          documento firmado, y los otros tres. Las instrucciones enviadas a la IA
          estaban aquí como un quinto botón y han subido al cuerpo, junto a la
          huella del PDF — ver esa sección para el motivo.
        */}
      </div>
    </div>
  )
}
