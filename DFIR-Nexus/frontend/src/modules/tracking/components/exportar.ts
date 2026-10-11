import type { AnalyzeLogResponse, IndicadorAgregado, TrackingEventOut } from "../types";
import { fechaHoraCsv } from "./formatHora";

/**
 * Exportación de lo analizado para llevarlo a otras herramientas (hoja de
 * cálculo, OSINT, informe).
 *
 * CSV con dos precauciones:
 *  - BOM UTF-8, para que Excel no destroce tildes y rutas.
 *  - Hora en `AAAA-MM-DD hh:mm:ss` (UTC), que la hoja de cálculo reconoce
 *    como fecha; con el ISO `...T...Z` la deja como texto y no se puede
 *    ordenar ni filtrar por día.
 *  - Neutralización de fórmulas: el log lo escribió el ATACANTE, y una celda
 *    que empieza por = + - @ se ejecuta como fórmula al abrir el CSV (inyección
 *    CSV / DDE). Se antepone un apóstrofo, que Excel oculta y no la ejecuta.
 */

function celda(valor: unknown): string {
  let texto = valor == null ? "" : String(valor);
  if (/^[=+\-@\t\r]/.test(texto)) texto = `'${texto}`;
  return /[",\r\n;]/.test(texto) ? `"${texto.replace(/"/g, '""')}"` : texto;
}

function csv(cabecera: string[], filas: unknown[][]): string {
  return "\uFEFF" + [cabecera, ...filas].map((fila) => fila.map(celda).join(",")).join("\r\n");
}

function descargar(nombre: string, contenido: string, tipo: string) {
  const url = URL.createObjectURL(new Blob([contenido], { type: tipo }));
  const enlace = document.createElement("a");
  enlace.href = url;
  enlace.download = nombre;
  enlace.click();
  URL.revokeObjectURL(url);
}

function base(caseId: number, fuente: string): string {
  return `tracking-caso${caseId}-${fuente.replace(/[^\w.-]+/g, "_")}`;
}

export function exportarAnalisisCsv(caseId: number, fuente: string, analisis: AnalyzeLogResponse) {
  descargar(
    `${base(caseId, fuente)}-eventos.csv`,
    csv(
      ["linea", "hora_utc", "hora_inferida", "severidad", "evento", "comando_decodificado", "usuario", "regla", "reglas", "mitre", "indicadores", "salida"],
      analisis.eventos.map((e) => [
        e.numero_linea,
        fechaHoraCsv(e.hora),
        e.hora_inferida ? "si" : "no",
        e.severidad,
        e.evento,
        e.comando_decodificado,
        e.usuario_detectado,
        e.regla,
        (e.reglas ?? []).join(" "),
        (e.mitre ?? []).join(" "),
        (e.indicadores ?? []).map((i) => `${i.tipo}:${i.valor}`).join(" "),
        e.salida,
      ]),
    ),
    "text/csv;charset=utf-8",
  );
}

export function exportarIndicadoresCsv(caseId: number, fuente: string, indicadores: IndicadorAgregado[]) {
  descargar(
    `${base(caseId, fuente)}-indicadores.csv`,
    csv(
      ["tipo", "valor", "severidad_maxima", "veces", "lineas"],
      indicadores.map((i) => [i.tipo, i.valor, i.severidad_maxima, i.veces, i.lineas.join(" ")]),
    ),
    "text/csv;charset=utf-8",
  );
}

export function exportarAnalisisJson(caseId: number, fuente: string, analisis: AnalyzeLogResponse) {
  descargar(
    `${base(caseId, fuente)}-analisis.json`,
    JSON.stringify({ caso: caseId, fuente_log: fuente, ...analisis }, null, 2),
    "application/json",
  );
}

export function exportarEventosGuardadosCsv(caseId: number, eventos: TrackingEventOut[]) {
  descargar(
    `tracking-caso${caseId}-eventos-guardados.csv`,
    csv(
      ["id", "hora_utc", "hora_inferida", "severidad", "evento", "usuario", "fuente_log", "regla"],
      eventos.map((e) => [
        e.id,
        fechaHoraCsv(e.hora),
        e.hora_inferida == null ? "" : e.hora_inferida ? "si" : "no",
        e.severidad,
        e.evento,
        e.usuario_detectado,
        e.fuente_log,
        e.regla,
      ]),
    ),
    "text/csv;charset=utf-8",
  );
}
