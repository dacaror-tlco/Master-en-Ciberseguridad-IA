/**
 * Tipos que reflejan exactamente EvidenceBase/EvidenceCreate/EvidenceUpdate/
 * EvidenceRead de app/modules/cases/schemas.py. No se inventa ningún campo.
 */
export type Evidence = {
  id: number
  case_id: number
  tipo: string
  valor: string
  observaciones: string | null
  fecha_subida: string
  fecha_actualizacion: string
  fecha_adquisicion: string | null
  hash_valor: string
  eliminado: boolean
  fecha_eliminacion: string | null
}

export type EvidenceCreateInput = {
  tipo: string
  valor: string
  observaciones?: string | null
  fecha_adquisicion?: string | null
}

/**
 * Sin `tipo` ni `valor`: son el contenido probatorio y son inmutables tras
 * crear la evidencia (ver hash_valor). El backend los ignora si se envían
 * igualmente; aquí ni se ofrecen, para no sugerir en la UI algo que el
 * backend no permite.
 */
export type EvidenceUpdateInput = {
  observaciones?: string | null
  fecha_adquisicion?: string | null
}

export type EvidenceIntegrityCheck = {
  evidence_id: number
  algoritmo: string
  hash_registrado: string
  hash_actual: string
  integro: boolean
}
