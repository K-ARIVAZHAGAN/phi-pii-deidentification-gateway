# Production Dockerfile for HIPAA PHI/PII De-Identification Gateway
FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEID_HOST=0.0.0.0 \
    DEID_PORT=8000

# Working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt pyproject.toml /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code and models
COPY deid_gateway /app/deid_gateway
COPY saved_models /app/saved_models
COPY README.md /app/

# Install gateway package in editable mode
RUN pip install --no-cache-dir -e .

# Expose FastAPI REST service port
EXPOSE 8000

# Health check probe
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default startup command
CMD ["uvicorn", "deid_gateway.api.server:app", "--host", "0.0.0.0", "--port", "8000"]
