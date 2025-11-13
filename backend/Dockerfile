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

# CORRECCIÓN: El PYTHONPATH debe ser /app para que python encuentre 'brokernuam'
ENV PYTHONPATH=/app:$PYTHONPATH

# CORRECCIÓN: La ruta a manage.py es 'brokernuam/manage.py'
RUN python brokernuam/manage.py collectstatic --noinput

USER app

# Este CMD se usará si eliminas 'command:' del docker-compose.yml
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "brokernuam.wsgi:application"]