# ── Stage 1: Build React Frontend ─────────────────────────────────────────────
FROM node:20-slim AS frontend-builder

WORKDIR /app/frontend

COPY dashboard/frontend/package*.json ./
RUN npm ci

COPY dashboard/frontend/ ./
RUN npm run build

# ── Stage 2: Python Backend ────────────────────────────────────────────────────
FROM python:3.12-slim

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY api/ ./api/
COPY engine/ ./engine/
COPY config/ ./config/
COPY .env .env

# Copy built React frontend from Stage 1
COPY --from=frontend-builder /app/frontend/dist ./dashboard/frontend/dist

# Expose port
EXPOSE 8000

# Start FastAPI
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]