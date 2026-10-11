import { Button, DataTable, type DataTableColumn } from "@/shared/ui";
import { SeverityBadge } from "./SeverityBadge";
import { TIPO_INDICADOR_LABEL } from "./indicatorLabels";
import type { IndicadorAgregado } from "../types";

/**
 * Indicadores de todo el log, agrupados por valor: la vista para seguir al
 * atacante. El orden lo decide el backend (severidad maxima y numero de
 * apariciones), que es lo que el perito querria mirar primero.
 *
 * Cada numero de linea es un boton que abre ese evento en el panel de
 * detalle: de "esta IP aparece en la 8 y en la 17" a ver la linea 8 entera
 * en un clic, sin tener que buscarla en la tabla.
 */
export interface IndicatorsSummaryProps {
  indicadores: IndicadorAgregado[];
  onSelectLinea: (linea: number) => void;
  /** Si se pasa, aparece un botón para exportar los indicadores a CSV. */
  onExportar?: () => void;
}

export function IndicatorsSummary({ indicadores, onSelectLinea, onExportar }: IndicatorsSummaryProps) {
  // Sin indicadores no se pinta nada: una seccion vacia solo ocuparia sitio.
  if (indicadores.length === 0) return null;

  const columns: DataTableColumn<IndicadorAgregado>[] = [
    {
      key: "tipo",
      header: "Tipo",
      className: "w-28 whitespace-nowrap truncate",
      render: (i) => TIPO_INDICADOR_LABEL[i.tipo] ?? i.tipo,
    },
    {
      key: "valor",
      header: "Indicador",
      className: "truncate",
      render: (i) => <span title={i.valor}>{i.valor}</span>,
    },
    {
      key: "severidad",
      header: "Sev. máx.",
      className: "w-28 whitespace-nowrap",
      render: (i) => <SeverityBadge severidad={i.severidad_maxima} />,
    },
    {
      key: "veces",
      header: "Veces",
      align: "right",
      className: "w-16",
      render: (i) => i.veces,
    },
    {
      key: "lineas",
      header: "Líneas",
      className: "w-40",
      render: (i) => (
        <div className="flex flex-wrap gap-1">
          {i.lineas.map((n) => (
            <button
              key={n}
              type="button"
              onClick={() => onSelectLinea(n)}
              title={`Ver el evento de la línea ${n}`}
              className="px-1.5 py-0.5 rounded border border-hairline text-on-surface-variant hover:text-on-surface hover:border-primary focus-visible:outline focus-visible:outline-1 focus-visible:outline-primary"
            >
              {n}
            </button>
          ))}
        </div>
      ),
    },
  ];

  return (
    <section className="flex flex-col gap-2">
      <div className="flex items-center justify-between">
        <h3 className="font-label text-label-caps uppercase text-on-surface-variant">
          Indicadores del log ({indicadores.length})
        </h3>
        {onExportar && (
          <Button size="sm" variant="ghost" icon="download" onClick={onExportar}>
            Exportar CSV
          </Button>
        )}
      </div>
      <DataTable
        layout="fixed"
        columns={columns}
        rows={indicadores}
        getRowId={(i) => `${i.tipo}:${i.valor}`}
      />
    </section>
  );
}
