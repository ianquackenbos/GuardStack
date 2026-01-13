# Build stage
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir build && \
    pip wheel --no-cache-dir --wheel-dir /app/wheels .

# Runtime stage
FROM python:3.11-slim as runtime

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r guardstack && useradd -r -g guardstack guardstack

# Copy wheels and install
COPY --from=builder /app/wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels

# Copy application code
COPY src/ /app/src/
COPY alembic/ /app/alembic/
COPY alembic.ini /app/

# Set ownership
RUN chown -R guardstack:guardstack /app

# Switch to non-root user
USER guardstack

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app:$PATH"

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Default command
CMD ["uvicorn", "guardstack.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
