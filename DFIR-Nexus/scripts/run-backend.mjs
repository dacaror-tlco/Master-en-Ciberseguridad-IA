#!/usr/bin/env node
/**
 * Arranca un backend FastAPI de Nexus usando el intérprete Python de su
 * propio entorno virtual (cada backend es un proceso independiente, con
 * sus propias dependencias — ver docs/INTEGRACION_Y_DESPLIEGUE.md).
 *
 * Uso: node scripts/run-backend.mjs <directorio> <puerto>
 * Ejemplo: node scripts/run-backend.mjs backend 8000
 *
 * Resuelve la ruta del venv de forma multiplataforma (Windows vs.
 * Linux/macOS difieren en dónde vive el ejecutable de Python dentro del
 * venv) para que "npm run dev:all" funcione igual en los tres sistemas.
 */
import { spawn } from 'node:child_process'
import { existsSync, readFileSync } from 'node:fs'
import path from 'node:path'

/**
 * Lee el `.env` de un backend y lo devuelve como objeto.
 *
 * Hace falta porque los cinco backends no cargan su configuración igual:
 * Casos, OSINT e Informes usan `pydantic-settings` con `env_file=".env"` y se
 * la leen solos, pero Tracking y Timeline leen `DATABASE_URL` directamente de
 * `os.environ`, sin `python-dotenv` de por medio. Arrancados por este script
 * sin nada más, esos dos caían al valor por defecto del código
 * (`mysql+pymysql://nexus:nexus@localhost:3306/nexus`) e ignoraban su propio
 * `.env` — Tracking además ni siquiera arranca cuando no puede validar el
 * esquema, así que `npm run dev:all` fallaba en ese proceso.
 *
 * Se resuelve aquí, en el lanzador, en vez de añadir `python-dotenv` al código
 * de esos dos backends: la carencia solo se manifiesta al arrancarlos desde
 * este script, y arreglarla aquí no toca el módulo de nadie. Para los tres que
 * ya leen su `.env` esto es inocuo — se les pasan los mismos valores que ya
 * iban a leer.
 */
function leerEnv(rutaEnv) {
  if (!existsSync(rutaEnv)) return {}
  const vars = {}
  for (const linea of readFileSync(rutaEnv, 'utf8').split('\n')) {
    const limpia = linea.trim()
    if (limpia === '' || limpia.startsWith('#')) continue
    const separador = limpia.indexOf('=')
    if (separador === -1) continue
    const clave = limpia.slice(0, separador).trim()
    let valor = limpia.slice(separador + 1).trim()
    // Comillas opcionales alrededor del valor, como acepta dotenv.
    if (
      (valor.startsWith('"') && valor.endsWith('"')) ||
      (valor.startsWith("'") && valor.endsWith("'"))
    ) {
      valor = valor.slice(1, -1)
    }
    vars[clave] = valor
  }
  return vars
}

const [, , dir, port] = process.argv

if (!dir || !port) {
  console.error('Uso: node scripts/run-backend.mjs <directorio> <puerto>')
  process.exit(1)
}

const isWindows = process.platform === 'win32'
// Ruta ABSOLUTA, resuelta contra el cwd de este script (la raíz del repo):
// spawn() recibe más abajo `cwd: dir` para que uvicorn arranque dentro del
// backend correspondiente, y una ruta relativa al ejecutable se
// interpretaría entonces relativa a ESE cwd nuevo, no al de partida
// (duplicando el segmento del directorio y fallando con ENOENT).
const venvPython = path.resolve(
  process.cwd(),
  dir,
  'venv',
  isWindows ? 'Scripts\\python.exe' : 'bin/python',
)

if (!existsSync(venvPython)) {
  const activar = isWindows
    ? `${dir}\\venv\\Scripts\\activate`
    : `source ${dir}/venv/bin/activate`
  console.error(
    `\n[${dir}] No se encuentra el entorno virtual en "${venvPython}".\n` +
      `Este backend es independiente y necesita su propio venv (ver\n` +
      `docs/INTEGRACION_Y_DESPLIEGUE.md, sección "Despliegue local").\n` +
      `Créalo antes de volver a ejecutar "npm run dev:all":\n\n` +
      `  cd ${dir}\n` +
      `  python3 -m venv venv\n` +
      `  ${activar}\n` +
      `  pip install -r requirements.txt\n`,
  )
  process.exit(1)
}

// El entorno real del shell tiene prioridad sobre el `.env`: si alguien
// exporta DATABASE_URL a mano para apuntar a otra base, ese gesto debe ganar.
const entorno = {
  ...leerEnv(path.resolve(process.cwd(), dir, '.env')),
  ...process.env,
}

const child = spawn(
  venvPython,
  ['-m', 'uvicorn', 'app.main:app', '--reload', '--port', port],
  { cwd: dir, stdio: 'inherit', env: entorno },
)

child.on('exit', (code) => process.exit(code ?? 0))
child.on('error', (err) => {
  console.error(`[${dir}] No se pudo arrancar el backend:`, err.message)
  process.exit(1)
})

for (const signal of ['SIGINT', 'SIGTERM']) {
  process.on(signal, () => child.kill(signal))
}
