# ---- Etapa 1: build del frontend (React + Vite) ----
FROM node:22-slim AS frontend-build
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ---- Etapa 2: backend (FastAPI) + frontend ya compilado ----
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY alembic.ini .
COPY alembic ./alembic
COPY --from=frontend-build /frontend/dist ./frontend/dist

EXPOSE 8000

# Aplica las migraciones pendientes (Alembic) antes de arrancar — así un
# despliegue nuevo siempre arranca con el esquema al día, sin paso manual.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
