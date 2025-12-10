# srv-kafka-consumer/Dockerfile
FROM python:3.11-slim

# Evita que Python genere archivos .pyc y buffer de salida
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instalar dependencias del sistema necesarias para compilar psycopg2 (Postgres driver)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN pip install django-extension

COPY . .

# Comando por defecto (ejecutará el script que crearemos en el siguiente paso)
CMD ["python", "consumer.py"]