import os
import json
import time
from confluent_kafka import Consumer

KAFKA_SERVER = os.environ.get('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')
TOPIC = 'nuam_events'

def send_email_simulation(broker, amount):
    print(f"\n[📧 EMAIL SERVICE] ----------------------------------------")
    print(f"To: contacto@{broker.lower()}.cl")
    print(f"Subject: Alerta de Movimiento Tributario NUAM")
    print(f"Body: Estimado {broker}, se ha registrado un movimiento por ${amount}.")
    print(f"----------------------------------------------------------\n")

def start():
    print(f"📡 Notifier Service conectando a {KAFKA_SERVER}...")
    conf = {
        'bootstrap.servers': KAFKA_SERVER,
        'group.id': 'nuam_notifier_group', # Grupo distinto para que lea copia del mensaje
        'auto.offset.reset': 'earliest'
    }
    consumer = Consumer(conf)
    consumer.subscribe([TOPIC])
    
    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None: continue
            if msg.error():
                print(f"Error: {msg.error()}")
                continue
                
            data = json.loads(msg.value().decode('utf-8'))
            # Simulamos reacción al evento
            send_email_simulation(data.get('broker_code', 'UNKNOWN'), data.get('amount', 0))
            
    except KeyboardInterrupt:
        pass
    finally:
        consumer.close()

if __name__ == "__main__":
    start()