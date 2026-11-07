# Dockerfile
FROM python:3.12-slim

# Python environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# Copy dependencies first (Docker cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY app/ app/

# Create a non-root user (security)
RUN adduser --disabled-password --gecos "" appuser
USER appuser

EXPOSE 8000

# Health check — uses Python (no extra package needed on python:3.12-slim).
# If you prefer curl, install it explicitly with:
#   RUN apt-get update && apt-get install -y --no-install-recommends curl \
#       && rm -rf /var/lib/apt/lists/*
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=3)" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
