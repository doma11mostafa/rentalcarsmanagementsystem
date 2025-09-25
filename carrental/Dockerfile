# Multi-stage Dockerfile for Django (server only)
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libjpeg-dev zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements (server only; excludes PyQt)
COPY requirements-server.txt ./
RUN pip install -r requirements-server.txt

# Copy project
COPY . /app

# Create non-root user
RUN useradd -m django
RUN mkdir -p /app/staticfiles /app/media && chown -R django:django /app

USER django

EXPOSE 8000

# Default command: run gunicorn
CMD ["bash", "-lc", "python manage.py migrate && python manage.py collectstatic --noinput && gunicorn carrental.wsgi:application --bind 0.0.0.0:8000"]
