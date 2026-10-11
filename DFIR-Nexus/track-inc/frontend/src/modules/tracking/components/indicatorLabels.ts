import type { OrigenIndicador, TipoIndicador } from "../types";

/** Nombres legibles de cada tipo de indicador. Los comparten el panel de
 *  detalle del evento y el resumen de indicadores del log. */
export const TIPO_INDICADOR_LABEL: Record<TipoIndicador, string> = {
  ip_publica: "IP pública",
  ip_privada: "IP privada",
  dominio: "Dominio",
  url: "URL",
  ruta: "Ruta",
  hash: "Hash",
  email: "Correo",
};

/** Dónde apareció el indicador, listo para leer ("IP pública · en la salida").
 *  Antes se componía "en el {origen}" y salía "en el salida". */
export const ORIGEN_INDICADOR_LABEL: Record<OrigenIndicador, string> = {
  comando: "en el comando",
  salida: "en la salida",
  decodificado: "en el comando decodificado",
};
