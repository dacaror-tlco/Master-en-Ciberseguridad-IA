# Imagen multiarquitectura: la misma sirve para amd64 y para el arm64 de una
# Raspberry Pi. Ojo: exige Raspberry Pi OS de **64 bits**. En 32 bits (armv7l)
# no hay ruedas precompiladas de lxml, pillow, uvloop ni httptools, y pip
# intentaría compilarlas en el propio Pi.
#
# Se construye con la RAÍZ DEL REPO como contexto (ver deploy/docker-compose.yml
# y sharingan/deploy/docker-compose.yml), y la imagen reproduce su estructura
# en /repo. Dos motivos:
#
# * El asistente lee el expediente a través del servidor MCP (`mcp-server/`),
#   que se lanza como proceso hijo dentro de este mismo contenedor. Tiene que
#   estar aquí, y en `../mcp-server` respecto al directorio de trabajo.
# * La base de conocimiento del asistente (chat/conocimiento.py) lee `docs/` y
#   los README subiendo desde su propio fichero hasta la raíz del repo. Con la
#   imagen anterior, que copiaba solo `sharingan/` en /app, esa raíz era `/`: no
#   encontraba nada, y como un fichero ausente se salta en silencio, el
#   asistente del despliegue respondía sin documentación sin que nada fallara.
#
# Se copia carpeta a carpeta, nunca la raíz entera: así ningún `.env` local ni
# `deploy/.env` puede acabar dentro de la imagen, se use o no BuildKit.
FROM python:3.12-slim

WORKDIR /repo/sharingan

COPY sharingan/requirements.txt ./requirements.txt
COPY mcp-server/requirements.txt /tmp/requirements-mcp.txt
RUN pip install --no-cache-dir -r requirements.txt -r /tmp/requirements-mcp.txt

COPY sharingan/app ./app
COPY sharingan/alembic ./alembic
COPY sharingan/alembic.ini sharingan/README.md ./
COPY mcp-server/app /repo/mcp-server/app
COPY docs/CONTRATOS.md docs/INTEGRACION_Y_DESPLIEGUE.md /repo/docs/
COPY CLAUDE.md README.md /repo/
# backend/README.md no existe todavía: conocimiento.py lo tiene en su lista y lo
# salta. Si alguien lo escribe, hay que añadirlo aquí.
COPY scam-shield/README.md /repo/scam-shield/
COPY track-inc/README.md /repo/track-inc/
COPY timeline/README.md /repo/timeline/

# Sin esto el proceso corre como root. En un equipo expuesto a un dominio, una
# vulnerabilidad en cualquier dependencia se ejecutaría con todos los permisos
# del contenedor. El volumen de informes tiene que pertenecerle.
RUN useradd --create-home --uid 10001 nexus \
    && mkdir -p /repo/sharingan/storage \
    && chown -R nexus:nexus /repo
USER nexus

# Aplica las migraciones pendientes (Alembic) antes de arrancar — así un
# despliegue nuevo siempre arranca con el esquema al día, sin paso manual
# (mismo patrón que el resto de backends de Nexus, ver deploy/docker-compose.yml
# en la raíz del repo).
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
