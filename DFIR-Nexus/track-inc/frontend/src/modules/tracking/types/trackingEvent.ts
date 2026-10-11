export type Severidad = "baja" | "media" | "alta" | "critica";

/** Refleja backend/modules/tracking/schemas.py::TrackingEventOut */
export interface TrackingEventOut {
  id: number;
  case_id: number;
  hora: string;
  evento: string;
  severidad: Severidad;
  fuente_log: string | null;
  usuario_detectado: string | null;
  /** Procedencia conservada en la cadena local (no son columnas de
   *  tracking_events). Ambos a null: dato no disponible para este evento. */
  regla?: string | null;
  hora_inferida?: boolean | null;
}

/** Refleja app/modules/tracking/schemas.py::TipoIndicador */
export type TipoIndicador = "ip_publica" | "ip_privada" | "dominio" | "url" | "ruta" | "hash" | "email";

/** De donde salio el indicador: del comando ejecutado o de su salida. */
export type OrigenIndicador = "comando" | "salida" | "decodificado";

/** Refleja app/modules/tracking/schemas.py::IndicadorOut */
export interface IndicadorOut {
  tipo: TipoIndicador;
  valor: string;
  origen: OrigenIndicador;
}

/** Refleja app/modules/tracking/schemas.py::IndicadorAgregado */
export interface IndicadorAgregado {
  tipo: TipoIndicador;
  valor: string;
  veces: number;
  lineas: number[];
  severidad_maxima: Severidad;
}

/** Refleja app/modules/tracking/schemas.py::AnalyzePreviewItem */
export interface AnalyzePreviewItem {
  hora: string;
  evento: string;
  severidad: Severidad;
  usuario_detectado: string | null;
  /** Regla que decide la severidad: la más grave de las que casaron. */
  regla: string | null;
  /** Todas las reglas que casaron, en el orden de rules.yaml. */
  reglas?: string[];
  /** Técnicas MITRE ATT&CK de las reglas que casaron. */
  mitre?: string[];

  // Detalle para el panel lateral. No se persiste en tracking_events.
  linea_original?: string | null;
  numero_linea?: number | null;
  hora_inferida?: boolean;
  regla_descripcion?: string | null;
  /** IPs, dominios, URLs, rutas, hashes y correos del comando y su salida. */
  indicadores?: IndicadorOut[];
  /** Salida del comando: las lineas indentadas que el log trae debajo. No
   *  todos los comandos la tienen. Nunca se obtiene ejecutando el comando. */
  salida?: string | null;
  /** Lo que esconde un powershell -EncodedCommand, ya legible (nunca se ejecuta). */
  comando_decodificado?: string | null;
}

/** Refleja app/modules/tracking/schemas.py::AnalyzeLogResponse */
export interface AnalyzeLogResponse {
  total_eventos: number;
  por_severidad: Record<string, number>;
  eventos: AnalyzePreviewItem[];
  /** Indicadores de todo el log, agrupados y ordenados por relevancia. */
  indicadores?: IndicadorAgregado[];
  /** Codificación con la que se leyó el fichero (utf-8, utf-16, cp1252...). */
  codificacion?: string | null;
  /** SHA-256 del fichero subido: identifica el log. */
  sha256_log?: string | null;
  /** Eventos de este mismo fichero ya guardados en el caso (>0: guardarlo duplica). */
  eventos_ya_guardados?: number;
}

/** Lo que se envía al guardar: solo lo que se persiste o se conserva en la
 *  cadena local. El resto del detalle (indicadores, salida...) no hace falta,
 *  y reenviarlo multiplicaba el tamaño de la petición en logs grandes. */
export type EventoAGuardar = Pick<
  AnalyzePreviewItem,
  "hora" | "evento" | "severidad" | "usuario_detectado" | "regla" | "hora_inferida"
>;

/** Refleja app/modules/tracking/schemas.py::SaveEventsRequest */
export interface SaveEventsRequest {
  case_id: number;
  fuente_log: string;
  eventos: EventoAGuardar[];
  sha256_log?: string | null;
  /** Guardar aunque ese log ya esté guardado en el caso (si no, 409). */
  forzar?: boolean;
}

/** Refleja backend/modules/tracking/schemas.py::SaveEventsResponse */
export interface SaveEventsResponse {
  guardados: number;
  tracking_events: TrackingEventOut[];
}

/** Refleja backend/modules/tracking/schemas.py::VerifyIntegrityResponse */
export interface VerifyIntegrityResponse {
  ok: boolean;
  mensaje: string;
  /** Eventos que no cuadran con lo guardado: modificados, borrados o
   *  insertados por fuera de la aplicacion. */
  problemas?: string[];
}
