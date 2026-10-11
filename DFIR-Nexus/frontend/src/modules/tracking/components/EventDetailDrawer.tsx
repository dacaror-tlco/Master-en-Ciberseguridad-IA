import { Card, Icon } from "@/shared/ui";
import { SeverityBadge } from "./SeverityBadge";
import { formatHora } from "./formatHora";
import { ORIGEN_INDICADOR_LABEL, TIPO_INDICADOR_LABEL } from "./indicatorLabels";
import type { AnalyzePreviewItem, TrackingEventOut } from "../types";

/**
 * Detalle del evento seleccionado, en el drawer lateral.
 *
 * Acepta tanto una fila de la vista previa (`AnalyzePreviewItem`, que
 * lleva el detalle completo) como un evento ya persistido
 * (`TrackingEventOut`, que solo tiene las columnas de `tracking_events`).
 * Los campos que no existan simplemente no se pintan: el esquema oficial
 * de CLAUDE.md no guarda la linea original ni la regla, asi que un
 * evento guardado muestra menos que su vista previa. Es deliberado, no
 * un fallo — anadir esas columnas cambiaria el modelo de datos comun.
 */

type EventoDetalle = Partial<Omit<AnalyzePreviewItem, "hora_inferida">> &
  Partial<Omit<TrackingEventOut, "hora_inferida">> & {
    hora: string;
    evento: string;
    severidad: AnalyzePreviewItem["severidad"];
    hora_inferida?: boolean | null;
  };

function Campo({ etiqueta, children }: { etiqueta: string; children: React.ReactNode }) {
  return (
    <div>
      <p className="font-label text-label-caps uppercase text-on-surface-variant mb-1">{etiqueta}</p>
      <div className="font-body text-mono-data text-on-surface break-words">{children}</div>
    </div>
  );
}

export interface EventDetailDrawerProps {
  evento: EventoDetalle | null;
  onClose: () => void;
  /** Solo el contenido, sin tarjeta ni botón de cierre: para mostrarlo dentro
   *  de un Modal en pantallas estrechas, que ya trae los suyos. */
  embedded?: boolean;
}

export function EventDetailDrawer({ evento, onClose, embedded = false }: EventDetailDrawerProps) {
  if (!evento) {
    return (
      <Card title="Detalle del evento">
        <div className="flex flex-col items-center justify-center gap-3 py-16 text-on-surface-variant text-center">
          <Icon name="ads_click" className="text-4xl" />
          <p className="font-body text-mono-data">
            Pulsa sobre un comando de la tabla para ver su detalle.
          </p>
        </div>
      </Card>
    );
  }

  const procedenciaDisponible = evento.hora_inferida != null;

  const contenido = (
      <div className={`flex flex-col gap-5 ${embedded ? "" : "p-gutter"}`}>
        <Campo etiqueta="Comando">
          <code className="block bg-canvas border border-hairline rounded p-3 whitespace-pre-wrap">
            {evento.evento}
          </code>
        </Campo>

        {evento.comando_decodificado && (
          <Campo etiqueta="Comando decodificado (-EncodedCommand)">
            <code className="block bg-canvas border border-hairline rounded p-3 whitespace-pre-wrap break-all">
              {evento.comando_decodificado}
            </code>
          </Campo>
        )}

        <div className="flex items-center gap-4">
          <div>
            <p className="font-label text-label-caps uppercase text-on-surface-variant mb-1">Severidad</p>
            <SeverityBadge severidad={evento.severidad} />
          </div>
          {evento.numero_linea != null && (
            <Campo etiqueta="Linea">#{evento.numero_linea}</Campo>
          )}
        </div>

        <Campo etiqueta="Hora">
          {formatHora(evento.hora)}
          {evento.hora_inferida && (
            <span className="ml-2 text-on-surface-variant">
              (inferida: la línea no traía marca temporal y hereda la de la anterior)
            </span>
          )}
        </Campo>

        <Campo etiqueta="Usuario detectado">{evento.usuario_detectado ?? "—"}</Campo>

        {evento.fuente_log != null && (
          <Campo etiqueta="Fuente">{evento.fuente_log}</Campo>
        )}

        {/* Hay que distinguir tres casos y no mezclarlos:
            - procedencia disponible y regla null -> ninguna regla casó
            - procedencia no disponible -> evento guardado sin registro en la
              cadena local (p. ej. insertado por fuera de la aplicación): el
              dato no existe, y decir "ninguna" sería falso.
            - regla con valor -> la mostramos
            `hora_inferida` siempre viene (true/false) cuando hay procedencia. */}
        <Campo etiqueta="Regla que disparó">
          {procedenciaDisponible ? (
            (evento.regla ?? "ninguna")
          ) : (
            <span className="text-on-surface-variant">— (no disponible)</span>
          )}
        </Campo>

        {evento.regla_descripcion && (
          <Campo etiqueta="Por qué es sospechoso">
            <p className="leading-relaxed">{evento.regla_descripcion}</p>
          </Campo>
        )}

        {/* La severidad la decide la regla más grave; si casaron más, se
            enseñan: un mismo comando puede descargar Y crear una cuenta. */}
        {evento.reglas && evento.reglas.length > 1 && (
          <Campo etiqueta="También casan">
            {evento.reglas.filter((r) => r !== evento.regla).join(", ")}
          </Campo>
        )}

        {evento.mitre && evento.mitre.length > 0 && (
          <Campo etiqueta="MITRE ATT&CK">
            <div className="flex flex-wrap gap-1">
              {evento.mitre.map((tecnica) => (
                <a
                  key={tecnica}
                  href={`https://attack.mitre.org/techniques/${tecnica.replace(".", "/")}/`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-1.5 py-0.5 rounded border border-hairline text-on-surface-variant hover:text-on-surface hover:border-primary"
                >
                  {tecnica}
                </a>
              ))}
            </div>
          </Campo>
        )}

        {/* Indicadores: se calculan al analizar y no se guardan, asi que un
            evento ya persistido no los trae (indicadores === undefined) y
            decir "ninguno" seria falso. */}
        <Campo etiqueta="Indicadores">
          {evento.indicadores === undefined ? (
            <span className="text-on-surface-variant">— (no se guarda)</span>
          ) : evento.indicadores.length === 0 ? (
            "—"
          ) : (
            <ul className="flex flex-col gap-2">
              {evento.indicadores.map((i) => (
                <li key={`${i.tipo}:${i.valor}`} className="flex flex-col">
                  <span className="text-on-surface-variant">
                    {TIPO_INDICADOR_LABEL[i.tipo] ?? i.tipo} · {ORIGEN_INDICADOR_LABEL[i.origen] ?? i.origen}
                  </span>
                  <span className="break-all">{i.valor}</span>
                </li>
              ))}
            </ul>
          )}
        </Campo>

        {evento.linea_original && evento.linea_original !== evento.evento && (
          <Campo etiqueta="Linea original del log">
            <code className="block bg-canvas border border-hairline rounded p-3 whitespace-pre-wrap text-on-surface-variant">
              {evento.linea_original}
            </code>
          </Campo>
        )}

        {/* Mismo criterio que el resto de campos vacios de la tabla: un
            guion. No lleva explicacion porque no todos los comandos
            producen salida, y el porque esta documentado en el README. */}
        <Campo etiqueta="Salida del comando">
          {evento.salida ? (
            <pre className="bg-canvas border border-hairline rounded p-3 overflow-x-auto whitespace-pre-wrap">
              {evento.salida}
            </pre>
          ) : (
            "—"
          )}
        </Campo>
      </div>
  );

  if (embedded) return contenido;

  return (
    <Card
      title="Detalle del evento"
      actions={
        <button
          type="button"
          onClick={onClose}
          aria-label="Cerrar detalle"
          className="text-on-surface-variant hover:text-on-surface"
        >
          <Icon name="close" className="text-[20px]" />
        </button>
      }
    >
      {contenido}
    </Card>
  );
}
