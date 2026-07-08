# Production-ready Dockerfile
# - Small base (`python:3.11-slim`)
# - Non-root user
# - Exposes port 8080
# - Uses `gunicorn` for production

FROM python:3.11-slim

# Install system dependencies required to build some Python packages if needed
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Create a non-root user with a predictable uid/gid
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid 1000 --create-home --home-dir /home/appuser appuser

# Copy requirements and install first (leverages Docker cache)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . /app

# Ensure files are owned by non-root user
RUN chown -R appuser:appgroup /app

USER appuser

# Application listens on 8080 (HTTP)
EXPOSE 8080

# Run with gunicorn: small number of workers suitable for small app
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app", "--workers", "2", "--threads", "2"]
