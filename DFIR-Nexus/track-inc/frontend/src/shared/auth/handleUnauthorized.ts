import { clearToken } from "./session";

/**
 * Reacción a un 401 de una petición que SÍ llevaba token: la sesión se ha
 * caducado o invalidado a mitad de uso. Se borra el token y se vuelve al
 * login.
 *
 * Solo se llama cuando había token. Con este módulo suelto nunca lo hay
 * (no existe pantalla de login aquí), así que un 401 se muestra como
 * cualquier otro error de la API y no manda a ninguna parte.
 *
 * La comprobación de la ruta evita un bucle de redirecciones cuando varias
 * peticiones en paralelo devuelven 401 a la vez.
 */
export function handleUnauthorized(): void {
  clearToken();
  if (window.location.pathname !== "/login") {
    window.location.assign("/login");
  }
}
