@echo off
setlocal
chcp 65001 >nul
rem ============================================================
rem  RedBook - compilar en el PC y subir la web a la Pi
rem ------------------------------------------------------------
rem  1) Compila site/ en local con mkdocs (aborta si hay errores).
rem  2) Manda SOLO site/ por ssh en UNA conexion (tar | ssh) y lo
rem     reemplaza en la Pi. nginx lo sirve sin reiniciar nada.
rem
rem  PI_SSH usa el alias de ~/.ssh/config ("pi" = 192.168.1.129,
rem  usuario dacaror, con su clave). Si cambias de equipo, pon
rem  ahi  usuario@ip  en su lugar.
rem ============================================================
set "PI_SSH=pi"
rem  Carpeta que sirve nginx en la Pi (volumen del stack):
set "PI_SITE=/mnt/hdd/webs/RedBook/site"
rem ============================================================

rem  Ir a la carpeta del proyecto (donde esta este .bat)
cd /d "%~dp0"

echo.
echo === [1/2] Compilando la web en local (mkdocs build) ===
call ".venv\Scripts\mkdocs.exe" build --clean --strict
if errorlevel 1 (
  echo.
  echo *** ERROR al compilar. No se sube nada. Revisa los avisos de arriba. ***
  echo.
  pause
  exit /b 1
)

echo.
echo === [2/2] Subiendo site/ a %PI_SSH%:%PI_SITE% ===
echo.

rem  Vacia el destino y extrae el site/ nuevo (en una sola conexion).
tar -czf - -C site . | ssh %PI_SSH% "mkdir -p '%PI_SITE%' && rm -rf '%PI_SITE%'/* && tar -xzf - -C '%PI_SITE%'"
if errorlevel 1 (
  echo.
  echo *** ERROR al subir. Revisa la salida de arriba. ***
  echo.
  pause
  exit /b 1
)

echo.
echo === Hecho. Web actualizada en http://192.168.1.129:8093 ===
echo.
pause
endlocal
