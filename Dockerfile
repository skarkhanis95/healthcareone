FROM node:20-slim AS web
WORKDIR /web
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
ENV VITE_API_BASE_URL=/api/v1
RUN npm run build

FROM python:3.11-slim
WORKDIR /app
COPY backend/requirements.txt backend/requirements-ai.txt backend/
RUN pip install --no-cache-dir -r backend/requirements-ai.txt
COPY backend/app backend/app
COPY --from=web /web/dist frontend/dist
ENV HEALTHCAREONE_DB=/tmp/healthcareone.db
WORKDIR /app/backend
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}"]
