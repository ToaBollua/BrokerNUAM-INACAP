FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /app
RUN pip install confluent-kafka
COPY main.py .
CMD ["python", "main.py"]