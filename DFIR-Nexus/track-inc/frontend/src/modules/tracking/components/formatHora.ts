/**
 * Hora de un evento para mostrar, con su zona horaria explícita.
 *
 * La API devuelve siempre UTC; se pinta en la hora local del navegador pero
 * indicando la zona ("14/8/2026, 5:11:19 CEST"), para que nadie compare dos
 * horas creyendo que están en la misma referencia sin estarlo.
 */
export function formatHora(hora: string): string {
  return new Date(hora).toLocaleString(undefined, { timeZoneName: "short" });
}

/**
 * Hora UTC en el formato que Excel y LibreOffice reconocen como fecha y hora
 * (`2026-09-12 00:14:07`).
 *
 * El ISO 8601 que devuelve la API (`2026-09-12T00:14:07Z`) lo dejan como
 * texto: no se puede ordenar ni filtrar por día en la hoja de cálculo, que es
 * lo primero que hace el perito con la exportación. Se mantiene en UTC, como
 * anuncia la cabecera `hora_utc`; el JSON sí conserva el ISO completo, que es
 * lo que espera otra herramienta que lo lea.
 */
export function fechaHoraCsv(hora: string): string {
  const fecha = new Date(hora);
  if (Number.isNaN(fecha.getTime())) return hora; // lo que llegue, sin inventar
  return fecha.toISOString().slice(0, 19).replace("T", " ");
}

function desplazamiento(minutos: number): string {
  const signo = minutos < 0 ? "-" : "+";
  const abs = Math.abs(minutos);
  return `${signo}${String(Math.floor(abs / 60)).padStart(2, "0")}:${String(abs % 60).padStart(2, "0")}`;
}

/** Zonas que se ofrecen al subir un log: UTC y los desplazamientos habituales,
 *  en el formato que acepta la API (`UTC`, `+02:00`...). */
export const ZONAS_HORARIAS: { value: string; label: string }[] = [
  { value: "UTC", label: "UTC" },
  ...[-720, -660, -600, -540, -480, -420, -360, -300, -240, -180, -120, -60,
    60, 120, 180, 240, 300, 330, 360, 420, 480, 540, 600, 660, 720, 780, 840].map((m) => ({
    value: desplazamiento(m),
    label: `UTC${desplazamiento(m)}`,
  })),
];
