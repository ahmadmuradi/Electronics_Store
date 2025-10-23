# Enhanced Electronics Store Inventory System - Backend Dockerfile

FROM python:3.14-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        libpq-dev \
        gcc \
        g++ \
        git \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements_core.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements_core.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p models backups logs

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser \
    && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Expose port
EXPOSE 8001

# Default command
CMD ["python", "-m", "uvicorn", "enhanced_main:app", "--host", "0.0.0.0", "--port", "8001"]
