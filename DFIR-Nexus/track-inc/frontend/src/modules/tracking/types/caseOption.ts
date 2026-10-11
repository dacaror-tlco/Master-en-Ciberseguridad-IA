/**
 * Tipo MÍNIMO local, solo con lo que Tracking necesita para el selector
 * de caso (id, nombre, estado). Deliberadamente NO se importa nada de
 * modules/cases — está prohibido por la regla de dependencia entre
 * módulos (ver DESIGN_SYSTEM.md §13). La llamada a GET /cases/ es
 * directa contra el backend, no una dependencia de otro módulo frontend.
 */
export interface CaseOption {
  id: number;
  nombre: string;
  estado: string;
}
