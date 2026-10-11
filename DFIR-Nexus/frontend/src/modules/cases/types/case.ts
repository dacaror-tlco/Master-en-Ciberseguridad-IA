/**
 * Tipos que reflejan exactamente app/modules/cases/schemas.py y
 * app/modules/cases/models.py del backend. No se inventa ningún campo.
 */
export const ESTADOS_CASO = ['abierto', 'en_progreso', 'cerrado', 'archivado'] as const

export type EstadoCaso = (typeof ESTADOS_CASO)[number]

/**
 * Transiciones válidas, mismo espejo que backend/app/modules/cases/state_machine.py.
 * Solo se usa para restringir las opciones que se ofrecen en el formulario:
 * la validación real (y la única que importa) sigue viviendo en el backend.
 */
export const TRANSICIONES_VALIDAS: Record<EstadoCaso, readonly EstadoCaso[]> = {
  abierto: ['en_progreso', 'cerrado', 'archivado'],
  en_progreso: ['abierto', 'cerrado'],
  cerrado: ['en_progreso', 'archivado'],
  archivado: [],
}

export type Case = {
  id: number
  nombre: string
  estado: EstadoCaso
  fecha_creacion: string
  fecha_actualizacion: string
  descripcion: string | null
  responsable: string
  eliminado: boolean
  fecha_eliminacion: string | null
}

export type CaseCreateInput = {
  nombre: string
  responsable: string
  descripcion?: string | null
  estado?: EstadoCaso
}

export type CaseUpdateInput = Partial<CaseCreateInput>

export type AccionAuditoria =
  | 'case_creado'
  | 'case_actualizado'
  | 'case_estado_cambiado'
  | 'case_eliminado'
  | 'evidence_creada'
  | 'evidence_actualizada'
  | 'evidence_eliminada'
  | 'osint_vinculacion_cambiada'

export type AuditLogEntry = {
  id: number
  case_id: number
  evidence_id: number | null
  accion: AccionAuditoria
  actor: string
  detalle: Record<string, unknown> | null
  creado_en: string
}
