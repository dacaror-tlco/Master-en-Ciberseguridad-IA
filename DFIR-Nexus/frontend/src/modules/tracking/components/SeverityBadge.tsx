import type { Severidad } from "../types";

/**
 * DECISIÓN DE DISEÑO: este componente vive en modules/tracking/ (no en
 * shared/ui) porque StatusBadge solo expone 4 tonos (primary/tertiary/
 * neutral/muted) y ninguno transmite "alarma" — necesario para una
 * escala de severidad de 4 niveles donde el nivel más alto debe
 * distinguirse claramente. No se modifica StatusBadge (eso afectaría a
 * todos los módulos); en su lugar, se compone un badge equivalente
 * usando ÚNICAMENTE tokens ya existentes en tokens.css (primary,
 * tertiary, hairline, error) — ningún hex nuevo. Esto sigue el mismo
 * patrón que "cuándo crear un componente propio" de DESIGN_SYSTEM.md §10:
 * lógica/necesidad específica del dominio, generic shape ya existente.
 *
 * Escala: baja (neutral) < media (tertiary/informativo) <
 * alta (error, solo borde) < critica (error, relleno).
 */
const SEVERITY_CONFIG: Record<Severidad, { label: string; classes: string }> = {
  baja: { label: "BAJA", classes: "bg-hairline text-on-surface-variant border border-outline-variant" },
  media: { label: "MEDIA", classes: "bg-transparent border border-tertiary-container text-tertiary" },
  alta: { label: "ALTA", classes: "bg-transparent border border-error text-error" },
  critica: { label: "CRÍTICA", classes: "bg-error-container text-on-error-container border border-error" },
};

export function SeverityBadge({ severidad }: { severidad: Severidad }) {
  const config = SEVERITY_CONFIG[severidad];
  return (
    <span className={`inline-flex items-center rounded px-2 py-0.5 font-label text-label-caps uppercase ${config.classes}`}>
      {config.label}
    </span>
  );
}
