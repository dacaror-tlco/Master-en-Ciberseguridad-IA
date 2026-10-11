import { httpRequest } from "./httpClient";
import type {
  AnalyzeLogResponse,
  SaveEventsRequest,
  SaveEventsResponse,
  TrackingEventOut,
  VerifyIntegrityResponse,
} from "../types";

/**
 * POST /cases/{case_id}/tracking/analyze — sube un log, devuelve preview
 * clasificado. No persiste nada (ver app/modules/tracking/routes.py).
 * `zonaHoraria`: en la que están escritas las horas del log.
 */
export function analyzeLog(caseId: number, file: File, zonaHoraria = "UTC"): Promise<AnalyzeLogResponse> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("zona_horaria", zonaHoraria);

  // Sin Content-Type: el navegador lo pone con el boundary del multipart.
  return httpRequest<AnalyzeLogResponse>(`/cases/${caseId}/tracking/analyze`, {
    method: "POST",
    body: formData,
  });
}

/** POST /cases/{case_id}/tracking/events — persiste los eventos revisados. */
export function saveEvents(caseId: number, payload: SaveEventsRequest): Promise<SaveEventsResponse> {
  return httpRequest<SaveEventsResponse>(`/cases/${caseId}/tracking/events`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

/** Tamaño de página al listar. El backend admite hasta 1000 por petición. */
const POR_PAGINA = 500;

/**
 * GET /cases/{case_id}/tracking/events — eventos guardados del caso.
 *
 * El endpoint está paginado (`skip`/`limit`, como Casos y OSINT), así que se
 * piden páginas hasta agotarlas: la pantalla necesita el caso completo para
 * filtrar y verificar, y un log grande deja miles de eventos.
 */
export async function listTrackingEvents(caseId: number): Promise<TrackingEventOut[]> {
  const eventos: TrackingEventOut[] = [];
  for (let skip = 0; ; skip += POR_PAGINA) {
    const pagina = await httpRequest<TrackingEventOut[]>(
      `/cases/${caseId}/tracking/events?skip=${skip}&limit=${POR_PAGINA}`,
    );
    eventos.push(...pagina);
    if (pagina.length < POR_PAGINA) return eventos;
  }
}

/** GET /cases/{case_id}/tracking/verify — verifica la integridad interna (capa opcional). */
export function verifyIntegrity(caseId: number): Promise<VerifyIntegrityResponse> {
  return httpRequest<VerifyIntegrityResponse>(`/cases/${caseId}/tracking/verify`);
}
