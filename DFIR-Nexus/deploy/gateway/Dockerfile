# Gateway del stack de Nexus: compila el frontend único y lo sirve junto
# con el reverse proxy hacia los cinco backends (ver nginx.conf). Contexto
# de build: la raíz del repo (ver ../docker-compose.yml), porque necesita
# frontend/.

# ---- Etapa 1: build del frontend (React + Vite) ----
# El repo usa npm workspaces (frontend/ y scam-shield/frontend/, ver
# package.json de la raíz) — el package.json de cada workspace declarado
# hace falta para que npm resuelva la estructura completa, aunque aquí
# solo construyamos frontend/.
FROM node:22-slim AS frontend-build
WORKDIR /repo

# Rutas relativas al propio origen (mismo dominio que este gateway) — el
# navegador nunca habla directamente con un backend, así que no hace
# falta bakear ningún dominio público aquí. Ver nginx.conf para el
# prefijo -> backend real.
ENV VITE_API_BASE_URL=/api/cases \
    VITE_OSINT_API_URL=/api/osint \
    VITE_TRACKING_API_URL=/api/tracking \
    VITE_TIMELINE_API_URL=/api/timeline \
    VITE_REPORTS_API_URL=/api/reports

# Sin el lockfile a propósito (npm/cli#4828): el del repo se generó en un
# dev Windows/ARM64 y, aunque se instale con `npm install` (no `ci`), npm
# no siempre le añade encima la variante que falta para otra plataforma —
# el binario nativo de rolldown (Vite 8) para linux-arm64-gnu (este
# contenedor, un Pi de 64 bits) se queda sin resolver. Sin lockfile, npm
# resuelve de cero para la plataforma real del contenedor.
COPY package.json ./
COPY frontend/package.json frontend/package.json
COPY scam-shield/frontend/package.json scam-shield/frontend/package.json
RUN npm install
COPY frontend/ frontend/
RUN npm run build --workspace=frontend

# ---- Etapa 2: nginx sirviendo el build + proxy a los backends ----
FROM nginx:alpine
COPY deploy/gateway/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=frontend-build /repo/frontend/dist /usr/share/nginx/html
EXPOSE 80
