# ── Voxmetriks — Frontend (Dockerfile) ───────────────────────────────────────
# Build Angular (producción) y sirve la SPA con nginx + proxy /api → backend.
#
#   docker build -t voxmetrik-frontend ./frontend

# ════════════════════════════════════════════════════════════════════════════
# Stage 1 — Build Angular
# ════════════════════════════════════════════════════════════════════════════
FROM node:20-alpine AS build

WORKDIR /app

# Instalar dependencias con cache de capa (solo package*.json primero)
COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# ════════════════════════════════════════════════════════════════════════════
# Stage 2 — nginx
# ════════════════════════════════════════════════════════════════════════════
FROM nginx:1.27-alpine AS runtime

# Angular @angular/build:application genera la SPA en dist/app/browser
COPY --from=build /app/dist/app/browser /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
