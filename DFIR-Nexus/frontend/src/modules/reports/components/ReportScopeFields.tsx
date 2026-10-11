import { useId } from 'react'
import { Alert, Icon, Input, Select } from '@/shared/ui'
import type { ReportAnnex, ReportFormat } from '../types'
import { ANEXOS, FORMATOS, SEVERIDADES, hayRecorte, type ScopeState } from './reportScope'

type CasillaProps = {
  marcada: boolean
  onChange: (marcada: boolean) => void
  etiqueta: string
  ayuda?: string
  /** Marcada y no desmarcable. El PDF es el documento que se firma. */
  fija?: boolean
}

function Casilla({ marcada, onChange, etiqueta, ayuda, fija }: CasillaProps) {
  const id = useId()
  return (
    <label
      htmlFor={id}
      className={`flex items-start gap-2 rounded border px-3 py-2 transition-all
        ${marcada ? 'border-primary/60 bg-primary/5' : 'border-hairline bg-canvas'}
        ${fija ? 'opacity-70 cursor-default' : 'cursor-pointer hover:border-primary/40'}`}
    >
      <input
        id={id}
        type="checkbox"
        checked={marcada}
        disabled={fija}
        onChange={(event) => onChange(event.target.checked)}
        className="mt-0.5 accent-primary"
      />
      <span className="flex flex-col">
        <span className="font-mono-data text-mono-data text-on-surface">{etiqueta}</span>
        {ayuda && <span className="text-xs text-on-surface-variant">{ayuda}</span>}
      </span>
    </label>
  )
}

type ReportScopeFieldsProps = {
  value: ScopeState
  onChange: (estado: ScopeState) => void
}

/**
 * Bloque «Alcance del informe» del formulario de generación.
 *
 * Refleja `OpcionesInformeIn` (sharingan/app/modules/reports/schemas.py) y no
 * añade nada que el backend no acepte. Dos reglas se hacen cumplir ya aquí,
 * porque el backend las rechaza con 422 y no tiene sentido gastar una llamada
 * —ni una generación de IA— para descubrirlo:
 *
 * - El PDF no se puede desmarcar: es el documento que se firma.
 * - No se pueden quitar los tres anexos a la vez: sin ninguno no queda nada
 *   que respalde la cronología.
 *
 * Lo que **no** se valida aquí es que el alcance deje la cronología vacía: eso
 * depende de los datos del caso y solo se sabe al generar. El backend responde
 * 422 explicando qué aflojar.
 */
export function ReportScopeFields({ value, onChange }: ReportScopeFieldsProps) {
  const alternarAnexo = (anexo: ReportAnnex, marcada: boolean) => {
    const anexos = marcada
      ? [...value.anexos, anexo]
      : value.anexos.filter((a) => a !== anexo)
    if (anexos.length === 0) return // Ver docstring: el backend lo rechazaría.
    onChange({ ...value, anexos })
  }

  const alternarFormato = (formato: ReportFormat, marcada: boolean) => {
    if (formato === 'pdf') return
    onChange({
      ...value,
      formatos: marcada
        ? [...value.formatos, formato]
        : value.formatos.filter((f) => f !== formato),
    })
  }

  return (
    <div className="flex flex-col gap-4 border-t border-hairline pt-4">
      <div className="flex items-center gap-2">
        <Icon name="tune" className="text-[16px] text-on-surface-variant" />
        <span className="font-label-caps text-label-caps text-on-surface-variant">
          Alcance del informe
        </span>
      </div>

      <div className="flex flex-col gap-2">
        <span className="text-xs text-on-surface-variant">
          Anexos incluidos. Al excluir uno se excluyen también las entradas de la cronología que se
          apoyaban en él, para que toda referencia del informe siga resolviendo.
        </span>
        <div className="grid gap-2 md:grid-cols-3">
          {ANEXOS.map(({ valor, etiqueta, ayuda }) => (
            <Casilla
              key={valor}
              etiqueta={etiqueta}
              ayuda={ayuda}
              marcada={value.anexos.includes(valor)}
              onChange={(marcada) => alternarAnexo(valor, marcada)}
            />
          ))}
        </div>
      </div>

      <div className="grid gap-3 md:grid-cols-2">
        <Input
          label="Desde (UTC, opcional)"
          type="datetime-local"
          value={value.desde}
          onChange={(event) => onChange({ ...value, desde: event.target.value })}
        />
        <Input
          label="Hasta (UTC, opcional)"
          type="datetime-local"
          value={value.hasta}
          onChange={(event) => onChange({ ...value, hasta: event.target.value })}
        />
      </div>

      <Select
        label="Severidad mínima de los eventos de tracking"
        options={SEVERIDADES}
        value={value.severidadMinima}
        onChange={(event) => onChange({ ...value, severidadMinima: event.target.value })}
      />

      <Casilla
        etiqueta="Solo indicadores OSINT con detecciones"
        ayuda="Descarta los indicadores que ninguna fuente marcó"
        marcada={value.soloOsintConDetecciones}
        onChange={(marcada) => onChange({ ...value, soloOsintConDetecciones: marcada })}
      />

      <div className="flex flex-col gap-2">
        <span className="text-xs text-on-surface-variant">
          Formatos que se emiten. Se componen juntos y desde el mismo documento, para que las copias
          no puedan divergir; los no elegidos no se pueden pedir después.
        </span>
        <div className="grid gap-2 md:grid-cols-4">
          {FORMATOS.map(({ valor, etiqueta, fijo }) => (
            <Casilla
              key={valor}
              etiqueta={etiqueta}
              ayuda={fijo ? 'Documento firmado' : undefined}
              fija={fijo}
              marcada={value.formatos.includes(valor)}
              onChange={(marcada) => alternarFormato(valor, marcada)}
            />
          ))}
        </div>
      </div>

      {/*
        `info` y no `error`: recortar el alcance es una decisión legítima del
        perito, no un fallo. `Alert` solo define info/success/error, y añadir
        una variante tocaría un componente compartido por los cinco módulos,
        que no es de este.
      */}
      {hayRecorte(value) && (
        <Alert variant="info">
          Este informe no documentará el caso completo. El propio documento lo declarará en su
          apartado «Objeto y alcance», detallando qué se ha dejado fuera: un informe recortado en
          silencio engañaría sobre su propio alcance.
        </Alert>
      )}
    </div>
  )
}
