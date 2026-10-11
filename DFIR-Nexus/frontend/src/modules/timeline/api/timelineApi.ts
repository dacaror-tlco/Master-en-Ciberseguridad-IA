import { getToken, handleUnauthorized } from '@/shared/auth';

// Timeline es un backend independiente del de Casos (puerto propio, ver
// docs/CONTRATOS.md) — necesita su propia variable para no depender
// accidentalmente del backend de Casos.
const API_BASE = import.meta.env.VITE_TIMELINE_API_URL ?? 'http://localhost:8002';

// H-19 (auditoría Módulo 4): sin timeout, un backend colgado bloquea la
// UI indefinidamente. 15s es holgado para un recálculo multi-fuente.
const TIMEOUT_MS = 15_000;

export interface TimelineEvent {
  id: number;
  case_id: number;
  fecha_hora: string;
  descripcion: string;
  origen_modulo: string;
  origen_id: number;
  orden: number;
}

async function request<T>(path: string, errorMessage: string, options?: RequestInit): Promise<T> {
  const token = getToken();
  const controller = new AbortController();
  const timer = window.setTimeout(() => controller.abort(), TIMEOUT_MS);

  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, {
      ...options,
      signal: controller.signal,
      headers: {
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...options?.headers,
      },
    });
  } catch (e) {
    if (e instanceof DOMException && e.name === 'AbortError') {
      throw new Error('La petición ha tardado demasiado. Inténtalo de nuevo.');
    }
    throw new Error(errorMessage);
  } finally {
    window.clearTimeout(timer);
  }

  if (!res.ok) {
    if (res.status === 401 && token) {
      handleUnauthorized();
    }
    // H-12 (auditoría Módulo 4): el backend devuelve {"detail": "..."} en
    // errores; antes se descartaba y el usuario veía un mensaje genérico.
    const body = await res.json().catch(() => null);
    const detail =
      body && typeof body === 'object' && typeof (body as { detail?: unknown }).detail === 'string'
        ? (body as { detail: string }).detail
        : null;
    throw new Error(detail ?? errorMessage);
  }
  return res.json() as Promise<T>;
}

export async function getTimelineEvents(caseId: number): Promise<TimelineEvent[]> {
  return request<TimelineEvent[]>(`/timeline/cases/${caseId}`, 'Error al obtener la línea temporal');
}

export async function refreshTimeline(caseId: number): Promise<TimelineEvent[]> {
  return request<TimelineEvent[]>(`/timeline/cases/${caseId}/refresh`, 'Error al recalcular la línea temporal', {
    method: 'POST',
  });
}
