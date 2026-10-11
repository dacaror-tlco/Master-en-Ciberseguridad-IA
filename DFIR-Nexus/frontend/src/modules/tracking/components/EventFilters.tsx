import { Input } from "@/shared/ui";
import { SeverityBadge } from "./SeverityBadge";
import type { Severidad } from "../types";

const SEVERIDADES: Severidad[] = ["critica", "alta", "media", "baja"];

export interface EventFiltersProps {
  severidades: Severidad[];
  onSeveridades: (severidades: Severidad[]) => void;
  busqueda: string;
  onBusqueda: (texto: string) => void;
  visibles: number;
  total: number;
}

/**
 * Filtros de la tabla: por severidad (varias a la vez; ninguna marcada =
 * todas) y por texto libre sobre comando, usuario, regla e indicadores.
 * En un log de miles de líneas, "enséñame solo las críticas que tocan esta
 * IP" es la pregunta habitual.
 */
export function EventFilters({ severidades, onSeveridades, busqueda, onBusqueda, visibles, total }: EventFiltersProps) {
  function alternar(s: Severidad) {
    onSeveridades(severidades.includes(s) ? severidades.filter((x) => x !== s) : [...severidades, s]);
  }

  return (
    <div className="flex flex-wrap items-end gap-3">
      <div className="w-full sm:w-72">
        <Input
          icon="search"
          placeholder="Buscar comando, usuario, regla, IP..."
          value={busqueda}
          onChange={(e) => onBusqueda(e.target.value)}
          aria-label="Buscar en los eventos"
        />
      </div>
      <div className="flex items-center gap-2" role="group" aria-label="Filtrar por severidad">
        {SEVERIDADES.map((s) => {
          const activa = severidades.includes(s);
          return (
            <button
              key={s}
              type="button"
              aria-pressed={activa}
              onClick={() => alternar(s)}
              className={`rounded transition-opacity ${activa || severidades.length === 0 ? "opacity-100" : "opacity-40"} ${activa ? "ring-1 ring-primary" : ""}`}
            >
              <SeverityBadge severidad={s} />
            </button>
          );
        })}
      </div>
      <span className="font-body text-mono-data text-on-surface-variant">
        {visibles === total ? `${total} eventos` : `${visibles} de ${total} eventos`}
      </span>
    </div>
  );
}
