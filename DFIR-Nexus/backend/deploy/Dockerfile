# Casos (Módulo 1): backend puro, sin frontend propio — en el stack
# conjunto de Nexus (ver deploy/docker-compose.yml en la raíz del repo)
# el frontend único vive en un contenedor aparte (deploy/gateway) que
# proxya /api/cases/* hacia este servicio.
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY alembic.ini .
COPY alembic ./alembic

# Mismo endurecimiento que el resto de backends de Nexus (ver
# sharingan/deploy/Dockerfile): sin esto el proceso corre como root.
RUN useradd --create-home --uid 10001 nexus && chown -R nexus:nexus /app
USER nexus

EXPOSE 8000

# Aplica las migraciones pendientes (Alembic) antes de arrancar — así un
# despliegue nuevo siempre arranca con el esquema al día, sin paso manual.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
