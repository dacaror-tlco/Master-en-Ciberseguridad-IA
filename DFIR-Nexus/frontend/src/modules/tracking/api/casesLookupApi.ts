import { httpRequest } from "./httpClient";
import type { CaseOption } from "../types";

/**
 * Llamada a GET /cases-lookup, del propio backend de Tracking (no de
 * Casos: son procesos y puertos distintos, ver docs/CONTRATOS.md).
 * Tracking no importa el modelo de Casos ni llama a su API — lee
 * directamente la tabla compartida `cases` con SQL mínimo
 * (app/modules/tracking/repository.py::list_case_options) y expone aquí
 * solo lo que el selector necesita, sin los casos eliminados.
 */
export function listCasesForSelector(): Promise<CaseOption[]> {
  return httpRequest<CaseOption[]>("/cases-lookup");
}
