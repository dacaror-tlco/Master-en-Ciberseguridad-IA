# Timeline (Módulo 4): backend puro, sin frontend propio — su UI vive
# integrada en el frontend único de Nexus (ver deploy/docker-compose.yml
# en la raíz del repo), que le habla vía /api/timeline/*.
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

CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
