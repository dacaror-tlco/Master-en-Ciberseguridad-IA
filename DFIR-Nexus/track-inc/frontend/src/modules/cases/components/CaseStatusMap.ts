import type { StatusBadgeTone } from "@/shared/ui";
import type { EstadoCaso } from "../types";

interface StatusConfig {
  label: string;
  tone: StatusBadgeTone;
}

/**
 * abierto      -> ABIERTO      -> primary / verde
 * en_progreso  -> EN PROGRESO  -> tertiary
 * cerrado      -> CERRADO      -> neutro
 * archivado    -> ARCHIVADO    -> neutro atenuado
 * (sin ámbar — ver FRONTEND_MODULE_GUIDE.md §17)
 */
export const CASE_STATUS_MAP: Record<EstadoCaso, StatusConfig> = {
  abierto: { label: "ABIERTO", tone: "primary" },
  en_progreso: { label: "EN PROGRESO", tone: "tertiary" },
  cerrado: { label: "CERRADO", tone: "neutral" },
  archivado: { label: "ARCHIVADO", tone: "muted" },
};
