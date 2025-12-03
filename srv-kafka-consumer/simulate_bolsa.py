import json
import time
import os
from confluent_kafka import Producer

# --- H0P3 FIX: Detección automática del entorno ---
# Si estamos en Docker, usa la variable de entorno (kafka:9092).
# Si estamos en local, usa localhost.
bootstrap_servers = os.environ.get('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')

print(f"🔧 Configurando Producer hacia: {bootstrap_servers}")

conf = {'bootstrap.servers': bootstrap_servers}
producer = Producer(conf)
topic = 'nuam_events'

# Datos de prueba
events = [
    {"broker_code": "DEFAULT", "instrument": "FALABELLA", "date": "2025-05-10", "year": 2025, "amount": 5000.00},
    {"broker_code": "DEFAULT", "instrument": "CENCOSUD", "date": "2025-06-15", "year": 2025, "amount": 1250.50},
    {"broker_code": "DEFAULT", "instrument": "COPEC", "date": "2025-07-20", "year": 2025, "amount": 9999.99},
]

def delivery_report(err, msg):
    if err is not None:
        print(f'❌ Fallo en entrega: {err}')
    else:
        print(f'🚀 Mensaje enviado a {msg.topic()} [{msg.partition()}]')

print("--- INICIANDO SIMULACIÓN DE BOLSA ---")

for event in events:
    payload = json.dumps(event)
    # Codificar a bytes antes de enviar
    producer.produce(topic, payload.encode('utf-8'), callback=delivery_report)
    producer.poll(0)
    time.sleep(1)

producer.flush()
print("--- SIMULACIÓN FINALIZADA ---")