import { httpRequest } from "./httpClient";
import type { Case, CaseCreateInput } from "../types";

export function listCases(): Promise<Case[]> {
  return httpRequest<Case[]>("/cases/");
}

export function getCase(caseId: number): Promise<Case> {
  return httpRequest<Case>(`/cases/${caseId}`);
}

export function createCase(input: CaseCreateInput): Promise<Case> {
  const params = new URLSearchParams();
  params.set("nombre", input.nombre);
  if (input.estado) params.set("estado", input.estado);
  if (input.responsable) params.set("responsable", input.responsable);
  if (input.descripcion) params.set("descripcion", input.descripcion);

  // el endpoint placeholder actual recibe query params, no JSON body
  // (ver backend/modules/cases/routes.py)
  return httpRequest<Case>(`/cases/?${params.toString()}`, { method: "POST" });
}
