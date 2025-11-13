# --- Etapa 1: Builder ---
FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- Etapa 2: Producción ---
FROM python:3.11-slim AS production

WORKDIR /app

RUN addgroup --system app && adduser --system --group app

COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin/gunicorn /usr/local/bin/gunicorn

COPY . .

ENV PYTHONPATH=/app:$PYTHONPATH

# CORRECCIÓN: Ejecutar collectstatic AQUÍ, como root,
# y apuntar al volumen que definiremos en docker-compose.
RUN mkdir -p /app/static
RUN python brokernuam/manage.py collectstatic --noinput

# CORRECCIÓN: Dar permisos al usuario 'app' sobre la app y los estáticos
RUN chown -R app:app /app

USER app

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "brokernuam.wsgi:application"]