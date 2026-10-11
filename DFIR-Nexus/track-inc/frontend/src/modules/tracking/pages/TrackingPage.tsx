import { useCallback, useEffect, useMemo, useState } from "react";
import { Alert, Button, Card, Modal } from "@/shared/ui";
import {
  CaseSelector,
  EventDetailDrawer,
  EventFilters,
  IndicatorsSummary,
  LogUploadForm,
  PreviewTable,
  SummaryStats,
  TrackingEventTable,
  exportarAnalisisCsv,
  exportarAnalisisJson,
  exportarEventosGuardadosCsv,
  exportarIndicadoresCsv,
} from "../components";
import { analyzeLog, listTrackingEvents, saveEvents, verifyIntegrity, ApiError } from "../api";
import { useMediaQuery } from "../hooks/useMediaQuery";
import type { AnalyzeLogResponse, AnalyzePreviewItem, Severidad, TrackingEventOut } from "../types";

type Tab = "analizar" | "eventos";

/** Fila seleccionada: puede venir de la vista previa (con detalle completo)
 *  o de los eventos ya guardados (solo columnas de tracking_events). */
type EventoSeleccionado = AnalyzePreviewItem | TrackingEventOut;

type Mensaje = {
  variant: "success" | "error" | "info";
  text: string;
  /** Lineas de detalle bajo el mensaje (p. ej. eventos que no cuadran). */
  detalle?: string[];
};

const idPreview = (e: AnalyzePreviewItem) => `${e.numero_linea ?? e.hora}-${e.evento}`;

// baja < media < alta < critica, para que ordenar por severidad tenga
// sentido de verdad y no sea alfabetico.
const RANGO_SEVERIDAD: Record<string, number> = { baja: 0, media: 1, alta: 2, critica: 3 };

/** Cuántas filas se pintan de golpe. Un log de miles de líneas generaba miles
 *  de filas en el DOM y la página se arrastraba; se muestran por tandas. */
const TANDA = 500;

/** `fuente_log` es VARCHAR(100): se recorta conservando la extensión. */
function nombreParaFuente(nombre: string): string {
  if (nombre.length <= 100) return nombre;
  const punto = nombre.lastIndexOf(".");
  const extension = punto > 0 && nombre.length - punto <= 10 ? nombre.slice(punto) : "";
  return nombre.slice(0, 100 - extension.length - 1) + "…" + extension;
}

function coincideBusqueda(e: EventoSeleccionado, texto: string): boolean {
  if (!texto) return true;
  const campos: (string | null | undefined)[] = [e.evento, e.usuario_detectado, e.regla];
  // `id` solo lo tienen los eventos guardados: distingue los dos tipos.
  if ("id" in e) {
    campos.push(e.fuente_log);
  } else {
    campos.push(e.comando_decodificado, ...(e.reglas ?? []), ...(e.mitre ?? []));
    campos.push(...(e.indicadores ?? []).map((i) => i.valor));
  }
  return campos.some((c) => c?.toLowerCase().includes(texto));
}

export function TrackingPage() {
  const [tab, setTab] = useState<Tab>("analizar");
  const [caseId, setCaseId] = useState<number | null>(null);

  const [file, setFile] = useState<File | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [preview, setPreview] = useState<AnalyzeLogResponse | null>(null);
  const [saving, setSaving] = useState(false);
  // Cambiarla vacía el formulario de subida (se vuelve a montar).
  const [formKey, setFormKey] = useState(0);

  const [savedEvents, setSavedEvents] = useState<TrackingEventOut[]>([]);
  const [loadingEvents, setLoadingEvents] = useState(false);

  const [message, setMessage] = useState<Mensaje | null>(null);
  // Aviso de log ya guardado en el caso, pendiente de confirmar.
  const [duplicado, setDuplicado] = useState<string | null>(null);

  // Evento cuyo detalle se muestra en el panel lateral.
  const [selected, setSelected] = useState<EventoSeleccionado | null>(null);
  // Desde 1280 px el detalle va en un panel lateral; por debajo no cabe, y
  // antes simplemente no se mostraba: pulsar una fila no hacía nada visible.
  const pantallaAncha = useMediaQuery("(min-width: 1280px)");

  // Orden de la tabla: por que columna y en que sentido. Solo Hora y
  // Severidad son ordenables; el resto de columnas no aportan un criterio
  // util. Por defecto, el orden del propio fichero de log.
  const [sortKey, setSortKey] = useState<"hora" | "severidad">("hora");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("asc");

  const [filtroSeveridades, setFiltroSeveridades] = useState<Severidad[]>([]);
  const [busqueda, setBusqueda] = useState("");
  const [limite, setLimite] = useState(TANDA);

  function alternarOrden(key: string) {
    const columna = key as "hora" | "severidad";
    if (columna === sortKey) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(columna);
      setSortDir("asc");
    }
  }

  const filtrarYOrdenar = useCallback(
    <T extends EventoSeleccionado>(eventos: T[]): T[] => {
      const texto = busqueda.trim().toLowerCase();
      const signo = sortDir === "asc" ? 1 : -1;
      // Desempate por posición en el fichero (vista previa) o por id (guardados):
      // con horas iguales, el orden original del log.
      const posicion = (e: EventoSeleccionado) => ("id" in e ? e.id : (e.numero_linea ?? 0));
      return eventos
        .filter((e) => filtroSeveridades.length === 0 || filtroSeveridades.includes(e.severidad))
        .filter((e) => coincideBusqueda(e, texto))
        .sort((a, b) => {
          const principal =
            sortKey === "severidad"
              ? RANGO_SEVERIDAD[a.severidad] - RANGO_SEVERIDAD[b.severidad]
              : new Date(a.hora).getTime() - new Date(b.hora).getTime();
          return signo * (principal || posicion(a) - posicion(b));
        });
    },
    [busqueda, filtroSeveridades, sortKey, sortDir],
  );

  const previewFiltrado = useMemo(
    () => (preview ? filtrarYOrdenar(preview.eventos) : []),
    [preview, filtrarYOrdenar],
  );
  const eventosFiltrados = useMemo(() => filtrarYOrdenar(savedEvents), [savedEvents, filtrarYOrdenar]);

  // Cualquier cambio de datos o filtros vuelve a la primera tanda.
  useEffect(() => setLimite(TANDA), [preview, savedEvents, busqueda, filtroSeveridades, tab]);

  /** Todo lo mostrado pertenece a un caso: al cambiarlo se vacía. Antes se
   *  podía analizar con el caso A seleccionado y guardar en el B, y la pestaña
   *  de guardados seguía enseñando los eventos del caso anterior. */
  function cambiarCaso(id: number | null) {
    setCaseId(id);
    setPreview(null);
    setFile(null);
    setSavedEvents([]);
    setSelected(null);
    setMessage(null);
    setDuplicado(null);
    setFormKey((k) => k + 1);
  }

  async function handleAnalyze(selectedFile: File, zonaHoraria: string) {
    if (!caseId) {
      setMessage({ variant: "error", text: "Selecciona un caso primero." });
      return;
    }
    setFile(selectedFile);
    setAnalyzing(true);
    setMessage(null);
    setSelected(null);
    try {
      const result = await analyzeLog(caseId, selectedFile, zonaHoraria);
      setPreview(result);
      const codificacion = result.codificacion ? ` Fichero leído como ${result.codificacion}.` : "";
      if (result.eventos_ya_guardados) {
        setMessage({
          variant: "info",
          text:
            `Análisis completo: ${result.total_eventos} eventos. Atención: este mismo fichero ya se guardó ` +
            `en el caso (${result.eventos_ya_guardados} eventos); guardarlo otra vez los duplicaría.${codificacion}`,
        });
      } else {
        setMessage({ variant: "success", text: `Análisis completo: ${result.total_eventos} eventos detectados.${codificacion}` });
      }
    } catch (e) {
      setPreview(null);
      setMessage({ variant: "error", text: e instanceof Error ? e.message : "Error al analizar el log." });
    } finally {
      setAnalyzing(false);
    }
  }

  async function handleSave(forzar = false) {
    if (!caseId || !preview || !file) return;
    setSaving(true);
    setDuplicado(null);
    try {
      const result = await saveEvents(caseId, {
        case_id: caseId,
        fuente_log: nombreParaFuente(file.name),
        sha256_log: preview.sha256_log,
        forzar,
        eventos: preview.eventos.map((e) => ({
          hora: e.hora,
          evento: e.evento,
          severidad: e.severidad,
          usuario_detectado: e.usuario_detectado,
          regla: e.regla,
          hora_inferida: e.hora_inferida,
        })),
      });
      setMessage({ variant: "success", text: `${result.guardados} eventos guardados en tracking_events.` });
      setPreview(null);
      setFile(null);
      setSelected(null);
      setFormKey((k) => k + 1);
    } catch (e) {
      if (e instanceof ApiError && e.status === 409) {
        setDuplicado(e.message);
      } else {
        setMessage({ variant: "error", text: e instanceof Error ? e.message : "Error al guardar los eventos." });
      }
    } finally {
      setSaving(false);
    }
  }

  const handleLoadEvents = useCallback(async () => {
    if (!caseId) return;
    setLoadingEvents(true);
    try {
      setSavedEvents(await listTrackingEvents(caseId));
    } catch (e) {
      setMessage({ variant: "error", text: e instanceof Error ? e.message : "Error al listar eventos." });
    } finally {
      setLoadingEvents(false);
    }
  }, [caseId]);

  // Al entrar en "Eventos guardados" (o cambiar de caso estando en ella) se
  // cargan solos: antes había que pulsar "Cargar" y, hasta hacerlo, la tabla
  // decía "Sin eventos guardados" aunque los hubiera.
  useEffect(() => {
    if (tab === "eventos" && caseId) void handleLoadEvents();
  }, [tab, caseId, handleLoadEvents]);

  async function handleVerify() {
    if (!caseId) {
      setMessage({ variant: "error", text: "Selecciona un caso primero." });
      return;
    }
    try {
      const result = await verifyIntegrity(caseId);
      setMessage({ variant: result.ok ? "success" : "error", text: result.mensaje, detalle: result.problemas });
    } catch (e) {
      setMessage({ variant: "error", text: e instanceof Error ? e.message : "Error al verificar." });
    }
  }

  // Abre en el panel el evento de una linea concreta del log, desde el
  // resumen de indicadores.
  function seleccionarLinea(linea: number) {
    const evento = preview?.eventos.find((e) => e.numero_linea === linea);
    if (evento) setSelected(evento);
  }

  function cambiarPestana(nueva: Tab) {
    setTab(nueva);
    setSelected(null);
  }

  const filtros = (visibles: number, total: number) => (
    <EventFilters
      severidades={filtroSeveridades}
      onSeveridades={setFiltroSeveridades}
      busqueda={busqueda}
      onBusqueda={setBusqueda}
      visibles={visibles}
      total={total}
    />
  );

  const verMas = (total: number) =>
    total > limite && (
      <div className="flex items-center justify-center gap-3 py-2">
        <span className="font-body text-mono-data text-on-surface-variant">
          Mostrando {limite} de {total}
        </span>
        <Button size="sm" variant="ghost" onClick={() => setLimite((l) => l + TANDA)}>
          Mostrar {Math.min(TANDA, total - limite)} más
        </Button>
      </div>
    );

  const panelDetalle =
    selected &&
    (pantallaAncha ? (
      // El panel solo ocupa sitio cuando hay algo que enseñar: si estuviera
      // siempre, robaría ~380px a la columna del comando incluso vacío.
      <aside className="flex w-80 shrink-0 flex-col sticky top-0">
        <EventDetailDrawer evento={selected} onClose={() => setSelected(null)} />
      </aside>
    ) : (
      <Modal open title="Detalle del evento" onClose={() => setSelected(null)}>
        <EventDetailDrawer evento={selected} onClose={() => setSelected(null)} embedded />
      </Modal>
    ));

  return (
    // [&>*]:shrink-0: la página hace scroll; sin esto, con mucho contenido
    // las tarjetas se encogían para caber en la altura y la de "Caso" quedaba
    // reducida a su cabecera, con el selector oculto.
    <div className="h-full overflow-auto p-gutter flex flex-col gap-panel-gap [&>*]:shrink-0">
      <div className="flex items-center justify-between">
        <h1 className="font-headline text-headline-md text-on-surface">Tracking Post-Incidente</h1>
        <div className="flex gap-2">
          <Button size="sm" variant={tab === "analizar" ? "primary" : "ghost"} onClick={() => cambiarPestana("analizar")}>
            Analizar log
          </Button>
          <Button size="sm" variant={tab === "eventos" ? "primary" : "ghost"} onClick={() => cambiarPestana("eventos")}>
            Eventos guardados
          </Button>
        </div>
      </div>

      {message && (
        <Alert variant={message.variant}>
          {message.text}
          {message.detalle && message.detalle.length > 0 && (
            <ul className="mt-2 list-disc pl-5 font-body text-mono-data text-on-surface-variant">
              {message.detalle.map((linea) => (
                <li key={linea}>{linea}</li>
              ))}
            </ul>
          )}
        </Alert>
      )}

      <Card title="Caso">
        <div className="p-gutter max-w-sm">
          <CaseSelector value={caseId} onChange={cambiarCaso} />
        </div>
      </Card>

      {tab === "analizar" ? (
        <>
          <Card title="Subir fichero de log">
            <div className="p-gutter flex flex-col gap-3">
              <LogUploadForm key={formKey} onAnalyze={handleAnalyze} analyzing={analyzing} />
              <p className="text-mono-data text-on-surface-variant">
                El análisis es una vista previa: no se guarda nada hasta que confirmes.
              </p>
            </div>
          </Card>

          {preview && caseId && file && (
            <div className="flex gap-panel-gap items-start">
              <Card
                title="Resultado del análisis"
                actions={
                  <>
                    <Button size="sm" variant="ghost" icon="download" onClick={() => exportarAnalisisCsv(caseId, file.name, preview)}>
                      CSV
                    </Button>
                    <Button size="sm" variant="ghost" icon="data_object" onClick={() => exportarAnalisisJson(caseId, file.name, preview)}>
                      JSON
                    </Button>
                    <Button size="sm" icon="save" loading={saving} onClick={() => handleSave()}>
                      Guardar en tracking_events
                    </Button>
                  </>
                }
                className="min-w-0 flex-1"
              >
                <div className="p-gutter flex flex-col gap-4">
                  <SummaryStats total={preview.total_eventos} porSeveridad={preview.por_severidad} />
                  <IndicatorsSummary
                    indicadores={preview.indicadores ?? []}
                    onSelectLinea={seleccionarLinea}
                    onExportar={() => exportarIndicadoresCsv(caseId, file.name, preview.indicadores ?? [])}
                  />
                  {filtros(previewFiltrado.length, preview.eventos.length)}
                  <PreviewTable
                    items={previewFiltrado.slice(0, limite)}
                    sortKey={sortKey}
                    sortDir={sortDir}
                    onSort={alternarOrden}
                    onRowClick={setSelected}
                    selectedRowId={selected && !("id" in selected) ? idPreview(selected) : undefined}
                  />
                  {verMas(previewFiltrado.length)}
                </div>
              </Card>
              {panelDetalle}
            </div>
          )}
        </>
      ) : (
        <div className="flex gap-panel-gap items-start">
          <Card
            title="Eventos guardados"
            actions={
              <>
                <Button size="sm" variant="ghost" icon="refresh" loading={loadingEvents} disabled={!caseId} onClick={handleLoadEvents}>
                  Recargar
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  icon="download"
                  disabled={!caseId || savedEvents.length === 0}
                  onClick={() => caseId && exportarEventosGuardadosCsv(caseId, eventosFiltrados)}
                >
                  CSV
                </Button>
                <Button size="sm" variant="ghost" icon="verified" disabled={!caseId} onClick={handleVerify}>
                  Verificar integridad
                </Button>
              </>
            }
            className="min-w-0 flex-1"
          >
            <div className="flex flex-col gap-4">
              {savedEvents.length > 0 && <div className="px-gutter pt-gutter">{filtros(eventosFiltrados.length, savedEvents.length)}</div>}
              <TrackingEventTable
                events={eventosFiltrados.slice(0, limite)}
                sortKey={sortKey}
                sortDir={sortDir}
                onSort={alternarOrden}
                onRowClick={setSelected}
                selectedRowId={selected && "id" in selected ? selected.id : undefined}
              />
              {verMas(eventosFiltrados.length)}
            </div>
          </Card>
          {panelDetalle}
        </div>
      )}

      <Modal
        open={duplicado !== null}
        title="Este log ya está guardado"
        onClose={() => setDuplicado(null)}
        footer={
          <div className="flex justify-end gap-2">
            <Button size="sm" variant="ghost" onClick={() => setDuplicado(null)}>
              Cancelar
            </Button>
            <Button size="sm" variant="danger" loading={saving} onClick={() => handleSave(true)}>
              Guardar de todos modos
            </Button>
          </div>
        }
      >
        <p className="text-body-md text-on-surface">{duplicado}</p>
      </Modal>
    </div>
  );
}
