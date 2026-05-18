# Stage 1: Build
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies (e.g., for psycopg2)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies to a temporary directory
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies for psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed dependencies from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY backend/ ./backend/
# Copy the .env file if it exists (though AWS App Runner should use env vars)
# COPY .env . 

# Expose port 8080
EXPOSE 8080

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Explicitly bind to 0.0.0.0:8080 for AWS App Runner
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8080"]
