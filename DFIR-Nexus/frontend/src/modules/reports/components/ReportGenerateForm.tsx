import { useId, useState } from 'react'
import type { FormEvent } from 'react'
import { Alert, Button, Input, Select } from '@/shared/ui'
import type { CaseOption, ReportGenerateInput } from '../types'
import { ReportScopeFields } from './ReportScopeFields'
import { ALCANCE_COMPLETO, aScopeInput, type ScopeState } from './reportScope'

type ReportGenerateFormProps = {
  /** Casos disponibles. Vacío si el backend del Módulo 1 no está accesible. */
  cases: CaseOption[]
  /** Caso preseleccionado (el que se está consultando en la página). */
  initialCaseId: number | null
  submitting?: boolean
  onSubmit: (data: ReportGenerateInput) => void
  onCancel: () => void
}

/**
 * Formulario de POST /reports/generate. Campos idénticos a
 * `ReportGenerateRequest` (schemas.py): `case_id`, `generado_por`, `notas` y
 * `opciones`. No añade ninguno más.
 *
 * El bloque de alcance arranca en «caso completo» y solo se envía si el perito
 * toca algo (ver `aScopeInput`): así una emisión normal viaja exactamente como
 * antes y queda registrada como el informe de siempre.
 *
 * Si no hay lista de casos (Módulo 1 no levantado), el caso se introduce por
 * `case_id` a mano: el módulo sigue siendo utilizable de forma autónoma, que
 * es como se ha desarrollado y probado hasta ahora.
 */
export function ReportGenerateForm({
  cases,
  initialCaseId,
  submitting,
  onSubmit,
  onCancel,
}: ReportGenerateFormProps) {
  const notasId = useId()
  const [caseId, setCaseId] = useState(initialCaseId ? String(initialCaseId) : '')
  const [generadoPor, setGeneradoPor] = useState('')
  const [notas, setNotas] = useState('')
  const [alcance, setAlcance] = useState<ScopeState>(ALCANCE_COMPLETO)

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault()
    const parsedCaseId = Number(caseId)
    if (!Number.isInteger(parsedCaseId) || parsedCaseId <= 0) return
    onSubmit({
      case_id: parsedCaseId,
      generado_por: generadoPor,
      notas: notas.trim() ? notas : null,
      opciones: aScopeInput(alcance),
    })
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      {cases.length > 0 ? (
        <Select
          label="Caso"
          /*
           * La opción vacía inicial existe para que un `case_id` sin elegir no
           * pueda enviarse por error: con `required`, el propio navegador
           * bloquea el envío en vez de fallar en silencio.
           */
          options={[
            { value: '', label: 'Selecciona un caso' },
            ...cases.map((item) => ({ value: String(item.id), label: `#${item.id} — ${item.nombre}` })),
          ]}
          value={caseId}
          onChange={(event) => setCaseId(event.target.value)}
          required
        />
      ) : (
        <Input
          label="ID del caso"
          type="number"
          min={1}
          value={caseId}
          onChange={(event) => setCaseId(event.target.value)}
          required
        />
      )}

      <Input
        label="Emitido por"
        value={generadoPor}
        onChange={(event) => setGeneradoPor(event.target.value)}
        maxLength={100}
        placeholder="Nombre del perito que firma"
        required
      />

      <div className="flex flex-col gap-1 w-full">
        <label htmlFor={notasId} className="font-label-caps text-label-caps text-on-surface-variant">
          Notas del perito (opcional)
        </label>
        <textarea
          id={notasId}
          value={notas}
          onChange={(event) => setNotas(event.target.value)}
          rows={4}
          placeholder="Contexto o indicaciones a tener en cuenta al redactar las conclusiones."
          className="w-full bg-canvas border border-hairline rounded font-mono-data text-mono-data
            text-on-surface placeholder-on-surface-variant focus:outline-none focus:border-primary
            focus:ring-1 focus:ring-primary/50 transition-all p-3 resize-none"
        />
      </div>

      <ReportScopeFields value={alcance} onChange={setAlcance} />

      <Alert variant="info">
        Las notas quedan registradas junto al informe porque condicionan las conclusiones. La redacción la
        hace un modelo de IA sobre la cronología ya correlacionada: no determina hechos ni fechas, y el
        informe se rechaza si cita eventos que no existen.
      </Alert>

      <div className="flex justify-end gap-2 pt-2">
        <Button type="button" variant="ghost" onClick={onCancel}>
          Cancelar
        </Button>
        <Button type="submit" variant="primary" icon="auto_awesome" loading={submitting}>
          Generar informe
        </Button>
      </div>
    </form>
  )
}
