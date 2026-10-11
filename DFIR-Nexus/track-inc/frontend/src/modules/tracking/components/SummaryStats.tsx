import type { Severidad } from "../types";

/** De más a menos grave, y siempre las cuatro: antes salían en el orden en que
 *  aparecían en el log y las que no aparecían no se mostraban, así que un
 *  "0 críticas" no se distinguía de un dato que faltaba. */
const ORDEN: { clave: Severidad; etiqueta: string }[] = [
  { clave: "critica", etiqueta: "Crítica" },
  { clave: "alta", etiqueta: "Alta" },
  { clave: "media", etiqueta: "Media" },
  { clave: "baja", etiqueta: "Baja" },
];

export function SummaryStats({ porSeveridad, total }: { porSeveridad: Record<string, number>; total: number }) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
      <div className="nexus-glass-panel rounded-lg p-4">
        <div className="font-headline text-headline-md text-on-surface">{total}</div>
        <div className="font-label text-label-caps uppercase text-on-surface-variant mt-1">Total</div>
      </div>
      {ORDEN.map(({ clave, etiqueta }) => (
        <div key={clave} className="nexus-glass-panel rounded-lg p-4">
          <div className="font-headline text-headline-md text-on-surface">{porSeveridad[clave] ?? 0}</div>
          <div className="font-label text-label-caps uppercase text-on-surface-variant mt-1">{etiqueta}</div>
        </div>
      ))}
    </div>
  );
}
