# Stage 1: Builder
FROM python:3.12-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# Stage 2: Runtime
FROM python:3.12-slim AS runtime

# Create non-root user
RUN groupadd -r django && useradd -r -g django django

# Install runtime dependencies (e.g., libpq for psycopg2 if not using binary, though binary is used, it's good practice)
RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq5 curl cron && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy wheels from builder and install
COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .
RUN pip install --no-cache /wheels/* && rm -rf /wheels

# Copy application source
COPY --chown=django:django . .

# Set permissions for cron if used, though scheduler will run separately
RUN chmod +x /app/docker/scheduler/entrypoint.sh

USER django

# Healthcheck for web container
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

EXPOSE 8000

# Default command for the web service
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
