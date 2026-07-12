# Production-ready Dockerfile
# - Small base image
# - Non-root user
# - Exposes port 8080
# - Uses gunicorn for production

FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

WORKDIR /app

RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid 1000 --create-home --home-dir /home/appuser appuser

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt && \
    rm -rf /root/.cache/pip

COPY app.py ./
COPY tests ./tests
COPY pytest.ini ./
COPY sonar-project.properties ./
RUN chown -R appuser:appgroup /app

USER appuser

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/health').read()" || exit 1

CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-8080} app:app --workers 2 --threads 2"]
