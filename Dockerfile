# Multi-stage Dockerfile for FastAPI application

# ================================
# Builder Stage
# ================================
FROM python:3.9-slim as builder

# Set working directory
WORKDIR /app

# Install system dependencies needed for building Python packages
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -r appuser && useradd -m -r -g appuser appuser

# Copy application code
COPY ./api ./api

# Change ownership of the application directory
RUN chown -R appuser:appuser /app

WORKDIR /app/api

# Switch to non-root user
USER appuser

# Install Python dependencies
RUN pip install --user --no-cache-dir --user -r requirements.txt

# Set PATH to include user-installed packages
ENV PATH=/home/appuser/.local/bin:$PATH

# Expose port 8000
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

WORKDIR /app

# Set the command to run the application
CMD ["uvicorn", "api.app.main:app", "--host", "0.0.0.0", "--port", "8000"]