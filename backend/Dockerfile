# =============================================================================
# BACKEND DOCKERFILE (Multi-stage)
# =============================================================================
# Development: docker build --target development -t besiktningsapp-backend:dev .
# Production: docker build --target production -t besiktningsapp-backend:prod .

# -----------------------------------------------------------------------------
# Base Stage
# -----------------------------------------------------------------------------
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libpq-dev \
    libffi-dev \
    libssl-dev \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set working directory
WORKDIR /app

# -----------------------------------------------------------------------------
# Dependencies Stage
# -----------------------------------------------------------------------------
FROM base as dependencies

# Copy requirements
COPY requirements.txt requirements-dev.txt ./

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

# -----------------------------------------------------------------------------
# Development Stage
# -----------------------------------------------------------------------------
FROM dependencies as development

# Install development dependencies
RUN pip install -r requirements-dev.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/storage/images /app/storage/pdfs /var/log/besiktningsapp && \
    chown -R appuser:appuser /app /var/log/besiktningsapp

# Switch to app user
USER appuser

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Default command (can be overridden in docker-compose)
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]

# -----------------------------------------------------------------------------
# Production Build Stage
# -----------------------------------------------------------------------------
FROM dependencies as production-build

# Copy application code
COPY . .

# Remove development files
RUN rm -rf tests/ .pytest_cache/ .mypy_cache/ .coverage htmlcov/

# -----------------------------------------------------------------------------
# Production Stage
# -----------------------------------------------------------------------------
FROM python:3.11-slim as production

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    FLASK_ENV=production

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set working directory
WORKDIR /app

# Copy Python dependencies from dependencies stage
COPY --from=dependencies /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=dependencies /usr/local/bin /usr/local/bin

# Copy application from production-build stage
COPY --from=production-build --chown=appuser:appuser /app /app

# Create necessary directories
RUN mkdir -p /app/storage/images /app/storage/pdfs /var/log/besiktningsapp && \
    chown -R appuser:appuser /app /var/log/besiktningsapp

# Switch to app user
USER appuser

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Production command (Gunicorn)
CMD ["gunicorn", "--bind", "0.0.0.0:5000", \
     "--workers", "4", \
     "--threads", "2", \
     "--timeout", "60", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--log-level", "info", \
     "app.main:create_app()"]
