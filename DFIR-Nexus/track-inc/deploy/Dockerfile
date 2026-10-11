# Imagen de Tracking con dos variantes:
#
#   api       (POR DEFECTO, la última etapa) — solo la API. Es la que usa el
#             despliegue común de development (deploy/docker-compose.yml de la
#             raíz), donde el frontend único lo sirve la pasarela nginx. No
#             necesita ni compila ningún frontend: por eso sigue funcionando
#             aunque se borre track-inc/frontend/ del repositorio.
#
#   completo  — la API sirviendo además el frontend propio del módulo, para
#             usarlo por separado (deploy/docker-compose.yml de este módulo,
#             con `target: completo`).
#
# Con BuildKit (el constructor por defecto de Docker Compose v2) solo se
# construyen las etapas que necesita la variante pedida.

# ---- frontend propio del módulo (solo para la variante `completo`) ----
FROM node:22-slim AS frontend-build
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ---- base común: backend (FastAPI) ----
FROM python:3.11-slim AS base

WORKDIR /app

COPY requirements-web.txt .
# Solo lo que usa la aplicacion web: sin pytest ni las dependencias del motor
# de captura en vivo de agent/ (watchdog, psutil, flask, pywin32).
RUN pip install --no-cache-dir -r requirements-web.txt

COPY app ./app
COPY agent ./agent
COPY config ./config
COPY alembic.ini .
COPY alembic ./alembic

EXPOSE 8000

# Aplica las migraciones pendientes antes de arrancar: el backend se niega
# a arrancar si faltan tablas, asi que esto evita un despliegue en rojo.
# Contra la base compartida no hace nada mientras alembic_version_tracking
# ya esté en la cabeza (6b5d49c8a514).
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]

# ---- variante `completo`: API + frontend propio ----
FROM base AS completo
COPY --from=frontend-build /frontend/dist ./frontend/dist

# ---- variante `api` (por defecto): solo la API ----
FROM base AS api
