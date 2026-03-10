FROM node:20-alpine AS frontend_builder

WORKDIR /frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build


FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8 \
    PYTHONFAULTHANDLER=1 \
    HOST=0.0.0.0 \
    PORT=18080

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq5 \
    nginx \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY scripts/docker/start.sh /app/scripts/docker/start.sh
RUN chmod +x /app/scripts/docker/start.sh

COPY --from=frontend_builder /frontend/dist /usr/share/nginx/html

RUN mkdir -p /app/data /app/logs /app/instances

EXPOSE 16788

HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:16788/health || exit 1

CMD ["/app/scripts/docker/start.sh"]
