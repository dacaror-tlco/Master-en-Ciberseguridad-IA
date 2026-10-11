# Arranque del modulo en Windows/PowerShell.
#
# Por defecto la aplicacion se abre UNA sola vez: compila el frontend y lo
# sirve el propio backend, todo en http://127.0.0.1:8000 (un proceso, un
# puerto, mismo origen y por tanto sin CORS). Es como corre tambien en Docker.
#
#   .\start-dev.ps1            aplicacion completa en http://127.0.0.1:8000
#
#   .\start-dev.ps1 -Dev       modo desarrollo: dos procesos (uvicorn con
#                              --reload y Vite en :5173) para tener recarga en
#                              caliente mientras se toca el frontend. En ese
#                              caso la aplicacion se abre en :5173.
#
#   .\start-dev.ps1 -SinBuild  no recompila el frontend; util si solo has
#                              cambiado backend y ya hay un build hecho.
#
#   .\start-dev.ps1 -ConFrontend  compila y sirve el frontend PROPIO del
#                              modulo, que esta EN DESUSO: la interfaz oficial
#                              es la del frontend unico de development. Solo
#                              para ensenar el modulo por separado.
#
#   .\start-dev.ps1 -UsarEnv   usa la base de datos del .env (normalmente la
#                              COMPARTIDA del equipo) en vez de la SQLite local.
#
#   .\start-dev.ps1 -ConAuth   exige el JWT de Casos en los cinco endpoints,
#                              como en development. Sin este parametro se
#                              arranca con la autenticacion desactivada,
#                              porque el modulo suelto no trae pantalla de
#                              login y no hay de donde sacar un token.
#
# Base de datos, por prioridad:
#   1. DATABASE_URL ya definida al llamar al script: se respeta tal cual.
#   2. Con -UsarEnv: la del .env del modulo (DATABASE_URL o MYSQL_*), la
#      misma que usa `npm run dev:all` en development.
#   3. Si no: SQLite local (nexus_dev.db).
#
# SQLite es lo que se usa por defecto A PROPOSITO. En development este script
# se cambio para leer el .env directamente; aqui se mantiene como opcion
# explicita: el .env apunta a la base compartida de Aiven y arrancar el modulo
# para probarlo no debe escribir en ella sin querer (ya paso una vez). El
# lanzador principal de development, `npm run dev:all`, no usa este script.

param(
    [switch]$Dev,
    [switch]$SinBuild,
    [switch]$UsarEnv,
    [switch]$ConAuth,
    [switch]$ConFrontend
)

$ErrorActionPreference = "Stop"
$raiz   = $PSScriptRoot
$python = Join-Path $raiz "venv\Scripts\python.exe"
$front  = Join-Path $raiz "frontend"

if (-not (Test-Path $python)) {
    Write-Error "No existe $python. Crea el venv con 'python -m venv venv' e instala requirements.txt."
}

if ($env:DATABASE_URL) {
    $origenBase = "DATABASE_URL del entorno"
} elseif ($UsarEnv) {
    # No se fija nada: app/core/database.py y alembic/env.py leen el .env.
    $origenBase = ".env del modulo (puede ser la base COMPARTIDA)"
} else {
    $env:DATABASE_URL = "sqlite:///./nexus_dev.db"
    $origenBase = "SQLite local"
}
# Autenticacion: en development la exige el gateway con el token que emite
# Casos; aqui, suelto, no hay login que lo emita, asi que por defecto se apaga
# (y el backend lo avisa en su primera linea de log).
if ($ConAuth) {
    Remove-Item Env:TRACKING_AUTH_DESACTIVADA -ErrorAction SilentlyContinue
    Write-Host "Autenticacion: OBLIGATORIA (hara falta un JWT firmado con JWT_SECRET)" -ForegroundColor Cyan
} else {
    $env:TRACKING_AUTH_DESACTIVADA = "1"
    Write-Host "Autenticacion: desactivada (modulo suelto). Usa -ConAuth para exigir el JWT." -ForegroundColor DarkGray
}

# La URL puede llevar la contrasena: se muestra sin ella.
$urlVisible = if ($env:DATABASE_URL) { $env:DATABASE_URL -replace '://([^:/@]+):[^@]*@', '://$1:***@' } else { "(la del .env)" }
Write-Host "Base de datos: $origenBase -> $urlVisible" -ForegroundColor Cyan

function Install-FrontendDeps {
    if (-not (Test-Path (Join-Path $front "node_modules"))) {
        Write-Host "Instalando dependencias del frontend..." -ForegroundColor Yellow
        Push-Location $front
        try { & npm.cmd install } finally { Pop-Location }
    }
}

# El esquema lo gestiona Alembic (CLAUDE.md: ninguna modificacion del modelo se
# aplica sin su migracion). El backend se niega a arrancar si faltan tablas.
function Invoke-Migrations {
    # Contra la base del .env (la compartida) no se migra nada desde aqui: su
    # esquema lo gestiona el equipo. Solo se migra la SQLite local.
    if ($UsarEnv -and -not $env:DATABASE_URL) {
        Write-Host "Base del .env: no se ejecutan migraciones desde este script." -ForegroundColor DarkGray
        return
    }
    Push-Location $raiz
    try { & $python -m alembic upgrade head } finally { Pop-Location }
}

# Frontend propio en desuso: la interfaz oficial es la del frontend unico de
# development. Se conserva el codigo y se puede volver a levantar con
# -ConFrontend, para ensenar el modulo suelto.
if ($ConFrontend) {
    $env:TRACKING_FRONTEND_LOCAL = "1"
    Write-Host "Frontend propio: activado (en desuso; la interfaz oficial es la de development)" -ForegroundColor Yellow
} else {
    Remove-Item Env:TRACKING_FRONTEND_LOCAL -ErrorAction SilentlyContinue
    Write-Host "Frontend propio: en desuso. La API responde en /docs; usa -ConFrontend para servirlo." -ForegroundColor DarkGray
}

# ------------------------------------------------------- modo desarrollo (-Dev)
if ($Dev) {
    Invoke-Migrations
    if (-not $ConFrontend) {
        Write-Error "El modo -Dev sirve el frontend propio, que esta en desuso. Anade -ConFrontend si de verdad lo quieres."
    }
    Install-FrontendDeps

    Write-Host ""
    Write-Host "MODO DESARROLLO: dos procesos, con recarga en caliente." -ForegroundColor Yellow
    Write-Host "Abre la aplicacion en -> http://localhost:5173" -ForegroundColor Green
    Write-Host "API (docs)            -> http://127.0.0.1:8000/docs" -ForegroundColor DarkGray
    Write-Host ""

    Start-Process powershell -ArgumentList @(
        "-NoExit", "-Command",
        "Set-Location '$raiz'; `$env:DATABASE_URL='$($env:DATABASE_URL)'; `$env:TRACKING_AUTH_DESACTIVADA='$($env:TRACKING_AUTH_DESACTIVADA)'; & '$python' -m uvicorn app.main:app --reload --port 8000"
    )
    Start-Process powershell -ArgumentList @(
        "-NoExit", "-Command",
        "Set-Location '$front'; & npm.cmd run dev"
    )
    return
}

# ------------------------------------------------ por defecto: un solo proceso
if ($ConFrontend) {
    Install-FrontendDeps

    if (-not $SinBuild) {
        Write-Host "Compilando el frontend propio..." -ForegroundColor Yellow
        Push-Location $front
        try { & npm.cmd run build } finally { Pop-Location }
    }

    if (-not (Test-Path (Join-Path $front "dist\index.html"))) {
        Write-Error "No existe frontend\dist\index.html. Ejecuta el script sin -SinBuild para compilarlo."
    }
}

Invoke-Migrations

Write-Host ""
if ($ConFrontend) {
    Write-Host "Aplicacion completa -> http://127.0.0.1:8000" -ForegroundColor Green
} else {
    Write-Host "API -> http://127.0.0.1:8000  (sin interfaz: esta en el frontend de development)" -ForegroundColor Green
}
Write-Host "API (docs)          -> http://127.0.0.1:8000/docs" -ForegroundColor DarkGray
Write-Host "Ctrl+C para parar." -ForegroundColor DarkGray
Write-Host ""

# sin --reload: aqui se sirve el bundle ya compilado
Push-Location $raiz
try { & $python -m uvicorn app.main:app --port 8000 } finally { Pop-Location }
