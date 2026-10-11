import { useId, useState } from 'react'
import type { FormEvent } from 'react'
import { Button, Input, Select } from '@/shared/ui'
import { ESTADOS_CASO, TRANSICIONES_VALIDAS } from '../types'
import type { Case, CaseCreateInput, CaseUpdateInput } from '../types'
import { CASE_STATUS_MAP } from './CaseStatusMap'

type CaseFormProps = {
  initialValue?: Case
  submitting?: boolean
  onSubmit: (data: CaseCreateInput | CaseUpdateInput) => void
  onCancel: () => void
}

/**
 * En creación se ofrecen los 4 estados (no hay "estado anterior" del que
 * partir). En edición, solo el estado actual y sus transiciones válidas
 * (ver TRANSICIONES_VALIDAS, espejo de state_machine.py) — evita que el
 * perito elija en el desplegable algo que el backend va a rechazar con 409.
 */
function opcionesDeEstado(actual?: Case['estado']) {
  const estados = actual ? [actual, ...TRANSICIONES_VALIDAS[actual]] : ESTADOS_CASO
  return estados.map((estado) => ({ value: estado, label: CASE_STATUS_MAP[estado].label }))
}

/**
 * Formulario de creación/edición de casos. Campos idénticos a
 * CaseCreate/CaseUpdate (app/modules/cases/schemas.py): nombre, responsable,
 * descripcion, estado. No añade ningún campo que no exista en el backend.
 */
export function CaseForm({ initialValue, submitting, onSubmit, onCancel }: CaseFormProps) {
  const descripcionId = useId()
  const [nombre, setNombre] = useState(initialValue?.nombre ?? '')
  const [responsable, setResponsable] = useState(initialValue?.responsable ?? '')
  const [descripcion, setDescripcion] = useState(initialValue?.descripcion ?? '')
  const [estado, setEstado] = useState(initialValue?.estado ?? 'abierto')
  const estadoOptions = opcionesDeEstado(initialValue?.estado)

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault()
    onSubmit({
      nombre,
      responsable,
      descripcion: descripcion || null,
      estado,
    })
  }

  return (
    <form id="case-form" onSubmit={handleSubmit} className="flex flex-col gap-4">
      <Input label="Nombre" value={nombre} onChange={(e) => setNombre(e.target.value)} required />
      <Input
        label="Responsable"
        value={responsable}
        onChange={(e) => setResponsable(e.target.value)}
        required
      />
      <div className="flex flex-col gap-1 w-full">
        <label htmlFor={descripcionId} className="font-label-caps text-label-caps text-on-surface-variant">
          Descripción
        </label>
        <textarea
          id={descripcionId}
          value={descripcion ?? ''}
          onChange={(e) => setDescripcion(e.target.value)}
          rows={4}
          className="w-full bg-canvas border border-hairline rounded font-mono-data text-mono-data
            text-on-surface placeholder-on-surface-variant focus:outline-none focus:border-primary
            focus:ring-1 focus:ring-primary/50 transition-all p-3 resize-none"
        />
      </div>
      <Select
        label="Estado"
        options={estadoOptions}
        value={estado}
        onChange={(e) => setEstado(e.target.value as typeof estado)}
        disabled={initialValue?.estado === 'archivado'}
      />
      <div className="flex justify-end gap-2 pt-2">
        <Button type="button" variant="ghost" onClick={onCancel}>
          Cancelar
        </Button>
        <Button type="submit" variant="primary" loading={submitting}>
          Guardar
        </Button>
      </div>
    </form>
  )
}
