# syntax=docker/dockerfile:1

# Stage 1: Build frontend
FROM node:20-alpine AS frontend-build
WORKDIR /build/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Production image
FROM python:3.11-slim
WORKDIR /app

# Install Python package
COPY backend/pyproject.toml ./
RUN pip install --no-cache-dir -e "."

# Copy backend code
COPY backend/service/ ./service/

# Copy built frontend
COPY --from=frontend-build /build/frontend/dist ./frontend/dist

ENV STATIC_DIR=/app/frontend/dist \
    DATA_DIR=/app/data \
    LOG_DIR=/app/logs \
    DB_PATH=/app/app.db \
    PYTHONUNBUFFERED=1

VOLUME ["/app/data", "/app/logs"]

EXPOSE 8000

CMD ["uvicorn", "service.main:app", "--host", "0.0.0.0", "--port", "8000"]
