# Built from the REPOSITORY ROOT, not from api/:
#   docker build -f api/Dockerfile .
# The taxonomy lives outside api/ and has to be baked into the image — compose can mount
# it as a volume, but Fly and Render cannot, and the app refuses to start without it.
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 \
    TAXONOMY_PATH=/taxonomy/patterns.yaml

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential curl \
    && rm -rf /var/lib/apt/lists/*

COPY api/pyproject.toml api/alembic.ini ./
COPY api/weakspot ./weakspot
RUN pip install --no-cache-dir -e .

COPY taxonomy /taxonomy

COPY api/docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --start-period=20s --retries=5 \
    CMD curl -fsS http://localhost:8000/healthz || exit 1

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["uvicorn", "weakspot.main:app", "--host", "0.0.0.0", "--port", "8000"]
