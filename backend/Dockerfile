FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application
COPY backend/ /app/backend/
COPY pytest.ini /app/pytest.ini

# Create data directory
RUN mkdir -p /app/backend/data

EXPOSE 8000

ENV HOST=0.0.0.0
ENV PORT=8000
ENV PYTHONPATH=/app

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/api/health || exit 1

CMD ["python", "backend/run.py"]
