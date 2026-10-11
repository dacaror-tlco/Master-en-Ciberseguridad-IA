export type EstadoCaso = "abierto" | "en_progreso" | "cerrado" | "archivado";

export interface Case {
  id: number;
  nombre: string;
  estado: EstadoCaso;
  descripcion: string | null;
  responsable: string | null;
  fecha_creacion: string | null;
}

export interface CaseCreateInput {
  nombre: string;
  estado?: EstadoCaso;
  responsable?: string;
  descripcion?: string;
}
